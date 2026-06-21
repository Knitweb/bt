"""Explainable trust attestations for BT markets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_bytes, peer_id, record_id
from .keys import Keypair, verify


TRUST_KINDS = {
    "reserve_evidence",
    "settlement_history",
    "identity_check",
    "business_check",
    "dispute",
    "uptime",
}


@dataclass(frozen=True)
class Attestation:
    issuer: str
    subject: str
    kind: str
    score_delta: int
    issued_at: int
    expires_at: int
    evidence: str
    note: str

    def __post_init__(self) -> None:
        if self.kind not in TRUST_KINDS:
            raise ValueError(f"unknown trust attestation kind: {self.kind}")
        if not self.issuer.startswith("peer_") or not self.subject.startswith("peer_"):
            raise ValueError("issuer and subject must be peer ids")
        if not -100 <= self.score_delta <= 100:
            raise ValueError("score_delta must be between -100 and 100")
        if self.expires_at <= self.issued_at:
            raise ValueError("expires_at must be after issued_at")
        if not self.evidence:
            raise ValueError("evidence is required")

    @property
    def attestation_id(self) -> str:
        return record_id("att", self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence": self.evidence,
            "expires_at": self.expires_at,
            "issued_at": self.issued_at,
            "issuer": self.issuer,
            "kind": self.kind,
            "note": self.note,
            "score_delta": self.score_delta,
            "subject": self.subject,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Attestation":
        return cls(
            issuer=str(value["issuer"]),
            subject=str(value["subject"]),
            kind=str(value["kind"]),
            score_delta=int(value["score_delta"]),
            issued_at=int(value["issued_at"]),
            expires_at=int(value["expires_at"]),
            evidence=str(value["evidence"]),
            note=str(value["note"]),
        )


@dataclass(frozen=True)
class SignedAttestation:
    attestation: Attestation
    public_key: str
    signature: str

    @classmethod
    def sign(cls, attestation: Attestation, keypair: Keypair) -> "SignedAttestation":
        if attestation.issuer != keypair.peer_id:
            raise ValueError("attestation issuer does not match signing key")
        return cls(
            attestation=attestation,
            public_key=keypair.public_hex,
            signature=keypair.sign(canonical_bytes(attestation)),
        )

    @property
    def attestation_id(self) -> str:
        return self.attestation.attestation_id

    def verify(self) -> bool:
        return peer_id(self.public_key) == self.attestation.issuer and verify(
            self.public_key,
            canonical_bytes(self.attestation),
            self.signature,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "attestation": self.attestation.to_dict(),
            "attestation_id": self.attestation_id,
            "public_key": self.public_key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SignedAttestation":
        attestation = Attestation.from_dict(value["attestation"])
        signed = cls(
            attestation=attestation,
            public_key=str(value["public_key"]),
            signature=str(value["signature"]),
        )
        if value.get("attestation_id") and value["attestation_id"] != signed.attestation_id:
            raise ValueError("attestation id does not match payload")
        return signed


class TrustBook:
    def __init__(self) -> None:
        self._attestations: dict[str, SignedAttestation] = {}

    def add(self, signed: SignedAttestation, now: int | None = None, verify_signature: bool = True) -> str:
        attestation = signed.attestation
        if now is not None and attestation.expires_at <= now:
            raise ValueError("attestation is expired")
        if verify_signature and not signed.verify():
            raise ValueError("attestation signature is invalid")
        self._attestations[signed.attestation_id] = signed
        return signed.attestation_id

    def active_for(self, subject: str, now: int | None = None) -> list[SignedAttestation]:
        values = []
        for signed in self._attestations.values():
            attestation = signed.attestation
            if attestation.subject != subject:
                continue
            if now is not None and attestation.expires_at <= now:
                continue
            values.append(signed)
        return sorted(values, key=lambda signed: (signed.attestation.issued_at, signed.attestation_id))

    def score(self, subject: str, now: int | None = None) -> int:
        total = sum(signed.attestation.score_delta for signed in self.active_for(subject, now))
        return max(0, min(100, total))

    def explain(self, subject: str, now: int | None = None) -> str:
        active = self.active_for(subject, now)
        score = self.score(subject, now)
        if not active:
            return "No trust evidence is known for this peer yet."
        positives = [signed.attestation for signed in active if signed.attestation.score_delta > 0]
        negatives = [signed.attestation for signed in active if signed.attestation.score_delta < 0]
        parts = [f"Trust score is {score}/100 based on {len(active)} signed evidence record(s)."]
        if positives:
            labels = ", ".join(sorted({attestation.kind.replace("_", " ") for attestation in positives}))
            parts.append(f"Positive evidence: {labels}.")
        if negatives:
            labels = ", ".join(sorted({attestation.kind.replace("_", " ") for attestation in negatives}))
            parts.append(f"Risk evidence: {labels}.")
        strongest = max(active, key=lambda signed: abs(signed.attestation.score_delta)).attestation
        parts.append(f"Most important note: {strongest.note}")
        return " ".join(parts)
