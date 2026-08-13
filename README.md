# LOB Microstructure Lab

A research-oriented limit order book (LOB) reconstruction and market microstructure analysis project.

The goal of this project is not to build a production-grade exchange or a low-latency trading system. The goal is to **understand what is actually happening inside a limit order book** and build a system that lets us study it from real high-frequency market data.

---

## 1. Why This Project?

A lot of quantitative trading research eventually comes down to understanding how orders interact.

At the top level, a market looks simple:

```text
Bid:  100.00
Ask:  100.01
```

But underneath that quote is a constantly changing system of:

* limit order arrivals
* cancellations
* executions
* queue formation
* liquidity consumption
* spread changes
* order-flow imbalance
* price movements

The interesting question is:

> **Can we reconstruct this process and use it to understand how short-term price formation actually works?**

That is what this project is about.

Rather than treating the order book as a table of numbers, we want to treat it as a **dynamic system** and study how its state evolves over time.

---

# 2. Main Objective

The project has three broad goals:

### 1. Reconstruct the local limit order book

Take high-frequency order-book/message data and maintain an independent local representation of the market.

### 2. Build a microstructure research environment

Use the reconstructed book to study quantities such as:

* bid-ask spread
* market depth
* depth imbalance
* microprice
* order-flow imbalance (OFI)
* order arrival and cancellation intensity
* queue dynamics
* trade intensity
* liquidity consumption

### 3. Conduct empirical research

Use these quantities to investigate questions about:

* short-horizon price formation
* price impact
* liquidity
* order-flow predictability
* queue dynamics
* market regimes
* intraday patterns

The final objective is not simply to produce features.

It is to ask:

> **What do these features actually tell us about the market?**

---

# 3. Dataset

The primary dataset for the project will be **LOBSTER**, which provides high-frequency limit-order-book data reconstructed from NASDAQ TotalView-ITCH data.

LOBSTER is useful here because it allows us to focus on the **market microstructure research problem** without making the entire project depend on processing a multi-gigabyte raw binary exchange feed.

The raw NASDAQ ITCH dataset may be used later as an optional extension for working directly with the exchange-level message format.

### Primary data

```text
LOBSTER
├── Message data
└── Order book data
```

### Optional extension

```text
NASDAQ TotalView-ITCH
        ↓
Raw exchange messages
        ↓
Our parser
        ↓
Normalized events
        ↓
LOB engine
```

The distinction is intentional.

The main project is about **understanding market microstructure**, not becoming a feed-handler engineer.

---

# 4. Project Architecture

The project is organized into three main layers:

```text
                    MARKET DATA
                         │
                         ▼
                ┌─────────────────┐
                │  Data Ingestion  │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   LOB Engine    │
                │                 │
                │ Order State     │
                │ Price Levels    │
                │ FIFO Queues     │
                │ Book State      │
                └────────┬────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Microstructure Layer │
              │                      │
              │ OFI                  │
              │ Microprice           │
              │ Imbalance            │
              │ Spread               │
              │ Queue Dynamics       │
              │ Trade Flow           │
              └──────────┬───────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Research Layer  │
                │                 │
                │ Hypotheses      │
                │ Statistical     │
                │ Tests           │
                │ Robustness      │
                └─────────────────┘
```

The key design principle is **separation of concerns**.

The data loader should not know how the order book works.

The order book should not know how OFI is calculated.

The feature layer should not decide whether a feature is statistically useful.

And the research layer should not quietly change the underlying data.

---

# 5. Repository Structure

```
lob_engine/
├── pyproject.toml            
├── README.md
├── data/
│   ├── raw/                    
│   └── processed/             
├── notebooks/
│   └── 01_exploration.ipynb   
├── src/
│   └── lob_analytics/
│       ├── __init__.py
│       ├── types.py           
│       ├── parser.py           
│       ├── core/
│       │   ├── __init__.py
│       │   ├── order.py        
│       │   ├── price_level.py  
│       │   └── book_state.py   
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── reconstruction.py  
│       │   └── matching.py        
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── conservation.py    
│       │   └── snapshot.py        
│       ├── analytics/
│       │   ├── __init__.py
│       │   ├── metrics.py         
│       │   └── queueing.py        
│       └── viz/
│           ├── __init__.py
│           └── streamlit_app.py  
├── tests/
│   ├── __init__.py
│   ├── conftest.py             
│   ├── test_book_state.py      
│   ├── test_reconstruction.py  
│   ├── test_matching.py        
│   └── test_validation.py      
└── scripts/
    └── reconstruct_day.py      
    ```

---

# 6. Three-Phase Development Plan

## Phase I — Market State Engine

**Goal: Understand how the order book evolves.**

We will build the core LOB representation and learn how individual events change the state of the market.

Topics include:

* order representation
* price levels
* FIFO queues
* order additions
* cancellations
* executions
* deletions
* replacements
* best bid / ask
* depth
* book snapshots
* reconstruction validation

The fundamental process is:

```text
Event_t
   ↓
LOB State_t
   ↓
State Transition
   ↓
LOB State_(t+1)
```

The important question at this stage is:

> **Can our local book reproduce the market state correctly?**

---

# 7. Phase II — Microstructure Observatory

**Goal: Turn the LOB into something we can investigate.**

Once the book is working, we build the measurement layer.

We will calculate and visualize:

### Quotes

