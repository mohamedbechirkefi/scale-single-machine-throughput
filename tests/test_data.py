# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
import json
import random
import sqlite3
from collections import Counter

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scale.config import Workload
from scale.data import (ZipfSampler, build_database, item_body_length, make_row, render_item,
                        render_write, request_stream, sku_for)


def test_sku_format_and_bounds():
    assert sku_for(0) == "SKU-00000000"
    assert sku_for(42) == "SKU-00000042"
    with pytest.raises(ValueError):
        sku_for(-1)
    with pytest.raises(ValueError):
        sku_for(10**8)


def test_rows_deterministic_and_sized():
    a, b = make_row(3, 11, 256), make_row(3, 11, 256)
    assert a == b
    assert len(a.payload) == 256
    assert make_row(3, 12, 256) != a
    assert 0 <= a.category < 1000 and 100 <= a.price_cents < 1_000_000
    with pytest.raises(ValueError):
        make_row(0, 1, 0)


def test_render_item_golden():
    # hand-written expected bytes
    body = render_item((5, "SKU-00000005", 7, 1234, "abc"))
    assert body == (b'{"id":       5,"sku":"SKU-00000005","category":  7,'
                    b'"price_cents":     1234,"payload":"abc"}')
    parsed = json.loads(body)
    assert parsed == {"id": 5, "sku": "SKU-00000005", "category": 7, "price_cents": 1234, "payload": "abc"}
    assert render_write("SKU-00000005", 99) == b'{"sku":"SKU-00000005","price_cents":       99}'
    with pytest.raises(ValueError):
        render_write("x", -1)


@given(i=st.integers(0, 99_999_999), price=st.integers(0, 999_999_999), cat=st.integers(0, 999))
def test_item_body_length_constant(i, price, cat):
    body = render_item((i, sku_for(i), cat, price, "p" * 16))
    assert len(body) == item_body_length(16)
    json.loads(body)


def test_zipf_hand_computed_cdf():
    # n = 3, s = 1: weights 1, 1/2, 1/3, total 11/6 -> CDF 6/11, 9/11, 1
    z = ZipfSampler(3, 1.0, perm_seed=0)
    assert z.cdf == pytest.approx([6 / 11, 9 / 11, 1.0])
    assert z.rank(0.0) == 0 and z.rank(0.54) == 0
    assert z.rank(0.55) == 1 and z.rank(0.81) == 1
    assert z.rank(0.82) == 2 and z.rank(0.999999) == 2


def test_zipf_uniform_when_s_zero():
    z = ZipfSampler(4, 0.0, perm_seed=0)
    assert z.cdf == pytest.approx([0.25, 0.5, 0.75, 1.0])


@settings(max_examples=30)
@given(n=st.integers(1, 300), s=st.floats(0, 3), seed=st.integers(0, 10**6))
def test_zipf_property_bounds_and_perm(n, s, seed):
    z = ZipfSampler(n, s, seed)
    assert sorted(z.perm) == list(range(n))
    assert all(a <= b for a, b in zip(z.cdf, z.cdf[1:]))
    assert z.cdf[-1] == 1.0
    rng = random.Random(seed)
    assert all(0 <= z.sample(rng) < n for _ in range(50))


def test_zipf_skew_concentrates_mass():
    z = ZipfSampler(1000, 0.99, 3)
    rng = random.Random(1)
    counts = Counter(z.sample(rng) for _ in range(20_000))
    top = z.perm[0]
    assert counts[top] == max(counts.values())
    with pytest.raises(ValueError):
        ZipfSampler(0, 1.0, 0)
    with pytest.raises(ValueError):
        ZipfSampler(10, -1.0, 0)


def test_request_stream_deterministic_and_mix():
    wl = Workload(rows=1000, write_fraction=0.02)
    z = ZipfSampler(1000, 0.99, 5)
    a = [r for r, _ in zip(request_stream(wl, z, 9), range(20_000))]
    b = [r for r, _ in zip(request_stream(wl, z, 9), range(20_000))]
    assert a == b
    frac = sum(r.op == "write" for r in a) / len(a)
    assert 0.015 < frac < 0.025
    assert all(100 <= r.cents < 1_000_000 for r in a if r.op == "write")
    c = [r for r, _ in zip(request_stream(wl, z, 10), range(100))]
    assert c != a[:100]


def test_build_database(tmp_path):
    wl = Workload(rows=500, payload_bytes=32, dataset_seed=1)
    p1, p2 = str(tmp_path / "a.sqlite"), str(tmp_path / "b.sqlite")
    h1 = build_database(p1, wl, index=False)
    h2 = build_database(p2, wl, index=True)
    assert h1 == h2  # logical content is independent of the index
    con = sqlite3.connect(p2)
    assert con.execute("SELECT count(*) FROM items").fetchone()[0] == 500
    idx = [r[1] for r in con.execute("PRAGMA index_list(items)")]
    assert idx == ["ix_items_sku"]
    assert con.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    con.close()
    con = sqlite3.connect(p1)
    assert [r[1] for r in con.execute("PRAGMA index_list(items)")] == []
    plan = " ".join(str(r) for r in con.execute(
        "EXPLAIN QUERY PLAN SELECT * FROM items WHERE sku = 'SKU-00000001'"))
    assert "SCAN" in plan  # A0 really performs a full scan
    con.close()
    assert build_database(p1, wl, index=False) == h1  # rebuild is deterministic
