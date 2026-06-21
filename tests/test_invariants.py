from __future__ import annotations

import pytest

from bt.actors import PERSON, VOTEBANK_DAO, Actor, ActorRegistry
from bt.basket import (
    COMMODITY,
    CRYPTO_TRADE,
    CURRENCY_ANCHOR,
    FIAT_TRADE,
    VBankWeightPoint,
    derive_weights_from_vbank_series,
    bt_genesis_spec,
    normalise_weights,
)
from bt.models import SignedOrder
from bt.money import BT_MAX_ATOMS, BT_SCALE, parse_units, quote_amount_atoms

from .conftest import make_order


def test_invariant_normalise_weights_always_sums_to_weight_scale():
    weights = normalise_weights({CURRENCY_ANCHOR: 3, FIAT_TRADE: 2, CRYPTO_TRADE: 1, COMMODITY: 1})

    assert sum(weights.values()) == 1_000_000
    assert weights[CURRENCY_ANCHOR] >= weights[FIAT_TRADE] >= weights[CRYPTO_TRADE]


def test_invariant_money_rejects_float_and_caps_maximum():
    assert parse_units("888888.00000000") == BT_MAX_ATOMS
    with pytest.raises(TypeError):
        parse_units(1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="exceeds"):
        parse_units("888888.00000001")


def test_invariant_quote_rounding_never_underpays_seller():
    price_atoms = 3
    quantity_atoms = 1

    assert quote_amount_atoms(price_atoms, quantity_atoms) == 1
    assert quote_amount_atoms(BT_SCALE, parse_units("0.00000001")) == 1


def test_invariant_replay_same_inputs_same_basket_spec_id(auditor):
    registry = ActorRegistry()
    registry.add(Actor("dao:vbank", VOTEBANK_DAO, auditor.peer_id, identified=True))
    now = 100

    first = bt_genesis_spec(auditor, registry, now=now)
    second = bt_genesis_spec(auditor, registry, now=now)

    assert first.spec_id == second.spec_id
    assert first.spec.target_index_atoms() == second.spec.target_index_atoms()


def test_invariant_fresh_high_participation_vbank_point_dominates_stale_low_quality():
    now = 10_000
    stale = VBankWeightPoint(
        point_id="stale",
        observed_at=now - 10_000,
        weights_ppm={CURRENCY_ANCHOR: 900_000, FIAT_TRADE: 50_000, CRYPTO_TRADE: 25_000, COMMODITY: 25_000},
        participation_ppm=100_000,
        confidence_ppm=100_000,
        source="vbank://stale",
    )
    fresh = VBankWeightPoint(
        point_id="fresh",
        observed_at=now,
        weights_ppm={CURRENCY_ANCHOR: 200_000, FIAT_TRADE: 300_000, CRYPTO_TRADE: 250_000, COMMODITY: 250_000},
        participation_ppm=1_000_000,
        confidence_ppm=1_000_000,
        source="vbank://fresh",
    )

    weights = derive_weights_from_vbank_series((stale, fresh), now=now, window_seconds=1_000)

    assert weights[CURRENCY_ANCHOR] < 205_000
    assert weights[FIAT_TRADE] > 298_000
    assert weights[COMMODITY] > 247_000


def test_invariant_market_requires_actor_authority(pair, buyer):
    from bt.market import BtMarket

    market = BtMarket(pair)
    order = SignedOrder.sign(make_order(buyer, pair), buyer)

    with pytest.raises(ValueError, match="not registered"):
        market.submit_order(order)

    market.register_actor(Actor("person:buyer", PERSON, buyer.peer_id, identified=True))
    assert market.submit_order(order) == order.order_id

