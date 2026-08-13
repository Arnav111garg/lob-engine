import pytest
from lob_analytics.types import Side, IncomingOrder, Trade
from lob_analytics.core.order import Order
from lob_analytics.core.book_state import OrderBook
from lob_analytics.engine.matching import MatchingEngine


def _make_book() -> OrderBook:
    """Helper: empty healthy book."""
    return OrderBook()


def test_market_buy_full_fill():
    book = _make_book()
    book.add_order(Order(1, 1, Side.ASK, 101, 50))
    engine = MatchingEngine(book)

    trades = engine.submit(IncomingOrder(99, 99, Side.BID, float('inf'), 30))

    assert len(trades) == 1
    assert trades[0] == Trade(101, 30, 1)
    assert book.depth_at(Side.ASK, 101) == 20
    assert book.is_healthy()


def test_market_buy_insufficient_liquidity():
    """Chapter 4, Section 4.4.2: unfilled market remainder is cancelled."""
    book = _make_book()
    book.add_order(Order(1, 1, Side.ASK, 101, 20))
    engine = MatchingEngine(book)

    trades = engine.submit(IncomingOrder(99, 99, Side.BID, float('inf'), 50))

    assert len(trades) == 1
    assert trades[0] == Trade(101, 20, 1)
    assert 101 not in book.asks  # Level empty
    assert 99 not in book.loc     # Remainder cancelled, not rested
    assert book.is_healthy()


def test_limit_buy_full_fill_no_rest():
    book = _make_book()
    book.add_order(Order(1, 1, Side.ASK, 101, 20))
    engine = MatchingEngine(book)

    trades = engine.submit(IncomingOrder(99, 99, Side.BID, 101, 10))

    assert len(trades) == 1
    assert trades[0] == Trade(101, 10, 1)
    assert book.depth_at(Side.ASK, 101) == 10
    assert 99 not in book.loc  # No remainder to rest
    assert book.is_healthy()


def test_limit_buy_partial_fill_then_rest():
    """Incoming limit buy partially fills; remainder rests at limit price."""
    book = _make_book()
    book.add_order(Order(1, 1, Side.ASK, 101, 20))
    engine = MatchingEngine(book)

    trades = engine.submit(IncomingOrder(99, 99, Side.BID, 101, 30))

    assert len(trades) == 1
    assert trades[0] == Trade(101, 20, 1)
    # Remainder 10 rests as bid at 101
    assert book.depth_at(Side.BID, 101) == 10
    assert book.loc[99] == (Side.BID, 101)
    assert book.is_healthy()


def test_multi_level_walk():
    """Algorithm 1 walks multiple price levels until size exhausted."""
    book = _make_book()
    book.add_order(Order(1, 1, Side.ASK, 101, 20))
    book.add_order(Order(2, 2, Side.ASK, 102, 30))
    engine = MatchingEngine(book)

    trades = engine.submit(IncomingOrder(99, 99, Side.BID, 102, 50))

    assert len(trades) == 2
    assert trades[0] == Trade(101, 20, 1)
    assert trades[1] == Trade(102, 30, 2)
    assert 101 not in book.asks
    assert 102 not in book.asks
    assert book.is_healthy()


def test_multi_level_walk_partial_at_last_level():
    book = _make_book()
    book.add_order(Order(1, 1, Side.ASK, 101, 20))
    book.add_order(Order(2, 2, Side.ASK, 102, 30))
    engine = MatchingEngine(book)

    trades = engine.submit(IncomingOrder(99, 99, Side.BID, 102, 40))

    assert len(trades) == 2
    assert trades[0] == Trade(101, 20, 1)
    assert trades[1] == Trade(102, 20, 2)
    assert book.depth_at(Side.ASK, 102) == 10
    assert book.is_healthy()


def test_limit_buy_stops_at_non_marketable_level():
    """
    Lemma 4.1: once Submit exhausts all marketable opposing levels,
    every remaining level lies strictly beyond the incoming limit price.
    """
    book = _make_book()
    book.add_order(Order(1, 1, Side.ASK, 101, 20))
    book.add_order(Order(2, 2, Side.ASK, 103, 30))  # Not marketable against 102
    engine = MatchingEngine(book)

    trades = engine.submit(IncomingOrder(99, 99, Side.BID, 102, 50))

    assert len(trades) == 1
    assert trades[0] == Trade(101, 20, 1)
    # Remainder 30 rests at 102
    assert book.depth_at(Side.BID, 102) == 30
    assert book.best_ask() == 103
    assert book.is_healthy()
    assert book.best_bid() == 102
    assert book.best_ask() == 103


def test_sell_side_mirror():
    book = _make_book()
    book.add_order(Order(1, 1, Side.BID, 100, 25))
    book.add_order(Order(2, 2, Side.BID, 99, 15))
    engine = MatchingEngine(book)

    trades = engine.submit(IncomingOrder(99, 99, Side.ASK, 99, 30))

    assert len(trades) == 2
    assert trades[0] == Trade(100, 25, 1)
    assert trades[1] == Trade(99, 5, 2)
    assert book.depth_at(Side.BID, 99) == 10
    assert book.is_healthy()


def test_self_trade_prevention():
    """Chapter 4, Section 4.4.1: skip resting orders from same trader."""
    book = _make_book()
    book.add_order(Order(1, 1, Side.ASK, 101, 20, trader_id=42))
    book.add_order(Order(2, 2, Side.ASK, 101, 30, trader_id=7))
    engine = MatchingEngine(book)

    trades = engine.submit(
        IncomingOrder(99, 99, Side.BID, float('inf'), 50, trader_id=42)
    )

    # Should fill the non-self order (id=2) first, then skip id=1
    assert len(trades) == 1
    assert trades[0] == Trade(101, 30, 2)
    # Remaining 20 cannot fill id=1 (STP), so rests as bid if limit...
    # But this was a market order, so remainder is cancelled.
    assert 99 not in book.loc
    assert book.depth_at(Side.ASK, 101) == 20  # id=1 untouched
    assert book.is_healthy()


def test_healthiness_preserved_after_every_submit():
    """Proposition 4.1: random aggressive orders never cross the book."""
    import random
    random.seed(42)

    book = _make_book()
    # Seed the book with random liquidity
    for i in range(1, 51):
        side = Side.BID if i % 2 else Side.ASK
        price = 100 + (i % 5) if side == Side.ASK else 100 - (i % 5)
        book.add_order(Order(i, i, side, price, random.randint(1, 100)))

    engine = MatchingEngine(book)

    for n in range(100):
        side = Side.BID if random.random() < 0.5 else Side.ASK
        price = random.choice([98, 99, 100, 101, 102])
        size = random.randint(1, 50)
        incoming = IncomingOrder(1000 + n, 1000 + n, side, price, size)
        engine.submit(incoming)
        assert book.is_healthy(), f"Healthiness failed on submit {n}"