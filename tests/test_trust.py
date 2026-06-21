from __future__ import annotations

import pytest

from bt.trust import Attestation, SignedAttestation, TrustBook


def test_trust_book_scores_and_explains_signed_evidence(auditor, seller):
    book = TrustBook()
    positive = Attestation(
        issuer=auditor.peer_id,
        subject=seller.peer_id,
        kind="reserve_evidence",
        score_delta=70,
        issued_at=100,
        expires_at=200,
        evidence="ipfs://reserve-proof",
        note="seller showed reserve evidence",
    )
    negative = Attestation(
        issuer=auditor.peer_id,
        subject=seller.peer_id,
        kind="dispute",
        score_delta=-20,
        issued_at=101,
        expires_at=200,
        evidence="case://1",
        note="one small settlement dispute was reported",
    )

    book.add(SignedAttestation.sign(positive, auditor), now=120)
    book.add(SignedAttestation.sign(negative, auditor), now=120)

    assert book.score(seller.peer_id, now=120) == 50
    explanation = book.explain(seller.peer_id, now=120)
    assert "Trust score is 50/100" in explanation
    assert "Risk evidence" in explanation


def test_expired_attestation_is_rejected(auditor, seller):
    book = TrustBook()
    expired = Attestation(
        issuer=auditor.peer_id,
        subject=seller.peer_id,
        kind="uptime",
        score_delta=10,
        issued_at=100,
        expires_at=110,
        evidence="log://uptime",
        note="old uptime check",
    )

    with pytest.raises(ValueError, match="expired"):
        book.add(SignedAttestation.sign(expired, auditor), now=120)

