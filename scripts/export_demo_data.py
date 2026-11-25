# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Export the M5 demo's published results to demo/public/data/results.json.

Schema ``lab-demo-results`` 1.0.0 (the shared demo template). Every estimate
carries a ``kind`` (confirmatory, frozen sensitivity, descriptive,
exploratory) and an ``interval_kind``; project-specific top-level keys, which
``demo/src/results.ts`` validates and which fail closed:

* ``pending_owner_decisions``: the four SCALE decisions left open by the
  owner's instruction of 2026-11-25 ("Next" (second)), each with the readings
  the manuscript reports; none is chosen here;
* ``excluded_arms``: A2, which has no confirmatory estimate under the D-012
  reading, so the page can show it with the same weight as the estimates;
* ``exploratory``: the M4 re-analysis of recorded runs (X3, X4, X5, X10, X12),
  kept apart from the registered experiments;
* ``explorer``: per-level medians and ranges of the 50 accepted EXP-002 runs
  (goodput, p99 latency, server CPU, error rate, server memory), the
  generator ceiling and the generator-limited threshold, for the page's
  resource and latency explorer of recorded runs.

Inputs are committed files only: the two analysis files, the EXP-002 metrics
table, the M4 exploratory summary, the freeze record, the EXP-002 config, the
experiment registry, the claims register, the artifact manifest and the
manuscript. Nothing is read from ``results/raw/`` (its commit is an open owner
decision). Every ``display``, ``interval_display`` and ``interval95_display``
string is formatted to the precision the manuscript prints;
``tests/test_demo_export.py`` checks that each appears verbatim in
``research/paper/manuscript.md``. The output has no timestamp.

Usage: .venv/bin/python -I scripts/export_demo_data.py [repo root] [--check]
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

OUT = Path("demo/public/data/results.json")

EXP001 = "research/experiments/EXP-001/analysis.json"
EXP002 = "research/experiments/EXP-002/analysis.json"
EXP002_METRICS = "research/experiments/EXP-002/metrics.csv"
EXP002_CONFIG = "experiments/EXP-002.json"
M4X = "results/exploratory/M4-REANALYSIS-20261125/summary.json"
FREEZE = "research/freeze.json"
REGISTRY = "research/experiment_registry.csv"
CLAIMS = "research/claims_register.csv"
MANIFEST = "research/publication/artifact_manifest.json"
MANUSCRIPT = "research/paper/manuscript.md"

# Files whose content is a result; code_revision is the last commit that touched them.
RESULT_FILES = [EXP001, EXP002, EXP002_METRICS, M4X, FREEZE]

ARM_NAMES = {
    "A0": "A0 baseline",
    "A1": "A1 cache",
    "A2": "A2 index",
    "A3": "A3 batching",
    "A4": "A4 bounded concurrency",
}
KINDS = ("confirmatory", "frozen sensitivity", "descriptive", "exploratory")
B9875 = "98.75 % bootstrap, 10 blocks"


class ExportError(RuntimeError):
    pass


def f(x: float, d: int) -> str:
    return f"{x:.{d}f}"


def rng(lo: float, hi: float, d: int) -> str:
    return f"{f(lo, d)} to {f(hi, d)}"


def est(label: str, value: float, d: int, kind: str, unit: str = "ratio",
        ci: list[float] | None = None, ci_level: float | None = None,
        interval_kind: str | None = None, ci95: list[float] | None = None,
        di: int | None = None) -> dict[str, Any]:
    """One estimate. ``d`` decimals for the value, ``di`` for the interval (default d)."""
    if kind not in KINDS:
        raise ExportError(f"bad kind {kind}")
    di = d if di is None else di
    if (ci is None) != (interval_kind is None):
        raise ExportError(f"{label}: an interval needs its kind")
    return {
        "label": label,
        "kind": kind,
        "estimate": value,
        "ci_low": ci[0] if ci else None,
        "ci_high": ci[1] if ci else None,
        "ci_level": ci_level if ci else None,
        "unit": unit,
        "display": f(value, d),
        "interval_display": rng(ci[0], ci[1], di) if ci else None,
        "interval_kind": interval_kind,
        "interval95_display": rng(ci95[0], ci95[1], di) if ci95 else None,
    }


