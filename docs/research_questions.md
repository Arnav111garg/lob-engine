# Research Questions

This document contains the research questions that will guide the project.

The questions are intentionally not treated as fixed from the beginning. As we explore the data, new observations may lead to better questions.

The objective is not to manufacture trading signals.

The objective is to understand **how order-book dynamics relate to price formation and liquidity**.

---

# Phase I — Understanding the Book

Before testing predictive relationships, we need to understand the basic behavior of the market.

### Q1. How does the limit order book evolve over time?

Study:

* order arrivals
* cancellations
* executions
* deletions
* replacements
* changes in depth

---

### Q2. What does a typical order book look like?

Investigate:

* spread distribution
* depth distribution
* number of active orders
* depth across price levels
* order-size distribution

---

### Q3. How does market activity vary throughout the trading day?

Compare:

* early session
* middle session
* late session

using:

* event intensity
* spread
* depth
* volatility
* trade intensity

---

# Phase II — Order Flow and Price Formation

## Q4. Does order-flow imbalance predict short-horizon price movements?

Test:

[
OFI_t
\rightarrow
r_{t+\Delta}
]

for several horizons.

Possible horizons:

```text
10 ms
100 ms
1 sec
5 sec
10 sec
```

The exact horizons will depend on the data frequency.

---

## Q5. Does depth imbalance predict the next price movement?

Test whether:

[
I_t=
\frac{Q_{b,t}-Q_{a,t}}
{Q_{b,t}+Q_{a,t}}
]

contains information about:

[
sign(P_{t+\Delta}-P_t)
]

---

## Q6. Does microprice predict future mid-price movement?

Compare:

[
P_{\mu,t}
]

against:

[
P_{m,t}
]

as predictors of future price movement.

A useful question is whether microprice provides information beyond what is already contained in the mid-price.

---

# Phase III — Liquidity and Price Impact

## Q7. How does available depth affect price impact?

Investigate the relationship between:

[
\text{Available Depth}
]

and:

[
\Delta P
]

following trades or aggressive order flow.

---

## Q8. How does the bid-ask spread relate to short-term volatility?

Study whether wider spreads occur during periods of:

* high volatility
* high trading activity
* low depth
* strong order-flow imbalance

---

## Q9. How quickly does liquidity recover after being consumed?

Identify large liquidity-consuming events and measure:

```text
Liquidity immediately before
        ↓
Liquidity immediately after
        ↓
Recovery time
```

This can provide insight into the **resilience** of the order book.

---

# Phase IV — Queue Dynamics

## Q10. How does queue position affect execution probability?

For an order placed at a particular price, investigate:

[
P(\text{Fill within }\Delta t
\mid
\text{Queue Ahead})
]

---

## Q11. What determines order lifetime?

Study whether order lifetime depends on:

* distance from mid-price
* queue position
* spread
* volatility
* time of day
* market activity

---

## Q12. How does queue depletion relate to price movement?

Investigate whether rapid depletion of the best bid or ask is associated with subsequent price changes.

Conceptually:

```text
Best Bid Depletion
       ↓
Liquidity disappears
       ↓
Price pressure
       ↓
Mid-price movement?
```

---

# Phase V — Event Studies

## Q13. What happens immediately before a price move?

Identify events where:

[
\Delta P_m \neq 0
]

and examine the preceding order-book state.

Compare:

```text
Depth
Imbalance
OFI
Spread
Trade intensity
Cancellation intensity
```

between upward and downward price movements.

---

## Q14. What happens after a large aggressive trade?

Measure:

* immediate price response
* depth depletion
* spread change
* liquidity recovery
* subsequent returns

This helps distinguish temporary liquidity shocks from more persistent price impact.

---

# Phase VI — Conditional Microstructure

A relationship observed on average may behave very differently under different market conditions.

## Q15. Does OFI behave differently under different liquidity conditions?

Condition on:

* narrow vs wide spread
* high vs low depth
* high vs low volatility

---

## Q16. Does microprice become more informative when the book is imbalanced?

Compare predictive performance across different imbalance regimes.

---

## Q17. Does the relationship between order flow and returns vary throughout the trading day?

Compare different intraday periods.

---

# Phase VII — Robustness

Finding a relationship is not enough.

## Q18. Does the relationship survive different sampling horizons?

For example:

```text
event time
100 ms
1 sec
5 sec
10 sec
```

---

## Q19. Does the relationship survive different market conditions?

Test across:

* volatility regimes
* liquidity regimes
* trading-intensity regimes

---

## Q20. Does the relationship remain out-of-sample?

Separate:

```text
Research / Training Period
          ↓
Validation Period
          ↓
Out-of-Sample Test
```

A result that only exists in the period used to discover it should not be treated as strong evidence.

---

# Phase VIII — Economic Significance

## Q21. Is statistical predictability economically meaningful?

A statistically significant relationship may still be too small to exploit.

We therefore need to consider:

* transaction costs
* spread
* execution uncertainty
* latency
* turnover
* adverse selection

The purpose is not necessarily to build a profitable strategy.

Rather, these considerations help determine whether an observed relationship has meaningful economic magnitude.

---

# Research Workflow

Every research question should follow approximately the same process:

```text
Observation
     ↓
Hypothesis
     ↓
Feature Definition
     ↓
Target Definition
     ↓
Data Construction
     ↓
Exploratory Analysis
     ↓
Statistical Test
     ↓
Robustness Checks
     ↓
Economic Interpretation
```

---

# What Counts as a Good Result?

A good result is not necessarily:

```text
"Accuracy = 57%"
```

A much better result is something like:

> Under high-liquidity conditions, positive order-flow imbalance is associated with a measurable increase in the probability of an upward short-horizon mid-price movement. The relationship weakens substantially when the spread widens and is not stable across all intraday periods.

That gives us something to investigate.

---

# Research Principles

### 1. Avoid look-ahead bias

A feature at time (t) must only use information available at or before (t).

### 2. Separate discovery from validation

Interesting patterns found during exploration should be tested on data not used to discover them.

### 3. Don't optimize blindly

A more complicated feature is not automatically a better feature.

### 4. Look for mechanisms

Whenever a statistical relationship appears, ask:

> **Why should this relationship exist?**

### 5. Investigate failures

When a feature does not work, that is still useful information.

Understanding where a microstructure relationship breaks down may be more interesting than its average performance.

---

# The Ultimate Research Question

All of the individual questions eventually connect to one broader question:

> **How does the microscopic interaction of orders, liquidity, and queues translate into short-term price formation?**

That is the central question this project is trying to explore.
