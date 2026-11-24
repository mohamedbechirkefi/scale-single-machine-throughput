# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Ingestion: the synthetic dataset, the response encoding and the request streams.

Everything here is deterministic given its seed. The dataset is labelled
synthetic; it describes no real catalogue.
"""

from __future__ import annotations

import bisect
import hashlib
import os
import random
import sqlite3
from dataclasses import dataclass
from typing import Iterator

from .config import Workload

GENERATOR_VERSION = "items-v1.0"
NULL_BODY = b"0" * 64  # fixed 64-byte control body for GET /null
PRICE_DIGITS = 9
MAX_PRICE_CENTS = 10**PRICE_DIGITS - 1


@dataclass(frozen=True)
class Row:
    id: int
    sku: str
    category: int
    price_cents: int
    payload: str


@dataclass(frozen=True)
class Request:
    """One request of a stream. ``op`` is 'read' or 'write'; ``cents`` only for writes."""

    op: str
    sku: str
    cents: int = 0


def sku_for(i: int) -> str:
    if not isinstance(i, int) or i < 0 or i > 99_999_999:
        raise ValueError("row index must be an integer in [0, 99999999]")
    return f"SKU-{i:08d}"


def make_row(i: int, seed: int, payload_bytes: int) -> Row:
    """Row i of the dataset; payload is hex from SHA-256 chains, exactly payload_bytes long."""
    if payload_bytes < 1:
        raise ValueError("payload_bytes must be >= 1")
    h = hashlib.sha256(f"{seed}:{i}".encode()).hexdigest()
    category = int(h[:4], 16) % 1000
    price = 100 + int(h[4:12], 16) % 999_900
    chunks = []
    total = 0
    j = 0
    while total < payload_bytes:
        c = hashlib.sha256(f"{seed}:{i}:p{j}".encode()).hexdigest()
        chunks.append(c)
        total += len(c)
        j += 1
    return Row(i, sku_for(i), category, price, "".join(chunks)[:payload_bytes])


def iter_rows(workload: Workload) -> Iterator[Row]:
    for i in range(workload.rows):
        yield make_row(i, workload.dataset_seed, workload.payload_bytes)


def render_item(row: tuple | Row) -> bytes:
    """Fixed byte layout of a read response (identical for every arm). Numbers are
    right-aligned with spaces, so the body is valid JSON of constant length."""
    if isinstance(row, Row):
        rid, sku, cat, price, payload = row.id, row.sku, row.category, row.price_cents, row.payload
    else:
        rid, sku, cat, price, payload = row
    if not 0 <= price <= MAX_PRICE_CENTS:
        raise ValueError("price_cents out of range")
    return (
        f'{{"id":{rid:8d},"sku":"{sku}","category":{cat:3d},'
        f'"price_cents":{price:{PRICE_DIGITS}d},"payload":"{payload}"}}'
    ).encode("ascii")


def render_write(sku: str, cents: int) -> bytes:
    if not 0 <= cents <= MAX_PRICE_CENTS:
        raise ValueError("price_cents out of range")
    return f'{{"sku":"{sku}","price_cents":{cents:{PRICE_DIGITS}d}}}'.encode("ascii")


def item_body_length(payload_bytes: int) -> int:
    return len(render_item((0, sku_for(0), 0, 0, "x" * payload_bytes)))


def build_database(path: str, workload: Workload, index: bool) -> str:
    """Create the SQLite file (WAL). Returns the SHA-256 of the logical row content."""
    workload.validate()
    for suffix in ("", "-wal", "-shm"):
        if os.path.exists(path + suffix):
            os.remove(path + suffix)
    con = sqlite3.connect(path)
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute(
            "CREATE TABLE items(id INTEGER PRIMARY KEY, sku TEXT, category INTEGER,"
            " price_cents INTEGER, payload TEXT)"
        )
        digest = hashlib.sha256()
        batch = []
        for r in iter_rows(workload):
            batch.append((r.id, r.sku, r.category, r.price_cents, r.payload))
            digest.update(render_item(r))
            if len(batch) >= 10_000:
                con.executemany("INSERT INTO items VALUES (?,?,?,?,?)", batch)
                batch.clear()
        if batch:
            con.executemany("INSERT INTO items VALUES (?,?,?,?,?)", batch)
        if index:
            con.execute("CREATE INDEX ix_items_sku ON items(sku)")
        con.commit()
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        con.close()
    return digest.hexdigest()


class ZipfSampler:
    """Zipf(s) over n keys mapped through a seeded permutation; s = 0 is uniform.

    P(rank k) is proportional to k^-s for k = 1..n. Sampling inverts the CDF by
    bisection, so it is exact up to floating-point rounding of the CDF.
    """

    def __init__(self, n: int, s: float, perm_seed: int):
        if n < 1:
            raise ValueError("n must be >= 1")
        if s < 0:
            raise ValueError("s must be >= 0")
        weights = [k ** (-s) for k in range(1, n + 1)]
        total = sum(weights)
        acc = 0.0
        cdf = []
        for w in weights:
            acc += w
            cdf.append(acc / total)
        cdf[-1] = 1.0
        self.cdf = cdf
        perm = list(range(n))
        random.Random(perm_seed).shuffle(perm)
        self.perm = perm
        self.n = n

    def rank(self, u: float) -> int:
        """0-based rank for a uniform draw u in [0, 1)."""
        return min(bisect.bisect_right(self.cdf, u), self.n - 1)

    def sample(self, rng: random.Random) -> int:
        return self.perm[self.rank(rng.random())]


def request_stream(workload: Workload, sampler: ZipfSampler, seed: int) -> Iterator[Request]:
    """Infinite deterministic request stream for one connection."""
    rng = random.Random(seed)
    while True:
        key = sampler.sample(rng)
        if rng.random() < workload.write_fraction:
            yield Request("write", sku_for(key), rng.randrange(100, 1_000_000))
        else:
            yield Request("read", sku_for(key))
