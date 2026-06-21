const state = {
  pair: "BTC/EURBT",
  peers: [],
  orders: [],
  trades: [],
  wallet: null,
  basket: [
    { name: "EUR anchor", weight: 0.38, value: 100.0, color: "#55c5df" },
    { name: "Trade FX", weight: 0.24, value: 99.4, color: "#a58cff" },
    { name: "Crypto trade", weight: 0.18, value: 103.2, color: "#39c980" },
    { name: "Commodities", weight: 0.20, value: 101.8, color: "#e8b74d" },
  ],
};

const encoder = new TextEncoder();
const SCALE = 100000000n;
const MAX_ATOMS = 888888n * SCALE;

function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

async function sha256Hex(value) {
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(typeof value === "string" ? value : canonical(value)));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

function b64(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes)));
}

async function exportPublicKey(key) {
  const raw = await crypto.subtle.exportKey("raw", key);
  return b64(raw);
}

async function newWallet(label, trust, note, actorType = "person") {
  const keys = await crypto.subtle.generateKey(
    { name: "ECDSA", namedCurve: "P-256" },
    true,
    ["sign", "verify"],
  );
  const publicKey = await exportPublicKey(keys.publicKey);
  const peer = `peer_${(await sha256Hex(publicKey)).slice(0, 18)}`;
  return { actorType, label, trust, note, peer, publicKey, keys };
}

async function signPayload(wallet, payload) {
  const signature = await crypto.subtle.sign(
    { name: "ECDSA", hash: "SHA-256" },
    wallet.keys.privateKey,
    encoder.encode(canonical(payload)),
  );
  return b64(signature);
}

async function verifyPayload(publicKeyText, payload, signatureText) {
  const raw = Uint8Array.from(atob(publicKeyText), (char) => char.charCodeAt(0));
  const signature = Uint8Array.from(atob(signatureText), (char) => char.charCodeAt(0));
  const publicKey = await crypto.subtle.importKey(
    "raw",
    raw,
    { name: "ECDSA", namedCurve: "P-256" },
    false,
    ["verify"],
  );
  return crypto.subtle.verify(
    { name: "ECDSA", hash: "SHA-256" },
    publicKey,
    signature,
    encoder.encode(canonical(payload)),
  );
}

function nowSeconds() {
  return Math.floor(Date.now() / 1000);
}

