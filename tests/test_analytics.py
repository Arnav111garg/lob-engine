import pytest
from lob_analytics.types import Side
from lob_analytics.core.order import Order
from lob_analytics.core.book_state import OrderBook
from lob_analytics.analytics.metrics import compute_metrics, BookMetrics
from lob_analytics.analytics.queueing import fill_probability, fill_probabilities


def test_metrics_empty_book():
    book = OrderBook()
    m = compute_metrics(book)
    assert m.best_bid is None
    assert m.spread is None


def test_metrics_basic():
    book = OrderBook()
    book.add_order(Order(1, 1, Side.BID, 100, 50))
    book.add_order(Order(2, 2, Side.ASK, 101, 30))

    m = compute_metrics(book)
    assert m.best_bid == 100
    assert m.best_ask == 101
    assert m.spread == 1
    assert m.mid_price == 100.5
    # M_w = (100 * 30 + 101 * 50) / (30 + 50) = (3000 + 5050) / 80 = 100.625
    assert m.weighted_mid == pytest.approx(100.625)
    assert m.bid_depth_touch == 50
    assert m.ask_depth_touch == 30
    assert m.depth_imbalance == pytest.approx((50 - 30) / 80)


def test_fill_probability_limits():
    """
    Chapter 5 sanity checks:
    - As θ -> 0, f_k -> 1 for all k
    - As μ -> 0, f_k -> 0 for all k
    """
    # High execution, low cancel -> high fill prob even at back of queue
    f = fill_probability(k=5, mu=10.0, theta=0.1)
    assert f > 0.95

    # Low execution, high cancel -> low fill prob even at front
    f = fill_probability(k=1, mu=0.1, theta=10.0)
    assert f < 0.02


def test_fill_probability_geometric_decay():
    """Proposition 5.1: fill probability decays geometrically in k."""
    probs = fill_probabilities(max_k=5, mu=2.0, theta=1.0)
    # Ratio = (2+1)/(2+2) = 0.75
    # f1 = 2/3 ≈ 0.6667
    # f2 = 0.75 * 2/3 = 0.5
    assert probs[0] == pytest.approx(2 / 3)
    assert probs[1] == pytest.approx(0.5)
    assert probs[2] == pytest.approx(0.375)
    # Check geometric property: probs[k] / probs[k-1] ≈ 0.75
    for i in range(1, 5):
        assert probs[i] / probs[i - 1] == pytest.approx(0.75)