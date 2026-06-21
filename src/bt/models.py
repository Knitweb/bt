"""Market records for signed BT orders and deterministic trades."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import canonical_bytes, peer_id, record_id
from .keys import Keypair, verify
from .money import BT_DECIMALS, format_units, parse_units, quote_amount_atoms, validate_atoms


BUY = "buy"
SELL = "sell"
SIDES = {BUY, SELL}


@dataclass(frozen=True)
class Asset:
    symbol: str
    chain: str
    address: str = ""
    decimals: int = BT_DECIMALS

    def __post_init__(self) -> None:
        if not self.symbol or not self.chain:
            raise ValueError("asset symbol and chain are required")
        if self.decimals < 0:
            raise ValueError("asset decimals must be non-negative")

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "chain": self.chain,
            "decimals": self.decimals,
            "symbol": self.symbol,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Asset":
        return cls(
            symbol=str(value["symbol"]),
            chain=str(value["chain"]),
            address=str(value.get("address", "")),
            decimals=int(value.get("decimals", 18)),
        )


@dataclass(frozen=True)
class Pair:
    base: Asset
    quote: Asset

    def __post_init__(self) -> None:
        if self.base == self.quote:
            raise ValueError("pair assets must differ")

    @property
    def symbol(self) -> str:
        return f"{self.base.symbol}/{self.quote.symbol}"

    def to_dict(self) -> dict[str, Any]:
        return {"base": self.base.to_dict(), "quote": self.quote.to_dict()}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Pair":
        return cls(base=Asset.from_dict(value["base"]), quote=Asset.from_dict(value["quote"]))


@dataclass(frozen=True)
class Order:
    maker: str
    pair: Pair
    side: str
    price_atoms: int
    quantity_atoms: int
    expires_at: int
    nonce: str
    created_at: int
    min_quantity_atoms: int = 0
    trust_min: int = 0
    settlement: str = "atomic-swap"

    def __post_init__(self) -> None:
        if self.side not in SIDES:
            raise ValueError("order side must be buy or sell")
        if not self.maker.startswith("peer_"):
            raise ValueError("maker must be a BT peer id")
        if not self.nonce:
            raise ValueError("nonce is required")
        if isinstance(self.expires_at, bool) or isinstance(self.created_at, bool):
            raise ValueError("timestamps must be integers")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        if not 0 <= self.trust_min <= 100:
            raise ValueError("trust_min must be between 0 and 100")
        validate_atoms(self.price_atoms, field="price_atoms")
        validate_atoms(self.quantity_atoms, field="quantity_atoms")
        validate_atoms(self.min_quantity_atoms, field="min_quantity_atoms", allow_zero=True)
        if self.min_quantity_atoms > self.quantity_atoms:
            raise ValueError("min_quantity_atoms must be between zero and quantity_atoms")

    @classmethod
    def from_human(
        cls,
        *,
        maker: str,
        pair: Pair,
        side: str,
        price: str,
        quantity: str,
        expires_at: int,
        nonce: str,
        created_at: int,
        min_quantity: str = "0",
        trust_min: int = 0,
        settlement: str = "atomic-swap",
    ) -> "Order":
        return cls(
            maker=maker,
            pair=pair,
            side=side,
            price_atoms=parse_units(price, pair.quote.decimals),
            quantity_atoms=parse_units(quantity, pair.base.decimals),
            min_quantity_atoms=parse_units(min_quantity, pair.base.decimals),
            expires_at=expires_at,
            nonce=nonce,
            created_at=created_at,
            trust_min=trust_min,
            settlement=settlement,
        )

    @property
    def order_id(self) -> str:
        return record_id("ord", self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "maker": self.maker,
            "min_quantity_atoms": self.min_quantity_atoms,
            "nonce": self.nonce,
            "pair": self.pair.to_dict(),
            "price_atoms": self.price_atoms,
            "quantity_atoms": self.quantity_atoms,
            "settlement": self.settlement,
            "side": self.side,
            "trust_min": self.trust_min,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Order":
        return cls(
            maker=str(value["maker"]),
            pair=Pair.from_dict(value["pair"]),
            side=str(value["side"]),
            price_atoms=int(value["price_atoms"]) if "price_atoms" in value else parse_units(str(value["price"])),
            quantity_atoms=int(value["quantity_atoms"]) if "quantity_atoms" in value else parse_units(str(value["quantity"])),
            min_quantity_atoms=int(value.get("min_quantity_atoms", 0))
            if "min_quantity_atoms" in value
            else parse_units(str(value.get("min_quantity", "0"))),
            expires_at=int(value["expires_at"]),
            nonce=str(value["nonce"]),
            created_at=int(value["created_at"]),
            trust_min=int(value.get("trust_min", 0)),
            settlement=str(value.get("settlement", "atomic-swap")),
        )


@dataclass(frozen=True)
class SignedOrder:
    order: Order
    public_key: str
    signature: str

    @classmethod
    def sign(cls, order: Order, keypair: Keypair) -> "SignedOrder":
        if order.maker != keypair.peer_id:
            raise ValueError("order maker does not match signing key")
        return cls(order=order, public_key=keypair.public_hex, signature=keypair.sign(canonical_bytes(order)))

    @property
    def order_id(self) -> str:
        return self.order.order_id

    def verify(self) -> bool:
        return peer_id(self.public_key) == self.order.maker and verify(
            self.public_key,
            canonical_bytes(self.order),
            self.signature,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "order": self.order.to_dict(),
            "order_id": self.order_id,
            "public_key": self.public_key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "SignedOrder":
        order = Order.from_dict(value["order"])
        signed = cls(order=order, public_key=str(value["public_key"]), signature=str(value["signature"]))
        if value.get("order_id") and value["order_id"] != signed.order_id:
            raise ValueError("signed order id does not match payload")
        return signed


@dataclass(frozen=True)
class Trade:
    pair: Pair
    price_atoms: int
    quantity_atoms: int
    buy_order_id: str
    sell_order_id: str
    buy_maker: str
    sell_maker: str
    created_at: int

    @property
    def trade_id(self) -> str:
        return record_id("trd", self.to_dict(include_id=False))

    @property
    def quote_quantity_atoms(self) -> int:
        return quote_amount_atoms(self.price_atoms, self.quantity_atoms, self.pair.base.decimals)

    def to_dict(self, include_id: bool = True) -> dict[str, Any]:
        data = {
            "buy_maker": self.buy_maker,
            "buy_order_id": self.buy_order_id,
            "created_at": self.created_at,
            "pair": self.pair.to_dict(),
            "price_atoms": self.price_atoms,
            "price_display": format_units(self.price_atoms, self.pair.quote.decimals),
            "quantity_atoms": self.quantity_atoms,
            "quantity_display": format_units(self.quantity_atoms, self.pair.base.decimals),
            "quote_quantity_atoms": self.quote_quantity_atoms,
            "quote_quantity_display": format_units(self.quote_quantity_atoms, self.pair.quote.decimals),
            "sell_maker": self.sell_maker,
            "sell_order_id": self.sell_order_id,
        }
        if include_id:
            data["trade_id"] = self.trade_id
        return data

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Trade":
        trade = cls(
            pair=Pair.from_dict(value["pair"]),
            price_atoms=int(value["price_atoms"]),
            quantity_atoms=int(value["quantity_atoms"]),
            buy_order_id=str(value["buy_order_id"]),
            sell_order_id=str(value["sell_order_id"]),
            buy_maker=str(value["buy_maker"]),
            sell_maker=str(value["sell_maker"]),
            created_at=int(value["created_at"]),
        )
        if value.get("trade_id") and value["trade_id"] != trade.trade_id:
            raise ValueError("trade id does not match payload")
        return trade
