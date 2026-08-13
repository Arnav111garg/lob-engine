from __future__ import annotations

from sortedcontainers import SortedDict

from lob_analytics.types import Side
from lob_analytics.core.order import Order
from lob_analytics.core.price_level import PriceLevel


class OrderBook:
    """
    Canonical book state B = (Q^bid, Q^ask) with explicit loc index.

    Definition 3.2: Each side is a function from price to a priority-ordered
    sequence of orders. Here implemented as SortedDict[int, PriceLevel].

    The loc index maps order_id -> (side, price). Chapter 7, Section 7.2.1:
    "Without the auxiliary map loc, locating an order requires scanning every
    price level... O(book size) per message."
    """

    def __init__(self) -> None:
        # Sorted ascending internally. Best bid = max key; best ask = min key.
        self.bids: SortedDict[int, PriceLevel] = SortedDict()
        self.asks: SortedDict[int, PriceLevel] = SortedDict()

        # loc(ι) -> (side, price). Required for O(1) lookup on cancel/delete/exec.
        self.loc: dict[int, tuple[Side, int]] = {}

    # ------------------------------------------------------------------ #
    # Best prices and derived quantities (Chapter 2, Definitions 2.4)
    # ------------------------------------------------------------------ #
    def best_bid(self) -> int | None:
        """Highest price with positive bid-side depth (B)."""
        if not self.bids:
            return None
        return self.bids.keys()[-1]

    def best_ask(self) -> int | None:
        """Lowest price with positive ask-side depth (A)."""
        if not self.asks:
            return None
        return self.asks.keys()[0]

    def spread(self) -> int | None:
        """S = A - B. None if either side empty."""
        bb = self.best_bid()
        ba = self.best_ask()
        if bb is None or ba is None:
            return None
        return ba - bb

    def mid_price(self) -> float | None:
        """M = (A + B) / 2. None if either side empty."""
        bb = self.best_bid()
        ba = self.best_ask()
        if bb is None or ba is None:
            return None
        return (bb + ba) / 2.0

    def is_healthy(self) -> bool:
        """
        Proposition 3.1 invariant: B < A whenever both sides nonempty.
        Any failure after a transition is an unambiguous bug in code.
        """
        bb = self.best_bid()
        ba = self.best_ask()
        if bb is None or ba is None:
            return True
        return bb < ba

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _side_dict(self, side: Side) -> SortedDict[int, PriceLevel]:
        return self.bids if side == Side.BID else self.asks

    def _get_level(self, side: Side, price: int) -> PriceLevel:
        """Return existing PriceLevel or raise KeyError."""
        return self._side_dict(side)[price]

    def depth_at(self, side: Side, price: int) -> int:
        """Total resting depth V(p) at a specific price, or 0 if empty."""
        level = self._side_dict(side).get(price)
        return level.total_depth() if level else 0

    # ------------------------------------------------------------------ #
    # Passive transitions (Chapter 3, Section 3.3)
    # ------------------------------------------------------------------ #
    def add_order(self, order: Order) -> None:
        """
        T_ADD: Append order to the back of its price level; record in loc.
        """
        side_dict = self._side_dict(order.side)
        if order.price not in side_dict:
            side_dict[order.price] = PriceLevel(order.price)

        side_dict[order.price].append(order)
        self.loc[order.order_id] = (order.side, order.price)

        assert self.is_healthy(), (
            f"Healthiness violated after ADD {order.order_id} "
            f"at {order.side.name} {order.price}"
        )

    def cancel_order(self, order_id: int, amount: int) -> None:
        """
        T_CANCEL: Partial reduction of a resting order's remaining size.
        If size reaches zero, the order is removed entirely.
        """
        side, price = self.loc[order_id]
        side_dict = self._side_dict(side)
        level = side_dict[price]

        order = level.reduce_by_id(order_id, amount)

        if order.is_filled:
            del self.loc[order_id]

        if level.total_depth() == 0:
            del side_dict[price]

        assert self.is_healthy(), (
            f"Healthiness violated after CANCEL {order_id}"
        )

    def delete_order(self, order_id: int) -> None:
        """
        T_DELETE: Full removal of a resting order by identifier.
        """
        side, price = self.loc[order_id]
        side_dict = self._side_dict(side)
        level = side_dict[price]

        level.remove_by_id(order_id)
        del self.loc[order_id]

        if level.total_depth() == 0:
            del side_dict[price]

        assert self.is_healthy(), (
            f"Healthiness violated after DELETE {order_id}"
        )

    def execute_order(self, order_id: int, amount: int) -> None:
        """
        T_EXECUTE: Reduce size by amount (fill against incoming marketable order).
        If size reaches zero, remove entirely.
        """
        side, price = self.loc[order_id]
        side_dict = self._side_dict(side)
        level = side_dict[price]

        order = level.reduce_by_id(order_id, amount)

        if order.is_filled:
            del self.loc[order_id]

        if level.total_depth() == 0:
            del side_dict[price]

        assert self.is_healthy(), (
            f"Healthiness violated after EXECUTE {order_id}"
        )

    # ------------------------------------------------------------------ #
    # Snapshot / inspection helpers
    # ------------------------------------------------------------------ #
    def snapshot_level2(self, top_n: int = 10) -> dict:
        """
        Return a LOBSTER-style snapshot of the top N levels.
        Useful for validation against the orderbook_10 file.
        """
        asks = []
        for price in self.asks.keys()[:top_n]:
            level = self.asks[price]
            asks.append((price, level.total_depth()))

        bids = []
        for price in reversed(self.bids.keys()[-top_n:]):
            level = self.bids[price]
            bids.append((price, level.total_depth()))

        return {
            "bids": bids,  # Best first
            "asks": asks,  # Best first
            "best_bid": self.best_bid(),
            "best_ask": self.best_ask(),
            "spread": self.spread(),
            "mid": self.mid_price(),
        }

    def __repr__(self) -> str:
        return (
            f"OrderBook(bid_levels={len(self.bids)}, "
            f"ask_levels={len(self.asks)}, "
            f"loc_size={len(self.loc)}, "
            f"best_bid={self.best_bid()}, "
            f"best_ask={self.best_ask()})"
        )