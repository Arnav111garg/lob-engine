# Data Dictionary

This document describes the main data objects used throughout the project.

The exact fields of the LOBSTER dataset should always be checked against the dataset documentation before processing.

---

# 1. LOBSTER Message Data

LOBSTER message data describes events occurring in the limit order book.

A typical message contains information corresponding to:

| Field        | Description                          |
| ------------ | ------------------------------------ |
| `time`       | Event timestamp                      |
| `event_type` | Type of order-book event             |
| `order_id`   | Identifier associated with the order |
| `size`       | Number of shares/contracts involved  |
| `price`      | Price associated with the event      |
| `direction`  | Buy/sell direction where applicable  |

The exact interpretation of each field depends on the event type.

---

# 2. Event Types

LOBSTER message event types must be mapped into the project's normalized event representation.

The exact mapping should be verified from the dataset specification.

Conceptually, the system may encounter:

| Event   | Meaning                                |
| ------- | -------------------------------------- |
| Add     | New limit order enters the book        |
| Execute | Existing order is executed             |
| Cancel  | Part of an existing order is cancelled |
| Delete  | Existing order is removed              |
| Replace | Existing order is modified/replaced    |

The internal engine should operate on normalized events rather than directly on dataset-specific numeric event codes.

---

# 3. Normalized Event Schema

The project will use a common internal event representation.

Conceptually:

```python
MarketEvent(
    timestamp,
    event_type,
    order_id,
    side,
    price,
    quantity
)
```

Not every event requires every field.

For example, an event may not have a meaningful price or side depending on its type.

---

# 4. Order

An `Order` represents an individual order maintained by the local LOB engine.

| Field       | Description                  |
| ----------- | ---------------------------- |
| `order_id`  | Unique order identifier      |
| `side`      | BUY or SELL                  |
| `price`     | Limit price                  |
| `quantity`  | Remaining quantity           |
| `timestamp` | Original arrival time        |
| `next`      | Next order in FIFO queue     |
| `prev`      | Previous order in FIFO queue |

---

# 5. Price Level

A `PriceLevel` represents all active orders at one price.

| Field            | Description               |
| ---------------- | ------------------------- |
| `price`          | Price of the level        |
| `total_quantity` | Total resting quantity    |
| `head`           | First order in FIFO queue |
| `tail`           | Last order in FIFO queue  |
| `order_count`    | Number of active orders   |

Conceptually:

```text
Price Level: 100.00

HEAD
 │
 ▼
Order A → Order B → Order C
                         │
                         ▼
                        TAIL
```

---

# 6. Limit Order Book

The `LimitBook` represents the current market state.

It contains:

```text
Bid Price Levels
Ask Price Levels
Active Order Lookup
```

Important derived quantities include:

| Variable    | Definition                  |
| ----------- | --------------------------- |
| `best_bid`  | Highest active bid          |
| `best_ask`  | Lowest active ask           |
| `mid_price` | `(best_bid + best_ask) / 2` |
| `spread`    | `best_ask - best_bid`       |
| `bid_depth` | Available bid liquidity     |
| `ask_depth` | Available ask liquidity     |

---

# 7. Microstructure Features

## Mid Price

[
P_m=\frac{P_b+P_a}{2}
]

---

## Spread

[
S=P_a-P_b
]

---

## Top-of-Book Imbalance

[
I=
\frac{Q_b-Q_a}
{Q_b+Q_a}
]

---

## Microprice

[
P_{\mu}=
\frac{P_bQ_a+P_aQ_b}
{Q_b+Q_a}
]

---

## Return

For horizon (\Delta):

[
r_{t,\Delta}
============

\frac{P_{t+\Delta}-P_t}{P_t}
]

For very short horizons, tick returns or log returns may also be appropriate.

---

# 8. Research Variables

The research layer will generally distinguish between:

### State variables

Describe the current market.

Examples:

```text
spread
depth
imbalance
microprice
volatility
```

### Flow variables

Describe what is happening to the book.

Examples:

```text
order arrivals
cancellations
executions
OFI
trade intensity
```

### Target variables

Describe subsequent market behavior.

Examples:

```text
future return
future mid-price movement
future volatility
price impact
fill probability
```

This distinction is important when constructing empirical tests.

---

# 9. Time Representation

The project should preserve the highest available timestamp precision.

Where possible:

```text
Raw timestamp
      ↓
Integer timestamp
      ↓
Explicit time unit
```

The unit must always be documented.

We should avoid silently converting timestamps to floating-point seconds because precision can become important at high frequency.

---

# 10. Price Representation

Prices should preferably be represented using an exact integer tick representation where appropriate.

For example:

```text
$100.25
```

may be represented internally as:

```text
10025
```

if the chosen scale is 1/100 dollar.

This avoids unnecessary floating-point ambiguity.

The original dataset price convention must be preserved and documented.

---

# 11. Quantity Representation

Quantities represent the number of shares/contracts available or involved in an event.

Important distinction:

```text
Original Quantity
```

versus:

```text
Remaining Quantity
```

The LOB engine should track remaining quantity after executions and cancellations.

---

# 12. Research Dataset Schema

After processing, a research dataset may contain:

```text
timestamp
best_bid
best_ask
mid_price
spread
bid_depth
ask_depth
imbalance
microprice
ofi
trade_volume
trade_direction
trade_intensity
cancel_intensity
future_return
```

The exact schema will evolve as research questions are developed.

---

# 13. Data Integrity Rules

The processing pipeline should check for:

* invalid timestamps
* missing required fields
* negative quantities
* impossible price values
* duplicate active order identifiers
* inconsistent order state
* invalid cancellations
* invalid executions
* unexpected event ordering

Data should be validated before being used for statistical analysis.

---

# 14. Important Principle

A variable should never be added simply because it is common in market-microstructure literature.

For every variable we introduce, we should know:

1. What does it measure?
2. How is it calculated?
3. What assumptions does it make?
4. What information does it use?
5. Could it introduce look-ahead bias?
6. Why might it matter economically?

This dictionary should therefore evolve together with the research.