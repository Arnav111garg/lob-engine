import pytest
from lob_analytics.types import Event, EventType, Side
from lob_analytics.engine.reconstruction import ReconstructionEngine


def test_reconstruction_synthetic_stream():
    """End-to-end passive transitions: add, cancel, execute, delete."""
    engine = ReconstructionEngine(validate_conservation=True)

    events = [
        Event(0, 34200.0, EventType.ADD, 1, 50, 100, Side.BID),
        Event(1, 34200.1, EventType.ADD, 2, 30, 101, Side.ASK),
        Event(2, 34200.2, EventType.CANCEL, 1, 20, 100, Side.BID),
        Event(3, 34200.3, EventType.EXECUTE, 2, 10, 101, Side.ASK),
        Event(4, 34200.4, EventType.DELETE, 1, 30, 100, Side.BID),
    ]

    engine.process_stream(iter(events))

    assert engine.book.best_bid() is None
    assert engine.book.best_ask() == 101
    assert engine.book.depth_at(Side.ASK, 101) == 20
    assert engine.event_count == 5
    assert engine.book.is_healthy()


def test_mid_queue_delete_conservation():
    """
    Chapter 9, Section 9.2 + 9.3:
    Deleting a middle order preserves priority; conservation catches
    any front-popping bug immediately.
    """
    engine = ReconstructionEngine(validate_conservation=True)

    events = [
        Event(0, 0.0, EventType.ADD, 1, 20, 100, Side.ASK),
        Event(1, 0.1, EventType.ADD, 2, 30, 100, Side.ASK),
        Event(2, 0.2, EventType.ADD, 3, 10, 100, Side.ASK),
        Event(3, 0.3, EventType.DELETE, 2, 30, 100, Side.ASK),
    ]

    engine.process_stream(iter(events))

    level = engine.book.asks[100]
    orders = list(level)
    assert len(orders) == 2
    assert orders[0].order_id == 1
    assert orders[1].order_id == 3
    assert level.total_depth() == 30


def test_full_day_simulation_no_crash():
    """Property-based sanity: many random adds and deletes stay healthy."""
    engine = ReconstructionEngine(validate_conservation=True)

    import random
    random.seed(42)

    events = []
    next_id = 1
    active_ids = []

    for n in range(5_000):
        if not active_ids or random.random() < 0.4:
            # ADD
            side = Side.BID if random.random() < 0.5 else Side.ASK
            price = random.choice([99, 100, 101, 102])
            size = random.randint(1, 100)
            events.append(Event(n, float(n), EventType.ADD, next_id, size, price, side))
            active_ids.append(next_id)
            next_id += 1
        else:
            # DELETE or CANCEL or EXECUTE existing order
            oid = random.choice(active_ids)
            side = Side.BID  # dummy; engine looks up via loc
            price = 100      # dummy
            r = random.random()
            if r < 0.5:
                events.append(Event(n, float(n), EventType.DELETE, oid, 10, price, side))
                active_ids.remove(oid)
            elif r < 0.75:
                events.append(Event(n, float(n), EventType.CANCEL, oid, 5, price, side))
            else:
                events.append(Event(n, float(n), EventType.EXECUTE, oid, 5, price, side))

    engine.process_stream(iter(events))
    assert engine.book.is_healthy()
    assert engine.event_count == 5_000