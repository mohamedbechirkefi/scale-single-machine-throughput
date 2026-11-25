<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# M4-REANALYSIS-20261125: exploratory re-analysis of recorded runs

| Field | Value |
|---|---|
| Label | **Exploratory.** Not part of any frozen analysis; no frozen verdict is changed or replaced. Checks chosen at M4, after the confirmatory results were known. |
| Date | 2026-11-25 (M4) |
| What ran | `scripts/m4_exploratory_confounders.py`, a read-only re-analysis. No server, load generator or timing code was executed and no timing measurement was taken (the machine was shared with other agents during M4). X13 asks SQLite for query plans on a temporary 100-row database. |
| Inputs | `results/raw/EXP-002/EXP-002-M3` (50 accepted runs), `results/raw/PILOT-QUIET/PILOT-QUIET-M3` (25 runs), `results/raw/EXP-001/EXP-001-M3` and `GP4-M3`. All 219 files listed in the three `SHA256SUMS` files were verified first; 0 mismatches. |
| Output | `summary.json` in this directory |
| Bootstrap | Frozen settings reused: 10,000 resamples, seed 20261124, percentile intervals |
| Journal | J-0014 |

## Checks and results

| Id | Question (competing explanation) | Result |
|---|---|---|
| X1 | Are errors correctness failures? | No invalid body in any accepted run. Errors are transport errors (only at c = 256 and 512; A2 103 at c = 256; A4 759 at c = 512) and HTTP 500 from the server's generic exception handler (A0 from c = 64 or 128, A1 from c = 32 or 64; 271 and 1162 in measurement windows). The exception type is not logged, so the cause of the 500s is not identified; the 5 s SQLite busy timeout is a candidate only. |
| X2 | What limits each arm? | A0: server CPU per validated response 18.3 ms at c = 1, 33.3 ms at c = 4, 159.7 ms at c = 16 and 178.0 ms at c = 512, with all 10 cores busy and a system-time share of 0.89. A3: mean batch size 15.97, server CPU about 1.5 cores at the plateau. A1: median hit ratio 0.59 (whole run); bound 1 / (1 - h) = 2.44. Little's-law check (c against attempts per second times p50) is 0.89 to 1.05 for A0, A2 and A3 at the levels without errors; it is not interpretable for A1 and A4, whose latency is bimodal. |
| X3 | Are the included arms separable? (not in the frozen analysis) | R_A3 / R_A1 = 3.85, 98.75 % [3.72, 3.99]; R_A1 / R_A4 = 2.30 [2.24, 2.37]; R_A3 / R_A4 = 8.87 [8.74, 8.98]. |
| X4 | Is A3's G* truncated at c = 512? | A3 peaked at 512 in blocks 0, 2 and 7, where G(512) / G(256) was 1.016, 1.001 and 1.004. A3's goodput is on a plateau from c = 64 (per-block range at most 2.4 %). With G* over c <= 256, R_A3 = 8.99 [8.91, 9.08]. |
| X5 | Do the re-attempted, time-shifted blocks 8 and 9 matter? | Without them (8 blocks): R_A1 2.37 [2.29, 2.47], R_A3 9.00 [8.90, 9.11], R_A4 1.018 [1.002, 1.035], still inside [0.95, 1.05]. |
| X6 | Is the A4 null structural? | A4 / A0 goodput per level: 1.001, 1.002, 1.014 at c = 1, 2, 4 and 0.997 at c = 8, with no 503 below c = 32; 1.26 at c = 16; 1.05 to 1.24 from c = 32. Both arms peak at c = 4, below W = 8, where the limiter does not engage. |
| X7 | Did the 85 % generator-CPU criterion matter? | Maximum generator CPU at any arm's peak level: A2 0.48, A3 0.10, others at most 0.011. No arm reaches 0.85. |
| X8 | What sets A2's peak? | A2's median G* is 28131.4 rps, 1.008 times the 27919.4 rps ceiling; flagged levels c = 1, 2, 4 (threshold 13959.7 rps). Four generator processes on the null endpoint gave 27159.1, 27341.7 and 27079.9 rps (J-0011), no more than one. A2 falls to 10356.6 rps at c = 8 while its server CPU rises from 1.21 to 2.78 cores. |
| X9 | Background load as a confounder? | Over 50 runs, Spearman correlation of arm-centred log G* with the idle probe (1.9 % to 10.0 %) is 0.20, with the 1-min load average 0.007. |
| X10 | Does the pilot agree? (pilot never pooled) | Quiet pilot, unfiltered within-block geometric mean R over 5 blocks: A1 2.29, A3 8.72, A4 1.002, A2 242.1. |
| X11 | EXP-001 shortfall at c = 1 | SCALE/ab ratios at c = 1: 0.924 to 0.951, all inside [0.9, 1.1]. |
| X12 | Closed-loop latency-bounded goodput (not EXP-003; no coordinated-omission correction) | Highest G(c) with p99 <= 50 ms and errors <= 1 %: A1 2.50 [2.26, 2.92], A3 3.95 [3.06, 5.01], A4 1.086 [1.001, 1.248], A2 264.2 [243.5, 304.7] (unfiltered); R_A3 / R_A1 1.58 [1.25, 1.92]. |
| X13 | Does the batched lookup share one scan? (no timing) | SQLite 3.43.1, study schema, 100 rows: without the index both `WHERE sku = ?` and `WHERE sku IN (16 keys)` plan as `SCAN items`; with the index both plan as `SEARCH items USING INDEX ix_items_sku (sku=?)`. |

## Interpretation (exploratory)

None of these checks contradicts a frozen verdict. They narrow three of them:

- **A4 null.** It is structural: the baseline peaks at c = 4, where the admission limit (W = 8) is inactive.
- **A3 effect.** It is an amortisation of the baseline's full scan, so it is conditional on that baseline. Its size relative to A1 depends on the summary metric.
- **A2 exclusion.** The excluded peak sits on a ceiling that the 4-process check places in the shared server and loopback path rather than in the generator alone.

Whether to keep the D-012 reading that excludes A2 is the owner's decision and is pending (owner, 2026-11-25, "Next", leaves it open).
