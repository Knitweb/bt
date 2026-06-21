"""Build the DEX top-100 P2P/serverless research artifact.

Usage:
    python scripts/build_dex_research.py /path/to/defillama_dexs.json
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


SNAPSHOT_DATE = date(2026, 6, 21).isoformat()


TRUE_P2P_REFERENCE = {
    "name": "Bisq",
    "rank": None,
    "source": "https://bisq.wiki/Frequently_asked_questions",
    "architecture": "direct_p2p_fiat_crypto",
    "p2p_score": 5,
    "serverless_score": 5,
    "strict_true_p2p": True,
    "note": (
        "Reference model outside the DeFiLlama top-100: desktop clients trade directly "
        "over a P2P network, with no central website or order server."
    ),
}


ONCHAIN_CLOB = {
    "manifest-trade",
    "hyperliquid-spot",
    "dexalot",
    "kuru-clob",
    "deepbookv3-sui",
    "xrpl-dex",
    "lighter-spot",
    "temple",
    "proton-dex",
    "aqua-network",
}

APPCHAIN_ORDERBOOK = {
    "edgex-spot",
    "aster-spot",
    "sodex-spot",
    "flashnet",
}

INTENT_OR_RFH = {
    "angstrom",
    "brine",
    "tokenlon-dex",
}

CROSS_CHAIN = {
    "chainflip",
    "osmosis",
}

AGGREGATOR_OR_ROUTER = {
    "native",
    "jupiterz",
    "woofi",
}

AMM_HINTS = (
    "amm",
    "v2",
    "v3",
    "v4",
    "clmm",
    "-cl",
    "dlmm",
    "damm",
    "slipstream",
    "algebra",
    "lb",
    "curve",
    "balancer",
    "swap",
    "pool",
    "dex",
    "integral",
)

KNOWN_AMM_MODULES = {
    "aerodrome",
    "aquifer",
    "blackhole-cl",
    "bluefin-amm",
    "cetus",
    "ekubo",
    "hydration-dex",
    "liquidcore",
    "metric",
    "pulsex-v1",
    "ref-finance",
    "ramses-hl-cl",
    "ramsesx-poly-cl",
    "solfi",
    "solfi-v2",
    "ston",
    "tessera",
    "topaz-cl",
    "turbos",
}


def classify(protocol: dict[str, Any]) -> dict[str, Any]:
    module = str(protocol.get("module") or "").lower()
    name = str(protocol.get("name") or "").lower()
    chains = [str(chain).lower() for chain in protocol.get("chains") or []]
    methodology = protocol.get("methodology") or {}
    volume_text = str(methodology.get("Volume") or "").lower()

    if module in ONCHAIN_CLOB or "clob" in module or "orderbook" in name:
        return {
            "architecture": "onchain_or_ledger_clob",
            "p2p_score": 3,
            "serverless_score": 4,
            "strict_true_p2p": False,
            "note": "Maker/taker orders settle through ledger or chain state; close to P2P but not direct peer negotiation.",
        }

    if module in APPCHAIN_ORDERBOOK or "off chain" in chains:
        return {
            "architecture": "appchain_or_offchain_orderbook",
            "p2p_score": 1,
            "serverless_score": 1,
            "strict_true_p2p": False,
            "note": "Orderbook-style venue with material API, sequencer, or exchange infrastructure dependency.",
        }

    if module in INTENT_OR_RFH or "rfq" in volume_text or "api" in volume_text:
        return {
            "architecture": "intent_rfq_or_solver",
            "p2p_score": 2,
            "serverless_score": 2,
            "strict_true_p2p": False,
            "note": "Signed intent or RFQ style flow; settlement may be on-chain, but discovery/filling depends on specialized infrastructure.",
        }

    if module in CROSS_CHAIN or "cross-chain" in volume_text:
        return {
            "architecture": "cross_chain_amm_or_appchain",
            "p2p_score": 1,
            "serverless_score": 3,
            "strict_true_p2p": False,
            "note": "Cross-chain liquidity uses validator/vault infrastructure; decentralized, but not direct trader-to-trader P2P.",
        }

    if module in AGGREGATOR_OR_ROUTER:
        return {
            "architecture": "aggregator_or_router",
            "p2p_score": 1,
            "serverless_score": 2,
            "strict_true_p2p": False,
            "note": "Routes to other liquidity; useful UX, but the route service is not a serverless P2P market.",
        }

    if (
        module in KNOWN_AMM_MODULES
        or any(hint in module for hint in AMM_HINTS)
        or any(hint in name for hint in ("swap", "amm", "dex", "clmm", " cl "))
        or "swap event" in volume_text
        or "swap volume" in volume_text
        or "pools" in volume_text
    ):
        return {
            "architecture": "onchain_amm_or_pool",
            "p2p_score": 1,
            "serverless_score": 4,
            "strict_true_p2p": False,
            "note": "Good serverless settlement properties, but traders interact with pools/contracts rather than direct peers.",
        }

    return {
        "architecture": "unverified_dex_like",
        "p2p_score": 1,
        "serverless_score": 2,
        "strict_true_p2p": False,
        "note": "Insufficient public architecture signal in the volume snapshot; treat as not strict P2P until verified.",
    }


def money(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def build(raw_path: Path, repo_root: Path) -> list[dict[str, Any]]:
    raw = json.loads(raw_path.read_text())
    protocols = raw["protocols"]
    dexs = [p for p in protocols if p.get("category") == "Dexs"]
    top = sorted(dexs, key=lambda p: p.get("total24h") or 0, reverse=True)[:100]

    rows: list[dict[str, Any]] = []
    for rank, protocol in enumerate(top, 1):
        result = classify(protocol)
        rows.append(
            {
                "rank": rank,
                "name": protocol.get("name"),
                "slug": protocol.get("slug"),
                "module": protocol.get("module"),
                "chains": protocol.get("chains") or [],
                "total24h_usd": protocol.get("total24h"),
                "total30d_usd": protocol.get("total30d"),
                "methodology_url": protocol.get("methodologyURL"),
                **result,
            }
        )
    return rows


def write_json(rows: list[dict[str, Any]], repo_root: Path) -> None:
    out = {
        "snapshot_date": SNAPSHOT_DATE,
        "source": "https://api.llama.fi/overview/dexs",
        "ranking_basis": "DeFiLlama category=Dexs sorted by total24h descending",
        "score_scale": {
            "p2p_score": "0=no user P2P; 5=direct peer discovery/negotiation/settlement coordination",
            "serverless_score": "0=central service; 5=no privileged host or matching server",
        },
        "rows": rows,
        "strict_true_p2p_reference": TRUE_P2P_REFERENCE,
    }
    target = repo_root / "data" / f"dex_top100_{SNAPSHOT_DATE}.json"
    target.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


def write_markdown(rows: list[dict[str, Any]], repo_root: Path) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["architecture"]] = counts.get(row["architecture"], 0) + 1

    strict = [row for row in rows if row["strict_true_p2p"]]
    closest = sorted(rows, key=lambda row: (row["p2p_score"], row["serverless_score"]), reverse=True)[:12]

    lines = [
        "# Top-100 DEX P2P/Serverless Research",
        "",
        f"Snapshot date: {SNAPSHOT_DATE}",
        "",
        "Source ranking: DeFiLlama DEX overview API, category `Dexs`, sorted by `total24h` descending.",
        "",
        "## Scoring",
        "",
        "- `p2p_score`: 0 means no meaningful user-to-user market; 5 means peers can discover, negotiate, verify, and coordinate settlement directly.",
        "- `serverless_score`: 0 means central service; 5 means no privileged host, order server, or matching server.",
        "- `strict_true_p2p`: only true when both peer discovery/negotiation and market availability avoid privileged services.",
        "",
        "## Result",
        "",
    ]
    if strict:
        lines.append("Strict true-P2P venues inside this top-100 snapshot:")
        for row in strict:
            lines.append(f"- #{row['rank']} {row['name']}")
    else:
        lines.extend(
            [
                "No venue in this DeFiLlama top-100 snapshot qualifies as strict true P2P under the scoring rule.",
                "The closest designs are ledger/orderbook DEXes where maker and taker orders meet in chain state, but those still rely on validators, appchains, indexers, or public APIs rather than direct peer negotiation.",
            ]
        )

    lines.extend(
        [
            "",
            "Reference outside the top-100: Bisq is the cleanest strict-P2P model for fiat/crypto because the user runs software locally, offers propagate over a P2P network, fiat moves directly between traders, and there is no central website/order server.",
            "",
            "## Architecture Counts",
            "",
        ]
    )
    for architecture, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{architecture}`: {count}")

    lines.extend(["", "## Closest Serverless/P2P Designs In The Snapshot", ""])
    lines.append("| Rank | Name | Architecture | P2P | Serverless | Note |")
    lines.append("| ---: | --- | --- | ---: | ---: | --- |")
    for row in closest:
        lines.append(
            f"| {row['rank']} | {row['name']} | `{row['architecture']}` | {row['p2p_score']} | {row['serverless_score']} | {row['note']} |"
        )

    lines.extend(["", "## Full Top-100 Matrix", ""])
    lines.append("| # | DEX | 24h volume | Chains | Architecture | P2P | Serverless | Strict P2P |")
    lines.append("| ---: | --- | ---: | --- | --- | ---: | ---: | --- |")
    for row in rows:
        chains = ", ".join(row["chains"][:3])
        if len(row["chains"]) > 3:
            chains += ", ..."
        strict_text = "yes" if row["strict_true_p2p"] else "no"
        lines.append(
            f"| {row['rank']} | {row['name']} | {money(row['total24h_usd'])} | {chains} | `{row['architecture']}` | {row['p2p_score']} | {row['serverless_score']} | {strict_text} |"
        )

    lines.extend(
        [
            "",
            "## EURBT Design Implications",
            "",
            "1. Start with signed peer orders, not pools. AMMs are useful later, but they are not direct P2P.",
            "2. Make relays replaceable. A relay can cache messages, but it must never be the market authority.",
            "3. Keep matching deterministic and local. Every node should be able to recompute candidate fills.",
            "4. Use trust attestations instead of vague verification badges. Euro markets need reserve, settlement, and dispute context in common language.",
            "5. Separate settlement planning from execution. The core can generate auditable plans before any chain adapter moves funds.",
            "",
            "## Sources",
            "",
            "- DeFiLlama DEX overview API: https://api.llama.fi/overview/dexs",
            "- Bisq FAQ: https://bisq.wiki/Frequently_asked_questions",
            "- Uniswap v4 docs: https://developers.uniswap.org/docs/protocols/v4/overview",
            "- UniswapX docs: https://developers.uniswap.org/docs/liquidity/uniswapx/overview",
            "- 0x Protocol orders docs: https://docs.0xprotocol.org/en/latest/basics/orders.html",
            "- THORChain docs: https://docs.thorchain.org/",
            "- Sui DeepBookV3 docs: https://docs.sui.io/onchain-finance/deepbookv3/deepbook",
            "- XRPL DEX docs: https://xrpl.org/docs/concepts/tokens/decentralized-exchange",
            "",
        ]
    )
    target = repo_root / "docs" / "DEX_RESEARCH.md"
    target.write_text("\n".join(lines))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    repo_root = Path(__file__).resolve().parents[1]
    rows = build(Path(argv[1]), repo_root)
    write_json(rows, repo_root)
    write_markdown(rows, repo_root)
    print(f"wrote {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
