from __future__ import annotations

from pathlib import Path

import pandas as pd
import numpy as np

from lob_analytics.core.book_state import OrderBook


class SnapshotValidator:
    """
    Chapter 7, Section 7.3.2: Snapshot matching against LOBSTER orderbook file.

    The orderbook file has one row per message, aligned 1:1 with the message file.
    Row n should match the reconstructed book state after processing message n.

    LOBSTER Level-10 orderbook file layout (40 columns, no header):
        cols  0-19: Ask side  (ask_price_1, ask_size_1, ..., ask_price_10, ask_size_10)
        cols 20-39: Bid side  (bid_price_1, bid_size_1, ..., bid_price_10, bid_size_10)

    NOTE: Verify this column mapping against your actual file. If your file
    has bid columns first, swap the slice indices below.
    """

    def __init__(self, orderbook_path: str | Path) -> None:
        self.df = pd.read_csv(orderbook_path, header=None)
        self.mismatches: list[int] = []

    def _extract_expected(self, row_idx: int) -> tuple[list, list]:
        """Return (expected_asks, expected_bids) as list of (price, size)."""
        row = self.df.iloc[row_idx].values

        # Ask side: columns 0,1,2,3,...,18,19  -> 10 (price, size) pairs
        expected_asks = []
        for i in range(10):
            price = row[i * 2]
            size = row[i * 2 + 1]
            # LOBSTER uses 0 or negative sentinel for empty levels
            if price > 0 and size >= 0:
                expected_asks.append((int(price), int(size)))
            else:
                expected_asks.append((None, 0))

        # Bid side: columns 20,21,...,38,39
        expected_bids = []
        for i in range(10):
            price = row[20 + i * 2]
            size = row[20 + i * 2 + 1]
            if price > 0 and size >= 0:
                expected_bids.append((int(price), int(size)))
            else:
                expected_bids.append((None, 0))

        return expected_asks, expected_bids

    def check_row(self, row_idx: int, book: OrderBook) -> bool:
        """
        Compare reconstructed top-10 snapshot against LOBSTER ground truth.
        Returns True if match, False if mismatch (logged in self.mismatches).
        """
        expected_asks, expected_bids = self._extract_expected(row_idx)
        snap = book.snapshot_level2(top_n=10)

        # Normalize actual snapshot to 10 levels, padding with (None, 0)
        actual_asks = snap["asks"] + [(None, 0)] * (10 - len(snap["asks"]))
        actual_bids = snap["bids"] + [(None, 0)] * (10 - len(snap["bids"]))

        match = True

        for i in range(10):
            exp_p, exp_s = expected_asks[i]
            act_p, act_s = actual_asks[i]

            # Empty level agreement
            if exp_p is None and act_p is None:
                continue
            if exp_p != act_p or exp_s != act_s:
                match = False
                break

        if match:
            for i in range(10):
                exp_p, exp_s = expected_bids[i]
                act_p, act_s = actual_bids[i]
                if exp_p is None and act_p is None:
                    continue
                if exp_p != act_p or exp_s != act_s:
                    match = False
                    break

        if not match:
            self.mismatches.append(row_idx)

        return match