from __future__ import annotations

import pytest

from bt.actors import AGENT, PERSON, VOTEBANK_DAO, Actor, ActorRegistry
from bt.money import parse_units
from bt.transactions import INSTANT_ACCEPTED, SignedTransfer, Transfer, receive_transfer


def test_identified_person_transfer_is_instant_for_identified_receiver(pair, buyer, seller):
    registry = ActorRegistry()
    registry.add(Actor("person:buyer", PERSON, buyer.peer_id, identified=True))
    registry.add(Actor("person:seller", PERSON, seller.peer_id, identified=True))
    transfer = Transfer(
        sender=buyer.peer_id,
        receiver=seller.peer_id,
        asset=pair.quote,
        amount_atoms=parse_units("12.50"),
        created_at=100,
        nonce="tx-1",
    )

    receipt = receive_transfer(SignedTransfer.sign(transfer, buyer), registry)

    assert receipt.status == INSTANT_ACCEPTED
    assert receipt.receiver == seller.peer_id


def test_owned_agent_and_votebank_dao_can_transact(pair, buyer, seller):
    registry = ActorRegistry()
    registry.add(Actor("agent:buyer", AGENT, buyer.peer_id, owner_person_id="person:owner", identified=True))
    registry.add(Actor("dao:vbank", VOTEBANK_DAO, seller.peer_id, identified=True))
    transfer = Transfer(
        sender=buyer.peer_id,
        receiver=seller.peer_id,
        asset=pair.quote,
        amount_atoms=parse_units("1"),
        created_at=100,
        nonce="tx-agent",
    )

    receipt = receive_transfer(SignedTransfer.sign(transfer, buyer), registry)

    assert receipt.status == INSTANT_ACCEPTED
    assert "agent" in receipt.reason


def test_unidentified_agent_is_rejected(pair, buyer, seller):
    registry = ActorRegistry()
    registry.add(Actor("agent:buyer", AGENT, buyer.peer_id, owner_person_id="", identified=True))
    registry.add(Actor("person:seller", PERSON, seller.peer_id, identified=True))
    transfer = Transfer(
        sender=buyer.peer_id,
        receiver=seller.peer_id,
        asset=pair.quote,
        amount_atoms=parse_units("1"),
        created_at=100,
        nonce="tx-reject",
    )

    with pytest.raises(ValueError, match="not authorised"):
        receive_transfer(SignedTransfer.sign(transfer, buyer), registry)

