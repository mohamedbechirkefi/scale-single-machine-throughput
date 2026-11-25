# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Report generator: tables, figures and an optional PDF built only from validated
result files. Malformed results stop the report (fail closed)."""

from __future__ import annotations

import glob
import json
import math
import os
import re
import subprocess
from collections import defaultdict
from typing import Any

from . import metrics as m
from .schema import read_manifest, read_result

# Shared read-only tools live next to the repository (labs/.tools); override with env vars.
_TOOLS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".tools"))
PANDOC = os.environ.get("SCALE_PANDOC", os.path.join(_TOOLS, "pandoc"))
TYPST_PY = os.environ.get("SCALE_TYPST_PYTHON", os.path.join(_TOOLS, "py", "bin", "python"))


def load_runs(results_dir: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    paths = sorted(p for p in glob.glob(os.path.join(results_dir, "runs", "*.json"))
                   if not p.endswith(".manifest.json"))
    if not paths:
        raise FileNotFoundError(f"no result files under {results_dir}/runs")
    out = []
    for p in paths:
        res = read_result(p)
        man = read_manifest(p[: -len(".json")] + ".manifest.json")
        if man["run_id"] != res["run_id"] or man["config_hash"] != res["config_hash"]:
            raise ValueError(f"{p}: manifest does not match result")
        out.append((res, man))
    return out


def pilot_analysis(runs: list[tuple[dict, dict]], bootstrap_seed: int = 20261124) -> dict[str, Any]:
    """Within-block log ratios to A0 per arm, their between-block SD and the implied
    95 % half-width for planned block counts. Exploratory planning input only."""
    by_block: dict[tuple[str, int], dict[str, float]] = defaultdict(dict)
    for res, _ in runs:
        g = res["summary"]["peak_goodput_rps"]
        if res["status"] == "ok" and g and g > 0:
            by_block[(res["experiment_id"], res["block"])][res["arm"]] = g
    per_arm: dict[str, list[float]] = defaultdict(list)
    for arms in by_block.values():
        if "A0" in arms:
            for a, g in arms.items():
                if a != "A0":
                    per_arm[a].append(m.log_ratio(g, arms["A0"]))
    out: dict[str, Any] = {}
    for a, lr in sorted(per_arm.items()):
        e: dict[str, Any] = {"n_blocks": len(lr), "log_ratios": lr,
                             "geometric_mean_ratio": math.exp(sum(lr) / len(lr))}
        if len(lr) >= 2:
            sd = m.sample_sd(lr)
            mean, lo, hi = m.bootstrap_mean_ci(lr, 10_000, bootstrap_seed)
            e.update({"sd_log_ratio": sd, "half_width_n10": m.t_half_width(sd, 10),
                      "half_width_n20": m.t_half_width(sd, 20),
                      "bootstrap95_ratio": [math.exp(lo), math.exp(hi)]})
        out[a] = e
    return out


def degenerate_cases(runs: list[tuple[dict, dict]]) -> list[str]:
    notes = []
    for res, _ in runs:
        if res["status"] != "ok":
            notes.append(f"{res['run_id']}: status {res['status']} ({res['failure']})")
        cs = [lv["concurrency"] for lv in res["levels"]]
        peak_c = res["summary"].get("c_at_peak")
        if res["kind"] == "closed_sweep" and len(cs) > 1 and peak_c is not None:
            if peak_c == max(cs):
                notes.append(f"{res['run_id']}: peak at the highest swept concurrency c={peak_c};"
                             " saturation not reached, G* is truncated by the sweep")
            elif peak_c == min(cs):
                notes.append(f"{res['run_id']}: peak at the lowest swept concurrency c={peak_c};"
                             " goodput falls as concurrency rises")
        st = res.get("server_stats", {})
        if res["arm"] == "A4" and st.get("rejected_503") == 0 and res["status"] == "ok":
            notes.append(f"{res['run_id']}: A4 admission limit never triggered (no HTTP 503)")
        hits, misses = st.get("cache_hits"), st.get("cache_misses")
        if hits is not None and misses is not None and hits + misses > 0 and hits / (hits + misses) < 0.5:
            notes.append(f"{res['run_id']}: A1 cache hit ratio {hits / (hits + misses):.2f}"
                         f" ({hits} hits, {misses} misses); the cache is mostly cold")
        for lv in res["levels"]:
            tag = f"{res['run_id']} c={lv['concurrency']}"
            if lv.get("offered_rate_rps"):
                tag += f" rate={lv['offered_rate_rps']}"
            if lv["validated_ok"] == 0:
                notes.append(f"{tag}: zero validated responses")
            if lv["invalid_body"]:
                notes.append(f"{tag}: {lv['invalid_body']} invalid bodies")
            if lv["error_rate"]:
                notes.append(f"{tag}: error rate {lv['error_rate']:.4f} {lv['status_counts']}"
                             f" transport={lv['transport_errors']}")
            if lv["generator_limited"]:
                notes.append(f"{tag}: generator-limited ({'; '.join(lv['generator_limited_reasons'])})")
            if lv["connections_finished"] < lv["concurrency"]:
                notes.append(f"{tag}: only {lv['connections_finished']} connections finished")
    return notes


def project_runtime(runs: list[tuple[dict, dict]], levels: int, warmup_s: float, measure_s: float,
                    n_runs: int) -> dict[str, float]:
    """Project wall time of a matrix from the measured per-run overhead (runtime minus
    level windows) of the observed runs. Planning estimate only."""
    overheads = []
    for res, man in runs:
        cfg = man["config"]
        n = len(res["levels"])
        if n == 0:
            continue
        per_level = cfg["warmup_s"] + cfg["measure_s"] + 0.3  # 0.3 s start lead per level
        overheads.append(max(0.0, man["runtime_s"] - n * per_level) / 1.0)
    if not overheads:
        raise ValueError("no completed run to project from")
    overhead = max(overheads)
    per_run = overhead + levels * (warmup_s + measure_s + 0.3)
    return {"max_overhead_s": overhead, "per_run_s": per_run, "total_s": per_run * n_runs,
            "total_h": per_run * n_runs / 3600}


def _fmt(x: Any, nd: int = 1) -> str:
    if x is None:
        return "n/a"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def figure_goodput(runs: list[tuple[dict, dict]], path_stem: str) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    closed = [r for r, _ in runs if r["kind"] == "closed_sweep" and r["levels"] and r["endpoint"] == "item"]
    if not closed:
        return []
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    colors = {"A0": "#222222", "A1": "#1b6ca8", "A2": "#c0392b", "A3": "#27864a", "A4": "#8e44ad"}
    seen = set()
    for r in sorted(closed, key=lambda r: (r["arm"], r["block"])):
        xs = [lv["concurrency"] for lv in r["levels"]]
        ys = [lv["goodput_rps"] for lv in r["levels"]]
        lab = r["arm"] if r["arm"] not in seen else None
        seen.add(r["arm"])
        ax.plot(xs, ys, marker="o", color=colors.get(r["arm"]), alpha=0.75, label=lab)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlabel("closed-loop concurrency c (connections)")
    ax.set_ylabel("goodput G(c) (validated responses per second)")
    ax.set_title("EXPLORATORY: goodput versus concurrency, one line per run")
    ax.legend(title="arm")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    paths = []
    for ext in ("png", "svg"):
        p = f"{path_stem}.{ext}"
        fig.savefig(p, dpi=150)
        paths.append(p)
    plt.close(fig)
    return paths


def build_report(results_dir: str, full_levels: int = 7, full_warmup_s: float = 5.0,
                 full_measure_s: float = 15.0, full_runs: int = 50) -> dict[str, Any]:
    runs = load_runs(results_dir)
    labels = {r["label"] for r, _ in runs}
    fig_dir = os.path.join(results_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)
    figs = figure_goodput(runs, os.path.join(fig_dir, "goodput_vs_concurrency"))
    pilot = pilot_analysis(runs)
    degenerate = degenerate_cases(runs)
    projection = project_runtime(runs, full_levels, full_warmup_s, full_measure_s, full_runs)
    summary = {"results_dir": results_dir, "labels": sorted(labels), "n_runs": len(runs),
               "pilot": pilot, "degenerate": degenerate,
               "projection_full_matrix": {"levels": full_levels, "warmup_s": full_warmup_s,
                                          "measure_s": full_measure_s, "runs": full_runs,
                                          **projection},
               "figures": [os.path.relpath(p, results_dir) for p in figs]}
    with open(os.path.join(results_dir, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)

    title = "EXPLORATORY run report" if labels == {"exploratory"} else "Run report"
    L = [f"<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->",
         f"# SCALE: {title}", "",
         f"Generated by `scale report` from the validated result files in `{results_dir}`. "
         f"Labels present: {', '.join(sorted(labels))}."]
    if "exploratory" in labels:
        L += ["", "**Exploratory.** These runs were made while the protocol is unfrozen. "
              "They measure the harness and planning quantities; they are not findings."]
    L += ["", "## Runs", "",
          "| run id | block | position | arm | status | G* (rps) | c at peak | c_sat | runtime (s) | idle probe CPU % | load avg |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r, man in sorted(runs, key=lambda x: (x[0]["experiment_id"], x[0]["block"], x[0]["arm_position"])):
        s = r["summary"]
        L.append(f"| {r['run_id']} | {r['block']} | {r['arm_position']} | {r['arm']} | {r['status']} | "
                 f"{_fmt(s['peak_goodput_rps'])} | {_fmt(s['c_at_peak'])} | {_fmt(s['c_sat'])} | "
                 f"{_fmt(man['runtime_s'])} | {_fmt(man['idle_probe']['cpu_pct'])} | "
                 f"{' '.join(str(x) for x in man['load_average'])} |")
    L += ["", "## Levels", "",
          "| run id | c | rate (rps) | goodput (rps) | p50 (ms) | p95 (ms) | p99 (ms) | error rate | server CPU | generator CPU | gen-limited | ab (rps) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r, _ in runs:
        for lv in r["levels"]:
            L.append(f"| {r['run_id']} | {lv['concurrency']} | {_fmt(lv.get('offered_rate_rps'))} | "
                     f"{_fmt(lv['goodput_rps'])} | {_fmt(lv['p50_ms'], 2)} | {_fmt(lv['p95_ms'], 2)} | "
                     f"{_fmt(lv['p99_ms'], 2)} | {_fmt(lv['error_rate'], 4)} | "
                     f"{_fmt(lv['server_cpu_util'], 2)} | {_fmt(lv['generator_cpu_util'], 2)} | "
                     f"{'yes' if lv['generator_limited'] else 'no'} | {_fmt(lv.get('ab_rps'))} |")
    L += ["", "## Within-block ratios to A0 (planning input for the sample size)", ""]
    if pilot:
        L += ["| arm | blocks | geometric mean R | SD of log R | 95 % half-width at n=10 | at n=20 | bootstrap 95 % (R) |",
              "|---|---|---|---|---|---|---|"]
        for a, e in pilot.items():
            bs = e.get("bootstrap95_ratio")
            L.append(f"| {a} | {e['n_blocks']} | {e['geometric_mean_ratio']:.3f} | "
                     f"{_fmt(e.get('sd_log_ratio'), 4)} | {_fmt(e.get('half_width_n10'), 4)} | "
                     f"{_fmt(e.get('half_width_n20'), 4)} | "
                     f"{'n/a' if not bs else f'[{bs[0]:.3f}, {bs[1]:.3f}]'} |")
        L += ["", "With very few blocks the SD estimate is itself very uncertain; it is a planning value."]
    else:
        L.append("No block contains A0 together with another arm.")
    p = summary["projection_full_matrix"]
    L += ["", "## Projected runtime of the planned full matrix", "",
          f"Measured worst per-run overhead (database build, server start, generator start, "
          f"teardown): {p['max_overhead_s']:.1f} s. With {p['levels']} levels of "
          f"{p['warmup_s']} s warmup plus {p['measure_s']} s measurement, one run takes about "
          f"{p['per_run_s']:.0f} s and {p['runs']} runs about {p['total_h']:.2f} h. Planning estimate.",
          "", "## Degenerate cases and flags", ""]
    L += [f"- {d}" for d in degenerate] or ["- none"]
    if figs:
        L += ["", "## Figure", "",
              "![Exploratory goodput versus concurrency: one line per run, colour by arm, both axes "
              "logarithmic. Units: validated responses per second against open connections.]"
              "(figures/goodput_vs_concurrency.png)"]
    md_path = os.path.join(results_dir, "report.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    summary["report_md"] = md_path
    return summary


def has_yaml_title(md_path: str) -> bool:
    """True when the Markdown file opens with a YAML block that sets a title."""
    with open(md_path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---\n"):
        return False
    end = text.find("\n---", 4)
    return end > 0 and any(line.startswith("title:") for line in text[4:end].splitlines())


def escape_star_notation(source: str) -> str:
    """Escape the asterisk of the notation G* (peak goodput), so that two G* in one
    paragraph are not read as an emphasis span (M6 visual inspection). Source files
    stay unchanged; the escape is applied to the text handed to pandoc."""
    return re.sub(r"(?<=G)\*(?!\*)", r"\\*", source)


def build_pdf(md_path: str, pdf_path: str, typ_path: str | None = None) -> tuple[bool, str]:
    """pandoc Markdown -> Typst (mainfont workaround from M0), compiled with the typst
    Python package. Returns (ok, message); never fabricates a PDF on failure.

    A file without a YAML title (experiment reports, the supplementary file) has its
    leading level-1 heading promoted to the document title (M6), so that the PDF title
    metadata is set. With typ_path, the intermediate Typst file is compiled beside the
    Markdown source (Typst requires it inside the project root, and relative image
    paths resolve from it) and then moved to typ_path; otherwise it stays beside the PDF."""
    cwd = os.path.dirname(os.path.abspath(md_path))
    if typ_path:
        stem = os.path.splitext(os.path.basename(md_path))[0]
        typ = os.path.join(cwd, f".build-{stem}-{os.getpid()}.typ")
    else:
        typ = pdf_path[: -len(".pdf")] + ".typ"
    # --wrap=none (M6): with pandoc's default wrapping, a sentence such as "excludes 1. ..."
    # could start a Typst source line with "1. " and turn into a numbered list.
    # The header keeps narrow table cells unjustified and lets long tables break across
    # pages (M6 visual inspection).
    header = typ + ".header"
    with open(header, "w", encoding="utf-8") as fh:
        fh.write("#show table: set par(justify: false)\n"
                 "#show figure: set block(breakable: true)\n")
    args = [PANDOC, "-f", "markdown", "-s", "-t", "typst", "--wrap=none",
            "--include-in-header", header,
            "-V", "mainfont=Libertinus Serif", "-o", os.path.abspath(typ)]
    with open(md_path, encoding="utf-8") as fh:
        source = escape_star_notation(fh.read())
    if not has_yaml_title(md_path):
        # Leading HTML comments (the SPDX header) are not rendered; dropping them lets
        # pandoc promote the first level-1 heading to the title.
        source = re.sub(r"\A(\s*<!--.*?-->\s*)+", "", source, flags=re.S)
        args.append("--shift-heading-level-by=-1")
    r = subprocess.run(args, input=source, capture_output=True, text=True, cwd=cwd)
    os.remove(header)
    if r.returncode != 0:
        return False, f"pandoc failed: {r.stderr.strip()[:500]}"
    code = (f"import typst; typst.compile({os.path.abspath(typ)!r}, "
            f"output={os.path.abspath(pdf_path)!r}, root={cwd!r})")
    r = subprocess.run([TYPST_PY, "-c", code], capture_output=True, text=True, cwd=cwd)
    if typ_path:
        os.replace(typ, typ_path)
    if r.returncode != 0:
        return False, f"typst failed: {r.stderr.strip()[-500:]}"
    return True, pdf_path