class Reader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.used: dict[str, str] = {}

    def bytes(self, rel: str) -> bytes:
        b = (self.root / rel).read_bytes()
        self.used[rel] = hashlib.sha256(b).hexdigest()
        return b

    def json(self, rel: str) -> Any:
        return json.loads(self.bytes(rel))

    def text(self, rel: str) -> str:
        return self.bytes(rel).decode("utf-8")

    def csv(self, rel: str) -> list[dict[str, str]]:
        return list(csv.DictReader(self.text(rel).splitlines()))


def results_revision(root: Path) -> str:
    out = subprocess.run(["git", "-C", str(root), "log", "-1", "--format=%H", "--", *RESULT_FILES],
                         capture_output=True, text=True, check=True).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", out):
        raise ExportError("could not determine the commit of the results")
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", *RESULT_FILES],
                           capture_output=True, text=True, check=True).stdout.strip()
    if dirty:
        raise ExportError(f"result files differ from the commit: {dirty}")
    return out


def limitations_from_manuscript(text: str) -> list[str]:
    sec = re.search(r"^# 7\. Limitations and threats to validity\n(.*?)^# 8\.", text, re.S | re.M)
    if not sec:
        raise ExportError("manuscript section 7 not found")
    items = [re.sub(r"^\d+\.\s+", "", ln).strip() for ln in sec.group(1).splitlines() if re.match(r"^\d+\.\s", ln)]
    clean = [re.sub(r"\*\*|`", "", s) for s in items]
    if len(clean) < 10:
        raise ExportError("too few limitations found in manuscript section 7")
    return clean


def short_status(registry_status: str) -> str:
    s = registry_status.split(":")[0].strip()
    return s.replace(" at M3", "")


