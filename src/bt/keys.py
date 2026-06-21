"""Ed25519 identity helpers."""

from __future__ import annotations

from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .canonical import peer_id


@dataclass(frozen=True)
class Keypair:
    """A local signing identity.

    Private keys are exposed as hex only for tests, demos, and deterministic import.
    Production wallets should keep signing keys in a secure wallet or hardware module.
    """

    private_key: Ed25519PrivateKey

    @classmethod
    def generate(cls) -> "Keypair":
        return cls(Ed25519PrivateKey.generate())

    @classmethod
    def from_private_hex(cls, value: str) -> "Keypair":
        return cls(Ed25519PrivateKey.from_private_bytes(bytes.fromhex(value)))

    @property
    def private_hex(self) -> str:
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ).hex()

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self.private_key.public_key()

    @property
    def public_hex(self) -> str:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()

    @property
    def peer_id(self) -> str:
        return peer_id(self.public_hex)

    def sign(self, payload: bytes) -> str:
        return self.private_key.sign(payload).hex()


def verify(public_key_hex: str, payload: bytes, signature_hex: str) -> bool:
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
    try:
        public_key.verify(bytes.fromhex(signature_hex), payload)
    except InvalidSignature:
        return False
    return True

