# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Project-specific verification (master prompt section 10): response equivalence,
cache invalidation and correctness under concurrency, plus a differential test of
every arm against a plain dictionary reference model."""

import random
import threading
import time

import pytest

from scale.config import ARMS
from scale.data import ZipfSampler, make_row, render_item, request_stream, sku_for
from scale.loadgen import HttpClient
from scale.server import AdmissionLimiter, CachedBackend, Overloaded, ScaleServer

from conftest import SMALL

ALL = ["A0", "A1", "A2", "A3", "A4"]


def client(srv):
    return HttpClient("127.0.0.1", srv.server_address[1])


def test_binds_loopback_only(fresh_db):
    with pytest.raises(ValueError, match="loopback"):
        ScaleServer(("0.0.0.0", 0), ARMS["A0"], fresh_db(), SMALL.rows)


def test_response_equivalence_across_arms(server_factory):
    rng = random.Random(3)
    paths = [f"/item?sku={sku_for(rng.randrange(SMALL.rows))}" for _ in range(60)]
    paths += ["/item?sku=SKU-99999999", "/item", "/item?sku=", "/nope", "/null"]
    answers = {}
    for arm in ALL:
        c = client(server_factory(arm))
        answers[arm] = [c.request("GET", p) for p in paths + paths[:10]]  # repeats hit A1 cache
        c.close()
    for arm in ALL[1:]:
        assert answers[arm] == answers["A0"], arm
    first = answers["A0"][0]
    sku = paths[0].split("=")[1]
    i = int(sku[4:])
    assert first == (200, render_item(make_row(i, SMALL.dataset_seed, SMALL.payload_bytes)))
    statuses = [s for s, _ in answers["A0"][60:65]]
    assert statuses == [404, 400, 400, 404, 200]


@pytest.mark.parametrize("arm", ALL)
def test_write_validation_errors(server_factory, arm):
    c = client(server_factory(arm))
    assert c.request("POST", "/item/SKU-00000001/price")[0] == 400
    assert c.request("POST", "/item/SKU-00000001/price?cents=-5")[0] == 400
    assert c.request("POST", "/item/SKU-00000001/price?cents=abc")[0] == 400
    assert c.request("POST", "/item/SKU-99999999/price?cents=5")[0] == 404
    assert c.request("POST", "/elsewhere")[0] == 404
    c.close()


@pytest.mark.parametrize("arm", ALL)
def test_read_after_acknowledged_write(server_factory, arm):
    c = client(server_factory(arm))
    sku = sku_for(17)
    for cents in (111, 222, 333):
        c.request("GET", f"/item?sku={sku}")  # warm any cache
        assert c.request("POST", f"/item/{sku}/price?cents={cents}")[0] == 200
        status, body = c.request("GET", f"/item?sku={sku}")
        assert status == 200 and f'"price_cents":{cents:9d}'.encode() in body
    c.close()


def test_cache_invalidation_under_concurrent_readers(server_factory):
    """A1: while 8 readers hammer a hot key, each acknowledged write must be visible to
    every read that starts after the acknowledgement."""
    srv = server_factory("A1")
    sku = sku_for(5)
    stop = threading.Event()
    stale = []
    acked = {"cents": None, "t": 0.0}
    lock = threading.Lock()

    def reader():
        c = client(srv)
        while not stop.is_set():
            with lock:
                expect, t_ack = acked["cents"], acked["t"]
            t_start = time.perf_counter()
            _, body = c.request("GET", f"/item?sku={sku}")
            if expect is not None and t_start > t_ack:
                got = int(body.split(b'"price_cents":')[1].split(b",")[0])
                # written values increase; a value newer than the last ack may already be
                # committed, but an older one is a stale read
                if got < expect:
                    stale.append((expect, got))
        c.close()

    threads = [threading.Thread(target=reader) for _ in range(8)]
    for t in threads:
        t.start()
    w = client(srv)
    for k in range(150):
        cents = 900_000_000 + k  # above every generated price (< 1,000,000)
        assert w.request("POST", f"/item/{sku}/price?cents={cents}")[0] == 200
        with lock:
            acked["cents"], acked["t"] = cents, time.perf_counter()
        time.sleep(0.001)
    stop.set()
    for t in threads:
        t.join()
    w.close()
    assert stale == []
    assert srv.backend.hits > 0  # the cache was actually exercised


def test_cache_generation_blocks_stale_reinsert(fresh_db):
    """Deterministic interleaving: a read that fetched the old row before a write must
    not re-insert it into the cache after the write."""
    be = CachedBackend(fresh_db(), capacity=10)
    sku = sku_for(3)
    orig_get = super(CachedBackend, be).get
    old = orig_get(sku)

    # simulate: reader snapshots generation, writer commits and bumps it, reader inserts
    with be._lock:
        gen = be._gen.get(sku, 0)
    be.set_price(sku, 4242)
    with be._lock:
        if be._gen.get(sku, 0) == gen:
            be._cache[sku] = old
    assert sku not in be._cache
    assert b"4242" in be.get(sku)
    be.close()


def test_cache_capacity_bounded(fresh_db):
    be = CachedBackend(fresh_db(), capacity=5)
    for i in range(20):
        be.get(sku_for(i))
    assert len(be._cache) == 5
    assert list(be._cache) == [sku_for(i) for i in range(15, 20)]  # LRU keeps the newest
    with pytest.raises(ValueError):
        CachedBackend(fresh_db(), capacity=0)
    be.close()


@pytest.mark.parametrize("arm", ALL)
def test_no_lost_writes_under_concurrency(server_factory, arm):
    """Concurrent writers on distinct keys and on one shared key: the final state equals
    serial application (distinct keys) and the last acknowledged value (shared key)."""
    srv = server_factory(arm)
    n_threads, per = 8, 15
    shared = sku_for(1)
    acks = []
    lock = threading.Lock()

    def writer(t):
        c = client(srv)
        for k in range(per):
            sku = sku_for(100 + t * per + k)
            assert c.request("POST", f"/item/{sku}/price?cents={t * 1000 + k}")[0] == 200
            status, _ = c.request("POST", f"/item/{shared}/price?cents={500000 + t * 100 + k}")
            assert status == 200
            with lock:
                acks.append(500000 + t * 100 + k)
        c.close()

    threads = [threading.Thread(target=writer, args=(t,)) for t in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    c = client(srv)
    for t in range(n_threads):
        for k in range(per):
            _, body = c.request("GET", f"/item?sku={sku_for(100 + t * per + k)}")
            assert f'"price_cents":{t * 1000 + k:9d}'.encode() in body
    _, body = c.request("GET", f"/item?sku={shared}")
    final = int(body.split(b'"price_cents":')[1].split(b",")[0])
    assert final in acks
    c.close()


def test_batching_serves_concurrent_reads_correctly(server_factory):
    srv = server_factory("A3")
    errors = []

    def reader(t):
        c = client(srv)
        for k in range(30):
            i = (t * 37 + k) % SMALL.rows
            status, body = c.request("GET", f"/item?sku={sku_for(i)}")
            if status != 200 or body != render_item(make_row(i, SMALL.dataset_seed, SMALL.payload_bytes)):
                errors.append(i)
        c.close()

    threads = [threading.Thread(target=reader, args=(t,)) for t in range(12)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    sizes = srv.backend.batch_sizes
    assert max(sizes) <= ARMS["A3"].batch_max
    assert max(sizes) > 1  # batching actually happened


def test_admission_limiter_overflow():
    lim = AdmissionLimiter(workers=1, queue_size=1)
    entered = threading.Event()
    release = threading.Event()

    def hold():
        with lim:
            entered.set()
            release.wait()

    t1 = threading.Thread(target=hold)
    t1.start()
    entered.wait()
    t2 = threading.Thread(target=lambda: lim.__enter__() and lim.__exit__())  # waits in queue
    t2.start()
    time.sleep(0.05)
    with pytest.raises(Overloaded):
        lim.__enter__()
    assert lim.rejected == 1
    release.set()
    t1.join()
    t2.join()
    with lim:  # capacity freed again
        pass
    with pytest.raises(ValueError):
        AdmissionLimiter(0, 1)


def test_a4_returns_503_when_saturated(server_factory):
    """A4 path through HTTP with a small limiter (W = 2, Q = 2) and a blocked backend:
    of 10 concurrent requests, 4 are admitted and succeed, 6 get 503."""
    srv = server_factory("A4")
    srv.limiter = AdmissionLimiter(workers=2, queue_size=2)
    gate = threading.Event()
    orig = srv.backend.get

    def slow_get(sku):
        gate.wait(5)
        return orig(sku)

    srv.backend.get = slow_get
    results = []
    lock = threading.Lock()

    def one():
        c = client(srv)
        s, _ = c.request("GET", "/item?sku=SKU-00000001")
        with lock:
            results.append(s)
        c.close()

    threads = [threading.Thread(target=one) for _ in range(10)]
    for t in threads:
        t.start()
    time.sleep(0.3)
    gate.set()
    for t in threads:
        t.join()
    assert sorted(set(results)) == [200, 503]
    assert results.count(200) == 4 and results.count(503) == 6


@pytest.mark.parametrize("arm", ALL)
def test_differential_against_dict_reference(server_factory, arm):
    """Apply one seeded request stream serially to the server and to a dict model of
    the table; every response and the final state must agree byte for byte."""
    model = {sku_for(i): make_row(i, SMALL.dataset_seed, SMALL.payload_bytes) for i in range(SMALL.rows)}
    wl = SMALL.__class__(rows=SMALL.rows, payload_bytes=SMALL.payload_bytes,
                         dataset_seed=SMALL.dataset_seed, write_fraction=0.2)
    stream = request_stream(wl, ZipfSampler(wl.rows, 0.99, 1), seed=99)
    c = client(server_factory(arm))
    touched = set()
    for r, _ in zip(stream, range(400)):
        row = model[r.sku]
        if r.op == "write":
            model[r.sku] = row.__class__(row.id, row.sku, row.category, r.cents, row.payload)
            touched.add(r.sku)
            status, body = c.request("POST", f"/item/{r.sku}/price?cents={r.cents}")
            assert status == 200
        else:
            status, body = c.request("GET", f"/item?sku={r.sku}")
            assert (status, body) == (200, render_item(model[r.sku]))
    for sku in touched:
        assert c.request("GET", f"/item?sku={sku}") == (200, render_item(model[sku]))
    c.close()
