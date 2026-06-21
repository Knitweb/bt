from __future__ import annotations

import pytest

from bt.actors import PERSON, Actor
from bt.chains import BT_ON_KNITWEB, PULSE
from bt.market import BtMarket
from bt.models import BUY, SELL, Order, Pair, SignedOrder, Trade
from bt.money import parse_units
from bt.readiness import REAL_FUNDS, SIGNED_DRY_RUN, assess_pair_readiness
from bt.settlement import plan_settlement


def pulse_pair() -> Pair:
    return Pair(PULSE, BT_ON_KNITWEB)


def test_pulse_order_preserves_eighteen_decimal_quantity(buyer):
    pair = pulse_pair()

    order = Order.from_human(
        maker=buyer.peer_id,
        pair=pair,
        side=SELL,
        price="1.01",
        quantity="1.000000000000000001",
        min_quantity="0.100000000000000000",
        created_at=100,
        expires_at=200,
        nonce="pulse-sell",
    )

    assert order.quantity_atoms == 1_000_000_000_000_000_001
    assert order.min_quantity_atoms == 100_000_000_000_000_000
    assert order.price_atoms == parse_units("1.01", pair.quote.decimals)


def test_pulse_pair_is_ready_for_signed_dry_run_but_not_real_funds():
    pair = pulse_pair()

    dry_run = assess_pair_readiness(pair, mode=SIGNED_DRY_RUN)
    real_funds = assess_pair_readiness(pair, mode=REAL_FUNDS)

    assert dry_run.ready
    assert not dry_run.real_funds_ready
    assert not real_funds.real_funds_ready
    assert any(check.code == "quote_asset_real_funds" for check in real_funds.blockers)
    assert any(check.code == "settlement_contract" for check in real_funds.blockers)
    assert any(check.code == "audit_reference" for check in real_funds.blockers)


def test_market_blocks_real_funds_pulse_order_without_adapter_evidence(buyer):
    pair = pulse_pair()
    market = BtMarket(pair)
    market.register_actor(Actor("person:buyer", PERSON, buyer.peer_id, identified=True))
    order = SignedOrder.sign(
        Order.from_human(
            maker=buyer.peer_id,
            pair=pair,
            side=BUY,
            price="1.00",
            quantity="10",
            created_at=100,
            expires_at=200,
            nonce="real-funds",
        ),
        buyer,
    )

    with pytest.raises(ValueError, match="not ready"):
        market.submit_real_funds_order(order, settlement_contract="", audit_reference="", now=101)


def test_pulse_settlement_plan_uses_knitweb_route(buyer, seller):
    pair = pulse_pair()
    trade = Trade(
        pair=pair,
        price_atoms=parse_units("1.00", pair.quote.decimals),
        quantity_atoms=parse_units("10", pair.base.decimals, max_atoms=None),
        buy_order_id="ord_buy",
        sell_order_id="ord_sell",
        buy_maker=buyer.peer_id,
        sell_maker=seller.peer_id,
        created_at=100,
    )

    plan = plan_settlement(trade)

    assert plan.route == "knitweb-audited-escrow-required"
    assert "Knitweb escrow" in plan.legs[0].condition
    assert any("Native PULSE" in note for note in plan.risk_notes)
