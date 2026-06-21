"""Signed integer-value transfer records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .actors import ActorRegistry
from .canonical import canonical_bytes, peer_id, record_id
from .keys import Keypair, verify
from .models import Asset
from .money import format_units, max_atoms_for_decimals, validate_atoms


INSTANT_ACCEPTED = "instant_accepted"
PENDING_SETTLEMENT = "pending_settlement"


@dataclass(frozen=True)
class Transfer:
    sender: str
    receiver: str
    asset: Asset
    amount_atoms: int
    created_at: int
    nonce: str
    memo: str = ""

    def __post_init__(self) -> None:
        if not self.sender.startswith("peer_") or not self.receiver.startswith("peer_"):
            raise ValueError("sender and receiver must be peer ids")
        validate_atoms(self.amount_atoms, field="amount_atoms", max_atoms=max_atoms_for_decimals(self.asset.decimals))
        if not self.nonce:
            raise ValueError("nonce is required")
        if isinstance(self.created_at, bool) or not isinstance(self.created_at, int):
            raise TypeError("created_at must be an integer")

    @property
    def transfer_id(self) -> str:
        return record_id("tx", self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "amount_atoms": self.amount_atoms,
            "amount_display": format_units(self.amount_atoms, self.asset.decimals),
            "asset": self.asset.to_dict(),
            "created_at": self.created_at,
            "memo": self.memo,
            "nonce": self.nonce,
            "receiver": self.receiver,
            "sender": self.sender,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Transfer":
        return cls(
            sender=str(value["sender"]),
            receiver=str(value["receiver"]),
            asset=Asset.from_dict(value["asset"]),
            amount_atoms=int(value["amount_atoms"]),
            created_at=int(value["created_at"]),
            nonce=str(value["nonce"]),
            memo=str(value.get("memo", "")),
        )


@dataclass(frozen=True)
class SignedTransfer:
    transfer: Transfer
    public_key: str
    signature: str

    @classmethod
    def sign(cls, transfer: Transfer, keypair: Keypair) -> "SignedTransfer":
        if transfer.sender != keypair.peer_id:
            raise ValueError("transfer sender does not match signing key")
        return cls(
            transfer=transfer,
            public_key=keypair.public_hex,
            signature=keypair.sign(canonical_bytes(transfer)),
        )

    @property
    def transfer_id(self) -> str:
        return self.transfer.transfer_id

    def verify(self) -> bool:
        return peer_id(self.public_key) == self.transfer.sender and verify(
            self.public_key,
            canonical_bytes(self.transfer),
            self.signature,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "public_key": self.public_key,
            "signature": self.signature,
            "transfer": self.transfer.to_dict(),
            "transfer_id": self.transfer_id,
        }


@dataclass(frozen=True)
class Receipt:
    transfer_id: str
    receiver: str
    status: str
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {
            "reason": self.reason,
            "receiver": self.receiver,
            "status": self.status,
            "transfer_id": self.transfer_id,
        }


def receive_transfer(signed: SignedTransfer, registry: ActorRegistry) -> Receipt:
    if not signed.verify():
        raise ValueError("transfer signature is invalid")
    sender_actor = registry.require_transactor(signed.transfer.sender)
    if not registry.instant_receivable(signed.transfer.receiver):
        raise ValueError("receiver is not an identified person, owned agent, or VoteBank DAO")
    reason = f"sender is authorised as {sender_actor.actor_type}; receiver can show instant accepted balance"
    return Receipt(
        transfer_id=signed.transfer_id,
        receiver=signed.transfer.receiver,
        status=INSTANT_ACCEPTED,
        reason=reason,
    )
