from __future__ import annotations

from bt.models import SignedOrder
from bt.p2p import Envelope, PeerStore

from .conftest import make_order


def test_envelope_verifies_and_deduplicates(pair, buyer):
    signed = SignedOrder.sign(make_order(buyer, pair), buyer)
    envelope = Envelope.sign("order", signed.to_dict(), buyer, created_at=100, nonce="env-1")
    store = PeerStore()

    assert envelope.verify()
    assert store.ingest(envelope)
    assert not store.ingest(envelope)
    assert store.messages("order") == [envelope]


def test_envelope_rejects_sender_public_key_mismatch(pair, buyer, seller):
    signed = SignedOrder.sign(make_order(buyer, pair), buyer)
    envelope = Envelope.sign("order", signed.to_dict(), buyer, created_at=100, nonce="env-1")
    payload = envelope.to_dict()
    payload["sender"] = seller.peer_id
    payload.pop("envelope_id")
    tampered = Envelope.from_dict(payload)

    assert not tampered.verify()
