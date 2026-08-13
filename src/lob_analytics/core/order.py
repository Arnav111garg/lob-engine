from __future__ import annotations

from dataclasses import dataclass

from lob_analytics.types import Side


@dataclass(slots=True)
class Order:
    """
    A resting limit order: o = (ι, τ, x, p, s).
    
    Matches Definition 3.1 from the PDF, extended with side and price
    for implementation convenience.
    
    Fields ι (order_id) and τ (seq) are immutable identity fields.
    Field x (quantity) is mutable because passive transitions (CANCEL,
    EXECUTE) reduce it in place without altering queue position.
    """
    order_id: int   # ι: unique identifier
    seq: int        # τ: arrival sequence number (induces priority ≺)
    side: Side      # bid or ask
    price: int      # p: price in integer ticks
    quantity: int   # x: remaining resting size

    def __post_init__(self) -> None:
        if self.order_id < 0:
            raise ValueError("order_id must be non-negative")
        if self.seq < 0:
            raise ValueError("seq must be non-negative")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")

    @property
    def is_filled(self) -> bool:
        return self.quantity == 0

    def reduce(self, amount: int) -> None:
        """
        Reduce remaining quantity by amount.
        
        Used by T_CANCEL and T_EXECUTE transitions. The caller is
        responsible for removing the order from its PriceLevel if
        is_filled becomes True.
        """
        if amount <= 0:
            raise ValueError("Reduction amount must be positive")
        if amount > self.quantity:
            raise ValueError(
                f"Cannot reduce order {self.order_id} by {amount}; "
                f"only {self.quantity} remains"
            )
        self.quantity -= amount
        
@dataclass(slots=True)
class Order:
    order_id: int
    seq: int
    side: Side
    price: int
    quantity: int
    trader_id: int | None = None   # NEW: for self-trade prevention
    # ... rest unchanged