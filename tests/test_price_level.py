import pytest
from lob_analytics.types import Side
from lob_analytics.core.order import Order
from lob_analytics.core.price_level import PriceLevel


def test_price_level_priority_and_removal():
    """
    Proposition 1.1 in code: removing a middle order preserves
    the strict total order of the remaining elements.
    
    This is the exact test assigned in Phase 1.
    """
    level = PriceLevel(price=100)

    # Three orders with sequential arrival numbers (τ)
    order_a = Order(order_id=1, seq=1, side=Side.BID, price=100, quantity=10)
    order_b = Order(order_id=2, seq=2, side=Side.BID, price=100, quantity=20)
    order_c = Order(order_id=3, seq=3, side=Side.BID, price=100, quantity=30)

    # T_ADD: append all three
    level.append(order_a)
    level.append(order_b)
    level.append(order_c)

    assert len(level) == 3
    assert level.total_depth() == 60
    assert [o.order_id for o in level] == [1, 2, 3]

    # T_DELETE: remove B by identifier (middle of queue)
    removed = level.remove_by_id(order_id=2)
    assert removed.order_id == 2
    assert removed.quantity == 20

    # Assert remaining queue is [A, C] with priority order preserved
    remaining = list(level)
    assert len(remaining) == 2
    assert remaining[0].order_id == 1
    assert remaining[1].order_id == 3
    assert remaining[0].seq == 1  # Priority unchanged
    assert remaining[1].seq == 3  # Priority unchanged
    assert level.total_depth() == 40

    # T_CANCEL: partial reduce C by 5
    level.reduce_by_id(order_id=3, amount=5)
    assert level.total_depth() == 35
    assert len(level) == 2  # C still present
    assert list(level)[1].quantity == 25

    # T_EXECUTE: fully fill A (amount == remaining quantity)
    level.reduce_by_id(order_id=1, amount=10)
    assert len(level) == 1
    assert level.total_depth() == 25
    assert list(level)[0].order_id == 3


def test_remove_by_id_not_position():
    """
    Chapter 9, Section 9.3: A bug that pops the front instead of
    removing by identifier would return order_a here and corrupt depth.
    """
    level = PriceLevel(price=100)
    level.append(Order(order_id=1, seq=1, side=Side.BID, price=100, quantity=10))
    level.append(Order(order_id=2, seq=2, side=Side.BID, price=100, quantity=20))

    # Removing order_id=2 (at the back) must NOT remove order_id=1 (at front)
    removed = level.remove_by_id(order_id=2)
    assert removed.order_id == 2
    assert len(level) == 1
    assert list(level)[0].order_id == 1