# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""M4 exploratory re-analysis of recorded runs (no new measurement).

Reads only the recorded raw outputs of EXP-001, the quiet pilot and EXP-002
(checksums verified first against the SHA256SUMS files written at M3) and writes
results/exploratory/M4-REANALYSIS-20261125/summary.json.

Everything here is EXPLORATORY. Nothing in this file changes or replaces a frozen
verdict: the frozen analysis is src/scale/analysis.py (analysis-1.0) and its output
research/experiments/EXP-00{1,2}/analysis.json. No server, generator or timing code
is executed. Bootstrap settings reuse the frozen ones (10,000 resamples, seed
20261124) so that the exploratory intervals are comparable with the frozen ones.

Usage: .venv/bin/python scripts/m4_exploratory_confounders.py
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import statistics
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from scale import analysis as an  # noqa: E402
from scale.report import load_runs  # noqa: E402

RAW = os.path.join(ROOT, "results", "raw")
OUT_DIR = os.path.join(ROOT, "results", "exploratory", "M4-REANALYSIS-20261125")
EXP002 = os.path.join(RAW, "EXP-002", "EXP-002-M3")
PILOT = os.path.join(RAW, "PILOT-QUIET", "PILOT-QUIET-M3")
EXP001 = os.path.join(RAW, "EXP-001", "EXP-001-M3")
GP4 = os.path.join(RAW, "EXP-001", "GP4-M3")
BLOCKS = list(range(10))
ARMS = ("A0", "A1", "A2", "A3", "A4")


def verify_checksums() -> dict:
    out = {}
    for sub in ("EXP-001", "EXP-002", "PILOT-QUIET"):
        d = os.path.join(RAW, sub)
        sums = os.path.join(d, "SHA256SUMS")
        bad, n = [], 0
        with open(sums) as fh:
            for line in fh:
                h, p = line.strip().split(None, 1)
                with open(os.path.join(d, p), "rb") as f:
                    if hashlib.sha256(f.read()).hexdigest() != h:
                        bad.append(p)
                n += 1
        with open(sums, "rb") as f:
            out[sub] = {"files": n, "mismatches": bad,
                        "sha256_of_SHA256SUMS": hashlib.sha256(f.read()).hexdigest()}
    if any(v["mismatches"] for v in out.values()):
        raise SystemExit(f"checksum mismatch: {out}")
    return out


def lv(res: dict, c: int) -> dict:
    return next(x for x in res["levels"] if x["concurrency"] == c)


def estimate(vals: dict, arm: str, base: str = "A0", blocks=BLOCKS) -> dict:
    lr = [math.log(vals[arm][b] / vals[base][b]) for b in blocks]
    s = an.ratio_summary(lr)
    return {k: s[k] for k in ("n_blocks", "ratio", "ci95", "ci9875", "sd_log_ratio")}


