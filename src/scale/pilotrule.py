# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Pre-stated rule that turns the quiet-machine pilot into the two EXP-002 values the
owner left open at the freeze (research/protocol.md section 7.1, frozen v1.0):

* the top of the concurrency sweep, c_max (amendment AM-3: extend beyond 64 until
  A1 and A3 peak inside the range), and
* the number of blocks n (amendment AM-4: set after a quiet-machine pilot).

The rule reads only the location of the A1 and A3 goodput peaks and the
between-block spread of log R. It never reads the size or sign of any arm's
effect, so the confirmatory contrast is not tuned. The pilot itself is
exploratory; its blocks are never pooled with EXP-002.
"""

from __future__ import annotations

import math
import statistics
from typing import Any, Sequence

from . import metrics as m

RULE_VERSION = "pilot-rule-1.0"
PILOT_EXPERIMENT_ID = "PILOT-QUIET"
PILOT_ARMS = ("A0", "A1", "A2", "A3", "A4")
PILOT_LADDER = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
PILOT_BLOCKS = 5
EXTENSION_CANDIDATES = (128, 256, 512, 1024)  # c_max is one of these
PEAK_ARMS = ("A1", "A3")
SD_TRIGGER = 0.07
N_LOW, N_HIGH = 10, 20


class PilotRuleError(ValueError):
    """The pilot does not meet the preconditions of the rule; no value is set."""


def choose_c_max(peak_cs: Sequence[int]) -> tuple[int, bool]:
    """Smallest candidate strictly above every observed A1/A3 peak location.
    Returns (c_max, truncated); truncated is True when even 1024 is not above the
    highest peak, in which case c_max = 1024 and G* of A1/A3 is reported as truncated."""
    if not peak_cs:
        raise PilotRuleError("no peak locations")
    worst = max(peak_cs)
    for cand in EXTENSION_CANDIDATES:
        if cand > worst:
            return cand, False
    return EXTENSION_CANDIDATES[-1], True


def choose_n(sd_by_arm: dict[str, float]) -> int:
    """n = 10 if every treatment arm's between-block SD of log R is <= 0.07, else n = 20."""
    if not sd_by_arm:
        raise PilotRuleError("no SD values")
    for arm, sd in sd_by_arm.items():
        if sd is None or not math.isfinite(sd) or sd < 0:
            raise PilotRuleError(f"invalid SD for {arm}: {sd!r}")
    return N_LOW if max(sd_by_arm.values()) <= SD_TRIGGER else N_HIGH


def _level_pairs(res: dict[str, Any], c_max: int | None = None) -> list[tuple[int, float]]:
    return [(lv["concurrency"], lv["goodput_rps"]) for lv in res["levels"]
            if c_max is None or lv["concurrency"] <= c_max]


def resolve_pilot(runs: Sequence[tuple[dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    """Apply the rule to validated pilot runs (as returned by ``report.load_runs``).

    Preconditions (otherwise PilotRuleError and no value is set): experiment id
    PILOT-QUIET, label exploratory, the full ladder 1..1024, exactly five blocks with
    all five arms each, every run status ok with the idle probe enforced and passed."""
    blocks: dict[int, dict[str, dict[str, Any]]] = {}
    for res, man in runs:
        rid = res.get("run_id")
        if res.get("experiment_id") != PILOT_EXPERIMENT_ID:
            raise PilotRuleError(f"{rid}: not a {PILOT_EXPERIMENT_ID} run")
        if res.get("label") != "exploratory":
            raise PilotRuleError(f"{rid}: the pilot must be labelled exploratory")
        if res.get("status") != "ok":
            raise PilotRuleError(f"{rid}: status {res.get('status')}; repeat the whole pilot")
        probe = man.get("idle_probe") or {}
        if not (probe.get("enforced") and probe.get("passed")):
            raise PilotRuleError(f"{rid}: idle probe not enforced or not passed (quiet machine required)")
        if tuple(lv["concurrency"] for lv in res["levels"]) != PILOT_LADDER:
            raise PilotRuleError(f"{rid}: ladder differs from {PILOT_LADDER}")
        arms = blocks.setdefault(res["block"], {})
        if res["arm"] in arms:
            raise PilotRuleError(f"{rid}: duplicate arm in block {res['block']}")
        arms[res["arm"]] = res
    if len(blocks) != PILOT_BLOCKS:
        raise PilotRuleError(f"{len(blocks)} blocks found, {PILOT_BLOCKS} required")
    for b, arms in blocks.items():
        if set(arms) != set(PILOT_ARMS):
            raise PilotRuleError(f"block {b} has arms {sorted(arms)}, all of {PILOT_ARMS} required")

    peaks = {arm: [m.peak_goodput(_level_pairs(blocks[b][arm]))[1] for b in sorted(blocks)]
             for arm in PEAK_ARMS}
    c_max, truncated = choose_c_max([c for cs in peaks.values() for c in cs])

    log_r: dict[str, list[float]] = {a: [] for a in PILOT_ARMS if a != "A0"}
    for b in sorted(blocks):
        g0 = m.peak_goodput(_level_pairs(blocks[b]["A0"], c_max))[0]
        if g0 <= 0:
            raise PilotRuleError(f"block {b}: A0 peak goodput is 0")
        for arm in log_r:
            gj = m.peak_goodput(_level_pairs(blocks[b][arm], c_max))[0]
            if gj <= 0:
                raise PilotRuleError(f"block {b}: {arm} peak goodput is 0")
            log_r[arm].append(math.log(gj / g0))
    sd = {arm: statistics.stdev(v) for arm, v in log_r.items()}
    n = choose_n(sd)
    ladder = [c for c in PILOT_LADDER if c <= c_max]
    return {"rule_version": RULE_VERSION, "c_max": c_max, "truncated_at_cap": truncated,
            "concurrency": ladder, "blocks": n, "peak_concurrency": peaks,
            "sd_log_ratio": sd, "sd_trigger": SD_TRIGGER, "n_pilot_blocks": len(blocks)}
