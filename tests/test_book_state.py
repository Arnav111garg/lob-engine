import pytest
from lob_analytics.types import Side
from lob_analytics.core.order import Order
from lob_analytics.core.book_state import OrderBook


def test_empty_book():
    book = OrderBook()
    assert book.best_bid() is None
    assert book.best_ask() is None
    assert book.spread() is None
    assert book.mid_price() is None
    assert book.is_healthy()


def test_add_orders_and_best_prices():
    book = OrderBook()

    # Add bid at 100, ask at 101
    book.add_order(Order(order_id=1, seq=1, side=Side.BID, price=100, quantity=50))
    book.add_order(Order(order_id=2, seq=2, side=Side.ASK, price=101, quantity=30))

    assert book.best_bid() == 100
    assert book.best_ask() == 101
    assert book.spread() == 1
    assert book.mid_price() == 100.5
    assert book.is_healthy()

    # Deeper bid at 99 should not change best
    book.add_order(Order(order_id=3, seq=3, side=Side.BID, price=99, quantity=10))
    assert book.best_bid() == 100
    assert book.is_healthy()


def test_loc_index_tracks_orders():
    book = OrderBook()
    o1 = Order(order_id=10, seq=1, side=Side.BID, price=100, quantity=10)
    o2 = Order(order_id=20, seq=2, side=Side.ASK, price=101, quantity=20)

    book.add_order(o1)
    book.add_order(o2)

    assert book.loc[10] == (Side.BID, 100)
    assert book.loc[20] == (Side.ASK, 101)


def test_delete_middle_order_preserves_priority():
    """
    Chapter 9, Section 9.2: Deleting a mid-queue order preserves
    relative priority of everyone else.
    """
    book = OrderBook()
    book.add_order(Order(order_id=1, seq=1, side=Side.BID, price=100, quantity=10))
    book.add_order(Order(order_id=2, seq=2, side=Side.BID, price=100, quantity=20))
    book.add_order(Order(order_id=3, seq=3, side=Side.BID, price=100, quantity=30))

    # Delete the middle order
    book.delete_order(order_id=2)

    level = book.bids[100]
    orders = list(level)
    assert len(orders) == 2
    assert orders[0].order_id == 1
    assert orders[1].order_id == 3
    assert level.total_depth() == 40
    assert 2 not in book.loc
    assert book.is_healthy()


def test_cancel_partial():
    book = OrderBook()
    book.add_order(Order(order_id=1, seq=1, side=Side.BID, price=100, quantity=100))

    book.cancel_order(order_id=1, amount=30)

    assert book.depth_at(Side.BID, 100) == 70
    assert 1 in book.loc  # Order still resting
    assert book.bids[100].total_depth() == 70
    assert book.is_healthy()


def test_cancel_full_becomes_delete():
    book = OrderBook()
    book.add_order(Order(order_id=1, seq=1, side=Side.BID, price=100, quantity=50))

    book.cancel_order(order_id=1, amount=50)

    assert book.depth_at(Side.BID, 100) == 0
    assert 100 not in book.bids  # Price level removed when empty
    assert 1 not in book.loc
    assert book.is_healthy()


def test_execute_full_removes_order():
    book = OrderBook()
    book.add_order(Order(order_id=1, seq=1, side=Side.ASK, price=101, quantity=25))

    book.execute_order(order_id=1, amount=25)

    assert 101 not in book.asks
    assert 1 not in book.loc
    assert book.is_healthy()


def test_crossed_book_is_unhealthy():
    """
    Proposition 3.1 says a well-formed stream cannot produce this.
    But our engine must detect it if it ever happens (bug or bad data).
    """
    book = OrderBook()
    book.add_order(Order(order_id=1, seq=1, side=Side.BID, price=102, quantity=10))
    book.add_order(Order(order_id=2, seq=2, side=Side.ASK, price=101, quantity=10))

    assert not book.is_healthy()


def test_snapshot_level2_format():
    book = OrderBook()
    for i in range(1, 4):
        book.add_order(Order(order_id=i, seq=i, side=Side.BID, price=100 + i, quantity=10))
        book.add_order(Order(order_id=10 + i, seq=10 + i, side=Side.ASK, price=104 + i, quantity=10))

    snap = book.snapshot_level2(top_n=2)
    # Bids should be best-first: 103, 102
    assert snap["bids"] == [(103, 10), (102, 10)]
    # Asks should be best-first: 105, 106
    assert snap["asks"] == [(105, 10), (106, 10)]
    assert snap["best_bid"] == 103
    assert snap["best_ask"] == 105
    assert snap["spread"] == 2


def test_unknown_identifier_raises():
    book = OrderBook()
    with pytest.raises(KeyError):
        book.delete_order(order_id=999)