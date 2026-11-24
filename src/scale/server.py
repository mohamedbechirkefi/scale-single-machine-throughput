# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""System under test: one standard-library HTTP/1.1 server over SQLite, arms A0 to A4.

The arms differ only in the backend placed behind the identical HTTP layer:

* A0 ``DirectBackend`` on a table without an index on ``sku`` (full scan).
* A1 ``CachedBackend``: LRU of read responses, invalidated before a write is acknowledged.
* A2 ``DirectBackend`` on the same table with ``ix_items_sku`` (index built by ``data``).
* A3 ``BatchingBackend``: reads collected for at most ``batch_window_ms`` or ``batch_max``
  requests, served by one ``SELECT ... WHERE sku IN (...)``.
* A4 ``DirectBackend`` behind ``AdmissionLimiter``: at most ``workers`` requests do
  database work at once, at most ``queue`` more wait, overflow gets HTTP 503.

Binding is restricted to loopback addresses.
"""

from __future__ import annotations

import argparse
import json
import queue
import resource
import sqlite3
import sys
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from .config import ARMS, ArmSpec
from .data import NULL_BODY, render_item, render_write

LOOPBACK = ("127.0.0.1", "localhost", "::1")
SELECT = "SELECT id, sku, category, price_cents, payload FROM items WHERE sku = ?"
UPDATE = "UPDATE items SET price_cents = ? WHERE sku = ?"


class NotFound(Exception):
    pass


class DirectBackend:
    """One query per request on a per-thread SQLite connection."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._all: list[sqlite3.Connection] = []
        self._all_lock = threading.Lock()

    def _con(self) -> sqlite3.Connection:
        con = getattr(self._local, "con", None)
        if con is None:
            con = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
            con.execute("PRAGMA busy_timeout=5000")
            self._local.con = con
            with self._all_lock:
                self._all.append(con)
        return con

    def get(self, sku: str) -> bytes:
        row = self._con().execute(SELECT, (sku,)).fetchone()
        if row is None:
            raise NotFound(sku)
        return render_item(row)

    def set_price(self, sku: str, cents: int) -> bytes:
        cur = self._con().execute(UPDATE, (cents, sku))
        if cur.rowcount == 0:
            raise NotFound(sku)
        return render_write(sku, cents)

    def close(self) -> None:
        with self._all_lock:
            for con in self._all:
                try:
                    con.close()
                except sqlite3.Error:
                    pass
            self._all.clear()


class CachedBackend(DirectBackend):
    """A1. Write path: commit, then (under the lock) bump the key generation and drop
    the entry, then acknowledge. A reader inserts into the cache only if the key's
    generation did not change while it read the database, so a read that started before
    a write can never re-insert the old value after the write is acknowledged."""

    def __init__(self, db_path: str, capacity: int):
        super().__init__(db_path)
        if capacity < 1:
            raise ValueError("cache capacity must be >= 1")
        self.capacity = capacity
        self._cache: OrderedDict[str, bytes] = OrderedDict()
        self._gen: dict[str, int] = {}
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, sku: str) -> bytes:
        with self._lock:
            body = self._cache.get(sku)
            if body is not None:
                self._cache.move_to_end(sku)
                self.hits += 1
                return body
            self.misses += 1
            gen = self._gen.get(sku, 0)
        body = super().get(sku)
        with self._lock:
            if self._gen.get(sku, 0) == gen:
                self._cache[sku] = body
                self._cache.move_to_end(sku)
                while len(self._cache) > self.capacity:
                    self._cache.popitem(last=False)
        return body

    def set_price(self, sku: str, cents: int) -> bytes:
        try:
            return super().set_price(sku, cents)
        finally:
            with self._lock:
                self._gen[sku] = self._gen.get(sku, 0) + 1
                self._cache.pop(sku, None)


class _Pending:
    __slots__ = ("sku", "event", "body", "error")

    def __init__(self, sku: str):
        self.sku = sku
        self.event = threading.Event()
        self.body: bytes | None = None
        self.error: BaseException | None = None


