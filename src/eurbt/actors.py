"""Transaction actor authorisation.

EURBT accepts transactions from identified people, agents owned by identified
people, or the VoteBank DAO. This keeps instant receiver UX tied to accountable
actors instead of anonymous keys.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


PERSON = "person"
AGENT = "agent"
VOTEBANK_DAO = "votebank_dao"
ACTOR_TYPES = {PERSON, AGENT, VOTEBANK_DAO}


@dataclass(frozen=True)
class Actor:
    actor_id: str
    actor_type: str
    peer_id: str
    owner_person_id: str = ""
    identified: bool = False

    def __post_init__(self) -> None:
        if self.actor_type not in ACTOR_TYPES:
            raise ValueError(f"unknown actor type: {self.actor_type}")
        if not self.actor_id:
            raise ValueError("actor_id is required")
        if not self.peer_id.startswith("peer_"):
            raise ValueError("peer_id must be a peer id")

    @property
    def can_transact(self) -> bool:
        if self.actor_type == PERSON:
            return self.identified
        if self.actor_type == AGENT:
            return bool(self.owner_person_id) and self.identified
        if self.actor_type == VOTEBANK_DAO:
            return self.identified
        return False

    @property
    def instant_receivable(self) -> bool:
        return self.can_transact

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "identified": self.identified,
            "owner_person_id": self.owner_person_id,
            "peer_id": self.peer_id,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Actor":
        return cls(
            actor_id=str(value["actor_id"]),
            actor_type=str(value["actor_type"]),
            peer_id=str(value["peer_id"]),
            owner_person_id=str(value.get("owner_person_id", "")),
            identified=bool(value.get("identified", False)),
        )


class ActorRegistry:
    def __init__(self) -> None:
        self._actors_by_peer: dict[str, Actor] = {}

    def add(self, actor: Actor) -> None:
        self._actors_by_peer[actor.peer_id] = actor

    def get(self, peer_id: str) -> Actor | None:
        return self._actors_by_peer.get(peer_id)

    def require_transactor(self, peer_id: str) -> Actor:
        actor = self.get(peer_id)
        if actor is None:
            raise ValueError("transaction actor is not registered")
        if not actor.can_transact:
            raise ValueError("transaction actor is not authorised")
        return actor

    def instant_receivable(self, peer_id: str) -> bool:
        actor = self.get(peer_id)
        return bool(actor and actor.instant_receivable)

