from __future__ import annotations

from bt.models import Asset
from bt.money import BT_DECIMALS


def test_asset_from_dict_defaults_decimals_to_bt_decimals():
    # Regression: from_dict used to default to 18 while the dataclass default
    # is BT_DECIMALS (8). A serialized asset omitting "decimals" therefore
    # round-tripped to a different atom scale (off by 10**(18-8)), mispricing
    # every quantity/price derived from it.
    asset = Asset.from_dict({"symbol": "BTC", "chain": "bitcoin"})
    assert asset.decimals == BT_DECIMALS


def test_asset_dict_roundtrip_preserves_decimals():
    original = Asset("BT", "ethereum", "demo:bt", decimals=6)
    restored = Asset.from_dict(original.to_dict())
    assert restored == original
    assert restored.decimals == 6


def test_asset_default_construction_matches_from_dict_default():
    constructed = Asset("BTC", "bitcoin")
    serialized = Asset.from_dict({"symbol": "BTC", "chain": "bitcoin"})
    assert constructed.decimals == serialized.decimals