class BatchingBackend(DirectBackend):
    """A3. Reads go through one batcher thread; writes stay direct."""

    def __init__(self, db_path: str, batch_max: int, window_ms: float):
        super().__init__(db_path)
        if batch_max < 1 or window_ms < 0:
            raise ValueError("batch_max must be >= 1 and window_ms >= 0")
        self.batch_max = batch_max
        self.window_s = window_ms / 1000.0
        self._q: queue.Queue[_Pending | None] = queue.Queue()
        self.batch_sizes: list[int] = []
        self._thread = threading.Thread(target=self._loop, name="batcher", daemon=True)
        self._thread.start()

    def get(self, sku: str) -> bytes:
        p = _Pending(sku)
        self._q.put(p)
        p.event.wait()
        if p.error is not None:
            raise p.error
        assert p.body is not None
        return p.body

    def _loop(self) -> None:
        con = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        con.execute("PRAGMA busy_timeout=5000")
        try:
            while True:
                first = self._q.get()
                if first is None:
                    return
                batch = [first]
                deadline = time.perf_counter() + self.window_s
                stop = False
                while len(batch) < self.batch_max:
                    remaining = deadline - time.perf_counter()
                    if remaining <= 0:
                        break
                    try:
                        nxt = self._q.get(timeout=remaining)
                    except queue.Empty:
                        break
                    if nxt is None:
                        stop = True
                        break
                    batch.append(nxt)
                self._serve(con, batch)
                if stop:
                    return
        finally:
            con.close()

    def _serve(self, con: sqlite3.Connection, batch: list[_Pending]) -> None:
        self.batch_sizes.append(len(batch))
        skus = sorted({p.sku for p in batch})
        try:
            marks = ",".join("?" * len(skus))
            rows = con.execute(
                f"SELECT id, sku, category, price_cents, payload FROM items WHERE sku IN ({marks})",
                skus,
            ).fetchall()
            found = {r[1]: render_item(r) for r in rows}
            for p in batch:
                if p.sku in found:
                    p.body = found[p.sku]
                else:
                    p.error = NotFound(p.sku)
        except BaseException as exc:  # propagate any database error to every waiter
            for p in batch:
                p.error = exc
        finally:
            for p in batch:
                p.event.set()

    def close(self) -> None:
        self._q.put(None)
        self._thread.join(timeout=5)
        super().close()


class Overloaded(Exception):
    pass


class AdmissionLimiter:
    """A4. At most ``workers`` requests in service and ``queue`` waiting; overflow fails fast."""

    def __init__(self, workers: int, queue_size: int):
        if workers < 1 or queue_size < 0:
            raise ValueError("workers must be >= 1 and queue >= 0")
        self.workers = workers
        self.capacity = workers + queue_size
        self._in_system = 0
        self._lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(workers)
        self.rejected = 0

    def __enter__(self) -> "AdmissionLimiter":
        with self._lock:
            if self._in_system >= self.capacity:
                self.rejected += 1
                raise Overloaded()
            self._in_system += 1
        self._slots.acquire()
        return self

    def __exit__(self, *exc: object) -> None:
        self._slots.release()
        with self._lock:
            self._in_system -= 1


class _NoLimit:
    def __enter__(self) -> "_NoLimit":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def make_backend(arm: ArmSpec, db_path: str, rows: int):
    if arm.cache_capacity_fraction > 0:
        return CachedBackend(db_path, max(1, int(rows * arm.cache_capacity_fraction)))
    if arm.batch_max > 0:
        return BatchingBackend(db_path, arm.batch_max, arm.batch_window_ms)
    return DirectBackend(db_path)


class Stall:
    """Optional injected pause (EXP-001 coordinated-omission check): every request that
    arrives in the first ``stall_ms`` of each ``period_s`` waits until that window ends."""

    def __init__(self, period_s: float, stall_ms: float):
        self.period_s = period_s
        self.stall_s = stall_ms / 1000.0
        self.t0 = time.perf_counter()

    def wait(self) -> None:
        if self.period_s <= 0 or self.stall_s <= 0:
            return
        phase = (time.perf_counter() - self.t0) % self.period_s
        if phase < self.stall_s:
            time.sleep(self.stall_s - phase)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True
    server: "ScaleServer"

    def log_message(self, format: str, *args: object) -> None:  # silence access logs
        return

    def _send(self, status: int, body: bytes, ctype: str = "application/json") -> None:
        reason = {200: "OK", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed",
                  500: "Internal Server Error", 503: "Service Unavailable"}.get(status, "Status")
        conn = ""
        if self.request_version == "HTTP/1.0":
            # HTTP/1.0 clients (ApacheBench -k) need an explicit keep-alive token,
            # otherwise they wait for the server to close the connection.
            conn = "Connection: close\r\n" if self.close_connection else "Connection: keep-alive\r\n"
        head = (
            f"HTTP/1.1 {status} {reason}\r\nContent-Type: {ctype}\r\n"
            f"Content-Length: {len(body)}\r\n{conn}\r\n"
        ).encode("ascii")
        self.wfile.write(head + body)

    def _drain_body(self) -> None:
        n = int(self.headers.get("Content-Length") or 0)
        if n > 0:
            self.rfile.read(n)

    def do_GET(self) -> None:
        srv = self.server
        srv.stall.wait()
        parts = urlsplit(self.path)
        if parts.path == "/null":
            self._send(200, NULL_BODY, "text/plain")
            return
        if parts.path == "/health":
            self._send(200, b"ok", "text/plain")
            return
        if parts.path == "/stats":
            self._send(200, json.dumps(srv.stats()).encode())
            return
        if parts.path != "/item":
            self._send(404, b'{"error":"not found"}')
            return
        q = parse_qs(parts.query)
        skus = q.get("sku")
        if not skus or len(skus) != 1 or not skus[0]:
            self._send(400, b'{"error":"sku required"}')
            return
        try:
            with srv.limiter:
                body = srv.backend.get(skus[0])
            self._send(200, body)
        except Overloaded:
            self._send(503, b'{"error":"overloaded"}')
        except NotFound:
            self._send(404, b'{"error":"unknown sku"}')
        except Exception:
            srv.count_error()
            self._send(500, b'{"error":"internal"}')

    def do_POST(self) -> None:
        srv = self.server
        self._drain_body()
        srv.stall.wait()
        parts = urlsplit(self.path)
        segs = parts.path.strip("/").split("/")
        if len(segs) != 3 or segs[0] != "item" or segs[2] != "price" or not segs[1]:
            self._send(404, b'{"error":"not found"}')
            return
        q = parse_qs(parts.query)
        try:
            cents = int(q["cents"][0])
            if not 0 <= cents <= 999_999_999:
                raise ValueError
        except (KeyError, ValueError, IndexError):
            self._send(400, b'{"error":"cents must be an integer in [0, 999999999]"}')
            return
        try:
            with srv.limiter:
                body = srv.backend.set_price(segs[1], cents)
            self._send(200, body)
        except Overloaded:
            self._send(503, b'{"error":"overloaded"}')
        except NotFound:
            self._send(404, b'{"error":"unknown sku"}')
        except Exception:
            srv.count_error()
            self._send(500, b'{"error":"internal"}')


