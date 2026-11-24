# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Load generation: closed loop (primary) and open loop (intended-time latency).

One thread per keep-alive connection, inside one or more generator processes.
Each connection draws its own deterministic request stream from a seed derived
from (block request seed, level, connection index), so every arm of a block
sees the same streams (common random numbers). A request is attributed to the
measurement window if it completes inside it. Latency is measured with
``time.perf_counter_ns`` from send (closed loop) or from the intended send time
(open loop, coordinated-omission correction).
"""

from __future__ import annotations

import socket
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .config import Workload
from .data import NULL_BODY, ZipfSampler, item_body_length, render_write, request_stream


class TransportError(Exception):
    pass


class HttpClient:
    """Minimal HTTP/1.1 keep-alive client over a raw socket (Content-Length bodies only)."""

    def __init__(self, host: str, port: int, timeout_s: float = 10.0):
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ValueError("the SCALE load generator targets loopback only")
        self.host, self.port, self.timeout_s = host, port, timeout_s
        self.sock: socket.socket | None = None
        self.buf = b""

    def connect(self) -> None:
        self.close()
        s = socket.create_connection((self.host, self.port), timeout=self.timeout_s)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock, self.buf = s, b""

    def close(self) -> None:
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None

    def request(self, method: str, path: str) -> tuple[int, bytes]:
        req = (f"{method} {path} HTTP/1.1\r\nHost: {self.host}\r\n"
               f"Content-Length: 0\r\n\r\n").encode("ascii")
        try:
            if self.sock is None:
                self.connect()
            assert self.sock is not None
            self.sock.sendall(req)
            return self._read_response()
        except (OSError, ValueError, TransportError) as exc:
            self.close()
            raise TransportError(str(exc)) from exc

    def _recv(self) -> None:
        assert self.sock is not None
        chunk = self.sock.recv(65536)
        if not chunk:
            raise TransportError("connection closed by peer")
        self.buf += chunk

    def _read_response(self) -> tuple[int, bytes]:
        while b"\r\n\r\n" not in self.buf:
            self._recv()
        head, self.buf = self.buf.split(b"\r\n\r\n", 1)
        status, length = parse_head(head)
        while len(self.buf) < length:
            self._recv()
        body, self.buf = self.buf[:length], self.buf[length:]
        return status, body


def parse_head(head: bytes) -> tuple[int, int]:
    """Return (status, content length) from a raw response head."""
    lines = head.split(b"\r\n")
    parts = lines[0].split(b" ", 2)
    if len(parts) < 2 or not parts[0].startswith(b"HTTP/1."):
        raise TransportError(f"malformed status line {lines[0][:60]!r}")
    status = int(parts[1])
    length = None
    for line in lines[1:]:
        k, _, v = line.partition(b":")
        if k.strip().lower() == b"content-length":
            length = int(v.strip())
    if length is None or length < 0:
        raise TransportError("missing Content-Length")
    return status, length


@dataclass
class ConnStats:
    attempts: int = 0
    validated_ok: int = 0
    invalid_body: int = 0
    transport_errors: int = 0
    status_counts: Counter = field(default_factory=Counter)
    latencies_ns: list[int] = field(default_factory=list)
    lag_ns: list[int] = field(default_factory=list)
    total_sent: int = 0

    def merge(self, other: "ConnStats") -> None:
        self.attempts += other.attempts
        self.validated_ok += other.validated_ok
        self.invalid_body += other.invalid_body
        self.transport_errors += other.transport_errors
        self.status_counts.update(other.status_counts)
        self.latencies_ns.extend(other.latencies_ns)
        self.lag_ns.extend(other.lag_ns)
        self.total_sent += other.total_sent

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempts": self.attempts, "validated_ok": self.validated_ok,
            "invalid_body": self.invalid_body, "transport_errors": self.transport_errors,
            "status_counts": {str(k): v for k, v in sorted(self.status_counts.items())},
            "latencies_ns": self.latencies_ns, "lag_ns": self.lag_ns,
            "total_sent": self.total_sent,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ConnStats":
        return cls(d["attempts"], d["validated_ok"], d["invalid_body"], d["transport_errors"],
                   Counter({int(k): v for k, v in d["status_counts"].items()}),
                   list(d["latencies_ns"]), list(d["lag_ns"]), d["total_sent"])


class Validator:
    """Checks that a 200 response body is the correct kind of answer to its request."""

    def __init__(self, payload_bytes: int):
        self.item_len = item_body_length(payload_bytes)

    def ok(self, op: str, sku: str, cents: int, body: bytes) -> bool:
        if op == "null":
            return body == NULL_BODY
        if op == "write":
            return body == render_write(sku, cents)
        return len(body) == self.item_len and (b'"sku":"' + sku.encode() + b'"') in body


def _ops(endpoint: str, workload: Workload, sampler: ZipfSampler | None, seed: int):
    if endpoint == "null":
        while True:
            yield ("null", "", 0, "GET", "/null")
    assert sampler is not None
    for r in request_stream(workload, sampler, seed):
        if r.op == "write":
            yield ("write", r.sku, r.cents, "POST", f"/item/{r.sku}/price?cents={r.cents}")
        else:
            yield ("read", r.sku, 0, "GET", f"/item?sku={r.sku}")


def _record(st: ConnStats, val: Validator, op: str, sku: str, cents: int,
            status: int | None, body: bytes, lat_ns: int) -> None:
    st.attempts += 1
    if status is None:
        st.transport_errors += 1
        return
    st.status_counts[status] += 1
    if status == 200:
        if val.ok(op, sku, cents, body):
            st.validated_ok += 1
            st.latencies_ns.append(lat_ns)
        else:
            st.invalid_body += 1


def closed_connection(host: str, port: int, endpoint: str, workload: Workload,
                      sampler: ZipfSampler | None, seed: int, t_meas_ns: int, t_end_ns: int,
                      stop: threading.Event, val: Validator) -> ConnStats:
    """Closed loop, zero think time, until t_end_ns or stop."""
    st = ConnStats()
    cli = HttpClient(host, port)
    ops = _ops(endpoint, workload, sampler, seed)
    try:
        while not stop.is_set():
            if time.perf_counter_ns() >= t_end_ns:
                break
            op, sku, cents, method, path = next(ops)
            t0 = time.perf_counter_ns()
            st.total_sent += 1
            try:
                status, body = cli.request(method, path)
            except TransportError:
                status, body = None, b""
                time.sleep(0.001)
            t1 = time.perf_counter_ns()
            if t_meas_ns <= t1 <= t_end_ns:
                _record(st, val, op, sku, cents, status, body, t1 - t0)
    finally:
        cli.close()
    return st


class _Schedule:
    def __init__(self, t_start_ns: int, rate_rps: float, t_end_ns: int):
        self.t_start_ns, self.period_ns, self.t_end_ns = t_start_ns, 1e9 / rate_rps, t_end_ns
        self.i = 0
        self.lock = threading.Lock()

    def next_slot(self) -> int | None:
        with self.lock:
            t = self.t_start_ns + int(self.i * self.period_ns)
            self.i += 1
        return None if t >= self.t_end_ns else t


def open_connection(host: str, port: int, endpoint: str, workload: Workload,
                    sampler: ZipfSampler | None, seed: int, sched: _Schedule, t_meas_ns: int,
                    stop: threading.Event, val: Validator) -> ConnStats:
    """Open loop: take the next intended send time from a shared constant-rate schedule.
    Latency = completion time - intended time; lag = actual send - intended."""
    st = ConnStats()
    cli = HttpClient(host, port)
    ops = _ops(endpoint, workload, sampler, seed)
    try:
        while not stop.is_set():
            intended = sched.next_slot()
            if intended is None:
                break
            now = time.perf_counter_ns()
            if intended > now:
                time.sleep((intended - now) / 1e9)
            op, sku, cents, method, path = next(ops)
            sent = time.perf_counter_ns()
            st.total_sent += 1
            try:
                status, body = cli.request(method, path)
            except TransportError:
                status, body = None, b""
            t1 = time.perf_counter_ns()
            if intended >= t_meas_ns:
                st.lag_ns.append(sent - intended)
                _record(st, val, op, sku, cents, status, body, t1 - intended)
    finally:
        cli.close()
    return st


_SAMPLERS: dict[tuple, ZipfSampler] = {}


def get_sampler(workload: Workload, perm_seed: int) -> ZipfSampler:
    key = (workload.rows, workload.zipf_s, perm_seed)
    if key not in _SAMPLERS:
        _SAMPLERS[key] = ZipfSampler(workload.rows, workload.zipf_s, perm_seed)
    return _SAMPLERS[key]


def run_connections(spec: dict[str, Any], stop: threading.Event | None = None) -> dict[str, Any]:
    """Run ``spec['seeds']`` connections in threads of this process. ``spec`` holds:
    host, port, mode ('closed' or 'open'), endpoint, workload (dict), perm_seed, seeds,
    start_wall (time.time() at which to begin), warmup_s, measure_s, rate_rps (open)."""
    stop = stop or threading.Event()
    wl = Workload(**spec["workload"])
    sampler = None if spec["endpoint"] == "null" else get_sampler(wl, spec["perm_seed"])
    val = Validator(wl.payload_bytes)
    delay = spec["start_wall"] - time.time()
    if delay > 0:
        time.sleep(delay)
    t0 = time.perf_counter_ns()
    t_meas = t0 + int(spec["warmup_s"] * 1e9)
    t_end = t_meas + int(spec["measure_s"] * 1e9)
    results: list[ConnStats] = []
    lock = threading.Lock()
    sched = _Schedule(t0, spec["rate_rps"], t_end) if spec["mode"] == "open" else None

    def work(seed: int) -> None:
        if spec["mode"] == "open":
            assert sched is not None
            st = open_connection(spec["host"], spec["port"], spec["endpoint"], wl, sampler, seed,
                                 sched, t_meas, stop, val)
        else:
            st = closed_connection(spec["host"], spec["port"], spec["endpoint"], wl, sampler, seed,
                                   t_meas, t_end, stop, val)
        with lock:
            results.append(st)

    threads = [threading.Thread(target=work, args=(s,), daemon=True) for s in spec["seeds"]]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=spec["warmup_s"] + spec["measure_s"] + 30)
    stop.set()
    total = ConnStats()
    for st in results:
        total.merge(st)
    out = total.to_dict()
    out["connections_finished"] = len(results)
    out["connections_started"] = len(threads)
    out["start_lateness_s"] = max(0.0, -delay)
    return out
