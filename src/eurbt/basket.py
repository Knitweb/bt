"""Knowledge-stabilised basket index.

The basket is integer-first:

- component values use 8-decimal atoms;
- component weights use parts-per-million;
- the resulting target index is an integer atom value.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .actors import ActorRegistry, VOTEBANK_DAO
from .canonical import canonical_bytes, peer_id, record_id
from .keys import Keypair, verify
from .money import BT_SCALE, format_units, validate_atoms


WEIGHT_SCALE = 1_000_000
DEFAULT_WEIGHT_WINDOW_SECONDS = 30 * 86_400
EUR_ANCHOR = "eur_anchor"
FIAT_TRADE = "fiat_trade"
CRYPTO_TRADE = "crypto_trade"
COMMODITY = "commodity"
INFLATION = "inflation"
REQUIRED_COMPONENTS = {EUR_ANCHOR, FIAT_TRADE, CRYPTO_TRADE, COMMODITY}
COMPONENT_TYPES = REQUIRED_COMPONENTS | {INFLATION}


def validate_weight_ppm(value: int, *, field: str = "weight_ppm", allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{field} must be positive")
    if value > WEIGHT_SCALE:
        raise ValueError(f"{field} exceeds {WEIGHT_SCALE}")
    return value


def validate_weight_input(value: int, *, field: str = "weight") -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0:
        raise ValueError(f"{field} must be non-negative")
    return value


def weighted_average_atoms(weighted_values: tuple[tuple[int, int], ...]) -> int:
    if not weighted_values:
        raise ValueError("at least one weighted value is required")
    weight_sum = sum(weight for _, weight in weighted_values)
    if weight_sum != WEIGHT_SCALE:
        raise ValueError("weights must sum to 1_000_000 ppm")
    numerator = sum(value_atoms * weight for value_atoms, weight in weighted_values)
    return (numerator + WEIGHT_SCALE // 2) // WEIGHT_SCALE


def normalise_weights(raw_weights: dict[str, int]) -> dict[str, int]:
    if set(raw_weights) != REQUIRED_COMPONENTS:
        missing = REQUIRED_COMPONENTS - set(raw_weights)
        extra = set(raw_weights) - REQUIRED_COMPONENTS
        details = []
        if missing:
            details.append(f"missing: {', '.join(sorted(missing))}")
        if extra:
            details.append(f"extra: {', '.join(sorted(extra))}")
        raise ValueError("weights must cover required components (" + "; ".join(details) + ")")
    for component_type, value in raw_weights.items():
        validate_weight_input(value, field=f"{component_type}_weight")
    total = sum(raw_weights.values())
    if total <= 0:
        raise ValueError("weight total must be positive")
    scaled: dict[str, int] = {}
    remainders: list[tuple[int, str]] = []
    for component_type in sorted(raw_weights):
        numerator = raw_weights[component_type] * WEIGHT_SCALE
        scaled[component_type] = numerator // total
        remainders.append((numerator % total, component_type))
    remainder = WEIGHT_SCALE - sum(scaled.values())
    for _, component_type in sorted(remainders, reverse=True)[:remainder]:
        scaled[component_type] += 1
    return scaled


@dataclass(frozen=True)
class VBankWeightPoint:
    """One vBank time-series point for EURBT basket weights."""

    point_id: str
    observed_at: int
    weights_ppm: dict[str, int]
    participation_ppm: int
    confidence_ppm: int
    source: str

    def __post_init__(self) -> None:
        if not self.point_id:
            raise ValueError("point_id is required")
        if isinstance(self.observed_at, bool) or not isinstance(self.observed_at, int):
            raise TypeError("observed_at must be an integer")
        for component_type, weight in self.weights_ppm.items():
            validate_weight_ppm(weight, field=f"{component_type}_weight_ppm", allow_zero=True)
        normalise_weights(dict(self.weights_ppm))
        validate_weight_ppm(self.participation_ppm, field="participation_ppm")
        validate_weight_ppm(self.confidence_ppm, field="confidence_ppm")
        if not self.source:
            raise ValueError("source is required")

    def normalised_weights(self) -> dict[str, int]:
        return normalise_weights(dict(self.weights_ppm))

    def time_factor_ppm(self, now: int, window_seconds: int = DEFAULT_WEIGHT_WINDOW_SECONDS) -> int:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        age = max(0, now - self.observed_at)
        if age >= window_seconds:
            return 1
        # Linear recency decay. Fresh samples carry full time weight; older samples
        # inside the window taper toward 1 ppm instead of disappearing abruptly.
        return max(1, ((window_seconds - age) * WEIGHT_SCALE) // window_seconds)

    def influence_ppm(self, now: int, window_seconds: int = DEFAULT_WEIGHT_WINDOW_SECONDS) -> int:
        return max(
            1,
            (self.participation_ppm * self.confidence_ppm * self.time_factor_ppm(now, window_seconds))
            // (WEIGHT_SCALE * WEIGHT_SCALE),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "confidence_ppm": self.confidence_ppm,
            "observed_at": self.observed_at,
            "participation_ppm": self.participation_ppm,
            "point_id": self.point_id,
            "source": self.source,
            "weights_ppm": self.normalised_weights(),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "VBankWeightPoint":
        return cls(
            point_id=str(value["point_id"]),
            observed_at=int(value["observed_at"]),
            weights_ppm={str(key): int(weight) for key, weight in dict(value["weights_ppm"]).items()},
            participation_ppm=int(value["participation_ppm"]),
            confidence_ppm=int(value["confidence_ppm"]),
            source=str(value["source"]),
        )


def derive_weights_from_vbank_series(
    points: tuple[VBankWeightPoint, ...],
    *,
    now: int,
    window_seconds: int = DEFAULT_WEIGHT_WINDOW_SECONDS,
) -> dict[str, int]:
    if not points:
        raise ValueError("at least one vBank weight point is required")
    totals = {component_type: 0 for component_type in REQUIRED_COMPONENTS}
    for point in points:
        influence = point.influence_ppm(now, window_seconds)
        for component_type, weight in point.normalised_weights().items():
            totals[component_type] += weight * influence
    return normalise_weights(totals)


@dataclass(frozen=True)
class KnowledgeClaim:
    issuer: str
    subject: str
    claim_type: str
    value_atoms: int
    confidence_ppm: int
    observed_at: int
    expires_at: int
    source: str
    note: str

    def __post_init__(self) -> None:
        if not self.issuer.startswith("peer_"):
            raise ValueError("issuer must be a peer id")
        if not self.subject:
            raise ValueError("subject is required")
        if self.claim_type not in COMPONENT_TYPES:
            raise ValueError(f"unknown claim_type: {self.claim_type}")
        validate_atoms(self.value_atoms, field="value_atoms")
        validate_weight_ppm(self.confidence_ppm, field="confidence_ppm")
        if self.expires_at <= self.observed_at:
            raise ValueError("expires_at must be after observed_at")
        if not self.source:
            raise ValueError("source is required")

    @property
    def claim_id(self) -> str:
        return record_id("knw", self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_type": self.claim_type,
            "confidence_ppm": self.confidence_ppm,
            "expires_at": self.expires_at,
            "issuer": self.issuer,
            "note": self.note,
            "observed_at": self.observed_at,
            "source": self.source,
            "subject": self.subject,
            "value_atoms": self.value_atoms,
            "value_display": format_units(self.value_atoms),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "KnowledgeClaim":
        return cls(
            issuer=str(value["issuer"]),
            subject=str(value["subject"]),
            claim_type=str(value["claim_type"]),
            value_atoms=int(value["value_atoms"]),
            confidence_ppm=int(value["confidence_ppm"]),
            observed_at=int(value["observed_at"]),
            expires_at=int(value["expires_at"]),
            source=str(value["source"]),
            note=str(value.get("note", "")),
        )


@dataclass(frozen=True)
class SignedKnowledgeClaim:
    claim: KnowledgeClaim
    public_key: str
    signature: str

    @classmethod
    def sign(cls, claim: KnowledgeClaim, keypair: Keypair) -> "SignedKnowledgeClaim":
        if claim.issuer != keypair.peer_id:
            raise ValueError("claim issuer does not match signing key")
        return cls(
            claim=claim,
            public_key=keypair.public_hex,
            signature=keypair.sign(canonical_bytes(claim)),
        )

    @property
    def claim_id(self) -> str:
        return self.claim.claim_id

    def verify(self) -> bool:
        return peer_id(self.public_key) == self.claim.issuer and verify(
            self.public_key,
            canonical_bytes(self.claim),
            self.signature,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim.to_dict(),
            "claim_id": self.claim_id,
            "public_key": self.public_key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SignedKnowledgeClaim":
        claim = KnowledgeClaim.from_dict(value["claim"])
        signed = cls(claim=claim, public_key=str(value["public_key"]), signature=str(value["signature"]))
        if value.get("claim_id") and value["claim_id"] != signed.claim_id:
            raise ValueError("claim id does not match payload")
        return signed


@dataclass(frozen=True)
class BasketComponent:
    component_id: str
    component_type: str
    label: str
    weight_ppm: int
    value_atoms: int
    claim_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.component_id:
            raise ValueError("component_id is required")
        if self.component_type not in COMPONENT_TYPES:
            raise ValueError(f"unknown component_type: {self.component_type}")
        validate_weight_ppm(self.weight_ppm)
        validate_atoms(self.value_atoms, field="value_atoms")
        if not self.claim_ids:
            raise ValueError("component must reference at least one knowledge claim")

    @property
    def weighted_atoms(self) -> int:
        return self.value_atoms * self.weight_ppm

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_ids": list(self.claim_ids),
            "component_id": self.component_id,
            "component_type": self.component_type,
            "label": self.label,
            "value_atoms": self.value_atoms,
            "value_display": format_units(self.value_atoms),
            "weight_ppm": self.weight_ppm,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BasketComponent":
        return cls(
            component_id=str(value["component_id"]),
            component_type=str(value["component_type"]),
            label=str(value["label"]),
            weight_ppm=int(value["weight_ppm"]),
            value_atoms=int(value["value_atoms"]),
            claim_ids=tuple(str(item) for item in value["claim_ids"]),
        )


@dataclass(frozen=True)
class BasketSpec:
    basket_id: str
    currency_code: str
    anchor_currency: str
    components: tuple[BasketComponent, ...]
    created_by: str
    created_at: int

    def __post_init__(self) -> None:
        if self.anchor_currency != "EUR":
            raise ValueError("EURBT basket anchor_currency must be EUR")
        if not self.currency_code or not self.basket_id:
            raise ValueError("basket_id and currency_code are required")
        if not self.created_by.startswith("peer_"):
            raise ValueError("created_by must be a peer id")
        types = {component.component_type for component in self.components}
        missing = REQUIRED_COMPONENTS - types
        if missing:
            raise ValueError(f"basket missing required component type(s): {', '.join(sorted(missing))}")
        weighted_average_atoms(tuple((component.value_atoms, component.weight_ppm) for component in self.components))

    @property
    def spec_id(self) -> str:
        return record_id("bsk", self.to_dict(include_id=False))

    def target_index_atoms(self) -> int:
        return weighted_average_atoms(tuple((component.value_atoms, component.weight_ppm) for component in self.components))

    def explain(self) -> str:
        component_text = ", ".join(
            f"{component.label} {component.weight_ppm / 10_000:.2f}%"
            for component in self.components
        )
        return (
            f"{self.currency_code} target is {format_units(self.target_index_atoms())} "
            f"{self.anchor_currency}-anchored atoms from {component_text}."
        )

    def to_dict(self, include_id: bool = True) -> dict[str, Any]:
        data = {
            "anchor_currency": self.anchor_currency,
            "basket_id": self.basket_id,
            "components": [component.to_dict() for component in self.components],
            "created_at": self.created_at,
            "created_by": self.created_by,
            "currency_code": self.currency_code,
            "target_index_atoms": self.target_index_atoms(),
            "target_index_display": format_units(self.target_index_atoms()),
        }
        if include_id:
            data["spec_id"] = self.spec_id
        return data

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BasketSpec":
        spec = cls(
            basket_id=str(value["basket_id"]),
            currency_code=str(value["currency_code"]),
            anchor_currency=str(value["anchor_currency"]),
            components=tuple(BasketComponent.from_dict(item) for item in value["components"]),
            created_by=str(value["created_by"]),
            created_at=int(value["created_at"]),
        )
        if value.get("spec_id") and value["spec_id"] != spec.spec_id:
            raise ValueError("basket spec id does not match payload")
        return spec


@dataclass(frozen=True)
class SignedBasketSpec:
    spec: BasketSpec
    public_key: str
    signature: str

    @classmethod
    def sign(cls, spec: BasketSpec, keypair: Keypair, registry: ActorRegistry) -> "SignedBasketSpec":
        actor = registry.require_transactor(spec.created_by)
        if actor.actor_type != VOTEBANK_DAO:
            raise ValueError("basket spec updates must be signed by the VoteBank DAO")
        if spec.created_by != keypair.peer_id:
            raise ValueError("basket spec creator does not match signing key")
        return cls(spec=spec, public_key=keypair.public_hex, signature=keypair.sign(canonical_bytes(spec)))

    @property
    def spec_id(self) -> str:
        return self.spec.spec_id

    def verify(self, registry: ActorRegistry | None = None) -> bool:
        if peer_id(self.public_key) != self.spec.created_by:
            return False
        if registry is not None:
            actor = registry.get(self.spec.created_by)
            if actor is None or actor.actor_type != VOTEBANK_DAO or not actor.can_transact:
                return False
        return verify(self.public_key, canonical_bytes(self.spec), self.signature)

    def to_dict(self) -> dict[str, Any]:
        return {
            "public_key": self.public_key,
            "signature": self.signature,
            "spec": self.spec.to_dict(),
            "spec_id": self.spec_id,
        }


def component_from_claim(
    signed_claim: SignedKnowledgeClaim,
    *,
    component_id: str,
    label: str,
    weight_ppm: int,
    now: int,
) -> BasketComponent:
    if not signed_claim.verify():
        raise ValueError("knowledge claim signature is invalid")
    if signed_claim.claim.expires_at <= now:
        raise ValueError("knowledge claim is expired")
    # Confidence reduces usable weight unless the DAO explicitly supplies a fresher
    # higher-confidence claim. This prevents weak claims from fully steering the basket.
    effective_weight = (weight_ppm * signed_claim.claim.confidence_ppm) // WEIGHT_SCALE
    validate_weight_ppm(effective_weight)
    return BasketComponent(
        component_id=component_id,
        component_type=signed_claim.claim.claim_type,
        label=label,
        weight_ppm=effective_weight,
        value_atoms=signed_claim.claim.value_atoms,
        claim_ids=(signed_claim.claim_id,),
    )


def eurbt_genesis_claims(issuer: Keypair, now: int) -> tuple[SignedKnowledgeClaim, ...]:
    examples = (
        (EUR_ANCHOR, "EUR anchor", BT_SCALE, "ecb://eur-anchor", "Euro numeraire baseline"),
        (FIAT_TRADE, "Trade weighted fiat basket", 99_400_000, "ecb://effective-exchange-rates", "Trade weighted fiat pressure"),
        (CRYPTO_TRADE, "Crypto trade basket", 103_200_000, "eurbt://crypto-volume", "Crypto trade demand against EURBT"),
        (COMMODITY, "Tradable commodity basket", 101_800_000, "worldbank://commodity-markets", "Liquid commodity value pressure"),
    )
    signed: list[SignedKnowledgeClaim] = []
    for claim_type, subject, value_atoms, source, note in examples:
        claim = KnowledgeClaim(
            issuer=issuer.peer_id,
            subject=subject,
            claim_type=claim_type,
            value_atoms=value_atoms,
            confidence_ppm=WEIGHT_SCALE,
            observed_at=now,
            expires_at=now + 86_400,
            source=source,
            note=note,
        )
        signed.append(SignedKnowledgeClaim.sign(claim, issuer))
    return tuple(signed)


def default_vbank_weight_series(now: int) -> tuple[VBankWeightPoint, ...]:
    return (
        VBankWeightPoint(
            point_id="vbank:eurbt:genesis:baseline",
            observed_at=now - 14 * 86_400,
            weights_ppm={
                EUR_ANCHOR: 420_000,
                FIAT_TRADE: 240_000,
                CRYPTO_TRADE: 140_000,
                COMMODITY: 200_000,
            },
            participation_ppm=720_000,
            confidence_ppm=850_000,
            source="vbank://eurbt/genesis/baseline",
        ),
        VBankWeightPoint(
            point_id="vbank:eurbt:genesis:latest",
            observed_at=now,
            weights_ppm={
                EUR_ANCHOR: 380_000,
                FIAT_TRADE: 240_000,
                CRYPTO_TRADE: 180_000,
                COMMODITY: 200_000,
            },
            participation_ppm=900_000,
            confidence_ppm=950_000,
            source="vbank://eurbt/genesis/latest",
        ),
    )


def eurbt_genesis_spec(
    votebank: Keypair,
    registry: ActorRegistry,
    now: int,
    vbank_series: tuple[VBankWeightPoint, ...] | None = None,
) -> SignedBasketSpec:
    claims = eurbt_genesis_claims(votebank, now)
    weights = derive_weights_from_vbank_series(vbank_series or default_vbank_weight_series(now), now=now)
    components = tuple(
        component_from_claim(
            claim,
            component_id=f"eurbt:{claim.claim.claim_type}",
            label=claim.claim.subject,
            weight_ppm=weights[claim.claim.claim_type],
            now=now,
        )
        for claim in claims
    )
    spec = BasketSpec(
        basket_id="eurbt-genesis",
        currency_code="EURBT",
        anchor_currency="EUR",
        components=components,
        created_by=votebank.peer_id,
        created_at=now,
    )
    return SignedBasketSpec.sign(spec, votebank, registry)
