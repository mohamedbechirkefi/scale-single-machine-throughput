# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
import math

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scale import metrics as m


def test_nearest_rank_golden():
    # Textbook nearest-rank example: 15, 20, 35, 40, 50
    v = [50, 15, 40, 20, 35]
    assert m.percentile_nearest_rank(v, 5) == 15
    assert m.percentile_nearest_rank(v, 30) == 20
    assert m.percentile_nearest_rank(v, 40) == 20
    assert m.percentile_nearest_rank(v, 50) == 35
    assert m.percentile_nearest_rank(v, 100) == 50
    ten = list(range(1, 11))
    assert m.percentile_nearest_rank(ten, 50) == 5
    assert m.percentile_nearest_rank(ten, 95) == 10
    assert m.percentile_nearest_rank(ten, 99) == 10
    assert m.percentile_nearest_rank([], 50) is None
    for bad in (0, -1, 101):
        with pytest.raises(ValueError):
            m.percentile_nearest_rank(ten, bad)


@given(st.lists(st.floats(-1e6, 1e6), min_size=1, max_size=200),
       st.floats(0.01, 100), st.floats(0.01, 100))
def test_percentile_bounded_and_monotone(v, p, q):
    a, b = sorted((p, q))
    pa, pb = m.percentile_nearest_rank(v, a), m.percentile_nearest_rank(v, b)
    assert min(v) <= pa <= pb <= max(v)
    assert pa in v


def test_goodput_and_error_rate():
    assert m.goodput_rps(300, 3.0) == 100.0
    assert m.goodput_rps(0, 1.0) == 0.0
    with pytest.raises(ValueError):
        m.goodput_rps(1, 0)
    with pytest.raises(ValueError):
        m.goodput_rps(-1, 1)
    assert m.error_rate(1, 4) == 0.25
    assert m.error_rate(0, 0) is None
    with pytest.raises(ValueError):
        m.error_rate(5, 4)


def test_peak_and_saturation_golden():
    levels = [(1, 100.0), (2, 190.0), (4, 300.0), (8, 310.0), (16, 290.0)]
    assert m.peak_goodput(levels) == (310.0, 8)
    # 0.95 * 310 = 294.5 -> smallest c with G >= 294.5 is 4
    assert m.saturation_concurrency(levels) == 4
    assert m.peak_goodput([(4, 5.0), (1, 5.0)]) == (5.0, 1)  # ties -> smallest c
    with pytest.raises(ValueError):
        m.peak_goodput([])
    with pytest.raises(ValueError):
        m.peak_goodput([(1, -1.0)])
    with pytest.raises(ValueError):
        m.saturation_concurrency(levels, frac=0)


@given(st.lists(st.tuples(st.integers(1, 1024), st.floats(0, 1e6)), min_size=1, max_size=10,
                unique_by=lambda t: t[0]))
def test_peak_is_max_and_csat_le_peak(levels):
    g, c = m.peak_goodput(levels)
    assert g == max(x for _, x in levels)
    assert m.saturation_concurrency(levels) <= c


def test_generator_limited_rule():
    assert m.generator_limited(100, 0.5, 1, None) == (False, [])
    flag, why = m.generator_limited(600, 0.5, 1, 1000.0)
    assert flag and "ceiling" in why[0]
    flag, why = m.generator_limited(10, 0.9, 1, None)
    assert flag and "CPU" in why[0]
    assert m.generator_limited(10, 0.9, 2, None)[0] is False
    with pytest.raises(ValueError):
        m.generator_limited(1, 0.1, 0, None)


def test_ratio_helpers():
    assert m.log_ratio(2.0, 1.0) == pytest.approx(math.log(2))
    with pytest.raises(ValueError):
        m.log_ratio(0, 1)
    assert m.geometric_mean([1, 4]) == pytest.approx(2.0)
    with pytest.raises(ValueError):
        m.geometric_mean([])
    with pytest.raises(ValueError):
        m.geometric_mean([1, -1])
    assert m.sample_sd([1.0, 3.0]) == pytest.approx(math.sqrt(2))
    with pytest.raises(ValueError):
        m.sample_sd([1.0])


def test_t_half_width_matches_protocol_planning_value():
    # protocol section 7: sd 0.05, n 10 -> 2.262 * 0.05 / sqrt(10) = 0.03577 (about 3.6 %)
    assert m.t_half_width(0.05, 10) == pytest.approx(0.035765, abs=1e-6)
    assert m.t_half_width(0.0, 5) == 0.0
    with pytest.raises(ValueError):
        m.t_half_width(0.05, 1)
    with pytest.raises(ValueError):
        m.t_half_width(-1, 5)


def test_bootstrap_deterministic_and_contains_mean():
    v = [0.1, 0.2, 0.15, 0.05, 0.3]
    a = m.bootstrap_mean_ci(v, 2000, seed=1)
    assert a == m.bootstrap_mean_ci(v, 2000, seed=1)
    mean, lo, hi = a
    assert mean == pytest.approx(np.mean(v))
    assert lo <= mean <= hi
    assert min(v) <= lo and hi <= max(v)
    assert m.bootstrap_mean_ci([0.2, 0.2, 0.2], 100, 0)[1:] == pytest.approx((0.2, 0.2))
    with pytest.raises(ValueError):
        m.bootstrap_mean_ci([], 10, 0)
    with pytest.raises(ValueError):
        m.bootstrap_mean_ci([1.0], 10, 0, level=1.0)


def test_latency_summary_ms():
    s = m.summarize_latencies_ms([1_000_000 * k for k in range(1, 101)])
    assert s == {"p50_ms": 50.0, "p95_ms": 95.0, "p99_ms": 99.0, "max_ms": 100.0}
    assert m.summarize_latencies_ms([])["p99_ms"] is None
