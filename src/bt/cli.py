"""Command line entrypoint."""

from __future__ import annotations

import argparse
import json

from .actors import Actor, AGENT, PERSON, VOTEBANK_DAO
from .basket import bt_genesis_spec
from .chains import BT_ON_PULSE, PLS
from .keys import Keypair
from .market import BtMarket
from .models import BUY, SELL, Asset, Order, Pair, SignedOrder
from .p2p import Envelope
from .readiness import REAL_FUNDS, SIGNED_DRY_RUN
from .trust import Attestation, SignedAttestation


def build_demo() -> dict[str, object]:
    now = 1_750_000_000
    buyer = Keypair.generate()
    seller = Keypair.generate()
    auditor = Keypair.generate()
    votebank = Keypair.generate()

    btc = Asset("BTC", "bitcoin", decimals=8)
    bt = Asset("BT", "ethereum", address="demo:bt", decimals=8)
    pair = Pair(btc, bt)
    market = BtMarket(pair)
    market.register_actor(Actor("person:buyer", PERSON, buyer.peer_id, identified=True))
    market.register_actor(Actor("agent:seller", AGENT, seller.peer_id, owner_person_id="person:seller-owner", identified=True))
    market.register_actor(Actor("dao:vbank", VOTEBANK_DAO, votebank.peer_id, identified=True))
    basket = bt_genesis_spec(votebank, market.actor_registry, now)

    for subject, note in (
        (buyer.peer_id, "buyer has completed small anchor-currency settlements before"),
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
        "basket": basket.spec.to_dict(),
        "basket_explanation": basket.spec.explain(),
        "trades": [trade.to_dict() for trade in trades],
        "settlement_plans": plans,
        "buyer_trust": market.explain_peer(buyer.peer_id, now=now + 3),
        "seller_trust": market.explain_peer(seller.peer_id, now=now + 3),
    }


def build_pls_demo() -> dict[str, object]:
    now = 1_750_000_000
    buyer = Keypair.generate()
    seller = Keypair.generate()
    auditor = Keypair.generate()
    pair = Pair(PLS, BT_ON_PULSE)
    market = BtMarket(pair)
    market.register_actor(Actor("person:pls-buyer", PERSON, buyer.peer_id, identified=True))
    market.register_actor(Actor("person:pls-seller", PERSON, seller.peer_id, identified=True))

    for subject, note in (
        (buyer.peer_id, "buyer has prior PulseChain settlement evidence"),
        (seller.peer_id, "seller controls the PLS offer key and has no open disputes"),
    ):
        attestation = Attestation(
            issuer=auditor.peer_id,
            subject=subject,
            kind="settlement_history",
            score_delta=75,
            issued_at=now,
            expires_at=now + 86_400,
            evidence=f"pls-demo://{subject}",
            note=note,
        )
        market.submit_attestation(SignedAttestation.sign(attestation, auditor), now=now)

    buy_order = Order.from_human(
        maker=buyer.peer_id,
        pair=pair,
        side=BUY,
        price="1.01",
        quantity="500",
        min_quantity="25",
        trust_min=70,
        created_at=now + 1,
        expires_at=now + 3600,
        nonce="pls-buyer-1",
        settlement="pulsechain-escrow",
    )
    sell_order = Order.from_human(
        maker=seller.peer_id,
        pair=pair,
        side=SELL,
        price="1.00",
        quantity="250",
        min_quantity="25",
        trust_min=70,
        created_at=now + 2,
        expires_at=now + 3600,
        nonce="pls-seller-1",
        settlement="pulsechain-escrow",
    )
    for keypair, order in ((buyer, buy_order), (seller, sell_order)):
        market.submit_order(SignedOrder.sign(order, keypair), now=now)

    trades = market.match(now=now + 3)
    plans = [market.settlement_plan(trade).to_dict() for trade in trades]
    dry_run = market.readiness_report(mode=SIGNED_DRY_RUN)
    real_funds = market.readiness_report(mode=REAL_FUNDS)
    return {
        "pair": pair.symbol,
        "dry_run_readiness": dry_run.to_dict(),
        "real_funds_readiness": real_funds.to_dict(),
        "trades": [trade.to_dict() for trade in trades],
        "settlement_plans": plans,
        "buyer_trust": market.explain_peer(buyer.peer_id, now=now + 3),
        "seller_trust": market.explain_peer(seller.peer_id, now=now + 3),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bt")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="run a local signed-order DEX demo")
    sub.add_parser("pls-demo", help="run a PulseChain PLS signed-order safety demo")
    args = parser.parse_args(argv)
    if args.command == "demo":
        print(json.dumps(build_demo(), indent=2, sort_keys=True))
        return 0
    if args.command == "pls-demo":
        print(json.dumps(build_pls_demo(), indent=2, sort_keys=True))
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
