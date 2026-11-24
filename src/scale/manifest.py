# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Run provenance: git revision, versions, platform, CPU, power state, load, idle probe."""

from __future__ import annotations

import datetime as _dt
import importlib.metadata
import os
import platform
import resource
import sqlite3
import subprocess
import sys
from typing import Any

import psutil

from . import __version__


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _run(cmd: list[str], cwd: str | None = None) -> str | None:
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def git_info(repo: str) -> dict[str, Any]:
    rev = _run(["git", "rev-parse", "HEAD"], cwd=repo)
    status = _run(["git", "status", "--porcelain"], cwd=repo)
    return {"revision": rev, "dirty": None if status is None else bool(status)}


def versions() -> dict[str, str | None]:
    out: dict[str, str | None] = {"scale": __version__, "python": platform.python_version(),
                                  "sqlite": sqlite3.sqlite_version}
    for pkg in ("numpy", "psutil", "jsonschema", "matplotlib"):
        try:
            out[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            out[pkg] = None
    return out


def platform_info() -> dict[str, Any]:
    return {"system": platform.system(), "release": platform.release(),
            "macos": platform.mac_ver()[0] or None, "machine": platform.machine(),
            "python_implementation": platform.python_implementation(),
            "python_executable": os.path.basename(sys.executable)}


def cpu_info() -> dict[str, Any]:
    brand = _run(["sysctl", "-n", "machdep.cpu.brand_string"]) if sys.platform == "darwin" else platform.processor()
    return {"brand": brand, "logical_cpus": psutil.cpu_count(logical=True),
            "physical_cpus": psutil.cpu_count(logical=False),
            "memory_bytes": psutil.virtual_memory().total}


def power_state() -> str | None:
    if sys.platform != "darwin":
        return None
    out = _run(["pmset", "-g", "batt"])
    return out.splitlines()[0] if out else None


def idle_probe(threshold_pct: float, enforced: bool, interval_s: float = 1.0) -> dict[str, Any]:
    """System-wide CPU over a short probe (protocol section 8)."""
    pct = psutil.cpu_percent(interval=interval_s)
    return {"cpu_pct": pct, "threshold_pct": threshold_pct, "passed": pct < threshold_pct,
            "enforced": enforced, "interval_s": interval_s}


def runner_peak_rss_mb() -> float:
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return (ru if sys.platform == "darwin" else ru * 1024) / 1e6


def load_average() -> list[float]:
    return [round(x, 2) for x in os.getloadavg()]
