from __future__ import annotations

from eurbt.market import EurbtMarket
from eurbt.models import SELL, SignedOrder
from eurbt.p2p import Envelope
from eurbt.trust import Attestation, SignedAttestation

from .conftest import make_order


def add_trust(market: EurbtMarket, auditor, subject: str, score: int, now: int) -> None:
    attestation = Attestation(
        issuer=auditor.peer_id,
        subject=subject,
        kind="settlement_history",
        score_delta=score,
        issued_at=now,
        expires_at=now + 1000,
        evidence=f"demo://{subject}",
        note="demo settlement history",
    )
    signed = SignedAttestation.sign(attestation, auditor)
    envelope = Envelope.sign("attestation", signed.to_dict(), auditor, created_at=now, nonce=f"att-{subject}")
    market.ingest_envelope(envelope, now=now)


def test_market_ingests_p2p_orders_and_applies_trust(pair, buyer, seller, auditor):
    market = EurbtMarket(pair)
    now = 100
    add_trust(market, auditor, buyer.peer_id, 60, now)
    add_trust(market, auditor, seller.peer_id, 60, now)

    buy = SignedOrder.sign(
        make_order(buyer, pair, price="100", quantity="1", created_at=101, trust_min=50, nonce="buy"),
        buyer,
    )
    sell = SignedOrder.sign(
        make_order(seller, pair, side=SELL, price="99", quantity="1", created_at=102, trust_min=50, nonce="sell"),
        seller,
    )
    for keypair, signed in ((buyer, buy), (seller, sell)):
        envelope = Envelope.sign("order", signed.to_dict(), keypair, created_at=signed.order.created_at, nonce=signed.order.nonce)
        assert market.ingest_envelope(envelope, now=now)

    trades = market.match(now=103)

    assert len(trades) == 1
    plan = market.settlement_plan(trades[0])
    assert plan.trade_id == trades[0].trade_id
    assert "Settlement route" in plan.explain()


def test_market_blocks_match_when_trust_is_missing(pair, buyer, seller):
    market = EurbtMarket(pair)
    buy = SignedOrder.sign(
        make_order(buyer, pair, price="100", quantity="1", created_at=101, trust_min=50, nonce="buy"),
        buyer,
    )
    sell = SignedOrder.sign(
        make_order(seller, pair, side=SELL, price="99", quantity="1", created_at=102, trust_min=50, nonce="sell"),
        seller,
    )

    market.submit_order(buy)
    market.submit_order(sell)

    assert market.match(now=103) == []

