"""High-level EURBT market facade."""

from __future__ import annotations

from .models import Pair, SignedOrder, Trade
from .orderbook import OrderBook
from .p2p import Envelope, PeerStore
from .settlement import SettlementPlan, plan_settlement
from .trust import SignedAttestation, TrustBook


class EurbtMarket:
    def __init__(self, pair: Pair, trust_book: TrustBook | None = None) -> None:
        self.pair = pair
        self.orderbook = OrderBook(pair)
        self.trust_book = trust_book or TrustBook()
        self.peer_store = PeerStore()

    def submit_order(self, signed_order: SignedOrder, now: int | None = None) -> str:
        return self.orderbook.add(signed_order, now=now)

    def submit_attestation(self, signed_attestation: SignedAttestation, now: int | None = None) -> str:
        return self.trust_book.add(signed_attestation, now=now)

    def ingest_envelope(self, envelope: Envelope, now: int | None = None) -> bool:
        inserted = self.peer_store.ingest(envelope)
        if not inserted:
            return False
        if envelope.message_type == "order":
            self.submit_order(SignedOrder.from_dict(envelope.payload), now=now)
        elif envelope.message_type == "attestation":
            self.submit_attestation(SignedAttestation.from_dict(envelope.payload), now=now)
        return True

    def match(self, now: int | None = None) -> list[Trade]:
        return self.orderbook.match(now=now, trust_book=self.trust_book)

    def settlement_plan(self, trade: Trade) -> SettlementPlan:
        return plan_settlement(trade)

    def explain_peer(self, peer_id: str, now: int | None = None) -> str:
        return self.trust_book.explain(peer_id, now=now)

