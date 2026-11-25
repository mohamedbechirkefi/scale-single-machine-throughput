# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Frozen analyses of EXP-001 and EXP-002 (research/protocol.md sections 4, 5, 6, 9,
10 and 12; EXP-001 protocol items 5, 16, 17 and 21; EXP-002 protocol items 15 to 20).

Written and tested before any EXP-001 or EXP-002 output existed (decision D-012).
The readings of the frozen text that the text leaves implicit are fixed here and in
D-012; everything labelled ``exploratory`` below goes beyond the frozen analysis.

EXP-002 confirmatory analysis, in order:

1. Cells. One cell is one (block, arm). The cell's run is the first attempt with
   status ok (re-attempts of protocol section 10 carry the suffix -r1, -r2). A cell
   with no ok attempt is missing.
2. Generator-limited exclusion (section 4). A run's G* is the maximum goodput over
   its levels (ties to the smallest c). If the level that attains G* is flagged
   generator-limited, the run's confirmatory G* is undefined (the reading stated in
   D-008 item 5 and accepted with the rule by the owner).
3. An arm j enters the confirmatory comparison only if G*_j and G*_A0 are defined in
   every block of the frozen matrix. Otherwise the arm is reported as excluded
   (generator-limited or missing) and only exploratory estimates are given for it;
   dropping individual blocks would select blocks by outcome.
4. Per block log R_j = log(G*_j / G*_A0); estimate: mean, back-transformed. Percentile
   bootstrap over blocks, 10,000 resamples, seed BOOTSTRAP_SEED; 95 % and
   Bonferroni 98.75 % intervals. H0_j is rejected if the 98.75 % interval excludes
   R = 1. "No meaningful effect" only if the 98.75 % interval lies within
   [0.95, 1.05]; otherwise a non-rejection is "inconclusive".
5. Dominance (section 5). Only if all four treatment arms entered the comparison: the
   top arm t has the largest estimate; a dominance claim is made only if for every
   other arm k the 98.75 % bootstrap interval of R_t / R_k (per block log R_t -
   log R_k) excludes 1. Otherwise the ranking is "unresolved".
6. S3 (section 12 item 3): the same estimate with G* replaced by the mean goodput over
   c in {16, 32, 64}; the ranking of point estimates is compared with the primary
   ranking. Drift (section 12 item 4): OLS of log G* on arm indicators plus run
   order, slope interval by block bootstrap. Both are sensitivity analyses, reported
   as such.
