#!/usr/bin/env python3
"""
Run full-day reconstruction against LOBSTER CSV pair.

Usage:
    python scripts/reconstruct_day.py \
        data/raw/INTC_2012-06-21_..._message_10.csv \
        data/raw/INTC_2012-06-21_..._orderbook_10.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root without install
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lob_analytics.parser import LOBSTERParser
from lob_analytics.engine.reconstruction import ReconstructionEngine
from lob_analytics.validation.snapshot import SnapshotValidator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconstruct limit order book from LOBSTER message stream"
    )
    parser.add_argument("message_file", help="Path to LOBSTER message CSV")
    parser.add_argument("orderbook_file", help="Path to LOBSTER orderbook CSV")
    parser.add_argument(
        "--check-every",
        type=int,
        default=10_000,
        help="Print progress every N events",
    )
    parser.add_argument(
        "--snapshot-check",
        action="store_true",
        help="Enable row-by-row snapshot validation (slower)",
    )
    args = parser.parse_args()

    print(f"Parsing: {args.message_file}")
    events = LOBSTERParser().parse_events(args.message_file)

    snapshot_validator = None
    if args.snapshot_check:
        print(f"Loading ground truth: {args.orderbook_file}")
        snapshot_validator = SnapshotValidator(args.orderbook_file)

    engine = ReconstructionEngine(validate_conservation=True)

    try:
        for event in events:
            engine.process_event(event)

            if engine.event_count % args.check_every == 0:
                print(f"  ... processed {engine.event_count:,} events")

            if snapshot_validator:
                snapshot_validator.check_row(event.seq_n, engine.book)

    except RuntimeError as exc:
        print(f"\nRECONSTRUCTION HALTED: {exc}")
        sys.exit(1)

    print(f"\nSuccess. Processed {engine.event_count:,} events.")
    print(f"Final state: {engine.book}")

    if snapshot_validator:
        mismatch_count = len(snapshot_validator.mismatches)
        if mismatch_count == 0:
            print("Snapshot validation: 100% match across all events.")
        else:
            print(f"Snapshot mismatches: {mismatch_count} rows")
            print(f"First 5 mismatch indices: {snapshot_validator.mismatches[:5]}")


if __name__ == "__main__":
    main()