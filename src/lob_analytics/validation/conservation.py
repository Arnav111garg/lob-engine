from __future__ import annotations

from lob_analytics.types import Event, EventType, Side
from lob_analytics.core.book_state import OrderBook


class ConservationValidator:
    """
    Proposition 7.1: Resting depth at any level equals cumulative adds
    minus cumulative removals at that level, exactly.

    We maintain a ledger per (side, price) and check against the book
    after every message that affects visible depth.
    """

    def __init__(self) -> None:
        # (side, price) -> net_depth
        self.ledger: dict[tuple[Side, int], int] = {}

    def update_and_check(self, event: Event, book: OrderBook) -> None:
        """
        Update ledger with event's signed size and assert equality
        against reconstructed book depth.
        """
        if event.event_type == EventType.HIDDEN_EXEC:
            return  # No visible impact

        key = (event.side, event.price)

        if event.event_type == EventType.ADD:
            self.ledger[key] = self.ledger.get(key, 0) + event.size
        elif event.event_type in (
            EventType.CANCEL,
            EventType.DELETE,
            EventType.EXECUTE,
        ):
            self.ledger[key] = self.ledger.get(key, 0) - event.size
        else:
            raise ValueError(f"Unexpected event type: {event.event_type}")

        expected = self.ledger[key]
        actual = book.depth_at(event.side, event.price)

        if expected != actual:
            raise RuntimeError(
                f"Conservation violation at message {event.seq_n} "
                f"(type={event.event_type.name}):\n"
                f"  side={event.side.name}, price={event.price}\n"
                f"  expected_depth={expected}, actual_depth={actual}\n"
                f"  This is an unambiguous bug (Prop 3.1) or data gap."
            )