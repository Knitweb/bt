"""Signed P2P message envelopes.

The store is intentionally transport-neutral. A node can move these records over a
DHT, local mesh, mailbox relay, Pulse/Knitweb fabric, or plain files without changing
the signed payload.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_bytes, peer_id, record_id
from .keys import Keypair, verify


MESSAGE_TYPES = {
    "attestation",
    "basket-spec",
    "knowledge-claim",
    "order",
    "settlement-plan",
    "trade",
    "transfer",
    "vbank-weight-point",
}


@dataclass(frozen=True)
class Envelope:
    message_type: str
    payload: dict[str, Any]
    sender: str
    created_at: int
    nonce: str
    public_key: str
    signature: str

    @classmethod
    def sign(
        cls,
        message_type: str,
        payload: dict[str, Any],
        keypair: Keypair,
        created_at: int,
        nonce: str,
    ) -> "Envelope":
        if message_type not in MESSAGE_TYPES:
            raise ValueError(f"unknown message type: {message_type}")
        if not nonce:
            raise ValueError("nonce is required")
        unsigned = {
            "created_at": created_at,
            "message_type": message_type,
            "nonce": nonce,
            "payload": payload,
            "sender": keypair.peer_id,
        }
        return cls(
            message_type=message_type,
            payload=payload,
            sender=keypair.peer_id,
            created_at=created_at,
            nonce=nonce,
            public_key=keypair.public_hex,
            signature=keypair.sign(canonical_bytes(unsigned)),
        )

    @property
    def envelope_id(self) -> str:
        return record_id("msg", self.unsigned_dict())

    def unsigned_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "message_type": self.message_type,
            "nonce": self.nonce,
            "payload": self.payload,
            "sender": self.sender,
        }

    def verify(self) -> bool:
        if self.message_type not in MESSAGE_TYPES:
            return False
        return peer_id(self.public_key) == self.sender and verify(
            self.public_key,
            canonical_bytes(self.unsigned_dict()),
            self.signature,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.unsigned_dict(),
            "envelope_id": self.envelope_id,
            "public_key": self.public_key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Envelope":
        envelope = cls(
            message_type=str(value["message_type"]),
            payload=dict(value["payload"]),
            sender=str(value["sender"]),
            created_at=int(value["created_at"]),
            nonce=str(value["nonce"]),
            public_key=str(value["public_key"]),
            signature=str(value["signature"]),
        )
        if value.get("envelope_id") and value["envelope_id"] != envelope.envelope_id:
            raise ValueError("envelope id does not match payload")
        return envelope


class PeerStore:
    def __init__(self) -> None:
        self._messages: dict[str, Envelope] = {}

    def ingest(self, envelope: Envelope, verify_signature: bool = True) -> bool:
        if verify_signature and not envelope.verify():
            raise ValueError("envelope signature is invalid")
        if envelope.envelope_id in self._messages:
            return False
        self._messages[envelope.envelope_id] = envelope
        return True

    def messages(self, message_type: str | None = None) -> list[Envelope]:
        values = self._messages.values()
        if message_type is not None:
            values = [message for message in values if message.message_type == message_type]
        return sorted(values, key=lambda message: (message.created_at, message.envelope_id))
