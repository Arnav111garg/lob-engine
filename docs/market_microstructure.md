# Market Microstructure

## 1. What Is Market Microstructure?

Market microstructure studies how trading actually happens.

Instead of looking only at daily prices or returns, we study the mechanisms through which orders interact to produce those prices.

The central object in this project is the **Limit Order Book (LOB)**.

At any point in time, the book contains resting buy and sell orders at different prices.

```text
                 SELL SIDE

Price        Quantity
101.05          300
101.04          500
101.03          200
-------------------------
101.02          400
101.01          700

                 BUY SIDE
```

The highest bid and lowest ask determine the best available prices.

---

# 2. Limit Orders and Market Orders

### Limit Order

A limit order specifies:

```text
Side
Price
Quantity
```

It provides liquidity if it rests in the book.

### Market Order

A market order seeks immediate execution against available liquidity.

It consumes liquidity from the opposite side of the book.

---

# 3. Price-Time Priority

At a particular price, orders are generally prioritized according to arrival time.

For example:

```text
Price = 100

Order A → 100 shares
Order B → 200 shares
Order C → 150 shares
```

If an incoming order consumes 150 shares at 100:

```text
Order A → 100 filled
Order B → 50 filled
```

Order C does not receive any fill.

This queue structure is central to understanding execution probability and liquidity.

---

# 4. Best Bid and Best Ask

Define:

[
P_b = \text{highest bid price}
]

[
P_a = \text{lowest ask price}
]

The mid-price is:

[
P_m=\frac{P_b+P_a}{2}
]

The bid-ask spread is:

[
S=P_a-P_b
]

The spread represents an important component of the immediate cost of trading.

---

# 5. Market Depth

The amount of resting liquidity at each price level represents market depth.

For example:

```text
Bid

100.00 → 500
99.99  → 800
99.98  → 1200
```

Depth can be examined at one level or across multiple levels.

A shallow book and a deep book can behave very differently when market orders arrive.

---

# 6. Depth Imbalance

A simple top-of-book imbalance measure is:

[
I_t=
\frac{Q_{b,t}-Q_{a,t}}
{Q_{b,t}+Q_{a,t}}
]

where:

* (Q_b) = bid quantity
* (Q_a) = ask quantity

The value lies between approximately:

[
- 1 \leq I_t \leq 1
]

Positive values indicate relatively greater bid-side liquidity.

Negative values indicate relatively greater ask-side liquidity.

The important research question is not merely whether imbalance exists, but whether it contains information about future price movements.

---

# 7. Microprice

The mid-price treats the bid and ask symmetrically.

Microprice incorporates the relative amount of liquidity at the two best prices:

[
P_{\mu}=
\frac{P_bQ_a+P_aQ_b}
{Q_b+Q_a}
]

If more liquidity is available at the bid than at the ask, the microprice shifts toward the ask.

This makes microprice useful for studying short-term pressure in the book.

---

# 8. Order Flow

The LOB changes because orders arrive, execute, cancel, or otherwise modify existing liquidity.

We can therefore study the flow of events rather than only the resulting book.

Examples:

```text
Limit-order arrivals
Cancellations
Executions
Deletions
Replacements
```

The sequence of these events can contain information about changes in liquidity and trading pressure.

---

# 9. Order Flow Imbalance

Order Flow Imbalance (OFI) attempts to measure changes in buying and selling pressure using changes in the book and/or order events.

A simplified conceptual representation is:

[
OFI_t
=====

## \text{Buy-side pressure}

\text{Sell-side pressure}
]

The exact implementation depends on the definition being used.

This project will explicitly document the chosen OFI definition rather than treating "OFI" as a single universal quantity.

---

# 10. Liquidity

Liquidity is not one-dimensional.

Important dimensions include:

* spread
* displayed depth
* resilience
* trading activity
* price impact
* queue availability

A market can have a narrow spread but relatively little depth.

Therefore, research should avoid using the spread alone as a complete measure of liquidity.

---

# 11. Price Impact

A central microstructure question is:

> How much does trading activity move the price?

One simple empirical relationship is:

[
Impact
======

\frac{\Delta P}{V}
]

where:

* (\Delta P) = price movement
* (V) = traded volume

In practice, the relationship can depend strongly on:

* available depth
* volatility
* spread
* order-flow imbalance
* trade direction
* market state

---

# 12. Queue Dynamics

A limit order does not simply exist at a price.

It has a position within a queue.

For example:

```text
Price = 100

HEAD
 │
 ▼
Order A
 │
 ▼
Order B
 │
 ▼
Order C
 │
 ▼
TAIL
```

The amount of liquidity ahead of an order can affect its probability of execution.

This creates interesting research questions around:

* queue position
* order lifetime
* cancellation
* execution probability
* queue depletion
* adverse selection

---

# 13. Event Time vs Clock Time

Traditional financial analysis often samples observations at fixed time intervals:

```text
09:30:00
09:30:01
09:30:02
...
```

High-frequency market data also allows us to study **event time**:

```text
Event 1
Event 2
Event 3
Event 4
...
```

This distinction is important because market activity is not uniform throughout the trading day.

Thousands of events may occur during a very short period of intense activity, while much less may happen during quieter periods.

---

# 14. The Central Research Perspective

The order book should not be viewed as a static table.

It is better thought of as a dynamic system:

[
S_{t+1}=F(S_t,E_t)
]

where the state of the market evolves in response to incoming events.

The purpose of this project is to study this evolution and determine which aspects of the microscopic state are related to subsequent market behavior.

---

# 15. Questions We Ultimately Want to Answer

Examples include:

* Does order-flow imbalance predict short-term returns?
* Does microprice contain information beyond mid-price?
* How does depth affect price impact?
* How quickly does liquidity recover after being consumed?
* How does queue position affect execution probability?
* What happens to the book before large price movements?
* How does microstructure change throughout the trading day?
* Which relationships remain stable across different market conditions?

These questions form the bridge between **LOB reconstruction** and **quantitative research**.
