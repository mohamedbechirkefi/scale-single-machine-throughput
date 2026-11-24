# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Pre-stated generator-ceiling rule (research/protocol.md section 15, AM-5,
owner-approved 2026-11-24 before any confirmatory data).

The generator ceiling used by EXP-002 (``generator_ceiling_rps``, the C_gen of
EXP-001 item 21) is the median of the EXP-001 ceiling runs. A ceiling run is one
EXP-001 repeat: the SCALE generator against ``GET /null`` over the frozen ladder
c in {1, 8, 32}. Its ceiling is its peak goodput over that ladder. The rule reads
EXP-001 runs only, never a study arm, so it cannot tune the primary contrast.
"""

from __future__ import annotations

import statistics
from typing import Any, Sequence

from . import metrics as m

RULE_VERSION = "ceiling-rule-1.0"
EXP001_ID = "EXP-001"
EXP001_LADDER = (1, 8, 32)
EXP001_REPEATS = 5


class CeilingRuleError(ValueError):
    """The EXP-001 runs do not meet the preconditions of the rule; no value is set."""


def run_ceiling(res: dict[str, Any]) -> float:
    """Ceiling of one EXP-001 run: peak goodput over its concurrency levels."""
    return m.peak_goodput([(lv["concurrency"], lv["goodput_rps"]) for lv in res["levels"]])[0]


def resolve_ceiling(runs: Sequence[tuple[dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    """Apply the rule to validated EXP-001 runs (as returned by ``report.load_runs``).

    Preconditions (otherwise CeilingRuleError and no value is set): experiment id
    EXP-001, label confirmatory, endpoint null, the frozen ladder 1, 8, 32, every run
    status ok with the idle probe enforced and passed, exactly five repeats (one per
    block)."""
    by_block: dict[int, float] = {}
    for res, man in runs:
        rid = res.get("run_id")
        if res.get("experiment_id") != EXP001_ID:
            raise CeilingRuleError(f"{rid}: not an {EXP001_ID} run")
        if res.get("label") != "confirmatory":
            raise CeilingRuleError(f"{rid}: only the confirmatory EXP-001 runs set the ceiling")
        if res.get("endpoint") != "null":
            raise CeilingRuleError(f"{rid}: endpoint {res.get('endpoint')!r}, GET /null required")
        if res.get("status") != "ok":
            raise CeilingRuleError(f"{rid}: status {res.get('status')}")
        probe = man.get("idle_probe") or {}
        if not (probe.get("enforced") and probe.get("passed")):
            raise CeilingRuleError(f"{rid}: idle probe not enforced or not passed")
        if tuple(lv["concurrency"] for lv in res["levels"]) != EXP001_LADDER:
            raise CeilingRuleError(f"{rid}: ladder differs from {EXP001_LADDER}")
        if res["block"] in by_block:
            raise CeilingRuleError(f"{rid}: duplicate repeat for block {res['block']}")
        by_block[res["block"]] = run_ceiling(res)
    if len(by_block) != EXP001_REPEATS:
        raise CeilingRuleError(f"{len(by_block)} ceiling runs found, {EXP001_REPEATS} required")
    ceilings = [by_block[b] for b in sorted(by_block)]
    median = statistics.median(ceilings)
    if median <= 0:
        raise CeilingRuleError("median ceiling is 0")
    return {"rule_version": RULE_VERSION, "generator_ceiling_rps": median,
            "run_ceilings_rps": ceilings, "n_runs": len(ceilings)}
