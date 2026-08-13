from __future__ import annotations

from typing import Iterator, Optional

from lob_analytics.types import Event, EventType
from lob_analytics.core.book_state import OrderBook
from lob_analytics.core.order import Order
from lob_analytics.validation.conservation import ConservationValidator


class ReconstructionEngine:
    """
    Algorithm 2: Reconstruction with explicit identifier index and inline validation.

    Chapter 7: B_n = T_mn(B_{n-1}) folded over the message stream.
    After every message, assert no-crossing invariant and conservation identity.
    """

    def __init__(self, validate_conservation: bool = True) -> None:
        self.book = OrderBook()
        self.validator = ConservationValidator() if validate_conservation else None
        self.event_count = 0

    def process_event(self, event: Event) -> None:
        """Apply the correct passive transition for a single event."""

        if event.event_type == EventType.ADD:
            order = Order(
                order_id=event.order_id,
                seq=event.seq_n,      # τ: arrival sequence number induces ≺
                side=event.side,
                price=event.price,
                quantity=event.size,
            )
            self.book.add_order(order)

        elif event.event_type == EventType.CANCEL:
            self.book.cancel_order(event.order_id, event.size)

        elif event.event_type == EventType.DELETE:
            # LOBSTER delete carries remaining size; our book removes the
            # full order. Any size mismatch is caught by conservation check.
            self.book.delete_order(event.order_id)

        elif event.event_type == EventType.EXECUTE:
            self.book.execute_order(event.order_id, event.size)

        elif event.event_type == EventType.HIDDEN_EXEC:
            # Type 5: non-displayed execution. No visible book impact.
            pass

        else:
            raise ValueError(f"Unhandled event type: {event.event_type}")

        # Inline validation: Proposition 7.1 (conservation identity)
        if self.validator is not None:
            self.validator.update_and_check(event, self.book)

        self.event_count += 1

    def process_stream(self, events: Iterator[Event]) -> None:
        """Fold over an entire event stream."""
        for event in events:
            self.process_event(event)