def main() -> int:
    out: dict = {"label": "exploratory", "kind": "re-analysis of recorded runs, no new measurement",
                 "script": "scripts/m4_exploratory_confounders.py",
                 "frozen_analysis_unchanged": "src/scale/analysis.py analysis-1.0",
                 "bootstrap": {"resamples": an.BOOTSTRAP_RESAMPLES, "seed": an.BOOTSTRAP_SEED}}
    rev = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    out["code_revision_at_run"] = rev
    out["checksums"] = verify_checksums()

    runs = load_runs(EXP002)
    chosen, _ = an.select_cells(runs)
    res = {(b, a): chosen[(b, a)][0] for (b, a) in chosen}
    man = {(b, a): chosen[(b, a)][1] for (b, a) in chosen}

    # X1 correctness and error composition across every accepted EXP-002 run.
    comp = {}
    for a in ARMS:
        tot = {"attempts": 0, "validated_ok": 0, "invalid_body": 0, "transport_errors": 0,
               "http_500": 0, "http_503": 0, "other_non_200": 0, "server_internal_errors": 0}
        first500 = []
        for b in BLOCKS:
            r = res[(b, a)]
            tot["server_internal_errors"] += r["server_stats"].get("internal_errors", 0)
            c500 = None
            for x in r["levels"]:
                sc = x["status_counts"]
                tot["attempts"] += x["attempts"]
                tot["validated_ok"] += x["validated_ok"]
                tot["invalid_body"] += x["invalid_body"]
                tot["transport_errors"] += x["transport_errors"]
                tot["http_500"] += sc.get("500", 0)
                tot["http_503"] += sc.get("503", 0)
                tot["other_non_200"] += sum(v for k, v in sc.items() if k not in ("200", "500", "503"))
                if sc.get("500", 0) and c500 is None:
                    c500 = x["concurrency"]
            first500.append(c500)
        tot["lowest_c_with_http_500_per_block"] = first500
        per_c: dict = {}
        for b in BLOCKS:
            for x in res[(b, a)]["levels"]:
                e = per_c.setdefault(str(x["concurrency"]), {"transport_errors": 0, "http_500": 0})
                e["transport_errors"] += x["transport_errors"]
                e["http_500"] += x["status_counts"].get("500", 0)
        tot["per_level_totals"] = {k: v for k, v in per_c.items() if v["transport_errors"] or v["http_500"]}
        comp[a] = tot
    out["X1_error_composition"] = comp

    # X2 mechanism descriptives at each arm's peak level and per level (medians over blocks).
    mech = {}
    for a in ARMS:
        per = {}
        for c in [x["concurrency"] for x in res[(0, a)]["levels"]]:
            L = [lv(res[(b, a)], c) for b in BLOCKS]
            g = statistics.median(x["goodput_rps"] for x in L)
            cpu = statistics.median(x["server_cpu_util"] for x in L)
            att = [x["attempts"] / x["window_s"] for x in L]
            p50 = [x["p50_ms"] for x in L if x["p50_ms"] is not None]
            # Little's law check for a closed loop with zero think time: c = X * mean R.
            # Only p50 is recorded, so c / (X * p50) is an approximate, descriptive check.
            little = statistics.median(c / (ar * p / 1000.0) for ar, p in zip(att, p50) if ar and p) if p50 else None
            per[str(c)] = {"goodput_median": g, "server_cpu_median": cpu,
                           "server_cpu_ms_per_validated_response": (1000.0 * cpu / g) if g else None,
                           "generator_cpu_median": statistics.median(x["generator_cpu_util"] for x in L),
                           "little_c_over_X_p50_median": little}
        st = [res[(b, a)]["server_stats"] for b in BLOCKS]
        mech[a] = {"per_level": per,
                   "sys_share_of_server_cpu_median": statistics.median(
                       s["cpu_sys_s"] / (s["cpu_sys_s"] + s["cpu_user_s"]) for s in st)}
        if a == "A1":
            h = [s["cache_hits"] / (s["cache_hits"] + s["cache_misses"]) for s in st]
            mech[a]["hit_ratio_median"] = statistics.median(h)
            mech[a]["amdahl_bound_1_over_1_minus_h"] = 1.0 / (1.0 - statistics.median(h))
        if a == "A3":
            mech[a]["mean_batch_size_median"] = statistics.median(s["mean_batch_size"] for s in st)
    out["X2_mechanism"] = mech

    # X3 pairwise contrasts among the arms in the confirmatory comparison (not in the frozen analysis).
    g = {a: {b: an.confirmatory_gstar(res[(b, a)]) for b in BLOCKS} for a in ("A0", "A1", "A3", "A4")}
    out["X3_pairwise_included_arms"] = {
        "A3_over_A1": estimate(g, "A3", "A1"), "A1_over_A4": estimate(g, "A1", "A4"),
        "A3_over_A4": estimate(g, "A3", "A4")}

    # X4 A3 truncation: G* over c <= 256 versus the full ladder.
    def gstar_le(r: dict, cmax: int) -> float:
        return max(x["goodput_rps"] for x in r["levels"] if x["concurrency"] <= cmax)
    g256 = {a: {b: gstar_le(res[(b, a)], 256) for b in BLOCKS} for a in ("A0", "A3")}
    peak512 = [b for b in BLOCKS if an.peak_cell(res[(b, "A3")])[1] == 512]
    out["X4_A3_truncation"] = {
        "blocks_peaking_at_512": peak512,
        "G512_over_G256_in_those_blocks": [lv(res[(b, "A3")], 512)["goodput_rps"] / lv(res[(b, "A3")], 256)["goodput_rps"] for b in peak512],
        "R_A3_gstar_le_256": estimate(g256, "A3"),
        "A3_goodput_range_c64_to_512_per_block": [
            [min(lv(res[(b, 'A3')], c)["goodput_rps"] for c in (64, 128, 256, 512)),
             max(lv(res[(b, 'A3')], c)["goodput_rps"] for c in (64, 128, 256, 512))] for b in BLOCKS]}

    # X5 blocks 8 and 9 (re-attempted cells, not adjacent in time) left out.
    keep = [b for b in BLOCKS if b not in (8, 9)]
    out["X5_without_blocks_8_9"] = {a: estimate(g, a, blocks=keep) for a in ("A1", "A3", "A4")}

    # X6 A4 versus A0 per level: admission engages only above W = 8 (503 only above W + Q = 24).
    out["X6_A4_over_A0_per_level"] = {
        str(c): {"ratio_median": statistics.median(lv(res[(b, 'A4')], c)["goodput_rps"] / lv(res[(b, 'A0')], c)["goodput_rps"] for b in BLOCKS),
                 "A4_503_total": sum(lv(res[(b, 'A4')], c)["status_counts"].get("503", 0) for b in BLOCKS)}
        for c in [x["concurrency"] for x in res[(0, "A4")]["levels"]]}

    # X7 generator CPU at every arm's peak level (the 85 % criterion of protocol section 4).
    out["X7_generator_cpu_at_peak_max"] = {
        a: max(lv(res[(b, a)], an.peak_cell(res[(b, a)])[1])["generator_cpu_util"] for b in BLOCKS) for a in ARMS}

    # X8 A2 against the EXP-001 null-endpoint ceiling and the 4-process sensitivity.
    a2 = [an.peak_cell(res[(b, "A2")]) for b in BLOCKS]
    gp4 = load_runs(GP4)
    out["X8_A2_vs_ceiling"] = {
        "A2_gstar_median": statistics.median(p[0] for p in a2),
        "A2_gstar_over_ceiling_median": statistics.median(p[0] for p in a2) / 27919.4,
        "A2_generator_limited_levels": sorted({c for b in BLOCKS for c in res[(b, "A2")]["summary"]["generator_limited_levels"]}),
        "A2_goodput_median_c8": statistics.median(lv(res[(b, "A2")], 8)["goodput_rps"] for b in BLOCKS),
        "A2_server_cpu_median_c2": statistics.median(lv(res[(b, "A2")], 2)["server_cpu_util"] for b in BLOCKS),
        "A2_server_cpu_median_c8": statistics.median(lv(res[(b, "A2")], 8)["server_cpu_util"] for b in BLOCKS),
        "gp4_gstar": [r["summary"]["peak_goodput_rps"] for r, _ in gp4],
        "threshold_50pct_of_ceiling": 0.5 * 27919.4}

    # X9 background state at run start versus the arm-centred log G* (descriptive).
    rows = []
    for (b, a), r in res.items():
        gs = an.gstar_unfiltered(r)
        rows.append((a, math.log(gs), man[(b, a)]["idle_probe"]["cpu_pct"], man[(b, a)]["load_average"][0]))
    cen = {a: statistics.fmean(x[1] for x in rows if x[0] == a) for a in ARMS}
    resid = [x[1] - cen[x[0]] for x in rows]

    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        rk = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                rk[order[k]] = (i + j) / 2.0
            i = j + 1
        return rk

    def spearman(x, y):
        rx, ry = rank(x), rank(y)
        mx, my = statistics.fmean(rx), statistics.fmean(ry)
        num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
        den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
        return num / den
    out["X9_background_vs_residual"] = {
        "n_runs": len(rows),
        "spearman_idle_probe_vs_residual": spearman([x[2] for x in rows], resid),
        "spearman_load1_vs_residual": spearman([x[3] for x in rows], resid),
        "idle_probe_range": [min(x[2] for x in rows), max(x[2] for x in rows)]}

    # X10 quiet pilot (exploratory, never pooled) against EXP-002: same direction and size?
    pr = load_runs(PILOT)
    pch, _ = an.select_cells(pr)
    pblocks = sorted({b for b, _ in pch})
    pil = {}
    for a in ("A1", "A3", "A4", "A2"):
        lr = []
        for b in pblocks:
            # c <= 512, the levels the pilot rule used for G* (protocol 7.1 item 4), unfiltered
            ga = max(x["goodput_rps"] for x in pch[(b, a)][0]["levels"] if x["concurrency"] <= 512)
            g0 = max(x["goodput_rps"] for x in pch[(b, "A0")][0]["levels"] if x["concurrency"] <= 512)
            lr.append(math.log(ga / g0))
        pil[a] = {"geometric_mean_R_unfiltered": math.exp(statistics.fmean(lr)), "n_blocks": len(lr)}
    out["X10_pilot_vs_exp002"] = pil

    # X11 EXP-001 c = 1 shortfall: SCALE generator below ab at c = 1 (descriptive).
    e1 = load_runs(EXP001)
    out["X11_exp001_c1"] = {"ratios_c1": sorted(lv(r, 1)["goodput_rps"] / lv(r, 1)["ab_rps"] for r, _ in e1)}

    # X12 closed-loop SLO-constrained goodput (NOT EXP-003: closed-loop latency, no
    # coordinated-omission correction): max G(c) over levels with p99 <= 50 ms and
    # error rate <= 1 %, the frozen SLO values. Generator-limited levels are not filtered.
    def slo_g(r: dict) -> float | None:
        ok = [x["goodput_rps"] for x in r["levels"]
              if x["p99_ms"] is not None and x["p99_ms"] <= 50.0 and (x["error_rate"] or 0) <= 0.01]
        return max(ok) if ok else None
    sg = {a: {b: slo_g(res[(b, a)]) for b in BLOCKS} for a in ARMS}
    out["X12_closed_loop_slo_goodput"] = {
        "undefined_blocks": {a: [b for b in BLOCKS if sg[a][b] is None] for a in ARMS},
        "estimates": {a: estimate(sg, a) for a in ("A1", "A2", "A3", "A4")
                      if all(sg[a][b] and sg["A0"][b] for b in BLOCKS)},
        "A3_over_A1": estimate(sg, "A3", "A1"),
        "A0_level_used_per_block": [max((x for x in res[(b, "A0")]["levels"] if x["goodput_rps"] == sg["A0"][b]),
                                        key=lambda x: x["concurrency"])["concurrency"] for b in BLOCKS],
        "A3_level_used_per_block": [max((x for x in res[(b, "A3")]["levels"] if x["goodput_rps"] == sg["A3"][b]),
                                        key=lambda x: x["concurrency"])["concurrency"] for b in BLOCKS]}

    # X13 query plans (no timing): the plan SQLite chooses for the A0 and A3 lookups on
    # the study schema without an index, and for A2 with the index. A small temporary
    # database built by the study's own builder is enough, because the plan does not
    # depend on N here; the database is deleted afterwards.
    import sqlite3
    import tempfile
    from scale.config import Workload
    from scale.data import build_database
    plans = {}
    with tempfile.TemporaryDirectory() as td:
        wl = Workload(rows=100, zipf_s=0.99, write_fraction=0.02, payload_bytes=256, dataset_seed=20261124)
        for name, idx in (("no_index", False), ("index", True)):
            path = os.path.join(td, f"{name}.db")
            build_database(path, wl, idx)
            con = sqlite3.connect(path)
            plans[name] = {
                "single": [r[-1] for r in con.execute("EXPLAIN QUERY PLAN SELECT id, sku, category, price_cents, payload FROM items WHERE sku = ?", ("x",))],
                "in_16": [r[-1] for r in con.execute("EXPLAIN QUERY PLAN SELECT id, sku, category, price_cents, payload FROM items WHERE sku IN (" + ",".join("?" * 16) + ")", tuple("x" * 16))]}
            con.close()
    plans["sqlite_version"] = sqlite3.sqlite_version
    out["X13_query_plans"] = plans

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "summary.json"), "w") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps({k: out[k] for k in ("X3_pairwise_included_arms", "X4_A3_truncation", "X5_without_blocks_8_9")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
