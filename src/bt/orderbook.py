"""Deterministic local order book."""

from __future__ import annotations

from dataclasses import dataclass

from .models import BUY, SELL, Pair, SignedOrder, Trade
from .trust import TrustBook


@dataclass
class BookEntry:
    signed_order: SignedOrder
    remaining_atoms: int

    @property
    def order_id(self) -> str:
        return self.signed_order.order_id

    @property
    def maker(self) -> str:
        return self.signed_order.order.maker


class OrderBook:
    def __init__(self, pair: Pair) -> None:
        self.pair = pair
        self._entries: dict[str, BookEntry] = {}

    def add(self, signed_order: SignedOrder, now: int | None = None, verify_signature: bool = True) -> str:
        order = signed_order.order
        if order.pair != self.pair:
            raise ValueError(f"order pair {order.pair.symbol} does not match book {self.pair.symbol}")
        if now is not None and order.expires_at <= now:
            raise ValueError("order is expired")
        if verify_signature and not signed_order.verify():
            raise ValueError("order signature is invalid")
        if signed_order.order_id not in self._entries:
            self._entries[signed_order.order_id] = BookEntry(signed_order, order.quantity_atoms)
        return signed_order.order_id

    def open_orders(self, side: str | None = None, now: int | None = None) -> list[BookEntry]:
        entries = []
        for entry in self._entries.values():
            order = entry.signed_order.order
            if entry.remaining_atoms <= 0:
                continue
            if entry.remaining_atoms < order.min_quantity_atoms:
                continue
            if now is not None and order.expires_at <= now:
                continue
            if side is not None and order.side != side:
                continue
            entries.append(entry)
        return entries

    def match(self, now: int | None = None, trust_book: TrustBook | None = None) -> list[Trade]:
        trades: list[Trade] = []
        while True:
            buys = sorted(
                self.open_orders(BUY, now),
                key=lambda entry: (-entry.signed_order.order.price_atoms, entry.signed_order.order.created_at, entry.order_id),
            )
            sells = sorted(
                self.open_orders(SELL, now),
                key=lambda entry: (entry.signed_order.order.price_atoms, entry.signed_order.order.created_at, entry.order_id),
            )
            matched = self._next_match(buys, sells, trust_book)
            if matched is None:
                break
            buy, sell = matched
            buy_order = buy.signed_order.order
            sell_order = sell.signed_order.order
            if buy_order.price_atoms < sell_order.price_atoms:
                break

            quantity_atoms = min(buy.remaining_atoms, sell.remaining_atoms)

            resting = buy_order if (buy_order.created_at, buy.order_id) <= (sell_order.created_at, sell.order_id) else sell_order
            trade = Trade(
                pair=self.pair,
                price_atoms=resting.price_atoms,
                quantity_atoms=quantity_atoms,
                buy_order_id=buy.order_id,
                sell_order_id=sell.order_id,
                buy_maker=buy_order.maker,
                sell_maker=sell_order.maker,
                created_at=max(buy_order.created_at, sell_order.created_at),
            )
            buy.remaining_atoms -= quantity_atoms
            sell.remaining_atoms -= quantity_atoms
            trades.append(trade)
        return trades

    def _next_match(
        self,
        buys: list[BookEntry],
        sells: list[BookEntry],
        trust_book: TrustBook | None,
    ) -> tuple[BookEntry, BookEntry] | None:
        for buy in buys:
            for sell in sells:
                # Self-trade / wash-trade prevention: a single maker must not
                # match their own crossing buy and sell (fake volume / price
                # and trust-history manipulation).
                if buy.maker == sell.maker:
                    continue
                if buy.signed_order.order.price_atoms < sell.signed_order.order.price_atoms:
                    continue
                quantity_atoms = min(buy.remaining_atoms, sell.remaining_atoms)
                if quantity_atoms < buy.signed_order.order.min_quantity_atoms or quantity_atoms < sell.signed_order.order.min_quantity_atoms:
                    continue
                if self._trust_allows(buy, sell, trust_book):
                    return buy, sell
        return None

    @staticmethod
    def _trust_allows(buy: BookEntry, sell: BookEntry, trust_book: TrustBook | None) -> bool:
        if trust_book is None:
            return buy.signed_order.order.trust_min == 0 and sell.signed_order.order.trust_min == 0
        buy_requires = buy.signed_order.order.trust_min
        sell_requires = sell.signed_order.order.trust_min
        return trust_book.score(sell.maker) >= buy_requires and trust_book.score(buy.maker) >= sell_requires
