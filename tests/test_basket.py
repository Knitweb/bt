from __future__ import annotations

import pytest

from eurbt.actors import PERSON, VOTEBANK_DAO, Actor, ActorRegistry
from eurbt.basket import (
    COMMODITY,
    CRYPTO_TRADE,
    EUR_ANCHOR,
    FIAT_TRADE,
    BasketComponent,
    BasketSpec,
    KnowledgeClaim,
    SignedBasketSpec,
    SignedKnowledgeClaim,
    VBankWeightPoint,
    component_from_claim,
    derive_weights_from_vbank_series,
    eurbt_genesis_spec,
)
from eurbt.money import BT_SCALE


def registry_with_votebank(votebank) -> ActorRegistry:
    registry = ActorRegistry()
    registry.add(Actor("dao:vbank", VOTEBANK_DAO, votebank.peer_id, identified=True))
    return registry


def claim(keypair, claim_type: str, value_atoms: int = BT_SCALE) -> SignedKnowledgeClaim:
    return SignedKnowledgeClaim.sign(
        KnowledgeClaim(
            issuer=keypair.peer_id,
            subject=claim_type,
            claim_type=claim_type,
            value_atoms=value_atoms,
            confidence_ppm=1_000_000,
            observed_at=100,
            expires_at=200,
            source=f"test://{claim_type}",
            note="test claim",
        ),
        keypair,
    )


def component(keypair, claim_type: str, weight_ppm: int, value_atoms: int = BT_SCALE) -> BasketComponent:
    return component_from_claim(
        claim(keypair, claim_type, value_atoms),
        component_id=f"test:{claim_type}",
        label=claim_type,
        weight_ppm=weight_ppm,
        now=120,
    )


def test_eurbt_genesis_spec_is_votebank_signed_and_deterministic(auditor):
    registry = registry_with_votebank(auditor)

    signed = eurbt_genesis_spec(auditor, registry, now=100)

    assert signed.verify(registry)
    assert signed.spec.anchor_currency == "EUR"
    assert signed.spec.currency_code == "EURBT"
    assert {component.component_type: component.weight_ppm for component in signed.spec.components} == {
        COMMODITY: 200_000,
        CRYPTO_TRADE: 168_949,
        EUR_ANCHOR: 391_051,
        FIAT_TRADE: 240_000,
    }
    assert signed.spec.target_index_atoms() == 100_756_637
    assert "EURBT target is 1.00756637" in signed.spec.explain()


def test_vbank_timeseries_recency_drives_dynamic_weights():
    now = 1_000
    older = VBankWeightPoint(
        point_id="old",
        observed_at=now - 900,
        weights_ppm={EUR_ANCHOR: 800_000, FIAT_TRADE: 100_000, CRYPTO_TRADE: 50_000, COMMODITY: 50_000},
        participation_ppm=1_000_000,
        confidence_ppm=1_000_000,
        source="vbank://old",
    )
    fresh = VBankWeightPoint(
        point_id="fresh",
        observed_at=now,
        weights_ppm={EUR_ANCHOR: 200_000, FIAT_TRADE: 300_000, CRYPTO_TRADE: 300_000, COMMODITY: 200_000},
        participation_ppm=1_000_000,
        confidence_ppm=1_000_000,
        source="vbank://fresh",
    )

    weights = derive_weights_from_vbank_series((older, fresh), now=now, window_seconds=1_000)

    assert sum(weights.values()) == 1_000_000
    assert weights[CRYPTO_TRADE] > 250_000
    assert weights[EUR_ANCHOR] < 300_000


def test_vbank_timeseries_participation_and_confidence_affect_influence():
    now = 1_000
    weak = VBankWeightPoint(
        point_id="weak",
        observed_at=now,
        weights_ppm={EUR_ANCHOR: 900_000, FIAT_TRADE: 50_000, CRYPTO_TRADE: 25_000, COMMODITY: 25_000},
        participation_ppm=100_000,
        confidence_ppm=100_000,
        source="vbank://weak",
    )
    strong = VBankWeightPoint(
        point_id="strong",
        observed_at=now,
        weights_ppm={EUR_ANCHOR: 200_000, FIAT_TRADE: 300_000, CRYPTO_TRADE: 250_000, COMMODITY: 250_000},
        participation_ppm=1_000_000,
        confidence_ppm=1_000_000,
        source="vbank://strong",
    )

    weights = derive_weights_from_vbank_series((weak, strong), now=now)

    assert weights[EUR_ANCHOR] < 210_000
    assert weights[FIAT_TRADE] > 295_000


def test_basket_requires_all_core_component_types(auditor):
    components = (
        component(auditor, EUR_ANCHOR, 400_000),
        component(auditor, FIAT_TRADE, 300_000),
        component(auditor, CRYPTO_TRADE, 300_000),
    )

    with pytest.raises(ValueError, match="commodity"):
        BasketSpec(
            basket_id="bad",
            currency_code="EURBT",
            anchor_currency="EUR",
            components=components,
            created_by=auditor.peer_id,
            created_at=100,
        )


def test_basket_rejects_non_one_million_weight_sum(auditor):
    components = (
        component(auditor, EUR_ANCHOR, 250_000),
        component(auditor, FIAT_TRADE, 250_000),
        component(auditor, CRYPTO_TRADE, 250_000),
        component(auditor, COMMODITY, 249_999),
    )

    with pytest.raises(ValueError, match="weights"):
        BasketSpec(
            basket_id="bad-weights",
            currency_code="EURBT",
            anchor_currency="EUR",
            components=components,
            created_by=auditor.peer_id,
            created_at=100,
        )


def test_only_votebank_dao_can_sign_basket_spec(auditor, buyer):
    registry = ActorRegistry()
    registry.add(Actor("person:buyer", PERSON, buyer.peer_id, identified=True))
    components = (
        component(auditor, EUR_ANCHOR, 250_000),
        component(auditor, FIAT_TRADE, 250_000),
        component(auditor, CRYPTO_TRADE, 250_000),
        component(auditor, COMMODITY, 250_000),
    )
    spec = BasketSpec(
        basket_id="person-update",
        currency_code="EURBT",
        anchor_currency="EUR",
        components=components,
        created_by=buyer.peer_id,
        created_at=100,
    )

    with pytest.raises(ValueError, match="VoteBank DAO"):
        SignedBasketSpec.sign(spec, buyer, registry)


def test_expired_knowledge_claim_cannot_become_component(auditor):
    signed = SignedKnowledgeClaim.sign(
        KnowledgeClaim(
            issuer=auditor.peer_id,
            subject="old commodity",
            claim_type=COMMODITY,
            value_atoms=BT_SCALE,
            confidence_ppm=1_000_000,
            observed_at=100,
            expires_at=110,
            source="test://old",
            note="expired",
        ),
        auditor,
    )

    with pytest.raises(ValueError, match="expired"):
        component_from_claim(signed, component_id="old", label="old", weight_ppm=250_000, now=120)
