# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Load-generator limits: parsing, validation, cancellation, extreme parameters,
transport failures and the coordinated-omission correction."""

import socket
import threading
import time

import pytest

from scale.config import Workload
from scale.loadgen import (ConnStats, HttpClient, TransportError, Validator, parse_head,
                           run_connections)
from scale.runner import parse_ab_rps

from conftest import SMALL


def spec(port, **kw):
    s = {"host": "127.0.0.1", "port": port, "mode": "closed", "endpoint": "item",
         "workload": SMALL.__dict__ | {}, "perm_seed": 1, "seeds": [1, 2], "start_wall": time.time(),
         "warmup_s": 0.1, "measure_s": 0.4, "rate_rps": 0.0}
    s.update(kw)
    return s


def test_parse_head():
    assert parse_head(b"HTTP/1.1 200 OK\r\nContent-Length: 12\r\nX: y") == (200, 12)
    assert parse_head(b"HTTP/1.0 503 Service Unavailable\r\ncontent-length: 0") == (503, 0)
    with pytest.raises(TransportError):
        parse_head(b"HTTP/1.1 200 OK\r\nX: y")
    with pytest.raises(TransportError):
        parse_head(b"garbage")


def test_client_refuses_remote_hosts():
    with pytest.raises(ValueError, match="loopback"):
        HttpClient("example.org", 80)


def test_validator():
    from scale.data import NULL_BODY, make_row, render_item, render_write

    v = Validator(SMALL.payload_bytes)
    body = render_item(make_row(4, SMALL.dataset_seed, SMALL.payload_bytes))
    assert v.ok("read", "SKU-00000004", 0, body)
    assert not v.ok("read", "SKU-00000005", 0, body)
    assert not v.ok("read", "SKU-00000004", 0, body[:-1])
    assert v.ok("write", "SKU-00000004", 7, render_write("SKU-00000004", 7))
    assert not v.ok("write", "SKU-00000004", 8, render_write("SKU-00000004", 7))
    assert v.ok("null", "", 0, NULL_BODY) and not v.ok("null", "", 0, b"x")


def test_conn_stats_roundtrip():
    s = ConnStats(attempts=3, validated_ok=2, invalid_body=0, transport_errors=1)
    s.status_counts[200] = 2
    s.latencies_ns = [5, 6]
    assert ConnStats.from_dict(s.to_dict()) == s


def test_closed_loop_counts_against_real_server(server_factory):
    srv = server_factory("A2")
    out = run_connections(spec(srv.server_address[1]))
    assert out["validated_ok"] > 0
    assert out["invalid_body"] == 0 and out["transport_errors"] == 0
    assert out["attempts"] == sum(out["status_counts"].values())
    assert len(out["latencies_ns"]) == out["validated_ok"]
    assert out["connections_finished"] == 2
    assert all(x > 0 for x in out["latencies_ns"])


def test_transport_errors_counted_not_crashing():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # nothing listens on this port now
    out = run_connections(spec(port, measure_s=0.2, endpoint="null"))
    assert out["validated_ok"] == 0
    assert out["transport_errors"] > 0
    assert out["attempts"] == out["transport_errors"]


def test_cancellation_stops_promptly(server_factory):
    srv = server_factory("A0")
    stop = threading.Event()
    t0 = time.perf_counter()
    timer = threading.Timer(0.3, stop.set)
    timer.start()
    out = run_connections(spec(srv.server_address[1], warmup_s=0.0, measure_s=30.0, seeds=[1, 2, 3, 4]), stop)
    assert time.perf_counter() - t0 < 3.0
    assert out["connections_finished"] == 4


def test_extreme_parameters(server_factory):
    srv = server_factory("A2")
    # 128 connections for a very short window, and a single tiny window
    out = run_connections(spec(srv.server_address[1], seeds=list(range(128)), warmup_s=0.0, measure_s=0.3))
    assert out["connections_finished"] == 128
    assert out["transport_errors"] == 0
    out = run_connections(spec(srv.server_address[1], warmup_s=0.0, measure_s=0.001))
    assert out["attempts"] >= 0


def test_open_loop_measures_stall_closed_loop_hides_it(server_factory):
    """Coordinated omission: a 200 ms server pause every 1 s. Intended-time latency
    (open loop) must show it; send-time latency (closed loop, 1 connection) sees each
    stall once per connection only."""
    srv = server_factory("A0", stall_period_s=1.0, stall_ms=200.0)
    port = srv.server_address[1]
    op = run_connections(spec(port, mode="open", endpoint="null", rate_rps=200.0, seeds=[1, 2],
                              warmup_s=0.0, measure_s=2.0))
    lat_ms = sorted(x / 1e6 for x in op["latencies_ns"])
    p99_open = lat_ms[int(0.99 * len(lat_ms)) - 1]
    assert p99_open >= 100.0
    cl = run_connections(spec(port, endpoint="null", seeds=[1], warmup_s=0.0, measure_s=2.0))
    lat_c = sorted(x / 1e6 for x in cl["latencies_ns"])
    p99_closed = lat_c[int(0.99 * len(lat_c)) - 1]
    assert p99_closed < p99_open


def test_parse_ab_output():
    text = ("Concurrency Level:      8\nTime taken for tests:   3.001 seconds\n"
            "Requests per second:    12345.67 [#/sec] (mean)\n")
    assert parse_ab_rps(text) == 12345.67
    assert parse_ab_rps("apr_socket_recv: Connection reset by peer") is None


def test_http10_keepalive_header_for_apachebench(server_factory):
    """ApacheBench -k sends HTTP/1.0 with Connection: Keep-Alive and needs the token back
    (found in the exploratory smoke run: ab hung until its 30 s timeout without it)."""
    srv = server_factory("A0")
    s = socket.create_connection(("127.0.0.1", srv.server_address[1]), timeout=5)
    s.sendall(b"GET /null HTTP/1.0\r\nConnection: Keep-Alive\r\n\r\n")
    data = b""
    while b"\r\n\r\n" not in data:
        data += s.recv(4096)
    assert b"connection: keep-alive" in data.lower()
    s.sendall(b"GET /null HTTP/1.0\r\n\r\n")  # no keep-alive: server must close
    time.sleep(0.2)
    rest = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        rest += chunk
    assert b"connection: close" in rest.lower()
    s.close()


def test_ab_crosscheck_runs_if_available(server_factory):
    import os

    from scale.runner import AB_PATH, run_ab

    if not os.path.exists(AB_PATH):
        pytest.skip("ApacheBench not installed")
    srv = server_factory("A0")
    t0 = time.perf_counter()
    rps, _ = run_ab(srv.server_address[1], 2, 1.0)
    assert rps is not None and rps > 0
    assert time.perf_counter() - t0 < 10