def build(root: Path) -> dict[str, Any]:
    r = Reader(root)
    a1 = r.json(EXP001)
    a2 = r.json(EXP002)
    x = r.json(M4X)
    freeze = r.json(FREEZE)
    cfg = r.json(EXP002_CONFIG)
    metrics = r.csv(EXP002_METRICS)
    reg = {row["experiment_id"]: row for row in r.csv(REGISTRY)}
    claims = r.csv(CLAIMS)
    manifest = r.json(MANIFEST)
    manuscript = r.text(MANUSCRIPT)

    # The analysis inputs must be the ones the M4 evidence audit pinned.
    for rel, sha in manifest["inputs_sha256"].items():
        if rel in r.used and r.used[rel] != sha:
            raise ExportError(f"{rel}: sha256 differs from the artifact manifest")
    if manifest["n_mismatches"] != 0:
        raise ExportError("the artifact manifest records mismatches")

    if a2["cells_ok"] != a2["cells_planned"] or a2["missing_cells"]:
        raise ExportError("EXP-002 has missing cells")

    claim_ids: dict[str, list[str]] = {"EXP-001": [], "EXP-002": [], "EXP-003": [], "EXP-004": [], "M4": []}
    for c in claims:
        rid = c["result_id"]
        if not c["claim_id"].startswith("C-"):
            continue
        if "M4-REANALYSIS" in rid:
            claim_ids["M4"].append(c["claim_id"])
        else:
            for e in ("EXP-001", "EXP-002", "EXP-003", "EXP-004"):
                if e in rid:
                    claim_ids[e].append(c["claim_id"])

    # EXP-001: generator validation.
    lv = a1["levels"]
    ceiling = freeze["resolutions"][0]["ceiling_rule"]["output"]
    c_gen = ceiling["generator_ceiling_rps"]
    if c_gen != cfg["generator_ceiling_rps"] or c_gen != lv["8"]["c_gen_median"]:
        raise ExportError("generator ceiling differs between freeze record, config and EXP-001")
    exp001_est = [
        est(f"SCALE/ab median ratio, c = {c}", lv[c]["ratio_median"], 3, "confirmatory",
            ci=[lv[c]["ratio_min"], lv[c]["ratio_max"]], interval_kind="range over 5 repeats")
        for c in ("1", "8", "32")
    ]
    exp001_est.append(est("Generator ceiling C_gen (AM-5: median of 5 run ceilings)", c_gen, 1,
                          "confirmatory", unit="rps"))
    if not (a1["h0_ratio_median_in_band_all_levels"] and a1["gate_exp002_may_start"]):
        raise ExportError("EXP-001 verdict differs from the manuscript")

    # EXP-002: confirmatory estimates.
    conf = a2["confirmatory"]
    exp002_est = []
    for arm in ("A1", "A3", "A4"):
        c = conf[arm]
        if not c["included"]:
            raise ExportError(f"{arm} unexpectedly excluded")
        exp002_est.append(est(f"R, {ARM_NAMES[arm]} / A0 (peak goodput)", c["ratio"], 3, "confirmatory",
                              ci=c["ci9875"], ci_level=0.9875, interval_kind=B9875, ci95=c["ci95"]))
    if conf["A2"]["included"] or a2["dominance"]["status"] != "unresolved":
        raise ExportError("A2 status or dominance differs from the manuscript")
    s3 = a2["sensitivity_s3"]["estimates"]
    for arm, d in (("A1", 3), ("A2", 2), ("A3", 3), ("A4", 3)):
        exp002_est.append(est(f"S3 ratio, {ARM_NAMES[arm]} / A0 (mean goodput over c in 16, 32, 64)",
                              s3[arm]["ratio"], d, "frozen sensitivity", ci=s3[arm]["ci9875"],
                              ci_level=0.9875, interval_kind=B9875))
    dr = a2["drift"]
    exp002_est.append(est("Drift slope of log G* per run (frozen drift check)",
                          dr["run_order"]["slope_log_gstar_per_step"], 5, "frozen sensitivity", unit="per run",
                          ci=dr["run_order"]["ci95"], ci_level=0.95, interval_kind="95 % block bootstrap"))
    exp002_est.append(est("Drift slope of log G* per position in block (frozen drift check)",
                          dr["position_in_block"]["slope_log_gstar_per_step"], 4, "frozen sensitivity",
                          unit="per position", ci=dr["position_in_block"]["ci95"], ci_level=0.95,
                          interval_kind="95 % block bootstrap"))
    desc = a2["descriptives"]
    for arm in ("A0", "A1", "A2", "A3", "A4"):
        dd = desc[arm]
        exp002_est.append(est(f"Peak goodput G*, {ARM_NAMES[arm]} (median over 10 blocks)",
                              dd["gstar_unfiltered_median"], 1, "descriptive", unit="rps",
                              ci=[dd["gstar_unfiltered_min"], dd["gstar_unfiltered_max"]],
                              interval_kind="range over 10 blocks"))

    ex = a2["exploratory"]
    a2_alternatives = [
        est("A2 / A0, unfiltered within-block ratio", ex["gstar_unfiltered"]["A2"]["ratio"], 1, "exploratory",
            ci=ex["gstar_unfiltered"]["A2"]["ci9875"], ci_level=0.9875, interval_kind=B9875),
        est("A2 / A0, G* over the levels not flagged (c of 8 and above)",
            ex["gstar_over_unlimited_levels"]["A2"]["ratio"], 1, "exploratory",
            ci=ex["gstar_over_unlimited_levels"]["A2"]["ci9875"], ci_level=0.9875, interval_kind=B9875),
    ]

    threshold = 0.5 * c_gen
    experiments = [
        {
            "id": "EXP-001",
            "title": reg["EXP-001"]["title"],
            "status": short_status(reg["EXP-001"]["status"]),
            "verdict": "H0 holds (the two generators agree within 10 % at every level); gate for EXP-002 passed",
            "estimates": exp001_est,
            "claim_ids": claim_ids["EXP-001"],
            "report_path": reg["EXP-001"]["report_location"],
            "notes": [
                "Run ceilings: " + ", ".join(f(v, 1) for v in ceiling["run_ceilings_rps"]) + " rps (freeze record).",
                "Intervals here are the range over the five repeats, not confidence intervals.",
            ],
        },
        {
            "id": "EXP-002",
            "title": reg["EXP-002"]["title"],
            "status": short_status(reg["EXP-002"]["status"]),
            "verdict": ("A1 and A3: H0 rejected, R > 1. A4: no meaningful effect (inside [0.95, 1.05]). "
                        "A2: excluded, peak generator-limited in every block (D-012 reading, pending owner decision). "
                        "Dominance: unresolved."),
            "estimates": exp002_est,
            "claim_ids": claim_ids["EXP-002"],
            "report_path": reg["EXP-002"]["report_location"],
            "notes": [
                "All 50 cells completed; 12 runs excluded by the idle probe were re-attempted, so no cell is missing.",
                "The frozen analysis contains no pairwise test among the included arms; the order A3 > A1 > A4 is a ranking of point estimates.",
                "Peak goodput intervals are the range over 10 blocks, not confidence intervals.",
            ],
        },
        {
            "id": "EXP-003",
            "title": reg["EXP-003"]["title"],
            "status": short_status(reg["EXP-003"]["status"]),
            "verdict": "None: not run (pending owner decision on four unset parameters)",
            "estimates": [],
            "claim_ids": claim_ids["EXP-003"],
            "report_path": reg["EXP-003"]["report_location"],
            "notes": ["The closed-loop ranking is therefore untested against an open-loop load model."],
        },
        {
            "id": "EXP-004",
            "title": reg["EXP-004"]["title"],
            "status": short_status(reg["EXP-004"]["status"]),
            "verdict": "None: not run (pending owner decision on whether it runs)",
            "estimates": [],
            "claim_ids": claim_ids["EXP-004"],
            "report_path": reg["EXP-004"]["report_location"],
            "notes": ["The ranking is therefore untested against other table sizes and key skews."],
        },
    ]
    for e in experiments:
        if e["id"] not in reg:
            raise ExportError(f"{e['id']} not registered")
    if set(reg) != {e["id"] for e in experiments}:
        raise ExportError("registry and export disagree on the experiments")

    # Exploratory M4 re-analysis.
    x3 = x["X3_pairwise_included_arms"]
    x4 = x["X4_A3_truncation"]["R_A3_gstar_le_256"]
    x5 = x["X5_without_blocks_8_9"]
    x10 = x["X10_pilot_vs_exp002"]
    x12 = x["X12_closed_loop_slo_goodput"]
    if x["label"] != "exploratory":
        raise ExportError("M4 summary is not labelled exploratory")
    exploratory = {
        "id": "M4-REANALYSIS-20261125",
        "title": "Exploratory re-analysis of the recorded EXP-002 runs (no new measurement)",
        "label": "exploratory",
        "note": ("Chosen after the confirmatory results were known; hypothesis-generating only. "
                 "None of it changes a frozen verdict."),
        "claim_ids": claim_ids["M4"],
        "report_path": "results/exploratory/M4-REANALYSIS-20261125/report.md",
        "groups": [
            {"title": "Separation of the included arms (X3)", "estimates": [
                est("R_A3 / R_A1", x3["A3_over_A1"]["ratio"], 2, "exploratory", ci=x3["A3_over_A1"]["ci9875"],
                    ci_level=0.9875, interval_kind=B9875),
                est("R_A1 / R_A4", x3["A1_over_A4"]["ratio"], 2, "exploratory", ci=x3["A1_over_A4"]["ci9875"],
                    ci_level=0.9875, interval_kind=B9875),
                est("R_A3 / R_A4", x3["A3_over_A4"]["ratio"], 2, "exploratory", ci=x3["A3_over_A4"]["ci9875"],
                    ci_level=0.9875, interval_kind=B9875),
            ]},
            {"title": "A3 truncation at the sweep top (X4)", "estimates": [
                est("R_A3 with G* over c up to 256", x4["ratio"], 2, "exploratory", ci=x4["ci9875"],
                    ci_level=0.9875, interval_kind=B9875),
            ]},
            {"title": "Without the time-shifted blocks 8 and 9 (X5)", "estimates": [
                est("R_A1, 8 blocks", x5["A1"]["ratio"], 2, "exploratory"),
                est("R_A3, 8 blocks", x5["A3"]["ratio"], 2, "exploratory"),
                est("R_A4, 8 blocks", x5["A4"]["ratio"], 3, "exploratory", ci=x5["A4"]["ci9875"],
                    ci_level=0.9875, interval_kind="98.75 % bootstrap, 8 blocks"),
            ]},
            {"title": "Closed-loop latency-bounded goodput, p99 at most 50 ms, errors at most 1 % (X12; not EXP-003)",
             "estimates": [
                est("A1 / A0", x12["estimates"]["A1"]["ratio"], 2, "exploratory",
                    ci=x12["estimates"]["A1"]["ci9875"], ci_level=0.9875, interval_kind=B9875),
                est("A3 / A0", x12["estimates"]["A3"]["ratio"], 2, "exploratory",
                    ci=x12["estimates"]["A3"]["ci9875"], ci_level=0.9875, interval_kind=B9875),
                est("A4 / A0", x12["estimates"]["A4"]["ratio"], 3, "exploratory",
                    ci=x12["estimates"]["A4"]["ci9875"], ci_level=0.9875, interval_kind=B9875),
                est("R_A3 / R_A1", x12["A3_over_A1"]["ratio"], 2, "exploratory", ci=x12["A3_over_A1"]["ci9875"],
                    ci_level=0.9875, interval_kind=B9875),
            ]},
            {"title": "Quiet pilot, never pooled with EXP-002 (X10; unfiltered geometric means over 5 blocks, no interval)",
             "estimates": [
                est("A1 / A0", x10["A1"]["geometric_mean_R_unfiltered"], 2, "exploratory"),
                est("A3 / A0", x10["A3"]["geometric_mean_R_unfiltered"], 2, "exploratory"),
                est("A4 / A0", x10["A4"]["geometric_mean_R_unfiltered"], 3, "exploratory"),
            ]},
        ],
    }

    pending = [
        {
            "id": "D-012",
            "title": "The reading of the frozen generator-limited rule that excludes the index arm (A2)",
            "readings": [
                {"label": "Frozen-rule reading as applied (D-012)",
                 "text": ("A run's G* is undefined when its peak level is generator-limited, and an arm enters the "
                          "comparison only if G* is defined in every block. A2 then has no confirmatory estimate and "
                          "the dominance question is unresolved."),
                 "estimates": []},
                {"label": "Exploratory alternatives the manuscript reports beside it (not verdicts)",
                 "text": ("Both place A2 far above every other arm, and both measure A2 against a ceiling or in a "
                          "region that the frozen design did not intend as its peak."),
                 "estimates": a2_alternatives},
            ],
        },
        {
            "id": "EXP-003 parameters",
            "title": "The four EXP-003 parameters the frozen text leaves unset",
            "readings": [
                {"label": "Unset",
                 "text": ("The open-loop connection count, the study seed, the warmup and measurement split of each "
                          "rung, and which G* centres A2's ladder. EXP-003 did not run."),
                 "estimates": []},
            ],
        },
        {
            "id": "EXP-004",
            "title": "Whether the optional EXP-004 runs",
            "readings": [
                {"label": "Not decided", "text": "Its config was never frozen; it did not run.", "estimates": []},
            ],
        },
        {
            "id": "results/raw",
            "title": "Whether the raw run outputs (results/raw/) are committed",
            "readings": [
                {"label": "Not decided",
                 "text": ("They are kept out of git by the repository's ignore rule and pinned by SHA256SUMS digests "
                          "in the artifact manifest. This page reads committed files only."),
                 "estimates": []},
            ],
        },
    ]

    # Explorer: per-level data of the 50 accepted runs (committed analysis and metrics table).
    levels = [int(c) for c in cfg["concurrency"]]
    rss: dict[tuple[str, int], list[float]] = {}
    for row in metrics:
        if row["status"] != "ok" or row["label"] != "confirmatory":
            raise ExportError("metrics.csv holds a row that is not an accepted confirmatory run")
        rss.setdefault((row["arm"], int(row["concurrency"])), []).append(float(row["server_rss_mb"]))
    arms_out = []
    for arm in ("A0", "A1", "A2", "A3", "A4"):
        pl = desc[arm]["per_level"]
        if sorted(int(k) for k in pl) != levels:
            raise ExportError(f"{arm}: levels differ from the config")
        rows = []
        for c in levels:
            p = pl[str(c)]
            mem = rss[(arm, c)]
            if len(mem) != p["n"] or p["n"] != 10:
                raise ExportError(f"{arm} c={c}: expected 10 runs")
            rows.append({
                "c": c,
                "goodput_median": p["goodput_median"], "goodput_min": p["goodput_min"],
                "goodput_max": p["goodput_max"],
                "p99_median_ms": p["p99_median_ms"], "p99_min_ms": p["p99_min_ms"], "p99_max_ms": p["p99_max_ms"],
                "server_cpu_median": p["server_cpu_median"],
                "error_rate_median": p["error_rate_median"], "error_rate_max": p["error_rate_max"],
                "server_rss_mb_median": statistics.median(mem),
                "server_rss_mb_min": min(mem), "server_rss_mb_max": max(mem),
                "generator_limited_runs": p["generator_limited_count"],
            })
        arms_out.append({"arm": arm, "name": ARM_NAMES[arm], "levels": rows})
    explorer = {
        "label": "measured (recorded EXP-002 runs)",
        "source": f"{EXP002} descriptives.per_level; server memory from {EXP002_METRICS}",
        "n_runs_per_cell": 10,
        "concurrency": levels,
        "generator_ceiling_rps": c_gen,
        "generator_limited_threshold_rps": threshold,
        "generator_limited_threshold_display": f(threshold, 1),
        "arms": arms_out,
    }

    excluded = [{
        "arm": "A2", "name": ARM_NAMES["A2"],
        "verdict": "Excluded: peak generator-limited in every block",
        "reason": (f"A2's peak (median {f(desc['A2']['gstar_unfiltered_median'], 1)} rps at c = 2) lies above the "
                   f"frozen 50 % threshold of {f(threshold, 1)} rps in every block; no confirmatory estimate under the "
                   "D-012 reading, which is a pending owner decision."),
        "display_values": [f(desc["A2"]["gstar_unfiltered_median"], 1), f(threshold, 1)],
    }]

    cfgv = cfg
    assumptions_spec = [
        ("Machine", "Apple M1 Pro, 10 cores, 16 GB, macOS 15.3.1", "manuscript 1"),
        ("Server", "Python 3.12 standard library http.server and sqlite3, 127.0.0.1 only", "manuscript 3.2"),
        ("Table", "N = 200,000 rows, 256-byte payload, rebuilt from a fixed seed for every run", "manuscript 3.2"),
        ("Workload", "98 % reads, 2 % writes; Zipf exponent 0.99", "manuscript 3.2"),
        ("Concurrency sweep", "c in {1, 2, 4, ..., 512}, closed loop, zero think time", "manuscript 4.3"),
        ("Window", f"{cfgv['warmup_s']:.0f} s warmup and a {cfgv['measure_s']:.0f} s measurement window per level",
         EXP002_CONFIG),
        ("Blocks", f"{cfgv['blocks']} paired blocks, arm order randomised within each block", EXP002_CONFIG),
        ("A1 cache", "In-process LRU of read responses, capacity 10 % of N", "manuscript 3.2"),
        ("A3 batching", "At most 1 ms or 32 requests", "manuscript 3.2"),
        ("A4 bounded concurrency", "W = 8 and a queue of Q = 16; overflow returns HTTP 503", "manuscript 3.2"),
        ("Generator-limited rule", f"Goodput above 50 % of C_gen ({f(threshold, 1)} rps) or generator CPU above 85 %",
         "protocol section 4"),
        ("Decision rule", "Bonferroni 98.75 % intervals; no meaningful effect if inside [0.95, 1.05]",
         "manuscript 4.5"),
        ("Bootstrap", f"10,000 resamples, seed {cfgv['study_seed']}", "manuscript 4.5"),
        ("Idle probe", "System-wide CPU below 15 % over 1 s before each run", "manuscript 4.2"),
    ]
    assumptions = [{"name": n, "value": v, "source": s} for n, v, s in assumptions_spec]
    for a in assumptions:
        for num in re.findall(r"\d[\d,.]*\d|\d", a["value"]):
            if num not in manuscript:
                raise ExportError(f"assumption value {num!r} ({a['name']}) not in the manuscript")

    out = {
        "schema": "lab-demo-results",
        "schema_version": "1.0.0",
        "project": "SCALE",
        "question": ("On one fixed machine and one fixed local HTTP workload, which single architecture change, "
                     "applied one factor at a time to a simple full-scan baseline, produces the largest change in "
                     "peak successful throughput: a cache (A1), an index (A2), read batching (A3) or bounded "
                     "concurrency (A4)?"),
        "status_label": ("Preprint draft, not peer-reviewed. Measured on one laptop, one synthetic workload and one "
                         "server on localhost; no result transfers to production traffic or other hardware. "
                         "EXP-001 and EXP-002 ran under a protocol frozen by the owner; EXP-003 and EXP-004 did not "
                         "run. Four owner decisions are pending."),
        "code_revision": results_revision(root),
        "sources": [],
        "experiments": experiments,
        "assumptions": assumptions,
        "limitations": limitations_from_manuscript(manuscript),
        "pending_owner_decisions": pending,
        "excluded_arms": excluded,
        "exploratory": exploratory,
        "explorer": explorer,
    }
    out["sources"] = [{"path": p, "sha256": h} for p, h in sorted(r.used.items())]
    return out


def render(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=1, ensure_ascii=False, sort_keys=False) + "\n"


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    root = Path(args[0]).resolve() if args else Path(__file__).resolve().parents[1]
    text = render(build(root))
    target = root / OUT
    if "--check" in argv:
        same = target.exists() and target.read_text(encoding="utf-8") == text
        print("EXPORT-CHECK " + ("PASS" if same else "FAIL"))
        return 0 if same else 1
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(f"wrote {OUT} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
