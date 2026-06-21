"""Canonical JSON helpers for signed BT records."""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
from decimal import Decimal
from typing import Any


def normalize(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return normalize(value.to_dict())
    if dataclasses.is_dataclass(value):
        return normalize(dataclasses.asdict(value))
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, tuple):
        return [normalize(item) for item in value]
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(value[key]) for key in sorted(value)}
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        normalize(value),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest_hex(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def record_id(prefix: str, value: Any) -> str:
    return f"{prefix}_{digest_hex(value)[:32]}"


def peer_id(public_key_hex: str) -> str:
    raw = bytes.fromhex(public_key_hex)
    digest = hashlib.sha256(raw).digest()
    encoded = base64.b32encode(digest).decode("ascii").lower().rstrip("=")
    return f"peer_{encoded[:32]}"

