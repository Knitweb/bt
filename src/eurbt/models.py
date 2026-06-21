"""Market records for signed EURBT orders and deterministic trades."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from .canonical import canonical_bytes, peer_id, record_id
from .keys import Keypair, verify


BUY = "buy"
SELL = "sell"
SIDES = {BUY, SELL}


def to_decimal(value: Decimal | str | int) -> Decimal:
    if isinstance(value, Decimal):
        result = value
    else:
        try:
            result = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValueError(f"invalid decimal value: {value!r}") from exc
    if not result.is_finite():
        raise ValueError(f"decimal value must be finite: {value!r}")
    return result


def decimal_text(value: Decimal) -> str:
    return format(value.normalize(), "f")


@dataclass(frozen=True)
class Asset:
    symbol: str
    chain: str
    address: str = ""
    decimals: int = 18

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
    price: Decimal
    quantity: Decimal
    expires_at: int
    nonce: str
    created_at: int
    min_quantity: Decimal = Decimal("0")
    trust_min: int = 0
    settlement: str = "atomic-swap"

    def __post_init__(self) -> None:
        if self.side not in SIDES:
            raise ValueError("order side must be buy or sell")
        if not self.maker.startswith("peer_"):
            raise ValueError("maker must be a EURBT peer id")
        if not self.nonce:
            raise ValueError("nonce is required")
        if isinstance(self.expires_at, bool) or isinstance(self.created_at, bool):
            raise ValueError("timestamps must be integers")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        if not 0 <= self.trust_min <= 100:
            raise ValueError("trust_min must be between 0 and 100")
        if self.price <= 0 or self.quantity <= 0:
            raise ValueError("price and quantity must be positive")
        if self.min_quantity < 0 or self.min_quantity > self.quantity:
            raise ValueError("min_quantity must be between zero and quantity")

    @property
    def order_id(self) -> str:
        return record_id("ord", self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "maker": self.maker,
            "min_quantity": decimal_text(self.min_quantity),
            "nonce": self.nonce,
            "pair": self.pair.to_dict(),
            "price": decimal_text(self.price),
            "quantity": decimal_text(self.quantity),
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
            price=to_decimal(value["price"]),
            quantity=to_decimal(value["quantity"]),
            min_quantity=to_decimal(value.get("min_quantity", "0")),
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
    price: Decimal
    quantity: Decimal
    buy_order_id: str
    sell_order_id: str
    buy_maker: str
    sell_maker: str
    created_at: int

    @property
    def trade_id(self) -> str:
        return record_id("trd", self.to_dict(include_id=False))

    @property
    def quote_quantity(self) -> Decimal:
        return self.price * self.quantity

    def to_dict(self, include_id: bool = True) -> dict[str, Any]:
        data = {
            "buy_maker": self.buy_maker,
            "buy_order_id": self.buy_order_id,
            "created_at": self.created_at,
            "pair": self.pair.to_dict(),
            "price": decimal_text(self.price),
            "quantity": decimal_text(self.quantity),
            "quote_quantity": decimal_text(self.quote_quantity),
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
            price=to_decimal(value["price"]),
            quantity=to_decimal(value["quantity"]),
            buy_order_id=str(value["buy_order_id"]),
            sell_order_id=str(value["sell_order_id"]),
            buy_maker=str(value["buy_maker"]),
            sell_maker=str(value["sell_maker"]),
            created_at=int(value["created_at"]),
        )
        if value.get("trade_id") and value["trade_id"] != trade.trade_id:
            raise ValueError("trade id does not match payload")
        return trade
