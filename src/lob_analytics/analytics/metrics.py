from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from lob_analytics.types import Side
from lob_analytics.core.book_state import OrderBook


@dataclass(frozen=True)
class BookMetrics:
    """
    Snapshot metrics derived from a single book state.
    Chapter 2: spread, mid, weighted mid, depth imbalance.
    """
    best_bid: Optional[int]
    best_ask: Optional[int]
    spread: Optional[int]
    mid_price: Optional[float]
    weighted_mid: Optional[float]
    bid_depth_touch: int
    ask_depth_touch: int
    depth_imbalance: Optional[float]  # (VB - VA) / (VB + VA), range [-1, 1]


def compute_metrics(book: OrderBook) -> BookMetrics:
    """Compute all metrics from current book state."""
    bb = book.best_bid()
    ba = book.best_ask()

    if bb is None or ba is None:
        return BookMetrics(
            best_bid=bb,
            best_ask=ba,
            spread=None,
            mid_price=None,
            weighted_mid=None,
            bid_depth_touch=0,
            ask_depth_touch=0,
            depth_imbalance=None,
        )

    vb = book.depth_at(Side.BID, bb)
    va = book.depth_at(Side.ASK, ba)

    spread = ba - bb
    mid = (ba + bb) / 2.0

    # Chapter 2, Eq. 2.2.1: weighted mid
    # M_w = (B * V_A + A * V_B) / (V_A + V_B)
    if (va + vb) > 0:
        weighted_mid = (bb * va + ba * vb) / (va + vb)
        imbalance = (vb - va) / (vb + va)
    else:
        weighted_mid = None
        imbalance = None

    return BookMetrics(
        best_bid=bb,
        best_ask=ba,
        spread=spread,
        mid_price=mid,
        weighted_mid=weighted_mid,
        bid_depth_touch=vb,
        ask_depth_touch=va,
        depth_imbalance=imbalance,
    )