"""Chain and asset registry for BT markets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Asset, Pair


KNITWEB = "knitweb"
ETHEREUM = "ethereum"
BITCOIN = "bitcoin"


@dataclass(frozen=True)
class ChainProfile:
    key: str
    display_name: str
    chain_id: int | None
    native_symbol: str
    native_decimals: int
    finality_blocks: int
    expected_finality_seconds: int
    evm: bool
    supports_contract_locks: bool
    explorer_tx_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "display_name": self.display_name,
            "evm": self.evm,
            "expected_finality_seconds": self.expected_finality_seconds,
            "explorer_tx_url": self.explorer_tx_url,
            "finality_blocks": self.finality_blocks,
            "key": self.key,
            "native_decimals": self.native_decimals,
            "native_symbol": self.native_symbol,
            "supports_contract_locks": self.supports_contract_locks,
        }


@dataclass(frozen=True)
class AssetProfile:
    asset: Asset
    real_funds_eligible: bool
    grade: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset.to_dict(),
            "grade": self.grade,
            "note": self.note,
            "real_funds_eligible": self.real_funds_eligible,
        }


CHAIN_PROFILES = {
    KNITWEB: ChainProfile(
        key=KNITWEB,
        display_name="Knitweb",
        chain_id=None,
        native_symbol="PULSE",
        native_decimals=18,
        finality_blocks=12,
        expected_finality_seconds=120,
        evm=False,
        supports_contract_locks=True,
        explorer_tx_url="",
    ),
    ETHEREUM: ChainProfile(
        key=ETHEREUM,
        display_name="Ethereum",
        chain_id=1,
        native_symbol="ETH",
        native_decimals=18,
        finality_blocks=64,
        expected_finality_seconds=768,
        evm=True,
        supports_contract_locks=True,
        explorer_tx_url="https://etherscan.io/tx/{tx_hash}",
    ),
    BITCOIN: ChainProfile(
        key=BITCOIN,
        display_name="Bitcoin",
        chain_id=None,
        native_symbol="BTC",
        native_decimals=8,
        finality_blocks=6,
        expected_finality_seconds=3600,
        evm=False,
        supports_contract_locks=True,
        explorer_tx_url="https://mempool.space/tx/{tx_hash}",
    ),
}


PULSE = Asset("PULSE", KNITWEB, decimals=18)
BT_ON_KNITWEB = Asset("BT", KNITWEB, address="demo:bt", decimals=8)


def asset_key(asset: Asset) -> tuple[str, str, str]:
    return (asset.chain.lower(), asset.symbol.upper(), asset.address.lower())


ASSET_PROFILES = {
    asset_key(PULSE): AssetProfile(
        asset=PULSE,
        real_funds_eligible=True,
        grade="native-chain-asset",
        note="Native PULSE can be locked by a Knitweb adapter without token allowance risk.",
    ),
    asset_key(BT_ON_KNITWEB): AssetProfile(
        asset=BT_ON_KNITWEB,
        real_funds_eligible=False,
        grade="demo-protocol-asset",
        note="BT is a protocol unit here; no production Knitweb token contract is registered.",
    ),
}


def get_chain_profile(chain: str) -> ChainProfile | None:
    return CHAIN_PROFILES.get(chain.lower())


def require_chain_profile(chain: str) -> ChainProfile:
    profile = get_chain_profile(chain)
    if profile is None:
        raise ValueError(f"unsupported chain: {chain}")
    return profile


def get_asset_profile(asset: Asset) -> AssetProfile | None:
    return ASSET_PROFILES.get(asset_key(asset))


def is_pulse_asset(asset: Asset) -> bool:
    return asset.chain.lower() == KNITWEB and asset.symbol.upper() == "PULSE" and not asset.address


def pair_contains_pulse(pair: Pair) -> bool:
    return is_pulse_asset(pair.base) or is_pulse_asset(pair.quote)
