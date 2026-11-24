# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Experiment runner: blocks of arms in seeded random order, one fresh server process
and one freshly built database per run, results validated and written per run.

The runner never decides whether a run is confirmatory; the CLI refuses
confirmatory configs while the protocol is unfrozen (see ``cli.freeze_status``).
"""

from __future__ import annotations

import json
import multiprocessing
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from typing import Any, Callable

import psutil

from . import manifest as mf
from . import metrics as m
from .data import build_database
from .config import ARMS, ExperimentConfig, config_hash, derive_seed
from .loadgen import run_connections
from .schema import RESULT_SCHEMA_VERSION, MANIFEST_SCHEMA_VERSION, write_manifest, write_result

AB_PATH = "/usr/sbin/ab"
READY_TIMEOUT_S = 30.0


def arm_order(arms: tuple[str, ...], study_seed: int, block: int) -> list[str]:
    order = list(arms)
    random.Random(derive_seed(study_seed, "order", block)).shuffle(order)
    return order


def block_seeds(cfg: ExperimentConfig, block: int) -> dict[str, int]:
    return {"study": cfg.study_seed, "dataset": cfg.workload.dataset_seed,
            "requests": derive_seed(cfg.study_seed, "requests", block),
            "permutation": derive_seed(cfg.study_seed, "permutation")}


def connection_seeds(request_seed: int, level_key: Any, c: int) -> list[int]:
    return [derive_seed(request_seed, level_key, k) for k in range(c)]


def parse_ab_rps(text: str) -> float | None:
    """Extract 'Requests per second' from ApacheBench 2.3 output."""
    mt = re.search(r"Requests per second:\s+([0-9.]+)", text)
    return float(mt.group(1)) if mt else None


def run_ab(port: int, c: int, seconds: float) -> tuple[float | None, str]:
    cmd = [AB_PATH, "-k", "-q", "-c", str(c), "-t", str(max(1, int(round(seconds)))),
           "-n", "10000000", f"http://127.0.0.1:{port}/null"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=seconds + 30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, f"ab failed: {exc}"
    return parse_ab_rps(out.stdout), out.stdout[-2000:] + out.stderr[-1000:]


class ServerProcess:
    def __init__(self, cfg: ExperimentConfig, arm: str, db_path: str, log_path: str):
        cmd = [sys.executable, "-m", "scale.server", "--db", db_path, "--arm", arm,
               "--rows", str(cfg.workload.rows),
               "--stall-period-s", str(cfg.stall_period_s), "--stall-ms", str(cfg.stall_ms)]
        self.log = open(log_path, "w")
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=self.log, text=True)
        self.port: int | None = None
        line: list[str] = []
        reader = threading.Thread(target=lambda: line.append(self.proc.stdout.readline()), daemon=True)
        reader.start()
        reader.join(READY_TIMEOUT_S)
        if not line or not line[0].startswith("READY "):
            self.stop()
            raise RuntimeError(f"server not ready within {READY_TIMEOUT_S} s")
        self.port = int(line[0].split()[1])
        self.ps = psutil.Process(self.proc.pid)
        if http_get(self.port, "/health") != b"ok":
            self.stop()
            raise RuntimeError("health check failed")

    def cpu_s(self) -> float:
        t = self.ps.cpu_times()
        return t.user + t.system

    def rss_mb(self) -> float:
        return self.ps.memory_info().rss / 1e6

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self.log.close()


def http_get(port: int, path: str, timeout: float = 5.0) -> bytes:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=timeout) as r:
        return r.read()


def _noop(x: float) -> int:
    time.sleep(x)
    return os.getpid()


def _children_cpu_s(pids: list[int]) -> float:
    total = 0.0
    for pid in pids:
        try:
            t = psutil.Process(pid).cpu_times()
            total += t.user + t.system
        except psutil.Error:
            pass
    return total


def _sleep_until(wall: float) -> None:
    d = wall - time.time()
    if d > 0:
        time.sleep(d)


def run_level(cfg: ExperimentConfig, srv: ServerProcess, pool: ProcessPoolExecutor,
              gen_pids: list[int], c: int, seeds: list[int], perm_seed: int,
              rate_rps: float | None) -> dict[str, Any]:
    gp = cfg.generator_processes
    start_wall = time.time() + 0.3
    specs = []
    for p in range(gp):
        specs.append({
            "host": "127.0.0.1", "port": srv.port, "endpoint": cfg.endpoint,
            "mode": "open" if rate_rps else "closed",
            "workload": cfg.to_dict()["workload"], "perm_seed": perm_seed,
            "seeds": seeds[p::gp], "start_wall": start_wall,
            "warmup_s": cfg.warmup_s, "measure_s": cfg.measure_s,
            "rate_rps": (rate_rps / gp) if rate_rps else 0.0,
        })
    futs = [pool.submit(run_connections, s) for s in specs]
    _sleep_until(start_wall + cfg.warmup_s)
    s0, g0, w0 = srv.cpu_s(), _children_cpu_s(gen_pids), time.perf_counter()
    _sleep_until(start_wall + cfg.warmup_s + cfg.measure_s)
    s1, g1, w1 = srv.cpu_s(), _children_cpu_s(gen_pids), time.perf_counter()
    rss = srv.rss_mb()
    outs = [f.result(timeout=cfg.warmup_s + cfg.measure_s + 60) for f in futs]
    agg: dict[str, Any] = {"attempts": 0, "validated_ok": 0, "invalid_body": 0,
                           "transport_errors": 0, "status_counts": {}, "latencies_ns": [],
                           "lag_ns": [], "connections_finished": 0}
    for o in outs:
        for k in ("attempts", "validated_ok", "invalid_body", "transport_errors", "connections_finished"):
            agg[k] += o[k]
        for k, v in o["status_counts"].items():
            agg["status_counts"][k] = agg["status_counts"].get(k, 0) + v
        agg["latencies_ns"].extend(o["latencies_ns"])
        agg["lag_ns"].extend(o["lag_ns"])
    wall = max(w1 - w0, 1e-9)
    g = m.goodput_rps(agg["validated_ok"], cfg.measure_s)
    errors = agg["attempts"] - agg["validated_ok"] - agg["invalid_body"]
    gen_util = (g1 - g0) / wall
    limited, reasons = m.generator_limited(g, gen_util, gp, cfg.generator_ceiling_rps)
    lat = m.summarize_latencies_ms(agg["latencies_ns"])
    lag = m.percentile_nearest_rank([x / 1e6 for x in agg["lag_ns"]], 99) if agg["lag_ns"] else None
    level = {
        "concurrency": c, "offered_rate_rps": rate_rps, "window_s": cfg.measure_s,
        "attempts": agg["attempts"], "validated_ok": agg["validated_ok"],
        "invalid_body": agg["invalid_body"], "transport_errors": agg["transport_errors"],
        "status_counts": agg["status_counts"], "goodput_rps": g,
        "error_rate": m.error_rate(errors, agg["attempts"]),
        **lat, "lag_p99_ms": lag,
        "server_cpu_util": max(0.0, (s1 - s0) / wall), "server_rss_mb": rss,
        "generator_cpu_util": max(0.0, gen_util), "generator_limited": limited,
        "generator_limited_reasons": reasons,
        "connections_finished": agg["connections_finished"], "ab_rps": None,
    }
    if cfg.ab_crosscheck and cfg.endpoint == "null" and rate_rps is None and os.path.exists(AB_PATH):
        level["ab_rps"], _ = run_ab(srv.port, c, cfg.measure_s)
    return level


def summarize(cfg: ExperimentConfig, levels: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"peak_goodput_rps": None, "c_at_peak": None, "c_sat": None,
                           "generator_limited_levels": [lv["concurrency"] if cfg.kind == "closed_sweep"
                                                        else int(lv["offered_rate_rps"])
                                                        for lv in levels if lv["generator_limited"]]}
    if cfg.kind == "closed_sweep" and levels:
        pairs = [(lv["concurrency"], lv["goodput_rps"]) for lv in levels]
        out["peak_goodput_rps"], out["c_at_peak"] = m.peak_goodput(pairs)
        out["c_sat"] = m.saturation_concurrency(pairs)
    if cfg.kind == "open_ladder":
        passing = [lv["offered_rate_rps"] for lv in levels
                   if lv["p99_ms"] is not None and lv["p99_ms"] <= cfg.slo_p99_ms
                   and lv["error_rate"] is not None and lv["error_rate"] <= cfg.slo_max_error_rate]
        out["slo_goodput_rps"] = max(passing) if passing else None
    return out


def run_one(cfg: ExperimentConfig, arm: str, block: int, position: int, out_dir: str,
            repo_root: str, command: list[str], log: Callable[[str], None]) -> tuple[dict, dict]:
    chash = config_hash(cfg)
    seeds = block_seeds(cfg, block)
    run_id = f"{cfg.experiment_id}-b{block:02d}-{arm}-{chash[:8]}"
    started, t0 = mf.utc_now(), time.perf_counter()
    probe = mf.idle_probe(cfg.idle_probe_threshold_pct, cfg.idle_probe_enforce)
    levels: list[dict[str, Any]] = []
    status, failure = "ok", None
    server_stats: dict[str, Any] = {}
    dataset_sha = None
    server_peak = None
    tmp = tempfile.mkdtemp(prefix="scale-run-")
    srv = None
    pool = None
    try:
        if probe["enforced"] and not probe["passed"]:
            raise _Excluded(f"idle probe failed: {probe['cpu_pct']} % >= {probe['threshold_pct']} %")
        db = os.path.join(tmp, "items.sqlite")
        if cfg.endpoint == "item":
            dataset_sha = build_database(db, cfg.workload, index=ARMS[arm].index)
        srv = ServerProcess(cfg, arm, db, os.path.join(tmp, "server.log"))
        pool = ProcessPoolExecutor(max_workers=cfg.generator_processes,
                                   mp_context=multiprocessing.get_context("spawn"))
        gen_pids = sorted(set(pool.map(_noop, [0.2] * cfg.generator_processes)))
        if cfg.kind == "closed_sweep":
            for c in cfg.concurrency:
                lv = run_level(cfg, srv, pool, gen_pids, c,
                               connection_seeds(seeds["requests"], c, c), seeds["permutation"], None)
                levels.append(lv)
                log(f"  {run_id} c={c} goodput={lv['goodput_rps']:.1f} rps p99={lv['p99_ms']} ms"
                    f" err={lv['error_rate']} gen_cpu={lv['generator_cpu_util']:.2f}"
                    + (f" ab={lv['ab_rps']}" if lv['ab_rps'] is not None else ""))
        else:
            c = cfg.concurrency[0]
            fails = 0
            for r in cfg.rates_rps:
                lv = run_level(cfg, srv, pool, gen_pids, c,
                               connection_seeds(seeds["requests"], ["rate", r], c), seeds["permutation"], r)
                levels.append(lv)
                ok = (lv["p99_ms"] is not None and lv["p99_ms"] <= cfg.slo_p99_ms and
                      lv["error_rate"] is not None and lv["error_rate"] <= cfg.slo_max_error_rate)
                log(f"  {run_id} rate={r} goodput={lv['goodput_rps']:.1f} p99={lv['p99_ms']} ms"
                    f" lag_p99={lv['lag_p99_ms']} slo_ok={ok}")
                fails = 0 if ok else fails + 1
                if fails >= 2:
                    break
        server_stats = json.loads(http_get(srv.port, "/stats"))
        server_peak = server_stats.get("ru_maxrss_bytes", 0) / 1e6
    except _Excluded as exc:
        status, failure = "excluded", str(exc)
    except Exception as exc:  # harness failure: recorded, never silently dropped
        status, failure = "failed", f"{type(exc).__name__}: {exc}"
    finally:
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)
        if srv is not None:
            srv.stop()
        shutil.rmtree(tmp, ignore_errors=True)
    result = {
        "schema_version": RESULT_SCHEMA_VERSION, "run_id": run_id,
        "experiment_id": cfg.experiment_id, "label": cfg.label, "kind": cfg.kind,
        "arm": arm, "factor": ARMS[arm].factor, "block": block, "arm_position": position,
        "config_hash": chash, "seeds": seeds, "endpoint": cfg.endpoint, "levels": levels,
        "summary": summarize(cfg, levels) if levels else
        {"peak_goodput_rps": None, "c_at_peak": None, "c_sat": None},
        "server_stats": server_stats, "status": status, "failure": failure,
    }
    man = {
        "schema_version": MANIFEST_SCHEMA_VERSION, "run_id": run_id, "label": cfg.label,
        "config_hash": chash, "config": cfg.to_dict(), "seeds": seeds,
        "git": mf.git_info(repo_root), "versions": mf.versions(), "platform": mf.platform_info(),
        "cpu": mf.cpu_info(), "started_utc": started, "finished_utc": mf.utc_now(),
        "runtime_s": time.perf_counter() - t0, "server_peak_rss_mb": server_peak,
        "runner_peak_rss_mb": mf.runner_peak_rss_mb(), "dataset_sha256": dataset_sha,
        "idle_probe": probe, "load_average": mf.load_average(), "command": command,
        "power": mf.power_state(),
    }
    runs_dir = os.path.join(out_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)
    write_result(os.path.join(runs_dir, f"{run_id}.json"), result)
    write_manifest(os.path.join(runs_dir, f"{run_id}.manifest.json"), man)
    return result, man


class _Excluded(Exception):
    pass


def run_experiment(cfg: ExperimentConfig, out_dir: str, repo_root: str, command: list[str],
                   log: Callable[[str], None] = print) -> dict[str, Any]:
    cfg.validate()
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "config.json"), "w", encoding="utf-8") as fh:
        json.dump(cfg.to_dict(), fh, indent=1, sort_keys=True)
    started, t0 = mf.utc_now(), time.perf_counter()
    runs = []
    for b in range(cfg.blocks):
        for pos, arm in enumerate(arm_order(cfg.arms, cfg.study_seed, b)):
            log(f"[{cfg.label}] {cfg.experiment_id} block {b} position {pos} arm {arm}")
            res, man = run_one(cfg, arm, b, pos, out_dir, repo_root, command, log)
            runs.append({"run_id": res["run_id"], "arm": arm, "block": b, "position": pos,
                         "status": res["status"], "failure": res["failure"],
                         "runtime_s": round(man["runtime_s"], 3),
                         "peak_goodput_rps": res["summary"]["peak_goodput_rps"]})
            log(f"  -> {res['status']} runtime {man['runtime_s']:.1f} s"
                f" G*={res['summary']['peak_goodput_rps']}")
    batch = {"experiment_id": cfg.experiment_id, "label": cfg.label,
             "config_hash": config_hash(cfg), "started_utc": started,
             "finished_utc": mf.utc_now(), "runtime_s": time.perf_counter() - t0, "runs": runs}
    with open(os.path.join(out_dir, "batch.json"), "w", encoding="utf-8") as fh:
        json.dump(batch, fh, indent=1, sort_keys=True)
    return batch
