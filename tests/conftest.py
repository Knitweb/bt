from __future__ import annotations

from decimal import Decimal

import pytest

from eurbt.keys import Keypair
from eurbt.models import BUY, SELL, Asset, Order, Pair


@pytest.fixture
def pair() -> Pair:
    return Pair(Asset("BTC", "bitcoin", decimals=8), Asset("EURBT", "ethereum", "demo:eurbt"))


@pytest.fixture
def buyer() -> Keypair:
    return Keypair.generate()


@pytest.fixture
def seller() -> Keypair:
    return Keypair.generate()


@pytest.fixture
def auditor() -> Keypair:
    return Keypair.generate()


def make_order(
    keypair: Keypair,
    pair: Pair,
    side: str = BUY,
    price: str = "100",
    quantity: str = "1",
    min_quantity: str = "0",
    created_at: int = 100,
    trust_min: int = 0,
    nonce: str = "n",
) -> Order:
    return Order(
        maker=keypair.peer_id,
        pair=pair,
        side=side,
        price=Decimal(price),
        quantity=Decimal(quantity),
        min_quantity=Decimal(min_quantity),
        trust_min=trust_min,
        created_at=created_at,
        expires_at=created_at + 1000,
        nonce=nonce,
    )
