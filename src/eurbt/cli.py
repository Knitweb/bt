"""Command line entrypoint."""

from __future__ import annotations

import argparse
import json

from .actors import Actor, AGENT, PERSON
from .keys import Keypair
from .market import EurbtMarket
from .models import BUY, SELL, Asset, Order, Pair, SignedOrder
from .p2p import Envelope
from .trust import Attestation, SignedAttestation


def build_demo() -> dict[str, object]:
    now = 1_750_000_000
    buyer = Keypair.generate()
    seller = Keypair.generate()
    auditor = Keypair.generate()

    btc = Asset("BTC", "bitcoin", decimals=8)
    eurbt = Asset("EURBT", "ethereum", address="demo:eurbt", decimals=8)
    pair = Pair(btc, eurbt)
    market = EurbtMarket(pair)
    market.register_actor(Actor("person:buyer", PERSON, buyer.peer_id, identified=True))
    market.register_actor(Actor("agent:seller", AGENT, seller.peer_id, owner_person_id="person:seller-owner", identified=True))

    for subject, note in (
        (buyer.peer_id, "buyer has completed small euro settlements before"),
        (seller.peer_id, "seller published recent reserve evidence for BTC liquidity"),
    ):
        attestation = Attestation(
            issuer=auditor.peer_id,
            subject=subject,
            kind="settlement_history",
            score_delta=60,
            issued_at=now,
            expires_at=now + 86_400,
            evidence=f"demo://{subject}",
            note=note,
        )
        signed = SignedAttestation.sign(attestation, auditor)
        envelope = Envelope.sign("attestation", signed.to_dict(), auditor, created_at=now, nonce=f"att-{subject}")
        market.ingest_envelope(envelope, now=now)

    buy_order = Order.from_human(
        maker=buyer.peer_id,
        pair=pair,
        side=BUY,
        price="61000",
        quantity="0.05",
        min_quantity="0.01",
        trust_min=50,
        created_at=now + 1,
        expires_at=now + 3600,
        nonce="buyer-1",
    )
    sell_order = Order.from_human(
        maker=seller.peer_id,
        pair=pair,
        side=SELL,
        price="60950",
        quantity="0.03",
        min_quantity="0.01",
        trust_min=50,
        created_at=now + 2,
        expires_at=now + 3600,
        nonce="seller-1",
    )
    for keypair, order in ((buyer, buy_order), (seller, sell_order)):
        signed = SignedOrder.sign(order, keypair)
        envelope = Envelope.sign("order", signed.to_dict(), keypair, created_at=order.created_at, nonce=order.nonce)
        market.ingest_envelope(envelope, now=now)

    trades = market.match(now=now + 3)
    plans = [market.settlement_plan(trade).to_dict() for trade in trades]
    return {
        "pair": pair.symbol,
        "trades": [trade.to_dict() for trade in trades],
        "settlement_plans": plans,
        "buyer_trust": market.explain_peer(buyer.peer_id, now=now + 3),
        "seller_trust": market.explain_peer(seller.peer_id, now=now + 3),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="eurbt")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="run a local signed-order DEX demo")
    args = parser.parse_args(argv)
    if args.command == "demo":
        print(json.dumps(build_demo(), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
