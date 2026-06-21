"""Auditable settlement plans.

These records describe how a matched trade should settle. They do not move funds.
Adapters can later turn a plan into EVM transactions, XRPL Offers, Sui PTBs, Bitcoin
HTLCs, SEPA proof workflows, or Knitweb records.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .chains import KNITWEB, get_chain_profile
from .canonical import record_id
from .models import Asset, Pair, Trade
from .money import format_units, max_atoms_for_decimals, validate_atoms


@dataclass(frozen=True)
class SettlementLeg:
    action: str
    party: str
    asset: Asset
    amount_atoms: int
    condition: str

    def __post_init__(self) -> None:
        validate_atoms(self.amount_atoms, field="amount_atoms", max_atoms=max_atoms_for_decimals(self.asset.decimals))

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "amount_atoms": self.amount_atoms,
            "amount_display": format_units(self.amount_atoms, self.asset.decimals),
            "asset": self.asset.to_dict(),
            "condition": self.condition,
            "party": self.party,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SettlementLeg":
        return cls(
            action=str(value["action"]),
            party=str(value["party"]),
            asset=Asset.from_dict(value["asset"]),
            amount_atoms=int(value["amount_atoms"]),
            condition=str(value["condition"]),
        )


@dataclass(frozen=True)
class SettlementPlan:
    trade_id: str
    route: str
    legs: tuple[SettlementLeg, ...]
    risk_notes: tuple[str, ...]

    @property
    def plan_id(self) -> str:
        return record_id("stl", self.to_dict(include_id=False))

    def to_dict(self, include_id: bool = True) -> dict[str, Any]:
        data = {
            "legs": [leg.to_dict() for leg in self.legs],
            "risk_notes": list(self.risk_notes),
            "route": self.route,
            "trade_id": self.trade_id,
        }
        if include_id:
            data["plan_id"] = self.plan_id
        return data

    def explain(self) -> str:
        steps = [
            f"{index + 1}. {leg.party} must {leg.action} {format_units(leg.amount_atoms, leg.asset.decimals)} {leg.asset.symbol}: {leg.condition}"
            for index, leg in enumerate(self.legs)
        ]
        notes = " ".join(self.risk_notes)
        return f"Settlement route: {self.route}. " + " ".join(steps) + (" Risks: " + notes if notes else "")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SettlementPlan":
        plan = cls(
            trade_id=str(value["trade_id"]),
            route=str(value["route"]),
            legs=tuple(SettlementLeg.from_dict(item) for item in value["legs"]),
            risk_notes=tuple(str(item) for item in value.get("risk_notes", [])),
        )
        if value.get("plan_id") and value["plan_id"] != plan.plan_id:
            raise ValueError("settlement plan id does not match payload")
        return plan


def route_for_pair(pair: Pair) -> str:
    base_chain = pair.base.chain.lower()
    quote_chain = pair.quote.chain.lower()
    if base_chain == quote_chain == KNITWEB:
        return "knitweb-audited-escrow-required"
    if base_chain == KNITWEB or quote_chain == KNITWEB:
        return "knitweb-cross-chain-adapter-required"
    return "crypto-escrow-plus-anchor-proof"


def plan_settlement(trade: Trade, route: str = "") -> SettlementPlan:
    base = trade.pair.base
    quote = trade.pair.quote
    route = route or route_for_pair(trade.pair)
    base_chain = get_chain_profile(base.chain)
    quote_chain = get_chain_profile(quote.chain)
    same_chain = base.chain.lower() == quote.chain.lower()
    if same_chain and base_chain is not None:
        lock_condition = (
            f"seller locks {base.symbol} in a non-custodial {base_chain.display_name} escrow "
            f"until {base_chain.finality_blocks} settlement confirmations are observed"
        )
        pay_condition = (
            f"buyer locks {quote.symbol} in the same escrow or proves the agreed quote-side transfer "
            f"after {base_chain.finality_blocks} settlement confirmations"
        )
    else:
        lock_condition = "seller locks the base asset in a non-custodial escrow or HTLC"
        pay_condition = f"buyer locks {quote.symbol} or proves the agreed quote-side payment"
    risk_notes = [
        "This plan is non-custodial only after a network/payment adapter enforces every leg.",
        "External fiat or payment rails can still create chargeback and compliance risk.",
    ]
    if base.chain.lower() == KNITWEB or quote.chain.lower() == KNITWEB:
        risk_notes.append("Native PULSE should not be accepted with real funds until a deployed Knitweb adapter and audit reference are configured.")
    if base_chain is None or quote_chain is None:
        risk_notes.append("At least one network has no registered profile, so the plan is a dry-run artifact only.")
    return SettlementPlan(
        trade_id=trade.trade_id,
        route=route,
        legs=(
            SettlementLeg(
                action="lock",
                party=trade.sell_maker,
                asset=base,
                amount_atoms=trade.quantity_atoms,
                condition=lock_condition,
            ),
            SettlementLeg(
                action="lock-or-pay",
                party=trade.buy_maker,
                asset=quote,
                amount_atoms=trade.quote_quantity_atoms,
                condition=pay_condition,
            ),
            SettlementLeg(
                action="release",
                party=trade.sell_maker,
                asset=base,
                amount_atoms=trade.quantity_atoms,
                condition="base asset releases only after the quote-side proof is accepted",
            ),
        ),
        risk_notes=tuple(risk_notes),
    )
