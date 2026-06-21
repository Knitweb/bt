from __future__ import annotations

import pytest

from bt.money import BT_MAX_ATOMS, BT_SCALE, format_units, parse_units, quote_amount_atoms


def test_parse_units_uses_eight_decimal_integer_atoms():
    assert parse_units("0.00000001") == 1
    assert parse_units("1.00000000") == BT_SCALE
    assert parse_units("888888,00") == BT_MAX_ATOMS
    assert format_units(BT_MAX_ATOMS) == "888888.00000000"


def test_parse_units_rejects_float_and_too_many_decimals():
    with pytest.raises(TypeError):
        parse_units(1.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="too many"):
        parse_units("0.000000001")


def test_quote_amount_atoms_rounds_up_to_quote_atom():
    assert quote_amount_atoms(parse_units("61000"), parse_units("0.03")) == parse_units("1830")
    assert quote_amount_atoms(3, 1) == 1

