# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Command line: ``scale smoke | run | report | test``.

``run`` refuses a confirmatory config unless the study protocol records an owner
freeze, ``research/freeze.json`` lists the protocol, the experiment protocol and the
config file with matching SHA-256 values, and no value of the experiment is still
deferred (G-FREEZE). ``resolve-pilot`` applies the pre-stated quiet-pilot rule;
``resolve-ceiling`` applies the pre-stated generator-ceiling rule (AM-5).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys

from .config import ConfigError, ExperimentConfig, load_config

EXIT_REFUSED = 3


def repo_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def freeze_status(cfg: ExperimentConfig, root: str, config_path: str | None = None) -> tuple[bool, str]:
    """Delegates to ``scale.freeze.check`` (protocol FROZEN, freeze record, protocol and
    config hashes, deferred values)."""
    from . import freeze

    return freeze.check(cfg, config_path, root)


def _default_out(cfg: ExperimentConfig, root: str) -> str:
    stamp = _dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    sub = "exploratory" if cfg.label == "exploratory" else "confirmatory"
    return os.path.join(root, "results", sub, f"{cfg.experiment_id}-{stamp}")


def cmd_run(config_path: str, out: str | None, argv: list[str]) -> int:
    root = repo_root()
    from . import freeze

    try:  # a deferred confirmatory config is refused before validation (its values are unset)
        with open(config_path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        raw = None
    if isinstance(raw, dict) and raw.get("label") == "confirmatory":
        why = freeze.deferred_reason(str(raw.get("experiment_id")), root)
        if why is not None:
            print(f"REFUSED: {raw.get('experiment_id')} is confirmatory and {why}.", file=sys.stderr)
            return EXIT_REFUSED
    try:
        cfg = load_config(config_path)
    except (ConfigError, OSError, TypeError) as exc:
        print(f"invalid config: {exc}", file=sys.stderr)
        return 2
    if cfg.label == "confirmatory":
        ok, why = freeze_status(cfg, root, config_path)
        if not ok:
            print(f"REFUSED: {cfg.experiment_id} is confirmatory and {why}.", file=sys.stderr)
            return EXIT_REFUSED
    from .runner import run_experiment

    out_dir = out or _default_out(cfg, root)
    batch = run_experiment(cfg, out_dir, root, ["scale"] + argv)
    print(f"results: {out_dir}")
    failed = [r for r in batch["runs"] if r["status"] != "ok"]
    print(f"runs: {len(batch['runs'])}, not ok: {len(failed)}, runtime {batch['runtime_s']:.1f} s")
    return 0


def cmd_report(results_dir: str, pdf: bool, levels: int, warmup: float, measure: float, runs: int) -> int:
    from .report import build_pdf, build_report

    try:
        summary = build_report(results_dir, levels, warmup, measure, runs)
    except Exception as exc:
        print(f"report failed (fail closed): {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(f"report: {summary['report_md']}")
    if pdf:
        ok, msg = build_pdf(summary["report_md"], os.path.join(results_dir, "report.pdf"))
        print(("pdf: " if ok else "pdf not built: ") + msg)
        return 0 if ok else 1
    return 0


def cmd_resolve_pilot(results_dir: str) -> int:
    from .pilotrule import PilotRuleError, resolve_pilot
    from .report import load_runs

    try:
        out = resolve_pilot(load_runs(results_dir))
    except (PilotRuleError, Exception) as exc:
        print(f"pilot rule not applicable (no value set): {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


def cmd_resolve_ceiling(results_dir: str) -> int:
    from .ceiling import CeilingRuleError, resolve_ceiling
    from .report import load_runs

    try:
        out = resolve_ceiling(load_runs(results_dir))
    except (CeilingRuleError, Exception) as exc:
        print(f"ceiling rule not applicable (no value set): {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "test":  # pass every remaining argument to pytest unchanged
        return subprocess.call([sys.executable, "-m", "pytest", *argv[1:]], cwd=repo_root())
    ap = argparse.ArgumentParser(prog="scale", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("smoke", help="exploratory smoke matrix (experiments/smoke.json)")
    s.add_argument("--config", default=None)
    s.add_argument("--out", default=None)
    r = sub.add_parser("run", help="run an experiment config (refuses confirmatory while unfrozen)")
    r.add_argument("config")
    r.add_argument("--out", default=None)
    p = sub.add_parser("report", help="tables, figures and optional PDF from a results directory")
    p.add_argument("results_dir")
    p.add_argument("--pdf", action="store_true")
    p.add_argument("--full-levels", type=int, default=7)
    p.add_argument("--full-warmup-s", type=float, default=5.0)
    p.add_argument("--full-measure-s", type=float, default=15.0)
    p.add_argument("--full-runs", type=int, default=50)
    q = sub.add_parser("resolve-pilot", help="apply the frozen quiet-pilot rule (protocol 7.1) to a pilot results directory")
    q.add_argument("results_dir")
    g = sub.add_parser("resolve-ceiling", help="apply the frozen generator-ceiling rule (AM-5) to an EXP-001 results directory")
    g.add_argument("results_dir")
    t = sub.add_parser("test", help="run the pytest suite")
    t.add_argument("pytest_args", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    if a.cmd == "smoke":
        path = a.config or os.path.join(repo_root(), "experiments", "smoke.json")
        cfg_label = load_config(path).label
        if cfg_label != "exploratory":
            print("REFUSED: smoke configs must be labelled exploratory", file=sys.stderr)
            return EXIT_REFUSED
        return cmd_run(path, a.out, argv)
    if a.cmd == "run":
        return cmd_run(a.config, a.out, argv)
    if a.cmd == "report":
        return cmd_report(a.results_dir, a.pdf, a.full_levels, a.full_warmup_s, a.full_measure_s, a.full_runs)
    if a.cmd == "resolve-pilot":
        return cmd_resolve_pilot(a.results_dir)
    if a.cmd == "resolve-ceiling":
        return cmd_resolve_ceiling(a.results_dir)
    if a.cmd == "test":
        return subprocess.call([sys.executable, "-m", "pytest", *a.pytest_args], cwd=repo_root())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