"""

from __future__ import annotations

import csv
import math
import os
import re
import statistics
from collections import defaultdict
from typing import Any, Sequence

import numpy as np

from . import metrics as m

ANALYSIS_VERSION = "analysis-1.0"
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261124  # the EXP-002 study seed, fixed before data (D-012)
LEVEL_95 = 0.95
LEVEL_BONF = 1 - 0.05 / 4  # 0.9875, four confirmatory comparisons
PRACTICAL = (0.95, 1.05)
S3_LEVELS = (16, 32, 64)
TREATMENTS = ("A1", "A2", "A3", "A4")
EXP001_RATIO_BAND = (0.9, 1.1)
EXP001_GATE_C = 32
DRIFT_RESAMPLES = 2_000

Runs = Sequence[tuple[dict[str, Any], dict[str, Any]]]


def _attempt(run_id: str) -> int:
    mt = re.search(r"-r(\d+)$", run_id)
    return int(mt.group(1)) if mt else 0


def select_cells(runs: Runs) -> tuple[dict[tuple[int, str], tuple[dict, dict]], list[dict[str, Any]]]:
    """Map (block, arm) to the first ok attempt; list every not-ok run (kept, reported)."""
    by_cell: dict[tuple[int, str], list[tuple[dict, dict]]] = defaultdict(list)
    for res, man in runs:
        by_cell[(res["block"], res["arm"])].append((res, man))
    chosen: dict[tuple[int, str], tuple[dict, dict]] = {}
    not_ok = []
    for cell, lst in by_cell.items():
        lst.sort(key=lambda rm: _attempt(rm[0]["run_id"]))
        for res, man in lst:
            if res["status"] != "ok":
                not_ok.append({"run_id": res["run_id"], "block": res["block"], "arm": res["arm"],
                               "status": res["status"], "failure": res["failure"]})
        oks = [rm for rm in lst if rm[0]["status"] == "ok"]
        if oks:
            chosen[cell] = oks[0]
    return chosen, sorted(not_ok, key=lambda d: d["run_id"])


def peak_cell(res: dict[str, Any]) -> tuple[float, int, bool]:
    """(G*, c at peak, peak level generator-limited) over all levels of a closed sweep."""
    pairs = [(lv["concurrency"], lv["goodput_rps"]) for lv in res["levels"]]
    g, c = m.peak_goodput(pairs)
    lim = next(lv["generator_limited"] for lv in res["levels"] if lv["concurrency"] == c)
    return g, c, lim


def confirmatory_gstar(res: dict[str, Any]) -> float | None:
    g, _, lim = peak_cell(res)
    return None if lim or g <= 0 else g


def gstar_unlimited_levels(res: dict[str, Any]) -> float | None:
    """Exploratory alternative: maximum over the levels that are not generator-limited."""
    vals = [lv["goodput_rps"] for lv in res["levels"] if not lv["generator_limited"]]
    return max(vals) if vals and max(vals) > 0 else None


def gstar_unfiltered(res: dict[str, Any]) -> float | None:
    g = peak_cell(res)[0]
    return g if g > 0 else None


def s3_value(res: dict[str, Any]) -> float | None:
    lv = {x["concurrency"]: x for x in res["levels"]}
    if not all(c in lv for c in S3_LEVELS):
        return None
    if any(lv[c]["generator_limited"] for c in S3_LEVELS):
        return None
    v = statistics.fmean(lv[c]["goodput_rps"] for c in S3_LEVELS)
    return v if v > 0 else None


def ratio_summary(log_r: Sequence[float], seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    """Back-transformed mean log ratio with percentile bootstrap 95 % and 98.75 % intervals."""
    mean, lo95, hi95 = m.bootstrap_mean_ci(log_r, BOOTSTRAP_RESAMPLES, seed, LEVEL_95)
    _, lob, hib = m.bootstrap_mean_ci(log_r, BOOTSTRAP_RESAMPLES, seed, LEVEL_BONF)
    out = {"n_blocks": len(log_r), "mean_log_ratio": mean, "ratio": math.exp(mean),
           "ci95": [math.exp(lo95), math.exp(hi95)], "ci9875": [math.exp(lob), math.exp(hib)],
           "sd_log_ratio": m.sample_sd(log_r) if len(log_r) >= 2 else None}
    return out


def verdict(summary: dict[str, Any]) -> str:
    lo, hi = summary["ci9875"]
    if lo > 1.0:
        return "H0 rejected: R > 1"
    if hi < 1.0:
        return "H0 rejected: R < 1"
    if PRACTICAL[0] <= lo and hi <= PRACTICAL[1]:
        return "no meaningful effect (98.75 % interval within [0.95, 1.05])"
    return "inconclusive (98.75 % interval includes 1 and extends beyond [0.95, 1.05])"


def _per_block(chosen: dict, blocks: Sequence[int], fn) -> dict[str, dict[int, float | None]]:
    out: dict[str, dict[int, float | None]] = defaultdict(dict)
    for (b, arm), (res, _) in chosen.items():
        out[arm][b] = fn(res)
    for arm in out:
        for b in blocks:
            out[arm].setdefault(b, None)
    return out


def _log_ratios(vals: dict[str, dict[int, float | None]], arm: str,
                blocks: Sequence[int]) -> tuple[list[float] | None, list[int]]:
    """Per-block log R for arm, or (None, undefined blocks) if any block is undefined."""
    bad = [b for b in blocks if vals.get(arm, {}).get(b) is None or vals.get("A0", {}).get(b) is None]
    if bad:
        return None, bad
    return [math.log(vals[arm][b] / vals["A0"][b]) for b in blocks], []


def _estimates(vals, blocks, arms=TREATMENTS) -> dict[str, Any]:
    out = {}
    for arm in arms:
        lr, bad = _log_ratios(vals, arm, blocks)
        if lr is None:
            out[arm] = {"included": False, "undefined_blocks": bad}
        else:
            out[arm] = {"included": True, **ratio_summary(lr), "log_ratios": lr}
    return out


def _partial_estimates(vals, blocks, arms=TREATMENTS) -> dict[str, Any]:
    """Exploratory: estimate over the blocks where both values are defined."""
    out = {}
    for arm in arms:
        ok = [b for b in blocks if vals.get(arm, {}).get(b) and vals.get("A0", {}).get(b)]
        if len(ok) >= 2:
            lr = [math.log(vals[arm][b] / vals["A0"][b]) for b in ok]
            out[arm] = {"blocks_used": ok, **ratio_summary(lr)}
        else:
            out[arm] = {"blocks_used": ok}
    return out


def dominance(est: dict[str, Any]) -> dict[str, Any]:
    if not all(est[a]["included"] for a in TREATMENTS):
        missing = [a for a in TREATMENTS if not est[a]["included"]]
        return {"status": "unresolved", "reason": f"arm(s) {missing} excluded from the confirmatory comparison",
                "top_arm": None, "pairwise": {}}
    top = max(TREATMENTS, key=lambda a: est[a]["mean_log_ratio"])
    pair = {}
    for k in TREATMENTS:
        if k == top:
            continue
        d = [a - b for a, b in zip(est[top]["log_ratios"], est[k]["log_ratios"])]
        s = ratio_summary(d)
        pair[k] = {"ratio": s["ratio"], "ci95": s["ci95"], "ci9875": s["ci9875"],
                   "excludes_1": s["ci9875"][0] > 1.0 or s["ci9875"][1] < 1.0}
    claim = all(p["excludes_1"] for p in pair.values())
    return {"status": "dominance claimed" if claim else "unresolved", "top_arm": top,
            "pairwise": pair, "reason": None if claim else "some R_t / R_k interval includes 1"}


def ranking(est: dict[str, Any], key: str = "mean_log_ratio") -> list[str]:
    inc = [a for a in est if est[a].get(key) is not None]
    return sorted(inc, key=lambda a: -est[a][key])


def drift(chosen: dict, seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    """Exploratory check (section 12 item 4): OLS log G* ~ arm indicators + run order
    and, separately, + position within block; slope intervals by block bootstrap."""
    rows = []
    for (b, arm), (res, man) in chosen.items():
        g = gstar_unfiltered(res)
        if g:
            rows.append((b, arm, res["arm_position"], man["started_utc"], math.log(g)))
    rows.sort(key=lambda r: r[3])
    order = {r[3]: i for i, r in enumerate(rows)}
    arms = sorted({r[1] for r in rows})
    blocks = sorted({r[0] for r in rows})

    def fit(sel: list[tuple], which: int) -> float:
        X = np.array([[1.0 if r[1] == a else 0.0 for a in arms] +
                      [float(order[r[3]] if which == 0 else r[2])] for r in sel])
        y = np.array([r[4] for r in sel])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return float(beta[-1])

    out = {}
    rng = np.random.default_rng(seed)
    for which, name in ((0, "run_order"), (1, "position_in_block")):
        slope = fit(rows, which)
        boots = []
        for _ in range(DRIFT_RESAMPLES):
            pick = rng.choice(blocks, size=len(blocks), replace=True)
            sel = [r for bb in pick for r in rows if r[0] == bb]
            boots.append(fit(sel, which))
        lo, hi = np.quantile(boots, [0.025, 0.975])
        out[name] = {"slope_log_gstar_per_step": slope, "ci95": [float(lo), float(hi)],
                     "n_runs": len(rows)}
    return out


def descriptives(chosen: dict) -> dict[str, Any]:
    by_arm: dict[str, list[dict]] = defaultdict(list)
    for (_, arm), (res, _) in chosen.items():
        by_arm[arm].append(res)
    out = {}
    for arm, lst in sorted(by_arm.items()):
        levels = sorted({lv["concurrency"] for r in lst for lv in r["levels"]})
        per_level = {}
        for c in levels:
            lvs = [lv for r in lst for lv in r["levels"] if lv["concurrency"] == c]
            g = [lv["goodput_rps"] for lv in lvs]
            p99 = [lv["p99_ms"] for lv in lvs if lv["p99_ms"] is not None]
            er = [lv["error_rate"] for lv in lvs if lv["error_rate"] is not None]
            per_level[c] = {"n": len(lvs), "goodput_median": statistics.median(g),
                            "goodput_min": min(g), "goodput_max": max(g),
                            "p99_median_ms": statistics.median(p99) if p99 else None,
                            "p99_min_ms": min(p99) if p99 else None,
                            "p99_max_ms": max(p99) if p99 else None,
                            "error_rate_median": statistics.median(er) if er else None,
                            "error_rate_max": max(er) if er else None,
                            "generator_limited_count": sum(lv["generator_limited"] for lv in lvs),
                            "server_cpu_median": statistics.median(lv["server_cpu_util"] for lv in lvs),
                            "generator_cpu_median": statistics.median(lv["generator_cpu_util"] for lv in lvs)}
        peaks = [peak_cell(r) for r in lst]
        st = [r.get("server_stats", {}) for r in lst]
        hits = [s.get("cache_hits") for s in st if s.get("cache_hits") is not None]
        miss = [s.get("cache_misses") for s in st if s.get("cache_misses") is not None]
        out[arm] = {"n_runs": len(lst), "per_level": per_level,
                    "gstar_unfiltered_median": statistics.median(p[0] for p in peaks),
                    "gstar_unfiltered_min": min(p[0] for p in peaks),
                    "gstar_unfiltered_max": max(p[0] for p in peaks),
                    "c_at_peak": sorted(p[1] for p in peaks),
                    "peak_generator_limited_runs": sum(p[2] for p in peaks),
                    "c_sat": sorted(r["summary"]["c_sat"] for r in lst),
                    "rejected_503_total": sum(s.get("rejected_503", 0) or 0 for s in st),
                    "cache_hit_ratio_median": (statistics.median(h / (h + mm) for h, mm in zip(hits, miss) if h + mm)
                                               if hits and miss else None)}
    return out


def analyse_exp002(runs: Runs, blocks_planned: int, arms_planned: Sequence[str]) -> dict[str, Any]:
    chosen, not_ok = select_cells(runs)
    blocks = list(range(blocks_planned))
    missing = [(b, a) for b in blocks for a in arms_planned if (b, a) not in chosen]
    prim_vals = _per_block(chosen, blocks, confirmatory_gstar)
    est = _estimates(prim_vals, blocks)
    for a in TREATMENTS:
        if est[a]["included"]:
            est[a]["verdict"] = verdict(est[a])
        else:
            est[a]["verdict"] = "excluded from the confirmatory comparison (generator-limited or missing cells)"
    out: dict[str, Any] = {
        "analysis_version": ANALYSIS_VERSION, "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES, "blocks_planned": blocks_planned,
        "cells_planned": blocks_planned * len(arms_planned), "cells_ok": len(chosen),
        "missing_cells": missing, "not_ok_runs": not_ok,
        "runs_total": len(runs),
        "gstar_per_block": {a: {str(b): v for b, v in d.items()} for a, d in prim_vals.items()},
        "confirmatory": est, "dominance": dominance(est), "ranking": ranking(est),
    }
    s3 = _estimates(_per_block(chosen, blocks, s3_value), blocks)
    out["sensitivity_s3"] = {"estimates": s3, "ranking": ranking(s3),
                             "ranking_equal_to_primary": ranking(s3) == ranking(est)}
    out["drift"] = drift(chosen)
    out["exploratory"] = {
        "gstar_over_unlimited_levels": _estimates(_per_block(chosen, blocks, gstar_unlimited_levels), blocks),
        "gstar_unfiltered": _estimates(_per_block(chosen, blocks, gstar_unfiltered), blocks),
        "primary_definition_defined_blocks_only": _partial_estimates(prim_vals, blocks),
    }
    out["descriptives"] = descriptives(chosen)
    return out


def analyse_exp001(runs: Runs) -> dict[str, Any]:
    """EXP-001 items 5, 16, 17, 21: per-level median and range over repeats of the SCALE
    generator goodput (C_gen), ApacheBench throughput and the SCALE/ab ratio."""
    chosen, not_ok = select_cells(runs)
    lst = [res for (_, _), (res, _) in sorted(chosen.items())]
    levels = sorted({lv["concurrency"] for r in lst for lv in r["levels"]})
    table = {}
    for c in levels:
        lvs = [lv for r in lst for lv in r["levels"] if lv["concurrency"] == c]
        g = [lv["goodput_rps"] for lv in lvs]
        ab = [lv["ab_rps"] for lv in lvs if lv.get("ab_rps")]
        ratios = [lv["goodput_rps"] / lv["ab_rps"] for lv in lvs if lv.get("ab_rps")]
        table[c] = {"n": len(lvs), "c_gen_median": statistics.median(g), "c_gen_min": min(g),
                    "c_gen_max": max(g), "ab_median": statistics.median(ab) if ab else None,
                    "ab_min": min(ab) if ab else None, "ab_max": max(ab) if ab else None,
                    "ratio_median": statistics.median(ratios) if ratios else None,
                    "ratio_min": min(ratios) if ratios else None,
                    "ratio_max": max(ratios) if ratios else None,
                    "ratio_median_in_band": (EXP001_RATIO_BAND[0] <= statistics.median(ratios) <= EXP001_RATIO_BAND[1])
                    if ratios else None,
                    "all_ratios_in_band": all(EXP001_RATIO_BAND[0] <= x <= EXP001_RATIO_BAND[1] for x in ratios)
                    if ratios else None,
                    "generator_cpu_median": statistics.median(lv["generator_cpu_util"] for lv in lvs),
                    "generator_cpu_max": max(lv["generator_cpu_util"] for lv in lvs),
                    "server_cpu_median": statistics.median(lv["server_cpu_util"] for lv in lvs),
                    "p99_median_ms": statistics.median(lv["p99_ms"] for lv in lvs if lv["p99_ms"] is not None),
                    "error_rate_max": max((lv["error_rate"] or 0) for lv in lvs)}
    gate = table.get(EXP001_GATE_C, {}).get("ratio_median")
    h0 = all(t["ratio_median_in_band"] for t in table.values() if t["ratio_median_in_band"] is not None)
    return {"analysis_version": ANALYSIS_VERSION, "runs_total": len(runs), "repeats_ok": len(lst),
            "not_ok_runs": not_ok, "levels": table,
            "h0_ratio_median_in_band_all_levels": h0,
            "gate_ratio_median_c32": gate,
            "gate_exp002_may_start": gate is not None and gate >= EXP001_RATIO_BAND[0]}


def write_levels_csv(runs: Runs, path: str) -> None:
    """One row per (run, level): the machine-readable metrics table (protocol item 21/22)."""
    cols = ["run_id", "experiment_id", "label", "arm", "block", "arm_position", "status",
            "concurrency", "offered_rate_rps", "goodput_rps", "attempts", "validated_ok",
            "invalid_body", "transport_errors", "error_rate", "p50_ms", "p95_ms", "p99_ms",
            "max_ms", "lag_p99_ms", "server_cpu_util", "server_rss_mb", "generator_cpu_util",
            "generator_limited", "ab_rps", "connections_finished"]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for res, _ in sorted(runs, key=lambda rm: rm[0]["run_id"]):
            for lv in res["levels"]:
                row = {**{k: res.get(k) for k in cols[:7]}, **lv}
                w.writerow([row.get(k) for k in cols])


def figures_exp002(analysis: dict[str, Any], out_stem: str) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colors = {"A0": "#222222", "A1": "#1b6ca8", "A2": "#c0392b", "A3": "#27864a", "A4": "#8e44ad"}
    paths = []
    fig, ax = plt.subplots(figsize=(6.6, 4.2))
    for arm, d in sorted(analysis["descriptives"].items()):
        cs = sorted(d["per_level"], key=int)
        med = [d["per_level"][c]["goodput_median"] for c in cs]
        lo = [d["per_level"][c]["goodput_min"] for c in cs]
        hi = [d["per_level"][c]["goodput_max"] for c in cs]
        xs = [int(c) for c in cs]
        ax.plot(xs, med, marker="o", color=colors[arm], label=arm)
        ax.fill_between(xs, lo, hi, color=colors[arm], alpha=0.2)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("closed-loop concurrency c (connections)")
    ax.set_ylabel("goodput G(c), validated responses per second")
    ax.set_title("EXP-002: median over blocks, band = min to max")
    ax.legend(title="arm")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(f"{out_stem}_goodput.{ext}", dpi=150)
        paths.append(f"{out_stem}_goodput.{ext}")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    est = analysis["confirmatory"]
    alt = analysis["exploratory"]["gstar_unfiltered"]
    for i, arm in enumerate(TREATMENTS):
        e, label = (est[arm], "confirmatory") if est[arm]["included"] else (alt[arm], "exploratory (unfiltered G*)")
        if not e.get("included", True) or "ratio" not in e:
            continue
        ax.plot(e["ci9875"], [i, i], color=colors[arm], lw=1.5)
        ax.plot(e["ci95"], [i, i], color=colors[arm], lw=4, alpha=0.6)
        ax.plot([e["ratio"]], [i], "o", color=colors[arm],
                mfc="white" if label != "confirmatory" else colors[arm])
    ax.axvline(1.0, color="grey", lw=0.8)
    ax.set_xscale("log")
    ax.set_yticks(range(len(TREATMENTS)))
    ax.set_yticklabels([a + ("" if est[a]["included"] else " (excl., exploratory)") for a in TREATMENTS])
    ax.set_xlabel("R_j = G*_j / G*_A0 (log scale); thick 95 %, thin 98.75 %")
    ax.set_title("EXP-002: geometric mean ratio to A0, bootstrap over blocks")
    ax.grid(True, axis="x", which="both", alpha=0.3)
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(f"{out_stem}_ratios.{ext}", dpi=150)
        paths.append(f"{out_stem}_ratios.{ext}")
    plt.close(fig)
    return paths


def figures_exp001(analysis: dict[str, Any], out_stem: str) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lv = analysis["levels"]
    cs = sorted(lv, key=int)
    xs = range(len(cs))
    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    for off, key, col, lab in ((-0.12, "c_gen", "#1b6ca8", "SCALE generator"), (0.12, "ab", "#c0392b", "ApacheBench 2.3")):
        med = [lv[c][f"{key}_median"] for c in cs]
        lo = [lv[c][f"{key}_median"] - lv[c][f"{key}_min"] for c in cs]
        hi = [lv[c][f"{key}_max"] - lv[c][f"{key}_median"] for c in cs]
        ax.errorbar([x + off for x in xs], med, yerr=[lo, hi], fmt="o", color=col, capsize=4, label=lab)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([str(c) for c in cs])
    ax.set_xlabel("concurrency c (connections), GET /null")
    ax.set_ylabel("requests per second")
    ax.set_title("EXP-001: median over 5 repeats, bars = min to max")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    paths = []
    for ext in ("png", "svg"):
        fig.savefig(f"{out_stem}_ceiling.{ext}", dpi=150)
        paths.append(f"{out_stem}_ceiling.{ext}")
    plt.close(fig)
    return paths