* best bid
* best ask
* mid-price
* spread

### Depth

* level-1 depth
* multi-level depth
* cumulative depth
* depth concentration

### Imbalance

* top-of-book imbalance
* multi-level imbalance
* depth imbalance

### Microprice

A liquidity-weighted estimate of where the next mid-price movement may be biased.

### Order Flow

* limit-order arrivals
* cancellations
* executions
* order-flow imbalance
* trade intensity

### Queue Dynamics

* queue size
* queue depletion
* order lifetime
* fill probability
* position within the queue

The purpose of this phase is not to immediately build a trading strategy.

It is to **learn how the market behaves**.

---

# 8. Phase III — Microstructure Research Laboratory

**Goal: Turn observations into testable research questions.**

This is where the project moves from engineering into quantitative research.

Examples of questions we may investigate:

### Order Flow

Does order-flow imbalance contain information about short-horizon returns?

```text
OFI(t)
   ↓
Return(t + Δ)
```

---

### Microprice

Does microprice predict the next mid-price movement better than the simple mid-price?

---

### Liquidity

How does available depth affect the price impact of trades?

---

### Queue Dynamics

How does the amount of liquidity ahead of an order affect its probability of execution?

---

### Price Formation

What does the order book look like immediately before a price move?

---

### Conditional Predictability

Does the predictive power of order flow change depending on:

* spread
* volatility
* depth
* trading intensity
* time of day
* market state

The exact research questions will evolve as we explore the data.

---

# 9. Research Philosophy

A major goal of this project is to avoid confusing **correlation with a useful trading signal**.

For every potentially interesting relationship, we want to ask:

1. Is the relationship statistically significant?
2. Is it economically meaningful?
3. How stable is it?
4. Does it survive different sampling horizons?
5. Does it survive different market conditions?
6. Does it survive out-of-sample testing?
7. Could it simply be an artifact of the dataset?
8. Does it remain meaningful after considering transaction costs?

For example, finding:

```text
OFI ↑  →  Future Return ↑
```

is only the beginning.

The interesting research starts when we ask:

> **Why?**

---

# 10. What We Are NOT Trying to Build

This project is deliberately not focused on:

* building a production exchange
* ultra-low-latency C++
* colocated trading infrastructure
* kernel bypass
* FPGA implementation
* exchange connectivity
* optimizing every operation to nanoseconds

Performance matters where it helps us understand the system, but **research correctness comes first**.

A clean, correct implementation that allows us to investigate market behavior is more valuable for this project than an unnecessarily complicated high-frequency trading system.

---

# 11. Why Build the LOB Engine Ourselves?

LOBSTER already provides reconstructed order-book information.

So why build our own engine?

Because the purpose isn't simply to obtain an LOB.

We want to understand **how the LOB gets there**.

Building the local engine forces us to understand:

```text
Order Arrival
      ↓
Queue Formation
      ↓
Cancellation / Execution
      ↓
Liquidity Changes
      ↓
Price Formation
```

That understanding is the main educational value of the project.

The LOBSTER data gives us the raw material.

Our engine gives us the laboratory.

---

# 12. Validation

The reconstruction engine will not be trusted simply because the code runs.

We will build consistency checks such as:

* bid prices remain below the best ask where appropriate
* quantities never become negative
* deleted orders cannot remain active
* cancelled quantity cannot exceed remaining quantity
* order references remain consistent
* reconstructed depth agrees with available reference data
* event timestamps remain ordered
* trade and book transitions are internally consistent

Where possible, reconstructed states will be compared against the corresponding LOBSTER order-book data.

---

# 13. Expected Outputs

By the end of the project, the system should be capable of producing:

### Market-state data

```text
timestamp
best_bid
best_ask
mid_price
spread
bid_depth
ask_depth
```

### Microstructure features

```text
microprice
depth_imbalance
ofi
trade_intensity
cancel_intensity
queue_statistics
```

### Research outputs

```text
correlation analysis
conditional distributions
event studies
predictive regressions
classification results
price-impact curves
queue-survival curves
intraday patterns
```

### Visualizations

Examples include:

* order-book heatmaps
* depth profiles
* spread distributions
* OFI vs. returns
* microprice vs. future mid-price
* price-impact curves
* queue dynamics
* intraday liquidity patterns

---

# 14. Long-Term Extension

Once the research engine is working with LOBSTER, the project can be extended to raw exchange feeds.

For example:

```text
LOBSTER
   │
   ├──────────────┐
   │              │
   ▼              ▼
Research       Validation
               │
               ▼
        Raw NASDAQ ITCH
               │
               ▼
          ITCH Parser
               │
               ▼
       Normalized Events
               │
               ▼
          Same LOB Engine
```

This gives us a clean path from **research-oriented work** toward deeper market-data engineering without making it a requirement for the core project.

---


# 15. Final Goal

The ultimate goal is not to say:

> "I built a limit order book."

The goal is to be able to sit in front of the system and ask:

> **What is the market doing?**

And then investigate the answer using data.

We want to understand how liquidity appears and disappears, how orders interact, how queues evolve, how trades consume liquidity, and how these microscopic changes eventually translate into price movements.

The LOB is not the end product.

**It is the microscope.**

## Installation
To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd lob-engine
pip install -r requirements.txt
```

## Usage
Run the main script to start the engine:

```bash
python main.py
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.