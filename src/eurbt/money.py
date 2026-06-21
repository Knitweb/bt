"""Integer money helpers for EURBT.

EURBT transaction values use fixed-point integer atoms. The canonical scale is
eight decimals, so 1.00000000 EURBT is stored as 100_000_000 atoms.
"""

from __future__ import annotations

import re


BT_DECIMALS = 8
BT_SCALE = 10**BT_DECIMALS
BT_MAX_MAJOR_UNITS = 888_888
BT_MAX_ATOMS = BT_MAX_MAJOR_UNITS * BT_SCALE

_AMOUNT_RE = re.compile(r"^(?P<int>\d+)(?P<frac>[.,]\d+)?$")


def parse_units(value: str, decimals: int = BT_DECIMALS, max_atoms: int | None = BT_MAX_ATOMS) -> int:
    """Parse a human decimal value into integer atoms.

    Both `1.23` and Dutch-style `1,23` are accepted. The parser rejects floats
    because binary floating point is not a transaction format.
    """

    if not isinstance(value, str):
        raise TypeError("money values must be parsed from strings")
    text = value.strip().replace("_", "")
    match = _AMOUNT_RE.match(text)
    if not match:
        raise ValueError(f"invalid money value: {value!r}")
    whole = int(match.group("int"))
    frac_text = (match.group("frac") or "")[1:]
    if len(frac_text) > decimals:
        raise ValueError(f"too many decimal places for {decimals}-decimal asset")
    atoms = whole * 10**decimals + int(frac_text.ljust(decimals, "0") or "0")
    if max_atoms is not None and atoms > max_atoms:
        raise ValueError(f"value exceeds max atoms {max_atoms}")
    return atoms


def format_units(atoms: int, decimals: int = BT_DECIMALS) -> str:
    if isinstance(atoms, bool) or not isinstance(atoms, int):
        raise TypeError("atoms must be an integer")
    sign = "-" if atoms < 0 else ""
    atoms = abs(atoms)
    scale = 10**decimals
    whole, frac = divmod(atoms, scale)
    return f"{sign}{whole}.{frac:0{decimals}d}"


def validate_atoms(value: int, *, field: str, max_atoms: int | None = BT_MAX_ATOMS, allow_zero: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer atom value")
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{field} must be positive")
    if max_atoms is not None and value > max_atoms:
        raise ValueError(f"{field} exceeds max atoms {max_atoms}")
    return value


def quote_amount_atoms(price_atoms: int, quantity_atoms: int, base_decimals: int = BT_DECIMALS) -> int:
    validate_atoms(price_atoms, field="price_atoms")
    validate_atoms(quantity_atoms, field="quantity_atoms")
    scale = 10**base_decimals
    # Round up by one quote atom on non-divisible fills so sellers are not underpaid.
    return (price_atoms * quantity_atoms + scale - 1) // scale

