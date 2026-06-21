"""Readiness checks before a BT market is used with real funds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .chains import get_asset_profile, get_chain_profile, pair_contains_pls
from .models import Pair


SIGNED_DRY_RUN = "signed_dry_run"
REAL_FUNDS = "real_funds"
INFO = "info"
WARNING = "warning"
BLOCKER = "blocker"


@dataclass(frozen=True)
class ReadinessCheck:
    code: str
    severity: str
    passed: bool
    message: str
    remedy: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "passed": self.passed,
            "remedy": self.remedy,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class DexReadinessReport:
    pair: Pair
    mode: str
    checks: tuple[ReadinessCheck, ...]

    @property
    def blockers(self) -> tuple[ReadinessCheck, ...]:
        return tuple(check for check in self.checks if check.severity == BLOCKER and not check.passed)

    @property
    def warnings(self) -> tuple[ReadinessCheck, ...]:
        return tuple(check for check in self.checks if check.severity == WARNING and not check.passed)

    @property
    def ready(self) -> bool:
        return not self.blockers

    @property
    def real_funds_ready(self) -> bool:
        return self.mode == REAL_FUNDS and self.ready

    def explain(self) -> str:
        if self.ready:
            if self.mode == REAL_FUNDS:
                return f"{self.pair.symbol} is ready for real-funds submission under the supplied adapter evidence."
            return f"{self.pair.symbol} is ready for signed dry-run orders; no funds move yet."
        first = self.blockers[0]
        return f"{self.pair.symbol} is not ready for {self.mode}: {first.message}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": [check.to_dict() for check in self.checks],
            "explanation": self.explain(),
            "mode": self.mode,
            "pair": self.pair.symbol,
            "ready": self.ready,
            "real_funds_ready": self.real_funds_ready,
        }


def assess_pair_readiness(
    pair: Pair,
    *,
    mode: str = SIGNED_DRY_RUN,
    settlement_contract: str = "",
    audit_reference: str = "",
) -> DexReadinessReport:
    if mode not in {SIGNED_DRY_RUN, REAL_FUNDS}:
        raise ValueError(f"unknown readiness mode: {mode}")

    checks: list[ReadinessCheck] = []
    base_chain = get_chain_profile(pair.base.chain)
    quote_chain = get_chain_profile(pair.quote.chain)

    for side, asset, chain in (("base", pair.base, base_chain), ("quote", pair.quote, quote_chain)):
        checks.append(
            ReadinessCheck(
                code=f"{side}_chain_supported",
                severity=INFO if chain is not None else BLOCKER,
                passed=chain is not None,
                message=(
                    f"{asset.chain} is registered as a supported chain for {side} {asset.symbol}."
                    if chain is not None
                    else f"{asset.chain} is not registered as a supported chain for {side} {asset.symbol}."
                ),
                remedy="" if chain is not None else "Add a ChainProfile before accepting orders on this chain.",
            )
        )
        profile = get_asset_profile(asset)
        if profile is None:
            checks.append(
                ReadinessCheck(
                    code=f"{side}_asset_profile",
                    severity=BLOCKER if mode == REAL_FUNDS else WARNING,
                    passed=False,
                    message=f"{side} asset {asset.symbol} has no verified BT asset profile.",
                    remedy="Register the token contract, decimals, risk grade, and verification source.",
                )
            )
        elif mode == REAL_FUNDS and not profile.real_funds_eligible:
            checks.append(
                ReadinessCheck(
                    code=f"{side}_asset_real_funds",
                    severity=BLOCKER,
                    passed=False,
                    message=f"{side} asset {asset.symbol} is registered only as {profile.grade}.",
                    remedy=profile.note,
                )
            )
        else:
            checks.append(
                ReadinessCheck(
                    code=f"{side}_asset_profile",
                    severity=INFO,
                    passed=True,
                    message=f"{side} asset {asset.symbol} profile is known: {profile.grade}.",
                )
            )

    same_chain = pair.base.chain.lower() == pair.quote.chain.lower()
    if same_chain and base_chain and base_chain.evm and base_chain.supports_contract_locks:
        checks.append(
            ReadinessCheck(
                code="settlement_route",
                severity=INFO,
                passed=True,
                message=f"{pair.symbol} can use a same-chain escrow route on {base_chain.display_name}.",
            )
        )
    else:
        checks.append(
            ReadinessCheck(
                code="settlement_route",
                severity=BLOCKER if mode == REAL_FUNDS else WARNING,
                passed=False,
                message=f"{pair.symbol} needs a cross-chain or non-EVM settlement adapter.",
                remedy="Add a tested HTLC/bridge adapter before accepting real-funds orders.",
            )
        )

    checks.append(
        ReadinessCheck(
            code="pls_market",
            severity=INFO if pair_contains_pls(pair) else WARNING,
            passed=pair_contains_pls(pair),
            message="Pair contains native PLS." if pair_contains_pls(pair) else "Pair does not contain native PLS.",
            remedy="Use PLS as base or quote for a PulseChain-focused market.",
        )
    )

    if mode == REAL_FUNDS:
        checks.append(
            ReadinessCheck(
                code="settlement_contract",
                severity=BLOCKER,
                passed=bool(settlement_contract and not settlement_contract.startswith("demo:")),
                message="A production settlement contract is registered." if settlement_contract else "No production settlement contract is registered.",
                remedy="Deploy and configure the audited PulseChain escrow/HTLC contract address.",
            )
        )
        checks.append(
            ReadinessCheck(
                code="audit_reference",
                severity=BLOCKER,
                passed=bool(audit_reference),
                message="Audit reference is present." if audit_reference else "No independent audit reference is present.",
                remedy="Attach an audit report or formal verification artifact before real funds.",
            )
        )
    else:
        checks.append(
            ReadinessCheck(
                code="dry_run_scope",
                severity=INFO,
                passed=True,
                message="Signed orders, matching, trust scoring, and settlement plans can be tested without moving funds.",
            )
        )

    return DexReadinessReport(pair=pair, mode=mode, checks=tuple(checks))
