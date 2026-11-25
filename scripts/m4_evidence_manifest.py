# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""M4 evidence manifest and number audit (master prompt 11.5).

1. Every displayed quantity in the manuscript, the supplementary file, the claims
   register and the M3 experiment reports is an entry below: displayed text,
   experiment id, run ids, metric definition, result path, locator, generator
   script, config/protocol hash and code revision. The raw value is read from the
   result file and the displayed text must equal the raw value rounded to the
   displayed number of decimals (matches_raw).
2. Coverage: every numeric token of the scanned documents must be an entry, a
   listed design parameter (not a result) or a structural token (dates, section
   numbers, identifiers). Uncovered tokens are reported and make the script fail.

Writes research/publication/artifact_manifest.json. Exit 1 on any mismatch or
uncovered token. Reads recorded outputs only; executes no benchmark code.
"""

from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A2P = "research/experiments/EXP-002/analysis.json"
A1P = "research/experiments/EXP-001/analysis.json"
XP = "results/exploratory/M4-REANALYSIS-20261125/summary.json"
FP = "research/freeze.json"
RAW2 = "results/raw/EXP-002/EXP-002-M3"
RAW1 = "results/raw/EXP-001/EXP-001-M3"

SCANNED = ["research/paper/manuscript.md", "research/paper/supplementary.md",
           "research/claims_register.csv", "research/experiments/EXP-001/report.md",
           "research/experiments/EXP-002/report.md", "research/experiments/EXP-003/report.md",
           "research/experiments/EXP-004/report.md"]


def load(p):
    with open(os.path.join(ROOT, p)) as fh:
        return json.load(fh)


def sha(p):
    with open(os.path.join(ROOT, p), "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def get(obj, path):
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        obj = obj[int(part[1:-1])] if part.startswith("[") else obj[part]
    return obj


A2J, A1J, XJ, FJ = load(A2P), load(A1P), load(XP), load(FP)
FREEZE = {"study": FJ["protocol"]["sha256"],
          **{p["experiment_id"]: p["sha256"] for p in FJ["experiment_protocols"]}}
CFG2 = next(c["sha256"] for c in FJ["configs"] if c["experiment_id"] == "EXP-002")
CFG1 = next(c["sha256"] for c in FJ["configs"] if c["experiment_id"] == "EXP-001")
REV2, REV1, REV_M4 = "3fb0c6624873a8335de64477cd65126776ee09c3", "6c3af82", XJ["code_revision_at_run"]
RUNS2 = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, RAW2, "runs", "*.json"))
               if not p.endswith(".manifest.json"))
OK2 = [r for r in RUNS2 if load(f"{RAW2}/runs/{r}.json")["status"] == "ok"]
RUNS1 = sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT, RAW1, "runs", "*.json"))
               if not p.endswith(".manifest.json"))

CTX = {
    "EXP-002": dict(run_ids="RS-EXP-002", config_hash={"EXP-002.json": CFG2, "run_config_hash": "439fce64bd3a896e009ac89786e6630bc804906d317a3541f28fdba5d4722be0"},
                    protocol_hash={"study": FREEZE["study"], "EXP-002": FREEZE["EXP-002"]}, code_revision=REV2,
                    generator_script="scale analyse EXP-002 (src/scale/analysis.py, analysis-1.0)", label="confirmatory"),
    "EXP-001": dict(run_ids="RS-EXP-001", config_hash={"EXP-001.json": CFG1},
                    protocol_hash={"study": FREEZE["study"], "EXP-001": FREEZE["EXP-001"]}, code_revision=REV1,
                    generator_script="scale analyse EXP-001 (src/scale/analysis.py, analysis-1.0); scale resolve-ceiling", label="confirmatory"),
    "M4": dict(run_ids="RS-EXP-002", config_hash={"EXP-002.json": CFG2}, protocol_hash={"study": FREEZE["study"], "EXP-002": FREEZE["EXP-002"]},
               code_revision=REV_M4, generator_script="scripts/m4_exploratory_confounders.py", label="exploratory"),
    "PILOT": dict(run_ids="RS-PILOT", config_hash={"pilot-quiet.json": FJ["pre_stated_rule_inputs"][0]["sha256"]},
                  protocol_hash={"study": FREEZE["study"]}, code_revision=REV1,
                  generator_script="scale resolve-pilot (src/scale/pilotrule.py, pilot-rule-1.0)", label="exploratory (rule input)"),
}

ENTRIES: list[dict] = []


def E(disp, ctx, path, loc, metric, value=None, exp=None):
    """Register one displayed number. value overrides the locator lookup."""
    if value is None:
        value = get(load(path) if path not in (A2P, A1P, XP, FP) else {A2P: A2J, A1P: A1J, XP: XJ, FP: FJ}[path], loc)
    ENTRIES.append({"displayed": disp, "experiment_id": exp or {"M4": "EXP-002 (M4 re-analysis)", "PILOT": "PILOT-QUIET"}.get(ctx, ctx),
                    "result_path": path, "locator": loc, "metric_definition": metric, "raw_value": value, **CTX[ctx]})


def matches(disp, raw):
    d = disp.replace(",", "")
    if isinstance(raw, str):
        return d in raw
    if re.fullmatch(r"-?\d+(\.\d+)?e-?\d+", d):
        return f"{raw:.2e}" == d
    dec = len(d.split(".")[1]) if "." in d else 0
    return f"{raw:.{dec}f}" == d


# ---------- EXP-001 ----------
for c in ("1", "8", "32"):
    L = f"levels.{c}"
    for key, dec, met in (("c_gen_median", 1, "SCALE generator goodput on GET /null, median of 5 repeats (rps)"),
                          ("c_gen_min", 1, "min of 5 repeats (rps)"), ("c_gen_max", 1, "max of 5 repeats (rps)"),
                          ("ab_median", 1, "ApacheBench 2.3 rps, median of 5"), ("ab_min", 1, "ab min"), ("ab_max", 1, "ab max"),
                          ("ratio_median", 3, "SCALE/ab ratio, median of 5"), ("ratio_min", 3, "ratio min"), ("ratio_max", 3, "ratio max"),
                          ("generator_cpu_median", 2, "generator CPU s per wall s, median"), ("generator_cpu_max", 2, "generator CPU max")):
        v = A1J["levels"][c][key]
        E(f"{v:.{dec}f}", "EXP-001", A1P, f"{L}.{key}", met)
E("0.898", "EXP-001", A1P, "levels.32.generator_cpu_median", "generator CPU at c = 32, median")
E("1.404", "EXP-001", A1P, "levels.32.generator_cpu_max", "generator CPU at c = 32, max")
for i, v in enumerate(FJ["resolutions"][0]["ceiling_rule"]["output"]["run_ceilings_rps"]):
    E(f"{v:.1f}", "EXP-001", FP, f"resolutions[0].ceiling_rule.output.run_ceilings_rps[{i}]", "run ceiling: peak goodput over c in {1, 8, 32} (rps)")
E("27919.4", "EXP-001", FP, "resolutions[0].ceiling_rule.output.generator_ceiling_rps", "AM-5 ceiling C_gen: median of the 5 run ceilings (rps)")
E("27,919", "EXP-001", FP, "resolutions[0].ceiling_rule.output.generator_ceiling_rps", "C_gen rounded to the unit (rps)")
E("13959.7", "M4", XP, "X8_A2_vs_ceiling.threshold_50pct_of_ceiling", "50 % of C_gen (rps)")
probes1 = [load(f"{RAW1}/runs/{r}.manifest.json")["idle_probe"]["cpu_pct"] for r in RUNS1]
E("1.9", "EXP-001", RAW1, "runs/*.manifest.json idle_probe.cpu_pct min", "idle probe, % CPU", min(probes1))
E("2.5", "EXP-001", RAW1, "runs/*.manifest.json idle_probe.cpu_pct max", "idle probe, % CPU", max(probes1))
la1 = [load(f"{RAW1}/runs/{r}.manifest.json")["load_average"][0] for r in RUNS1]
E("2.76", "EXP-001", RAW1, "runs/*.manifest.json load_average[0] min", "1-min load average at run start", min(la1))
E("4.05", "EXP-001", RAW1, "runs/*.manifest.json load_average[0] max", "1-min load average at run start", max(la1))
E("344.5", "EXP-001", f"{RAW1}/batch.json", "runtime_s", "EXP-001 wall-clock (s)")
E("1.015", "EXP-001", A1P, "gate_ratio_median_c32", "item 17 gate: median SCALE/ab at c = 32")
# exploratory supplements (J-0011)
st_o = [p for p in glob.glob(os.path.join(ROOT, "results/raw/EXP-001/STALL-OPEN-M3/runs/*.json")) if "manifest" not in p][0]
st_c = [p for p in glob.glob(os.path.join(ROOT, "results/raw/EXP-001/STALL-CLOSED-M3/runs/*.json")) if "manifest" not in p][0]
rel = lambda p: os.path.relpath(p, ROOT)  # noqa: E731
E("190.12", "EXP-001", rel(st_o), "levels[0].p99_ms", "open-loop intended-time p99 under injected stall (ms), exploratory", exp="EXP-001 supplement")
E("148.30", "EXP-001", rel(st_o), "levels[0].lag_p99_ms", "open-loop schedule lag p99 (ms), exploratory", exp="EXP-001 supplement")
E("0.91", "EXP-001", rel(st_c), "levels[0].p99_ms", "closed-loop p99 under the same stall (ms), exploratory", exp="EXP-001 supplement")
for i, v in enumerate(XJ["X8_A2_vs_ceiling"]["gp4_gstar"]):
    E(f"{v:.1f}", "M4", XP, f"X8_A2_vs_ceiling.gp4_gstar[{i}]", "4 generator processes, G* on GET /null (rps), exploratory", exp="EXP-001 supplement")
with open(os.path.join(ROOT, "results/raw/EXP-001/timer.txt")) as fh:
    res_t = float(re.search(r"resolution=([0-9.e-]+)", fh.read()).group(1))
E("4.17e-08", "EXP-001", "results/raw/EXP-001/timer.txt", "resolution", "perf_counter resolution (s)", res_t, exp="EXP-001 supplement")
for i, v in enumerate(XJ["X11_exp001_c1"]["ratios_c1"]):
    if i in (0, 4):
        E(f"{v:.3f}", "M4", XP, f"X11_exp001_c1.ratios_c1[{i}]", "SCALE/ab ratio at c = 1, per repeat", exp="EXP-001 (M4 re-analysis)")

# ---------- quiet pilot ----------
pr = FJ["resolutions"][0]["pilot_rule"]["output"]
E("512", "PILOT", FP, "resolutions[0].pilot_rule.output.c_max", "c_max by pilot-rule-1.0")
for a, d in (("A1", 4), ("A2", 4), ("A3", 4), ("A4", 4)):
    E(f"{pr['sd_log_ratio'][a]:.{d}f}", "PILOT", FP, f"resolutions[0].pilot_rule.output.sd_log_ratio.{a}", "between-block SD of log R, 5 pilot blocks")
for a, d in (("A1", 2), ("A3", 2), ("A4", 3), ("A2", 1)):
    E(f"{XJ['X10_pilot_vs_exp002'][a]['geometric_mean_R_unfiltered']:.{d}f}", "M4", XP, f"X10_pilot_vs_exp002.{a}.geometric_mean_R_unfiltered",
      "pilot within-block geometric mean R, unfiltered G* over c <= 512, exploratory", exp="PILOT-QUIET (M4 re-analysis)")

# ---------- EXP-002 confirmatory ----------
for a in ("A1", "A3", "A4"):
    c = A2J["confirmatory"][a]
    E(f"{c['ratio']:.3f}", "EXP-002", A2P, f"confirmatory.{a}.ratio", "geometric mean of within-block R = G*_j / G*_A0")
    E(f"{c['ratio']:.2f}", "EXP-002", A2P, f"confirmatory.{a}.ratio", "R, 2 decimals")
    for lv, key in (("95", "ci95"), ("9875", "ci9875")):
        for i in (0, 1):
            for d in (3, 2):
                E(f"{c[key][i]:.{d}f}", "EXP-002", A2P, f"confirmatory.{a}.{key}[{i}]", f"percentile bootstrap {lv} interval bound")
    E(f"{c['sd_log_ratio']:.3f}", "EXP-002", A2P, f"confirmatory.{a}.sd_log_ratio", "SD of per-block log R")
for a in ("A0", "A1", "A2", "A3", "A4"):
    d = A2J["descriptives"][a]
    for key in ("gstar_unfiltered_median", "gstar_unfiltered_min", "gstar_unfiltered_max"):
        E(f"{d[key]:.1f}", "EXP-002", A2P, f"descriptives.{a}.{key}", "G* over the full ladder, over 10 blocks (rps)")
    for c, v in d["per_level"].items():
        E(f"{v['goodput_median']:.1f}", "EXP-002", A2P, f"descriptives.{a}.per_level.{c}.goodput_median", "median G(c) over 10 blocks (rps)")
        E(f"{v['p99_median_ms']:.2f}", "EXP-002", A2P, f"descriptives.{a}.per_level.{c}.p99_median_ms", "median p99 latency over 10 blocks (ms)")
        E(f"{v['error_rate_max']:.3f}", "EXP-002", A2P, f"descriptives.{a}.per_level.{c}.error_rate_max", "max per-run error rate")
        E(f"{v['error_rate_max']:.2f}", "EXP-002", A2P, f"descriptives.{a}.per_level.{c}.error_rate_max", "max per-run error rate")
        E(f"{v['error_rate_median']:.2f}", "EXP-002", A2P, f"descriptives.{a}.per_level.{c}.error_rate_median", "median per-run error rate")
E("28131", "EXP-002", A2P, "descriptives.A2.gstar_unfiltered_median", "A2 G* median (rps), unit")
E("28,131", "EXP-002", A2P, "descriptives.A2.gstar_unfiltered_median", "A2 G* median (rps), unit")
E("0.59", "EXP-002", A2P, "descriptives.A1.cache_hit_ratio_median", "median cache hit ratio over the run")
E("14,737,227", "EXP-002", A2P, "descriptives.A4.rejected_503_total", "server count of HTTP 503 over 10 runs, including warmups")
E("10540.9", "EXP-002", f"{RAW2}/batch.json", "runtime_s", "EXP-002 wall-clock (s)", load(f"{RAW2}/batch.json")["runtime_s"])
E("12", "EXP-002", A2P, "len(not_ok_runs)", "runs excluded by the idle probe", len(A2J["not_ok_runs"]))
E("62", "EXP-002", A2P, "runs_total", "runs in the results directory")
E("50", "EXP-002", A2P, "cells_ok", "cells with an accepted run")
probes_x = [float(re.search(r"([0-9.]+) %", r["failure"]).group(1)) for r in A2J["not_ok_runs"]]
E("16.2", "EXP-002", A2P, "not_ok_runs[*].failure min", "idle probe of excluded runs (%)", min(probes_x))
E("35.4", "EXP-002", A2P, "not_ok_runs[*].failure max", "idle probe of excluded runs (%)", max(probes_x))
E("1.9", "M4", XP, "X9_background_vs_residual.idle_probe_range[0]", "idle probe of accepted runs (%)")
E("10.0", "M4", XP, "X9_background_vs_residual.idle_probe_range[1]", "idle probe of accepted runs (%)")
la2 = [load(f"{RAW2}/runs/{r}.manifest.json")["load_average"][0] for r in OK2]
E("1.9", "EXP-002", RAW2, "runs/*.manifest.json load_average[0] min (accepted)", "1-min load average at run start", min(la2))
E("142", "EXP-002", RAW2, "runs/*.manifest.json load_average[0] max (accepted)", "1-min load average at run start", max(la2))
# S3 and drift
for a in ("A1", "A2", "A3", "A4"):
    s = A2J["sensitivity_s3"]["estimates"][a]
    d = 2 if a == "A2" else 3
    E(f"{s['ratio']:.{d}f}", "EXP-002", A2P, f"sensitivity_s3.estimates.{a}.ratio", "S3: R with mean goodput over c in {16, 32, 64}")
    for i in (0, 1):
        E(f"{s['ci9875'][i]:.{d}f}", "EXP-002", A2P, f"sensitivity_s3.estimates.{a}.ci9875[{i}]", "S3 98.75 % bound")
for k, d in (("run_order", 5), ("position_in_block", 4)):
    v = A2J["drift"][k]
    E(f"{v['slope_log_gstar_per_step']:.{d}f}", "EXP-002", A2P, f"drift.{k}.slope_log_gstar_per_step", "drift slope of log G*")
    for i in (0, 1):
        E(f"{v['ci95'][i]:.{d}f}", "EXP-002", A2P, f"drift.{k}.ci95[{i}]", "drift slope 95 % bound")
# exploratory A2
for key, d in (("gstar_unfiltered", 1), ("gstar_over_unlimited_levels", 1)):
    v = A2J["exploratory"][key]["A2"]
    E(f"{v['ratio']:.{d}f}", "EXP-002", A2P, f"exploratory.{key}.A2.ratio", f"exploratory A2 R ({key})")
    for i in (0, 1):
        E(f"{v['ci9875'][i]:.{d}f}", "EXP-002", A2P, f"exploratory.{key}.A2.ci9875[{i}]", "98.75 % bound, exploratory")
E("247", "EXP-002", A2P, "exploratory.gstar_unfiltered.A2.ratio", "exploratory A2 R rounded", A2J["exploratory"]["gstar_unfiltered"]["A2"]["ratio"])
E("91", "EXP-002", A2P, "exploratory.gstar_over_unlimited_levels.A2.ratio", "exploratory A2 R rounded", A2J["exploratory"]["gstar_over_unlimited_levels"]["A2"]["ratio"])

# ---------- M4 re-analysis ----------
x = XJ
E("219", "M4", XP, "checksums", "raw files verified", sum(v["files"] for v in x["checksums"].values()))
for k, lab in (("A3_over_A1", "R_A3/R_A1"), ("A1_over_A4", "R_A1/R_A4"), ("A3_over_A4", "R_A3/R_A4")):
    v = x["X3_pairwise_included_arms"][k]
    E(f"{v['ratio']:.2f}", "M4", XP, f"X3_pairwise_included_arms.{k}.ratio", f"exploratory {lab}")
    for i in (0, 1):
        E(f"{v['ci9875'][i]:.2f}", "M4", XP, f"X3_pairwise_included_arms.{k}.ci9875[{i}]", "98.75 % bound, exploratory")
for i, v in enumerate(x["X4_A3_truncation"]["G512_over_G256_in_those_blocks"]):
    E(f"{v:.3f}", "M4", XP, f"X4_A3_truncation.G512_over_G256_in_those_blocks[{i}]", "A3 G(512)/G(256) in blocks peaking at 512")
v = x["X4_A3_truncation"]["R_A3_gstar_le_256"]
for disp, loc in ((f"{v['ratio']:.2f}", "ratio"), (f"{v['ci9875'][0]:.2f}", "ci9875[0]"), (f"{v['ci9875'][1]:.2f}", "ci9875[1]")):
    E(disp, "M4", XP, f"X4_A3_truncation.R_A3_gstar_le_256.{loc}", "R_A3 with G* over c <= 256, exploratory")
rng = x["X4_A3_truncation"]["A3_goodput_range_c64_to_512_per_block"]
E("2.4", "M4", XP, "X4_A3_truncation.A3_goodput_range_c64_to_512_per_block", "max per-block (max/min - 1) of A3 G(c), c 64 to 512 (%)",
  100 * max(hi / lo - 1 for lo, hi in rng))
for a, d in (("A1", 2), ("A3", 2), ("A4", 3)):
    v = x["X5_without_blocks_8_9"][a]
    E(f"{v['ratio']:.{d}f}", "M4", XP, f"X5_without_blocks_8_9.{a}.ratio", "R without blocks 8 and 9, exploratory")
    for i in (0, 1):
        E(f"{v['ci9875'][i]:.{d}f}", "M4", XP, f"X5_without_blocks_8_9.{a}.ci9875[{i}]", "98.75 % bound, exploratory")
for c, d in (("1", 3), ("2", 3), ("4", 3), ("8", 3), ("16", 2), ("512", 2), ("256", 2)):
    E(f"{x['X6_A4_over_A0_per_level'][c]['ratio_median']:.{d}f}", "M4", XP, f"X6_A4_over_A0_per_level.{c}.ratio_median", "median A4/A0 G(c)")
E("0.48", "M4", XP, "X7_generator_cpu_at_peak_max.A2", "max generator CPU at the peak level")
E("0.10", "M4", XP, "X7_generator_cpu_at_peak_max.A3", "max generator CPU at the peak level")
E("0.011", "M4", XP, "X7_generator_cpu_at_peak_max.A1", "max generator CPU at the peak level")
E("1.008", "M4", XP, "X8_A2_vs_ceiling.A2_gstar_over_ceiling_median", "A2 median G* / C_gen")
E("10356.6", "M4", XP, "X8_A2_vs_ceiling.A2_goodput_median_c8", "A2 median G(8) (rps)")
E("1.21", "M4", XP, "X8_A2_vs_ceiling.A2_server_cpu_median_c2", "A2 server CPU at c = 2")
E("2.78", "M4", XP, "X8_A2_vs_ceiling.A2_server_cpu_median_c8", "A2 server CPU at c = 8")
E("0.20", "M4", XP, "X9_background_vs_residual.spearman_idle_probe_vs_residual", "Spearman, idle probe vs arm-centred log G*")
E("0.007", "M4", XP, "X9_background_vs_residual.spearman_load1_vs_residual", "Spearman, load average vs arm-centred log G*")
for a in ("A1", "A2", "A3", "A4"):
    v = x["X12_closed_loop_slo_goodput"]["estimates"][a]
    d = 1 if a == "A2" else (3 if a == "A4" else 2)
    E(f"{v['ratio']:.{d}f}", "M4", XP, f"X12_closed_loop_slo_goodput.estimates.{a}.ratio", "closed-loop latency-bounded R, exploratory")
    for i in (0, 1):
        E(f"{v['ci9875'][i]:.{d}f}", "M4", XP, f"X12_closed_loop_slo_goodput.estimates.{a}.ci9875[{i}]", "98.75 % bound, exploratory")
v = x["X12_closed_loop_slo_goodput"]["A3_over_A1"]
for disp, loc in ((f"{v['ratio']:.2f}", "ratio"), (f"{v['ci9875'][0]:.2f}", "ci9875[0]"), (f"{v['ci9875'][1]:.2f}", "ci9875[1]")):
    E(disp, "M4", XP, f"X12_closed_loop_slo_goodput.A3_over_A1.{loc}", "closed-loop latency-bounded R_A3/R_A1, exploratory")
m = x["X2_mechanism"]
for a, c, key, d in (("A0", "1", "server_cpu_ms_per_validated_response", 1), ("A0", "4", "server_cpu_ms_per_validated_response", 1),
                     ("A0", "16", "server_cpu_ms_per_validated_response", 1), ("A0", "512", "server_cpu_ms_per_validated_response", 1),
                     ("A0", "512", "server_cpu_ms_per_validated_response", 0),
                     ("A3", "1", "server_cpu_ms_per_validated_response", 1), ("A3", "64", "server_cpu_ms_per_validated_response", 2),
                     ("A3", "512", "server_cpu_ms_per_validated_response", 2), ("A2", "2", "server_cpu_ms_per_validated_response", 3),
                     ("A2", "8", "server_cpu_ms_per_validated_response", 3),
                     ("A0", "1", "server_cpu_median", 3), ("A0", "4", "server_cpu_median", 3), ("A0", "4", "server_cpu_median", 1),
                     ("A0", "16", "server_cpu_median", 3), ("A0", "512", "server_cpu_median", 3), ("A3", "1", "server_cpu_median", 3),
                     ("A3", "64", "server_cpu_median", 3), ("A3", "512", "server_cpu_median", 3), ("A2", "2", "server_cpu_median", 3),
                     ("A2", "8", "server_cpu_median", 3), ("A3", "512", "server_cpu_ms_per_validated_response", 1)):
    E(f"{m[a]['per_level'][c][key]:.{d}f}", "M4", XP, f"X2_mechanism.{a}.per_level.{c}.{key}", key)
E("0.89", "M4", XP, "X2_mechanism.A0.sys_share_of_server_cpu_median", "system-time share of server CPU")
E("0.45", "M4", XP, "X2_mechanism.A3.sys_share_of_server_cpu_median", "system-time share of server CPU")
E("15.97", "M4", XP, "X2_mechanism.A3.mean_batch_size_median", "A3 mean batch size, median over blocks")
E("2.44", "M4", XP, "X2_mechanism.A1.amdahl_bound_1_over_1_minus_h", "1 / (1 - median hit ratio)")
ec = x["X1_error_composition"]
for a in ("A0", "A1", "A2", "A3", "A4"):
    for k in ("attempts", "validated_ok", "http_500", "http_503", "transport_errors", "invalid_body"):
        E(str(ec[a][k]), "M4", XP, f"X1_error_composition.{a}.{k}", f"{k}, sum over measurement windows of 10 accepted runs")
E("334", "M4", XP, "X1_error_composition.A0.server_internal_errors", "server internal-error counter incl. warmups")
E("1400", "M4", XP, "X1_error_composition.A1.server_internal_errors", "server internal-error counter incl. warmups")
E("10,996,866", "M4", XP, "X1_error_composition.A4.http_503", "HTTP 503 in measurement windows")

# ---------- added at the M4 audit (corrections and rounded mentions) ----------
rt2 = [load(f"{RAW2}/runs/{r}.manifest.json")["runtime_s"] for r in OK2]
E("206.9", "EXP-002", RAW2, "runs/*.manifest.json runtime_s min (accepted)", "per-run wall-clock (s)", min(rt2))
E("219.7", "EXP-002", RAW2, "runs/*.manifest.json runtime_s max (accepted)", "per-run wall-clock (s)", max(rt2))
E("207", "EXP-002", RAW2, "runs/*.manifest.json runtime_s min (accepted)", "per-run wall-clock (s)", min(rt2))
E("220", "EXP-002", RAW2, "runs/*.manifest.json runtime_s max (accepted)", "per-run wall-clock (s)", max(rt2))
E("216", "EXP-002", RAW2, "M3 misprint, kept in the correction note", "superseded value: M3 printed 216 s as the per-run maximum (actual 219.7)", "216")
E("0.6547", "EXP-001", A1P, "levels.8.generator_cpu_median", "generator CPU at c = 8, median")
E("0.66", "EXP-001", A1P, "M3 misprint, kept in the correction note", "superseded value: M3 printed 0.66 (actual 0.6547)", "0.66")
E("160", "M4", XP, "X2_mechanism.A0.per_level.16.server_cpu_ms_per_validated_response", "A0 CPU ms per response from c = 16, rounded to 10",
  round(XJ["X2_mechanism"]["A0"]["per_level"]["16"]["server_cpu_ms_per_validated_response"], -1))
E("28,000", "EXP-001", FP, "resolutions[0].ceiling_rule.output.generator_ceiling_rps", "C_gen rounded to the thousand", round(27919.4, -3))
E("42,000", "EXP-002", A2P, "1.5 x descriptives.A2.gstar_unfiltered_median", "150 % of A2 median G*, rounded to the thousand",
  round(1.5 * A2J["descriptives"]["A2"]["gstar_unfiltered_median"], -3))
E("1.05", "M4", XP, "X2_mechanism.{A0,A2,A3}.per_level.*.little_c_over_X_p50_median (levels without errors)", "max of c/(X p50)",
  max(XJ["X2_mechanism"][a]["per_level"][c]["little_c_over_X_p50_median"] for a in ("A0", "A2", "A3")
      for c in ("1", "2", "4", "8", "16", "32") if not (a == "A2" and c in ("1", "2", "4"))))
E("0.89", "M4", XP, "X2_mechanism.{A0,A2,A3}.per_level.*.little_c_over_X_p50_median (levels without errors)", "min of c/(X p50)",
  min(XJ["X2_mechanism"][a]["per_level"][c]["little_c_over_X_p50_median"] for a in ("A0", "A2", "A3")
      for c in ("1", "2", "4", "8", "16", "32") if not (a == "A2" and c in ("1", "2", "4"))))

with open(os.path.join(ROOT, "results/raw/quiet-checks-exp002.jsonl")) as fh:
    qc = [json.loads(line) for line in fh][1]
for i, v in enumerate(qc["probes_pct"]):
    E(f"{v:.1f}", "EXP-002", "results/raw/quiet-checks-exp002.jsonl", f"line 2 probes_pct[{i}]", "pre-start quiet check, 1 s probe (%)", v)

# ---------- design parameters (not results) ----------
DESIGN = {"100", "150", "200", "500", "503", "200,000", "256", "0.99", "20261124", "20261126", "27919.4x", "10,000", "2,000", "98.75", "0.95", "1.05", "0.9", "1.1",
          "0.07", "0.85", "1024", "128", "512", "15.0", "3.43.1", "15.3.1", "3.12", "2.3", "L", "10,000"}
DESIGN_NOTE = ("N = 200,000; payload 256 B; Zipf 0.99; dataset and EXP-002 seed 20261124; pilot seed 20261126; 10,000 bootstrap resamples; "
               "2,000 drift resamples; Bonferroni 98.75 %; band [0.95, 1.05]; EXP-001 band [0.9, 1.1]; pilot SD trigger 0.07; "
               "85 % generator CPU; sweep levels up to 1024; ApacheBench 2.3; SQLite 3.43.1; macOS 15.3.1; Python 3.12")


def tokens(text):
    text = re.sub(r"`[^`]*`", " ", text)                     # paths, commands, hashes
    text = re.sub(r"\b[0-9a-f]{7,64}\b", " ", text)          # revisions and hash prefixes
    text = re.sub(r"\b(?:J|D|C|EXP|AM|X|S)-?\d+\b", " ", text)
    text = re.sub(r"\b20\d\d-\d\d-\d\d\b|\b\d\d:\d\d:\d\dZ\b", " ", text)
    text = re.sub(r"arXiv:\S+|doi:\S+|10\.\d{4,}/\S+|https?://\S+", " ", text)
    text = re.sub(r"\b\d+\.\d+\.\d+(\.\d+)?\b", " ", text)            # versions, IP address
    text = re.sub(r"[A-Za-z]-\d+\.\d+\b|\bv\d+\.\d+\b", " ", text)      # analysis-1.0, v1.0
    text = re.sub(r"(?m)^#+ \d+(\.\d+)?|\b(?:sections?|items?) \d+(\.\d+)?(?:,? (?:and|to) \d+(\.\d+)?)?", " ", text)
    text = re.sub(r"(?:pp\. |\)|:)\d+-\d+", " ", text)                      # page ranges
    text = re.sub(r"\bHTTP \d{3}\b|\b(?:200|500|503) (?:responses?|rejections?)", " ", text)
    return re.findall(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?(?:e-\d+)?", text)


def structural(t):
    t2 = t.replace(",", "").lstrip("-")
    if "." not in t2 and "e" not in t2:
        n = int(t2)
        return n < 100 or 1950 <= n <= 2030      # counts, levels, section numbers, years
    return False


def main() -> int:
    for e in ENTRIES:
        e["matches_raw"] = matches(e["displayed"], e["raw_value"])
    displayed = {e["displayed"].replace(",", "") for e in ENTRIES}
    design = {d.replace(",", "") for d in DESIGN}
    coverage = {}
    for p in SCANNED:
        with open(os.path.join(ROOT, p)) as fh:
            if p.endswith(".csv"):    # the section column holds manuscript section numbers, not results
                import csv
                text = "\n".join(" ".join(v for k, v in row.items() if k != "section") for row in csv.DictReader(fh))
            else:
                text = fh.read()
            toks = tokens(text)
        unc = sorted({t for t in toks if t.replace(",", "").lstrip("-") not in displayed and t.replace(",", "") not in displayed
                      and t.replace(",", "") not in design and not structural(t)})
        coverage[p] = {"numeric_tokens": len(toks), "uncovered": unc}
    bad = [e for e in ENTRIES if not e["matches_raw"]]
    raw_sums = {s: hashlib.sha256(open(os.path.join(ROOT, "results/raw", s, "SHA256SUMS"), "rb").read()).hexdigest()
                for s in ("EXP-001", "EXP-002", "PILOT-QUIET")}
    figs = [{"figure": f, "experiment_id": "EXP-002", "source": A2P, "generator_script": "scale analyse EXP-002 (figures_exp002)",
             "sha256": sha(f"research/experiments/EXP-002/{f}"), "code_revision": REV2} for f in A2J["figures"]]
    figs += [{"figure": f, "experiment_id": "EXP-001", "source": A1P, "generator_script": "scale analyse EXP-001 (figures_exp001)",
              "sha256": sha(f"research/experiments/EXP-001/{f}"), "code_revision": REV1} for f in A1J["figures"]]
    out = {"schema_version": "1.0", "project": "SCALE", "updated": "2026-11-25", "status": "M4 evidence audit",
           "generator": "scripts/m4_evidence_manifest.py",
           "audit_head_revision": subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
           "scanned_documents": SCANNED, "design_parameters_not_results": DESIGN_NOTE,
           "raw_outputs": {"note": "results/raw/ is excluded from git by the repository ignore rule; these digests pin it",
                           "SHA256SUMS_sha256": raw_sums},
           "inputs_sha256": {p: sha(p) for p in (A2P, A1P, XP, FP)},
           "run_sets": {"RS-EXP-002": {"path": RAW2, "accepted_runs": OK2, "all_runs": RUNS2},
                        "RS-EXP-001": {"path": RAW1, "runs": RUNS1},
                        "RS-PILOT": {"path": "results/raw/PILOT-QUIET/PILOT-QUIET-M3", "runs": "PILOT-QUIET-b00..b04, arms A0 to A4 (25 runs)"}},
           "figures": figs, "n_entries": len(ENTRIES), "n_mismatches": len(bad), "coverage": coverage,
           "entries": [{"artifact_id": f"N-{i + 1:03d}", **e} for i, e in enumerate(ENTRIES)]}
    with open(os.path.join(ROOT, "research/publication/artifact_manifest.json"), "w") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    unc_all = {p: c["uncovered"] for p, c in coverage.items() if c["uncovered"]}
    print(f"entries {len(ENTRIES)}, mismatches {len(bad)}, uncovered {sum(len(v) for v in unc_all.values())}")
    for e in bad:
        print("MISMATCH", e["displayed"], e["locator"], e["raw_value"])
    for p, v in unc_all.items():
        print("UNCOVERED", p, v)
    return 1 if bad or unc_all else 0


if __name__ == "__main__":
    sys.exit(main())
