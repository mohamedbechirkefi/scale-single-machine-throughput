# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Pure metric and statistics functions (no I/O, no clocks).

Definitions follow research/protocol.md section 6 (draft v0.1). Units are in
names: ``_rps`` requests per second, ``_ms`` milliseconds, ``_s`` seconds.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence

import numpy as np

# Two-sided 95 % Student t quantiles t(0.975, df), df = 1..30 (standard tables).
T975 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
    9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086, 21: 2.080, 22: 2.074,
    23: 2.069, 24: 2.064, 25: 2.060, 26: 2.056, 27: 2.052, 28: 2.048, 29: 2.045,
    30: 2.042,
}


def percentile_nearest_rank(values: Sequence[float], p: float) -> float | None:
    """Nearest-rank percentile: the value at 1-based rank ceil(p/100 * n) of the sorted
    sample. Returns None for an empty sample. p must lie in (0, 100]."""
    if not (0 < p <= 100):
        raise ValueError("p must be in (0, 100]")
    n = len(values)
    if n == 0:
        return None
    s = sorted(values)
    rank = max(1, math.ceil(p / 100.0 * n))
    return float(s[rank - 1])


def goodput_rps(validated_ok: int, window_s: float) -> float:
    """Validated HTTP 200 responses completed in the window, per second."""
    if window_s <= 0:
        raise ValueError("window_s must be > 0")
    if validated_ok < 0:
        raise ValueError("validated_ok must be >= 0")
    return validated_ok / window_s


def error_rate(errors: int, attempts: int) -> float | None:
    """(non-200 + transport errors) / attempts; None when nothing was attempted."""
    if errors < 0 or attempts < 0:
        raise ValueError("counts must be >= 0")
    if errors > attempts:
        raise ValueError("errors cannot exceed attempts")
    if attempts == 0:
        return None
    return errors / attempts


def peak_goodput(levels: Sequence[tuple[int, float]]) -> tuple[float, int]:
    """G* = max over levels of G(c). Input: (c, G(c)) pairs. Returns (G*, c at peak);
    ties resolve to the smallest c."""
    if not levels:
        raise ValueError("at least one level is required")
    best_c, best_g = None, -1.0
    for c, g in sorted(levels):
        if g < 0 or not math.isfinite(g):
            raise ValueError("goodput must be finite and >= 0")
        if g > best_g:
            best_c, best_g = c, g
    assert best_c is not None
    return best_g, best_c


def saturation_concurrency(levels: Sequence[tuple[int, float]], frac: float = 0.95) -> int:
    """c_sat = smallest c with G(c) >= frac * G*."""
    if not 0 < frac <= 1:
        raise ValueError("frac must be in (0, 1]")
    g_star, _ = peak_goodput(levels)
    for c, g in sorted(levels):
        if g >= frac * g_star:
            return c
    raise AssertionError("unreachable: the peak level always qualifies")


def generator_limited(goodput: float, gen_cpu_util: float, gen_cores: int,
                      ceiling_rps: float | None, goodput_frac: float = 0.5,
                      cpu_frac: float = 0.85) -> tuple[bool, list[str]]:
    """Protocol section 4: a cell is generator-limited if goodput exceeds
    goodput_frac of the generator ceiling, or generator CPU exceeds cpu_frac of
    its allotted cores. Returns (flag, reasons)."""
    if gen_cores < 1:
        raise ValueError("gen_cores must be >= 1")
    reasons = []
    if ceiling_rps is not None and goodput > goodput_frac * ceiling_rps:
        reasons.append(f"goodput {goodput:.1f} > {goodput_frac} x ceiling {ceiling_rps:.1f}")
    if gen_cpu_util > cpu_frac * gen_cores:
        reasons.append(f"generator CPU {gen_cpu_util:.2f} > {cpu_frac} x {gen_cores} cores")
    return bool(reasons), reasons


def log_ratio(treatment: float, baseline: float) -> float:
    if treatment <= 0 or baseline <= 0:
        raise ValueError("ratio requires positive values")
    return math.log(treatment / baseline)


def geometric_mean(values: Iterable[float]) -> float:
    v = list(values)
    if not v:
        raise ValueError("empty input")
    if any(x <= 0 for x in v):
        raise ValueError("geometric mean requires positive values")
    return math.exp(sum(math.log(x) for x in v) / len(v))


def sample_sd(values: Sequence[float]) -> float:
    """Sample standard deviation (n - 1 denominator)."""
    if len(values) < 2:
        raise ValueError("at least two values are required")
    return float(np.std(np.asarray(values, dtype=float), ddof=1))


def t_half_width(sd: float, n: int) -> float:
    """95 % half-width t(0.975, n-1) * sd / sqrt(n) for a mean of n paired values."""
    if n < 2 or n - 1 not in T975:
        raise ValueError("n must be in [2, 31]")
    if sd < 0:
        raise ValueError("sd must be >= 0")
    return T975[n - 1] * sd / math.sqrt(n)


def bootstrap_mean_ci(values: Sequence[float], n_resamples: int, seed: int,
                      level: float = 0.95) -> tuple[float, float, float]:
    """Percentile bootstrap of the mean. Returns (mean, low, high)."""
    if len(values) < 1:
        raise ValueError("at least one value is required")
    if n_resamples < 1:
        raise ValueError("n_resamples must be >= 1")
    if not 0 < level < 1:
        raise ValueError("level must be in (0, 1)")
    x = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_resamples, len(x)))
    means = x[idx].mean(axis=1)
    alpha = (1 - level) / 2
    lo, hi = np.quantile(means, [alpha, 1 - alpha])
    return float(x.mean()), float(lo), float(hi)


def summarize_latencies_ms(latencies_ns: Sequence[int]) -> dict[str, float | None]:
    ms = [v / 1e6 for v in latencies_ns]
    return {
        "p50_ms": percentile_nearest_rank(ms, 50),
        "p95_ms": percentile_nearest_rank(ms, 95),
        "p99_ms": percentile_nearest_rank(ms, 99),
        "max_ms": max(ms) if ms else None,
    }
