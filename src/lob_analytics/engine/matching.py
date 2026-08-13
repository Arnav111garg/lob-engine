from __future__ import annotations

from lob_analytics.types import Side, IncomingOrder, Trade
from lob_analytics.core.book_state import OrderBook
from lob_analytics.core.order import Order


class MatchingEngine:
    """
    Algorithm 1: SUBMIT — active matching under price-time priority.

    Chapter 4: Given an unresolved incoming order, derive the decision the
    exchange's own matching engine would have made.
    """

    def __init__(self, book: OrderBook) -> None:
        self.book = book

    def submit(self, incoming: IncomingOrder) -> list[Trade]:
        """
        Execute an incoming order against the current book state.

        Returns the list of trades produced. The book is mutated in place.
        After this method returns, the book is guaranteed healthy
        (Proposition 4.1).
        """
        assert self.book.is_healthy(), "Book must be healthy before SUBMIT"
        assert incoming.size > 0, "Incoming size must be positive"

        trades: list[Trade] = []
        remaining = incoming.size

        # ------------------------------------------------------------------
        # 1. Identify marketable opposing levels (Lemma 4.1 boundary)
        # ------------------------------------------------------------------
        if incoming.side == Side.BID:
            # Incoming buy: walk asks from best (lowest) upward
            marketable_prices: list[int] = []
            for price in self.book.asks.keys():
                if price <= incoming.price:
                    marketable_prices.append(price)
                else:
                    break
            opposing = self.book.asks
        else:
            # Incoming sell: walk bids from best (highest) downward
            marketable_prices = []
            for price in reversed(self.book.bids.keys()):
                if price >= incoming.price:
                    marketable_prices.append(price)
                else:
                    break
            opposing = self.book.bids

        # ------------------------------------------------------------------
        # 2. Walk levels and fill front-of-queue orders (price-time priority)
        # ------------------------------------------------------------------
        for price in marketable_prices:
            if remaining <= 0:
                break

            level = opposing[price]

            # Iterate over a snapshot copy; execute_order mutates the real queue
            for order in level.orders():
                if remaining <= 0:
                    break

                # Self-trade prevention (Chapter 4, Section 4.4.1)
                if (incoming.trader_id is not None
                        and order.trader_id == incoming.trader_id):
                    continue

                take = min(remaining, order.quantity)
                trades.append(Trade(
                    price=price,
                    quantity=take,
                    resting_order_id=order.order_id,
                ))

                # Apply the fill via the same passive transition reconstruction uses
                self.book.execute_order(order.order_id, take)
                remaining -= take

        # ------------------------------------------------------------------
        # 3. Rest unfilled remainder if limit order; cancel if market order
        # ------------------------------------------------------------------
        is_market = incoming.price in (float('inf'), float('-inf'))

        if remaining > 0 and not is_market:
            # Remainder rests as a new limit order at price p
            rested = Order(
                order_id=incoming.order_id,
                seq=incoming.seq,
                side=incoming.side,
                price=int(incoming.price),
                quantity=remaining,
                trader_id=incoming.trader_id,
            )
            self.book.add_order(rested)

        # ------------------------------------------------------------------
        # 4. Invariant check: Proposition 4.1
        # ------------------------------------------------------------------
        assert self.book.is_healthy(), (
            f"Proposition 4.1 violated after SUBMIT {incoming.order_id}. "
            f"This is an unambiguous bug in the matching engine."
        )

        return trades