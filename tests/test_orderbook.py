from __future__ import annotations

from bt.models import SELL, SignedOrder
from bt.orderbook import OrderBook

from .conftest import make_order


def test_orderbook_matches_crossed_orders_deterministically(pair, buyer, seller):
    book = OrderBook(pair)
    buy = SignedOrder.sign(
        make_order(buyer, pair, price="100", quantity="1", created_at=10, nonce="buy"),
        buyer,
    )
    sell = SignedOrder.sign(
        make_order(seller, pair, side=SELL, price="99", quantity="0.4", created_at=11, nonce="sell"),
        seller,
    )

    book.add(sell)
    book.add(buy)
    trades = book.match(now=12)

    assert len(trades) == 1
    assert trades[0].price_atoms == buy.order.price_atoms
    assert trades[0].quantity_atoms == sell.order.quantity_atoms
    assert trades[0].buy_maker == buyer.peer_id
    assert trades[0].sell_maker == seller.peer_id

    remaining_buy = book.open_orders(now=12)[0]
    assert remaining_buy.order_id == buy.order_id
    assert remaining_buy.remaining_atoms == buy.order.quantity_atoms - sell.order.quantity_atoms


def test_orderbook_prefers_best_sell_price(pair, buyer, seller):
    other_seller = seller.generate()
    book = OrderBook(pair)
    buy = SignedOrder.sign(
        make_order(buyer, pair, price="100", quantity="1", min_quantity="0.5", created_at=10, nonce="buy"),
        buyer,
    )
    expensive = SignedOrder.sign(
        make_order(seller, pair, side=SELL, price="99", quantity="1", created_at=11, nonce="expensive"),
        seller,
    )
    cheap = SignedOrder.sign(
        make_order(other_seller, pair, side=SELL, price="98", quantity="1", created_at=12, nonce="cheap"),
        other_seller,
    )

    for order in (expensive, cheap, buy):
        book.add(order)

    trades = book.match(now=13)

    assert trades[0].sell_order_id == cheap.order_id


def test_orderbook_skips_pair_that_cannot_satisfy_minimum_fill(pair, buyer, seller):
    other_seller = seller.generate()
    book = OrderBook(pair)
    buy = SignedOrder.sign(
        make_order(buyer, pair, price="100", quantity="1", min_quantity="0.5", created_at=10, nonce="buy"),
        buyer,
    )
    too_small = SignedOrder.sign(
        make_order(seller, pair, side=SELL, price="98", quantity="0.1", created_at=11, nonce="small"),
        seller,
    )
    viable = SignedOrder.sign(
        make_order(other_seller, pair, side=SELL, price="99", quantity="1", created_at=12, nonce="viable"),
        other_seller,
    )
    for order in (too_small, viable, buy):
        book.add(order)

    trades = book.match(now=13)

    assert len(trades) == 1
    assert trades[0].sell_order_id == viable.order_id


def test_orderbook_prevents_self_trade(pair, buyer, seller):
    # Regression: a single maker posting a crossing buy and sell must not
    # match against themselves (wash trading / fake volume). A genuine
    # counterparty sell at the same price must still match.
    book = OrderBook(pair)
    buy = SignedOrder.sign(
        make_order(buyer, pair, price="100", quantity="1", created_at=10, nonce="buy"),
        buyer,
    )
    self_sell = SignedOrder.sign(
        make_order(buyer, pair, side=SELL, price="99", quantity="1", created_at=11, nonce="self-sell"),
        buyer,
    )
    book.add(buy)
    book.add(self_sell)
    assert book.match(now=12) == []

    # A real counterparty crossing the same buy still trades.
    real_sell = SignedOrder.sign(
        make_order(seller, pair, side=SELL, price="99", quantity="1", created_at=12, nonce="real-sell"),
        seller,
    )
    book.add(real_sell)
    trades = book.match(now=13)
    assert len(trades) == 1
    assert trades[0].sell_order_id == real_sell.order_id
    assert trades[0].sell_maker == seller.peer_id