function fmt(value, digits = 2) {
  return Number(value).toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function parseAtoms(value) {
  const text = String(value).trim().replace(",", ".");
  if (!/^\d+(\.\d{0,8})?$/.test(text)) throw new Error("invalid atom amount");
  const [whole, frac = ""] = text.split(".");
  const atoms = BigInt(whole) * SCALE + BigInt(frac.padEnd(8, "0"));
  if (atoms <= 0n || atoms > MAX_ATOMS) throw new Error("amount out of range");
  return atoms;
}

function formatAtoms(atoms) {
  const value = BigInt(atoms);
  const whole = value / SCALE;
  const frac = value % SCALE;
  return `${whole}.${String(frac).padStart(8, "0")}`;
}

function basketIndex() {
  return state.basket.reduce((sum, item) => sum + item.weight * item.value, 0);
}

async function makeOrder(wallet, side, price, quantity, trustMin, nonce) {
  const payload = {
    created_at: nowSeconds(),
    expires_at: nowSeconds() + 3600,
    maker: wallet.peer,
    min_quantity_atoms: String(parseAtoms("0.005")),
    nonce,
    pair: state.pair,
    price_atoms: String(parseAtoms(price)),
    quantity_atoms: String(parseAtoms(quantity)),
    side,
    trust_min: Number(trustMin),
  };
  const signature = await signPayload(wallet, payload);
  const id = `ord_${(await sha256Hex({ payload, signature })).slice(0, 24)}`;
  return {
    id,
    payload,
    publicKey: wallet.publicKey,
    signature,
    remainingAtoms: BigInt(payload.quantity_atoms),
    status: "open",
  };
}

function peerTrust(peer) {
  const found = state.peers.find((item) => item.peer === peer);
  return found ? found.trust : 0;
}

async function verifyOrder(order) {
  const peerHash = `peer_${(await sha256Hex(order.publicKey)).slice(0, 18)}`;
  return peerHash === order.payload.maker && verifyPayload(order.publicKey, order.payload, order.signature);
}

function matchOrders() {
  state.trades = [];
  for (const order of state.orders) {
    order.remainingAtoms = BigInt(order.payload.quantity_atoms);
    order.status = "open";
  }

  while (true) {
    const bids = state.orders
      .filter((order) => order.status === "open" && order.payload.side === "buy")
      .sort((a, b) => Number(BigInt(b.payload.price_atoms) - BigInt(a.payload.price_atoms)) || a.payload.created_at - b.payload.created_at || a.id.localeCompare(b.id));
    const asks = state.orders
      .filter((order) => order.status === "open" && order.payload.side === "sell")
      .sort((a, b) => Number(BigInt(a.payload.price_atoms) - BigInt(b.payload.price_atoms)) || a.payload.created_at - b.payload.created_at || a.id.localeCompare(b.id));

    let matched = null;
    for (const bid of bids) {
      for (const ask of asks) {
        const quantityAtoms = bid.remainingAtoms < ask.remainingAtoms ? bid.remainingAtoms : ask.remainingAtoms;
        const trustOk = peerTrust(ask.payload.maker) >= bid.payload.trust_min && peerTrust(bid.payload.maker) >= ask.payload.trust_min;
        if (BigInt(bid.payload.price_atoms) >= BigInt(ask.payload.price_atoms) && trustOk) {
          matched = { bid, ask, quantityAtoms };
          break;
        }
      }
      if (matched) break;
    }

    if (!matched) break;
    const { bid, ask, quantityAtoms } = matched;
    const resting = bid.payload.created_at <= ask.payload.created_at ? bid : ask;
    const priceAtoms = BigInt(resting.payload.price_atoms);
    bid.remainingAtoms -= quantityAtoms;
    ask.remainingAtoms -= quantityAtoms;
    if (bid.remainingAtoms <= 0n) bid.status = "filled";
    if (ask.remainingAtoms <= 0n) ask.status = "filled";
    const quoteAtoms = (priceAtoms * quantityAtoms + SCALE - 1n) / SCALE;
    state.trades.push({
      id: `trd_${state.trades.length + 1}_${bid.id.slice(-4)}${ask.id.slice(-4)}`,
      priceAtoms,
      quantityAtoms,
      quoteAtoms,
      bid,
      ask,
      status: "settlement planned",
    });
  }
}

function drawMarket() {
  const canvas = document.getElementById("marketCanvas");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#151922";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "#2b3340";
  ctx.lineWidth = 1;
  for (let i = 1; i < 6; i += 1) {
    const y = (height / 6) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }

  const mid = Number(document.getElementById("midPrice").dataset.value || 61000);
  const points = Array.from({ length: 90 }, (_, index) => {
    const drift = Math.sin(index / 8) * 160 + Math.cos(index / 13) * 90;
    const basketPull = (basketIndex() - 100) * 22;
    return mid + drift + basketPull;
  });
  const min = Math.min(...points) - 120;
  const max = Math.max(...points) + 120;
  ctx.strokeStyle = "#55c5df";
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach((point, index) => {
    const x = (width / (points.length - 1)) * index;
    const y = height - ((point - min) / (max - min)) * (height - 54) - 26;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  const asks = state.orders.filter((order) => order.payload.side === "sell" && order.status === "open").slice(0, 12);
  const bids = state.orders.filter((order) => order.payload.side === "buy" && order.status === "open").slice(0, 12);
  const barWidth = width / 32;
  bids.forEach((order, index) => {
    const h = Math.max(14, Number(order.remainingAtoms) / 65000);
    ctx.fillStyle = "rgba(57, 201, 128, 0.65)";
    ctx.fillRect(width / 2 - (index + 1) * barWidth, height - h - 18, barWidth - 5, h);
  });
  asks.forEach((order, index) => {
    const h = Math.max(14, Number(order.remainingAtoms) / 65000);
    ctx.fillStyle = "rgba(255, 109, 101, 0.65)";
    ctx.fillRect(width / 2 + index * barWidth + 5, height - h - 18, barWidth - 5, h);
  });

  ctx.fillStyle = "#eef3f8";
  ctx.font = "20px system-ui, sans-serif";
  ctx.fillText(`EURBT basket ${fmt(basketIndex(), 2)}`, 24, 34);
  ctx.fillStyle = "#a8b3c2";
  ctx.font = "14px system-ui, sans-serif";
  ctx.fillText("signed local order flow", 24, 58);
}

function renderBasket() {
  const node = document.getElementById("basketGrid");
  node.innerHTML = state.basket.map((item) => `
    <div class="basket-card" style="border-color:${item.color}">
      <span>${item.name} · ${(item.weight * 100).toFixed(0)}%</span>
      <strong>${fmt(item.value, 2)}</strong>
    </div>
  `).join("");
}

function renderTables() {
  const bids = state.orders
    .filter((order) => order.payload.side === "buy" && order.status === "open")
    .sort((a, b) => Number(BigInt(b.payload.price_atoms) - BigInt(a.payload.price_atoms)))
    .slice(0, 8);
  const asks = state.orders
    .filter((order) => order.payload.side === "sell" && order.status === "open")
    .sort((a, b) => Number(BigInt(a.payload.price_atoms) - BigInt(b.payload.price_atoms)))
    .slice(0, 8);

  document.getElementById("bidsBody").innerHTML = bids.map((order) => `
    <tr><td class="price-buy">${formatAtoms(order.payload.price_atoms)}</td><td>${formatAtoms(order.remainingAtoms)}</td><td>${order.payload.trust_min}</td></tr>
  `).join("");
  document.getElementById("asksBody").innerHTML = asks.map((order) => `
    <tr><td class="price-sell">${formatAtoms(order.payload.price_atoms)}</td><td>${formatAtoms(order.remainingAtoms)}</td><td>${order.payload.trust_min}</td></tr>
  `).join("");
  document.getElementById("bookCount").textContent = `${bids.length + asks.length} orders`;

  document.getElementById("tradesBody").innerHTML = state.trades.map((trade) => `
    <tr><td>${formatAtoms(trade.priceAtoms)}</td><td>${formatAtoms(trade.quantityAtoms)}</td><td>${formatAtoms(trade.quoteAtoms)}</td><td>${trade.status}</td></tr>
  `).join("");
  document.getElementById("tradeCount").textContent = `${state.trades.length} fills`;
}

function renderTrust() {
  document.getElementById("peerCount").textContent = `${state.peers.length} peers`;
  document.getElementById("trustList").innerHTML = state.peers.map((peer) => `
    <article class="trust-card">
      <div class="trust-row"><strong>${peer.label}</strong><span>${peer.actorType}</span></div>
      <div class="trust-row"><span>Trust</span><span>${peer.trust}/100</span></div>
      <div class="meter"><span style="width:${peer.trust}%"></span></div>
      <p>${peer.note}</p>
      <div class="peer-id">${peer.peer}</div>
    </article>
  `).join("");
}

function renderSettlement() {
  const latest = state.trades.at(-1);
  const node = document.getElementById("settlementText");
  if (!latest) {
    node.textContent = "Waiting for a matched trade.";
    return;
  }
  node.textContent = `${latest.ask.payload.maker.slice(0, 13)} locks ${formatAtoms(latest.quantityAtoms)} BTC; ${latest.bid.payload.maker.slice(0, 13)} is instant accepted for ${formatAtoms(latest.quoteAtoms)} EURBT after authorised actor signature.`;
}

function renderTopline() {
  const open = state.orders.filter((order) => order.status === "open");
  const bestBid = Math.max(...open.filter((order) => order.payload.side === "buy").map((order) => Number(BigInt(order.payload.price_atoms)) / 100000000), 0);
  const bestAsk = Math.min(...open.filter((order) => order.payload.side === "sell").map((order) => Number(BigInt(order.payload.price_atoms)) / 100000000), 999999);
  const mid = bestBid && bestAsk < 999999 ? (bestBid + bestAsk) / 2 : 61000;
  const midNode = document.getElementById("midPrice");
  midNode.textContent = fmt(mid, 2);
  midNode.dataset.value = String(mid);
  document.getElementById("basketIndex").textContent = fmt(basketIndex(), 2);
  const minTrust = Math.min(...state.orders.map((order) => Number(order.payload.trust_min)), 0);
  document.getElementById("trustFloor").textContent = `${minTrust}/100`;
}

function render() {
  matchOrders();
  renderTopline();
  renderBasket();
  renderTables();
  renderTrust();
  renderSettlement();
  drawMarket();
}

async function seed() {
  state.peers = [
    await newWallet("Amsterdam person", 82, "Identified person with reserve evidence.", "person"),
    await newWallet("Lisbon agent", 67, "Agent with an identified owner person.", "owned agent"),
    await newWallet("VoteBank DAO", 88, "DAO actor authorised by vBank governance.", "votebank dao"),
  ];
  state.wallet = await newWallet("Browser person", 72, "Local identified session key.", "person");
  state.peers.push(state.wallet);
  document.getElementById("walletBadge").textContent = state.wallet.peer.slice(0, 18);

  const [amsterdam, lisbon, tallinn] = state.peers;
  state.orders = [
    await makeOrder(amsterdam, "sell", 60940, 0.018, 45, "seed-1"),
    await makeOrder(lisbon, "sell", 61080, 0.044, 55, "seed-2"),
    await makeOrder(tallinn, "sell", 61240, 0.026, 40, "seed-3"),
    await makeOrder(lisbon, "buy", 60780, 0.031, 50, "seed-4"),
    await makeOrder(amsterdam, "buy", 60620, 0.025, 55, "seed-5"),
  ];
  render();
}

async function handleSubmit(event) {
  event.preventDefault();
  const side = document.getElementById("sideInput").value;
  const price = Number(document.getElementById("priceInput").value);
  const quantity = Number(document.getElementById("quantityInput").value);
  const trust = Number(document.getElementById("trustInput").value);
  if (!Number.isFinite(price) || price <= 0 || !Number.isFinite(quantity) || quantity <= 0) return;

  const order = await makeOrder(state.wallet, side, price, quantity, trust, `local-${Date.now()}`);
  if (!(await verifyOrder(order))) return;
  state.orders.push(order);
  render();
}

document.getElementById("trustInput").addEventListener("input", (event) => {
  document.getElementById("trustOutput").textContent = event.target.value;
});

document.getElementById("orderForm").addEventListener("submit", handleSubmit);
document.getElementById("seedButton").addEventListener("click", seed);
window.addEventListener("resize", drawMarket);

seed();
