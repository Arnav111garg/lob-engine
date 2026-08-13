from __future__ import annotations

import math


def fill_probability(k: int, mu: float, theta: float) -> float:
    """
    Proposition 5.1: Probability that an order at queue position k
    is eventually executed rather than cancelled.

    f_k = ((μ + θ) / (μ + 2θ))^(k-1) * (μ / (μ + θ))

    Args:
        k: Queue position (1 = front of queue).
        mu: Execution intensity (rate of marketable order arrivals).
        theta: Per-order cancellation intensity.
    """
    if k < 1:
        raise ValueError("Queue position k must be >= 1")
    if mu <= 0 or theta <= 0:
        raise ValueError("Rates must be positive")

    ratio = (mu + theta) / (mu + 2 * theta)
    return (ratio ** (k - 1)) * (mu / (mu + theta))


def fill_probabilities(max_k: int, mu: float, theta: float) -> list[float]:
    """Compute f_k for k = 1..max_k."""
    return [fill_probability(k, mu, theta) for k in range(1, max_k + 1)]


def estimate_rates_from_counts(
    n_executions: int,
    n_cancellations: int,
    total_resting_time: float,
) -> tuple[float, float]:
    """
    Naive rate estimation: μ = executions / time, θ = cancellations / time.
    In practice you would estimate these from message timestamps.
    """
    if total_resting_time <= 0:
        raise ValueError("total_resting_time must be positive")
    mu = n_executions / total_resting_time
    theta = n_cancellations / total_resting_time
    return mu, theta