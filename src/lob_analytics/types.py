from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    """
    Side of the book.
    
    LOBSTER direction encoding: 1 = buy (bid side), -1 = sell (ask side).
    Matches the PDF notation Q^bid, Q^ask.
    """
    BID = 1
    ASK = -1

    @classmethod
    def from_lobster(cls, value: int) -> Side:
        if value == 1:
            return cls.BID
        if value == -1:
            return cls.ASK
        raise ValueError(f"Invalid LOBSTER direction: {value}")


class EventType(Enum):
    """
    LOBSTER message event types relevant to Project 1 scope.
    
    Types 1-5 are the core events (Chapter 2, Section 2.4.2).
    Types 6-7 exist in the feed but are out of scope for reconstruction.
    """
    ADD = 1
    CANCEL = 2       # Partial cancellation
    DELETE = 3       # Full deletion
    EXECUTE = 4      # Visible execution
    HIDDEN_EXEC = 5  # Non-displayed execution

    @classmethod
    def from_lobster(cls, value: int) -> EventType:
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"Unknown LOBSTER event type: {value}") from exc


@dataclass(frozen=True, slots=True)
class Event:
    """
    Normalized representation of one LOBSTER message.
    
    seq_n is the message-stream index n (discrete event count), distinct
    from timestamp t (physical time). See Chapter 3, Section 3.5.
    
    Price is stored as an integer in LOBSTER price units (fixed-point).
    """
    seq_n: int        # n: message index in the stream (induces priority)
    timestamp: float  # t: seconds since midnight
    event_type: EventType
    order_id: int     # ι: unique identifier
    size: int         # x: quantity
    price: int        # p: integer ticks (never float)
    side: Side        # bid or ask

    def __post_init__(self) -> None:
        if self.seq_n < 0:
            raise ValueError("seq_n cannot be negative")
        if self.timestamp < 0:
            raise ValueError("timestamp cannot be negative")
        if self.size <= 0:
            raise ValueError("size must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")
        

@dataclass(frozen=True, slots=True)
class Trade:
    """
    A single fill produced by the matching engine.
    Triple: (price, quantity, resting_order_id).
    """
    price: int
    quantity: int
    resting_order_id: int


@dataclass(frozen=True, slots=True)
class IncomingOrder:
    """
    An order submitted by a trader (or strategy) into the matching engine.
    
    For market orders, use price=float('inf') (buy) or float('-inf') (sell).
    seq is the arrival sequence number for priority if the order rests.
    """
    order_id: int
    seq: int
    side: Side
    price: int | float   # float('inf') / float('-inf') for market orders
    size: int
    trader_id: int | None = None