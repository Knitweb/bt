"""High-level BT market facade."""

from __future__ import annotations

from .actors import Actor, ActorRegistry
from .models import Pair, SignedOrder, Trade
from .orderbook import OrderBook
from .p2p import Envelope, PeerStore
from .readiness import REAL_FUNDS, DexReadinessReport, assess_pair_readiness
from .settlement import SettlementPlan, plan_settlement
from .trust import SignedAttestation, TrustBook


class BtMarket:
    def __init__(self, pair: Pair, trust_book: TrustBook | None = None, actor_registry: ActorRegistry | None = None) -> None:
        self.pair = pair
        self.orderbook = OrderBook(pair)
        self.trust_book = trust_book or TrustBook()
        self.actor_registry = actor_registry or ActorRegistry()
        self.peer_store = PeerStore()

    def register_actor(self, actor: Actor) -> None:
        self.actor_registry.add(actor)

    def submit_order(self, signed_order: SignedOrder, now: int | None = None) -> str:
        self.actor_registry.require_transactor(signed_order.order.maker)
        return self.orderbook.add(signed_order, now=now)

    def submit_real_funds_order(
        self,
        signed_order: SignedOrder,
        *,
        settlement_contract: str,
        audit_reference: str,
        now: int | None = None,
    ) -> str:
        report = self.readiness_report(
            mode=REAL_FUNDS,
            settlement_contract=settlement_contract,
            audit_reference=audit_reference,
        )
        if not report.real_funds_ready:
            raise ValueError(report.explain())
        return self.submit_order(signed_order, now=now)

    def readiness_report(
        self,
        *,
        mode: str = "signed_dry_run",
        settlement_contract: str = "",
        audit_reference: str = "",
    ) -> DexReadinessReport:
        return assess_pair_readiness(
            self.pair,
            mode=mode,
            settlement_contract=settlement_contract,
            audit_reference=audit_reference,
        )

    def submit_attestation(self, signed_attestation: SignedAttestation, now: int | None = None) -> str:
        return self.trust_book.add(signed_attestation, now=now)

    def ingest_envelope(self, envelope: Envelope, now: int | None = None) -> bool:
        # SECURITY: bind the envelope sender to the inner payload's authority.
        # peer_store.ingest verifies the envelope signature (→ sender) and the
        # inner order/attestation signature is verified downstream, but without
        # this check peer X could relay peer Y's validly-signed order/attestation
        # in an envelope X signed: both signatures verify, yet the message would be
        # recorded and reputation-/attribution-keyed to the wrong peer (sender X,
        # author Y). Reject the mismatch before it ever enters the peer store.
        parsed: SignedOrder | SignedAttestation | None = None
        if envelope.message_type == "order":
            parsed = SignedOrder.from_dict(envelope.payload)
            if envelope.sender != parsed.order.maker:
                raise ValueError("envelope sender does not match order maker")
        elif envelope.message_type == "attestation":
            parsed = SignedAttestation.from_dict(envelope.payload)
            if envelope.sender != parsed.attestation.issuer:
                raise ValueError("envelope sender does not match attestation issuer")

        inserted = self.peer_store.ingest(envelope)
        if not inserted:
            return False
        if isinstance(parsed, SignedOrder):
            self.submit_order(parsed, now=now)
        elif isinstance(parsed, SignedAttestation):
            self.submit_attestation(parsed, now=now)
        return True

    def match(self, now: int | None = None) -> list[Trade]:
        return self.orderbook.match(now=now, trust_book=self.trust_book)

    def settlement_plan(self, trade: Trade) -> SettlementPlan:
        return plan_settlement(trade)

    def explain_peer(self, peer_id: str, now: int | None = None) -> str:
        return self.trust_book.explain(peer_id, now=now)
