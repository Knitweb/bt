from __future__ import annotations

import pytest

from bt.models import SignedOrder

from .conftest import make_order


def test_signed_order_verifies_and_detects_tampering(pair, buyer):
    order = make_order(buyer, pair)
    signed = SignedOrder.sign(order, buyer)

    assert signed.verify()

    payload = signed.to_dict()
    payload["order"]["quantity_atoms"] = payload["order"]["quantity_atoms"] + 1
    with pytest.raises(ValueError, match="order id"):
        SignedOrder.from_dict(payload)

    payload.pop("order_id")
    tampered = SignedOrder.from_dict(payload)

    assert not tampered.verify()


def test_signed_order_rejects_public_key_peer_mismatch(pair, buyer, seller):
    order = make_order(buyer, pair)
    signed = SignedOrder.sign(order, buyer)
    payload = signed.to_dict()
    payload["public_key"] = seller.public_hex
    mismatched = SignedOrder.from_dict(payload)

    assert not mismatched.verify()
