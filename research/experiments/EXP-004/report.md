<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# EXP-004 report: workload sensitivity (optional, not run)

| Field | Value |
|---|---|
| Status | **Optional; not run** at M3 (2026-11-25). No data exist. |
| Protocol | `research/experiments/EXP-004/protocol.md` (frozen v1.0, sha256 f3c62a26...) |
| Decision | D-014 |

## 1. Hypothesis

H0: the top arm under variant V1 (N = 10,000) and under variant V2 (uniform keys) equals the EXP-002 top arm. H1: it differs.

## 2. Why it did not run

The protocol marks EXP-004 optional. Its config was "written once c_max is resolved" and was never frozen: `research/freeze.json` lists it as not yet configured, and its block seeds ("distinct from EXP-002") are not set. The M3 brief allows an optional experiment to run only with a frozen config.

## 3. Verdict

None. The EXP-002 result is not tested against other table sizes or key skews. Note also that the EXP-002 top arm is unresolved (A2 excluded), which H0 depends on.

## 4. Needed from the owner

Decide whether EXP-004 runs. If it does, approve a config: c_max = 512 from the pilot rule, 5 blocks per variant, and a study seed.

## 5. Owner answer (2026-11-26)

Owner, 2026-11-26, decision sheet: EXP-004 is recorded as not run; it is to run later, after the owner sets its parameters.
