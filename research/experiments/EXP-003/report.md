<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# EXP-003 report: open-loop SLO goodput (not run)

| Field | Value |
|---|---|
| Status | **Not run** at M3 (2026-11-25). No data exist. |
| Protocol | `research/experiments/EXP-003/protocol.md` (frozen v1.0, sha256 82846c72...) |
| Decision | D-014 |

## 1. Hypothesis

H0: the arm ranking by open-loop SLO goodput equals the EXP-002 ranking. H1: it differs.

## 2. Why it did not run

`research/freeze.json` lists EXP-003 as not yet configured. Its ladder is to be "fixed from EXP-002 results before it runs". The frozen text fixes the ladder rule (8 geometric rungs from 10 % to 150 % of each arm's EXP-002 median G*), 5 blocks, the 50 ms SLO and a 1 % error limit. It does **not** fix:

- the open-loop connection count (the runner needs one),
- the study seed,
- the warmup and measurement split of the roughly 20 s rung,
- which G* centres A2's ladder: A2's G* is generator-limited in EXP-002, and 150 % of its median G* (about 42,000 rps) is above the generator ceiling.

These would have to be chosen after EXP-002 output exists. Under the M3 brief they are not chosen by the assistant.

## 3. Deviation

Planned sensitivity experiment not executed. Nothing was run, so no result is reported.

## 4. Verdict

None. The EXP-002 closed-loop ranking is untested against an open-loop load model (limitation 17).

## 5. Needed from the owner

Values for the four gaps above, recorded as a dated amendment, then a frozen config.

## 6. Owner answer (2026-11-26)

Owner, 2026-11-26, decision sheet: EXP-003 is recorded as not run; it is to run later, after the owner sets the four parameters above (a G-FREEZE step, then a quiet-machine run).