MIN_BACKLOG = 128


def listen_backlog(max_concurrency: int) -> int:
    """Listen backlog requested from the OS: at least 128 and at least the largest
    concurrency level of the sweep, so a level's connection burst is not refused."""
    if not isinstance(max_concurrency, int) or max_concurrency < 1:
        raise ValueError("max_concurrency must be an integer >= 1")
    return max(MIN_BACKLOG, max_concurrency)


class ScaleServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = MIN_BACKLOG  # default 5 drops connection bursts at c = 64

    def __init__(self, addr: tuple[str, int], arm: ArmSpec, db_path: str, rows: int,
                 stall_period_s: float = 0.0, stall_ms: float = 0.0, backlog: int = MIN_BACKLOG):
        if addr[0] not in LOOPBACK:
            raise ValueError("SCALE binds to loopback only")
        # Instance attribute read by server_activate(); raised with the sweep (amendment AM-3).
        # The kernel may cap it (macOS kern.ipc.somaxconn, 128 on this machine).
        self.request_queue_size = listen_backlog(backlog)
        self.arm = arm
        self.backend = make_backend(arm, db_path, rows)
        self.limiter = AdmissionLimiter(arm.workers, arm.queue) if arm.workers > 0 else _NoLimit()
        self.stall = Stall(stall_period_s, stall_ms)
        self._errors = 0
        self._err_lock = threading.Lock()
        super().__init__(addr, Handler)

    def count_error(self) -> None:
        with self._err_lock:
            self._errors += 1

    def stats(self) -> dict:
        ru = resource.getrusage(resource.RUSAGE_SELF)
        maxrss = ru.ru_maxrss if sys.platform == "darwin" else ru.ru_maxrss * 1024
        out = {"arm": self.arm.name, "ru_maxrss_bytes": maxrss,
               "cpu_user_s": ru.ru_utime, "cpu_sys_s": ru.ru_stime,
               "internal_errors": self._errors}
        if isinstance(self.backend, CachedBackend):
            out["cache_hits"] = self.backend.hits
            out["cache_misses"] = self.backend.misses
        if isinstance(self.backend, BatchingBackend):
            sizes = list(self.backend.batch_sizes)
            out["batches"] = len(sizes)
            out["mean_batch_size"] = (sum(sizes) / len(sizes)) if sizes else None
        if isinstance(self.limiter, AdmissionLimiter):
            out["rejected_503"] = self.limiter.rejected
        return out

    def server_close(self) -> None:
        super().server_close()
        self.backend.close()


def serve_in_thread(arm_name: str, db_path: str, rows: int, **kw) -> tuple[ScaleServer, threading.Thread]:
    """In-process server on an ephemeral port (tests)."""
    srv = ScaleServer(("127.0.0.1", 0), ARMS[arm_name], db_path, rows, **kw)
    t = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    t.start()
    return srv, t


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SCALE server (loopback only)")
    ap.add_argument("--db", required=True)
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--rows", type=int, required=True)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=0)
    ap.add_argument("--stall-period-s", type=float, default=0.0)
    ap.add_argument("--stall-ms", type=float, default=0.0)
    ap.add_argument("--backlog", type=int, default=MIN_BACKLOG)
    a = ap.parse_args(argv)
    srv = ScaleServer((a.host, a.port), ARMS[a.arm], a.db, a.rows, a.stall_period_s, a.stall_ms,
                      backlog=a.backlog)
    print(f"READY {srv.server_address[1]}", flush=True)
    try:
        srv.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
