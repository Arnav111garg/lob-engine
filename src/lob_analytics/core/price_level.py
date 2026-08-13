from __future__ import annotations

from lob_analytics.core.order import Order


class PriceLevel:
    """
    All resting orders at one exact price p, ordered by priority ≺.
    
    Proposition 1.1: price-time priority restricted to a single price
    level is a strict total order. Here it is implemented as a list
    ordered by seq (arrival sequence number τ).
    
    Chapter 7 notes that a simple sequence representation requires
    O(k) scan for removal by identifier, where k is queue depth.
    This is acceptable for a first implementation.
    """

    def __init__(self, price: int) -> None:
        if price <= 0:
            raise ValueError("price must be positive")
        self.price = price
        self._orders: list[Order] = []  # Ordered by seq (price-time priority)
        self._total_depth: int = 0

    @property
    def orders(self) -> list[Order]:
        """Return a shallow copy of the priority-ordered order list."""
        return self._orders.copy()

    def append(self, order: Order) -> None:
        """
        T_ADD: Append a new order to the back of the queue.
        
        Preconditions:
            - order.price == self.price
            - order.seq > all existing seq (stream is well-formed)
        """
        if order.price != self.price:
            raise ValueError(
                f"Order price {order.price} does not match level {self.price}"
            )
        self._orders.append(order)
        self._total_depth += order.quantity

    def remove_by_id(self, order_id: int) -> Order:
        """
        T_DELETE: Remove an order by its identifier ι, wherever it sits.
        
        This is the correct implementation per Chapter 3. Removing
        "whatever is at the front" is the single most common reconstruction
        bug (Chapter 9, Section 9.3).
        """
        for idx, order in enumerate(self._orders):
            if order.order_id == order_id:
                self._orders.pop(idx)
                self._total_depth -= order.quantity
                if self._total_depth < 0:
                    raise RuntimeError("Negative price-level depth")
                return order
        raise KeyError(f"Order {order_id} not found at price {self.price}")

    def reduce_by_id(self, order_id: int, amount: int) -> Order:
        """
        T_CANCEL or T_EXECUTE (partial): Reduce order size by amount.
        If quantity reaches zero, remove the order entirely.
        """
        if amount <= 0:
            raise ValueError("amount must be positive")

        for idx, order in enumerate(self._orders):
            if order.order_id == order_id:
                if amount > order.quantity:
                    raise ValueError(
                        f"Reduction {amount} exceeds order {order_id} "
                        f"quantity {order.quantity}"
                    )
                order.reduce(amount)
                self._total_depth -= amount

                if order.is_filled:
                    self._orders.pop(idx)

                if self._total_depth < 0:
                    raise RuntimeError("Negative price-level depth")

                return order

        raise KeyError(f"Order {order_id} not found at price {self.price}")

    def total_depth(self) -> int:
        """Total resting quantity V(p) at this price level."""
        return self._total_depth

    def __len__(self) -> int:
        """Number of orders (not shares) resting at this level."""
        return len(self._orders)

    def __iter__(self):
        """Iterate in priority order (front of queue first)."""
        return iter(self._orders)

    def validate(self) -> None:
        """Consistency check: sum of order quantities equals total_depth."""
        total = sum(o.quantity for o in self._orders)
        assert total == self._total_depth, (
            f"Validation failed: sum={total}, tracked={self._total_depth}"
        )
        if not self._orders:
            assert self._total_depth == 0
        else:
            assert self._total_depth > 0

    def __repr__(self) -> str:
        return (
            f"PriceLevel(price={self.price}, orders={len(self._orders)}, "
            f"depth={self._total_depth})"
        )