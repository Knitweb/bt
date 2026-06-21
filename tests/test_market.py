from __future__ import annotations

import pytest

from eurbt.actors import AGENT, PERSON, VOTEBANK_DAO, Actor
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
    market.register_actor(Actor("person:buyer", PERSON, buyer.peer_id, identified=True))
    market.register_actor(Actor("agent:seller", AGENT, seller.peer_id, owner_person_id="person:seller-owner", identified=True))
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
    market.register_actor(Actor("person:buyer", PERSON, buyer.peer_id, identified=True))
    market.register_actor(Actor("agent:seller", AGENT, seller.peer_id, owner_person_id="person:seller-owner", identified=True))
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


def test_market_rejects_unregistered_actor(pair, buyer):
    market = EurbtMarket(pair)
    order = SignedOrder.sign(make_order(buyer, pair, nonce="buy"), buyer)

    with pytest.raises(ValueError, match="not registered"):
        market.submit_order(order)


def test_votebank_dao_actor_can_transact(pair, buyer):
    market = EurbtMarket(pair)
    market.register_actor(Actor("dao:vbank", VOTEBANK_DAO, buyer.peer_id, identified=True))
    order = SignedOrder.sign(make_order(buyer, pair, nonce="dao"), buyer)

    assert market.submit_order(order) == order.order_id
