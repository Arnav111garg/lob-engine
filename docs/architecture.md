# Project Architecture

## 1. Overview

The LOB Microstructure Lab is designed as a research-oriented system for studying the dynamics of a limit order book (LOB).

The architecture separates four responsibilities:

```text
Data
  ↓
Market State
  ↓
Microstructure Features
  ↓
Research
```

The main design principle is **separation of concerns**.

A data source should not know how the LOB works.
The LOB engine should not know how a research feature is calculated.
The research layer should operate on well-defined data produced by the earlier layers.

---

## 2. High-Level Architecture

```text
                         MARKET DATA
                              │
                              ▼
                    ┌──────────────────┐
                    │  Data Ingestion  │
                    │                  │
                    │ LOBSTER Reader   │
                    │ Future: ITCH     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Event Normalizer │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    LOB Engine    │
                    │                  │
                    │ Orders           │
                    │ Price Levels     │
                    │ FIFO Queues      │
                    │ Book State       │
                    └────────┬─────────┘
                             │
                             ▼
                ┌──────────────────────────┐
                │ Microstructure Features │
                │                          │
                │ Spread                   │
                │ Depth                    │
                │ Imbalance                │
                │ Microprice               │
                │ OFI                      │
                │ Queue Dynamics           │
                │ Trade Flow               │
                └────────────┬─────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Research Layer   │
                    │                  │
                    │ Hypotheses       │
                    │ Statistical Tests│
                    │ Event Studies    │
                    │ Robustness       │
                    └──────────────────┘
```

---

# 3. Data Layer

The data layer is responsible only for obtaining and validating market data.

Current primary source:

```text
LOBSTER
```

Potential future sources:

```text
NASDAQ TotalView-ITCH
Other exchange feeds
Simulated order flow
```

The data layer converts source-specific formats into a normalized internal representation.

For example:

```python
AddOrder(...)
CancelOrder(...)
ExecuteOrder(...)
DeleteOrder(...)
ReplaceOrder(...)
```

The rest of the system should not depend on the original file format.

---

# 4. Engine Layer

The engine maintains the current state of the limit order book.

Core components:

### Order

Represents an individual resting order.

### OrderList

Maintains FIFO priority between orders at the same price level.

### PriceLevel

Represents all resting liquidity at a particular price.

### LimitBook

Maintains bid and ask sides and provides access to the current book state.

### BookState

Represents the complete state of the market at a particular point in time.

Conceptually:

```text
LimitBook
│
├── Bid Side
│   ├── Price Level
│   │   └── FIFO Orders
│   └── Price Level
│       └── FIFO Orders
│
└── Ask Side
    ├── Price Level
    │   └── FIFO Orders
    └── Price Level
        └── FIFO Orders
```

---

# 5. Feature Layer

The feature layer transforms raw book state into measurable market-microstructure variables.

Examples:

```text
Book State
    │
    ├── Best Bid / Ask
    ├── Mid Price
    ├── Spread
    ├── Depth
    ├── Imbalance
    ├── Microprice
    ├── OFI
    ├── Trade Intensity
    └── Queue Statistics
```

This layer should not contain trading decisions.

It answers:

> "What is happening in the market?"

---

# 6. Research Layer

The research layer answers:

> "What does it mean?"

Examples:

```text
OFI
 ↓
Future Return
```

or:

```text
Depth
 ↓
Price Impact
```

or:

```text
Queue Position
 ↓
Fill Probability
```

Research modules should produce reproducible statistical results rather than hard-coded trading rules.

---

# 7. Data Flow

A typical processing pipeline is:

```text
LOBSTER Message
      ↓
Parsed Event
      ↓
Normalized Event
      ↓
LOB State Update
      ↓
Book Snapshot
      ↓
Feature Calculation
      ↓
Research Dataset
      ↓
Statistical Analysis
```

The central state transition is:

[
S_{t+1}=F(S_t,E_t)
]

where:

* (S_t) = current LOB state
* (E_t) = incoming market event
* (F) = state transition function
* (S_{t+1}) = updated LOB state

---

# 8. Design Principles

### Correctness before optimization

The first objective is to correctly reconstruct market state.

### Reproducibility

The same input data should produce the same output.

### Separation of concerns

Each component should have a clear responsibility.

### Data-source independence

The LOB engine should not depend on LOBSTER-specific implementation details.

### Research-first design

Engineering decisions should serve the goal of understanding market microstructure.

### Validation

Every important reconstruction step should have consistency checks.

---

# 9. Three-Phase Development

## Phase I — Market State Engine

```text
Data → Events → LOB
```

Focus:

* data ingestion
* event normalization
* order representation
* FIFO queues
* book reconstruction
* validation

## Phase II — Microstructure Observatory

```text
LOB → Features → Visualization
```

Focus:

* spread
* depth
* imbalance
* microprice
* OFI
* queue dynamics
* trade flow

## Phase III — Research Laboratory

```text
Features → Hypotheses → Statistical Evidence
```

Focus:

* predictive relationships
* price impact
* liquidity
* queue behavior
* robustness
* economic interpretation
