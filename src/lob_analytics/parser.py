from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pandas as pd

from lob_analytics.types import Event, EventType, Side


class LOBSTERParser:
    """
    Parse LOBSTER message CSV into a stream of Event objects.

    LOBSTER message file columns (no header):
        0: Time            (seconds since midnight, float)
        1: Event Type      (int: 1-5)
        2: Order ID        (int)
        3: Size            (int)
        4: Price           (int, fixed-point)
        5: Direction       (int: -1 or 1)
    """

    def __init__(self, price_scale: float = 10_000.0) -> None:
        """
        price_scale: divisor to convert integer prices to dollars.
        Default 10_000 matches NASDAQ ITCH 4-decimal fixed-point.
        """
        self.price_scale = price_scale

    def load_messages_df(self, path: str | Path) -> pd.DataFrame:
        """Raw DataFrame load for exploration."""
        df = pd.read_csv(
            path,
            header=None,
            names=["time", "event_type", "order_id", "size", "price", "direction"],
        )
        return df

    def parse_events(self, path: str | Path) -> Iterator[Event]:
        """
        Yield Event objects in message-stream order.

        seq_n is the row index (0-based), serving as the discrete message
        index n in the left fold B_n = T_mn(B_{n-1}).
        """
        df = self.load_messages_df(path)

        for seq_n, row in enumerate(df.itertuples(index=False)):
            # row: (time, event_type, order_id, size, price, direction)
            yield Event(
                seq_n=seq_n,
                timestamp=float(row.time),
                event_type=EventType.from_lobster(int(row.event_type)),
                order_id=int(row.order_id),
                size=int(row.size),
                price=int(row.price),
                side=Side.from_lobster(int(row.direction)),
            )