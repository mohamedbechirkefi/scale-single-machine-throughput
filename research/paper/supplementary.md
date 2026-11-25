<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Supplementary material

Companion to `research/paper/manuscript.md` (draft of 2026-11-25, M4). Independent research preprint draft, not peer-reviewed. Every number is listed in `research/publication/artifact_manifest.json`.

## S1. Complete experimental matrix

| Experiment | Label | Matrix | Runs | Status |
|---|---|---|---|---|
| EXP-001 | Confirmatory | SCALE generator on `GET /null`, c in {1, 8, 32}, 2 s warmup + 10 s window, 5 repeats, ab cross-check | 5 of 5 ok | Complete |
| EXP-001 supplements | Exploratory | Stall check (open and closed loop, 1 repeat each); 4 generator processes (3 repeats); timer resolution | 2 + 3 runs | Complete |
| PILOT-QUIET | Exploratory (rule input only) | 5 arms x 11 levels (c 1 to 1024) x 5 blocks, seed 20261126 | 25 of 25 ok | Used only through pilot-rule-1.0 |
| EXP-002 | Confirmatory | 5 arms x 10 levels (c 1 to 512) x 10 blocks, 5 s + 15 s per level, seed 20261124 | 62 runs: 50 accepted, 12 excluded by the idle probe | 50 of 50 cells |
| EXP-003 | Confirmatory (planned) | 5 arms x 8 open-loop rungs x 5 blocks | 0 | Not run: four parameters unset, pending the owner |
| EXP-004 | Confirmatory (optional) | 2 variants x 5 arms x 5 blocks | 0 | Not run: pending the owner's decision |
| M4-REANALYSIS-20261125 | Exploratory | Read-only re-analysis of the recorded runs (X1 to X13; X13 asks SQLite for query plans, no timing) | 0 new runs | Complete |

Earlier exploratory runs made on a loaded machine before the freeze (J-0002 to J-0009, `results/exploratory/`) are kept and are never used as findings.

## S2. Extended tables

### S2.1 EXP-002 median goodput and p99 latency per level (10 blocks)

Goodput in requests per second; p99 in milliseconds (closed loop, from send to full response). Source: `research/experiments/EXP-002/analysis.json`, `descriptives.<arm>.per_level`.

| c | A0 G | A0 p99 | A1 G | A1 p99 | A2 G | A2 p99 | A3 G | A3 p99 | A4 G | A4 p99 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 54.1 | 19.83 | 90.7 | 19.66 | 21282.5 | 0.08 | 50.0 | 21.36 | 54.1 | 19.92 |
| 2 | 79.6 | 28.40 | 157.2 | 26.83 | 28131.4 | 0.11 | 93.0 | 25.68 | 79.7 | 27.77 |
| 4 | 114.6 | 45.32 | 265.1 | 41.87 | 18795.3 | 0.41 | 155.2 | 29.90 | 115.3 | 43.69 |
| 8 | 75.8 | 110.68 | 177.1 | 115.20 | 10356.6 | 1.64 | 290.7 | 34.98 | 75.7 | 111.70 |
| 16 | 60.8 | 308.00 | 150.6 | 354.08 | 9889.1 | 3.51 | 537.4 | 49.03 | 76.0 | 412.03 |
| 32 | 60.8 | 722.26 | 155.5 | 808.87 | 9800.4 | 7.18 | 709.3 | 67.93 | 68.5 | 1883.66 |
| 64 | 61.2 | 1621.90 | 164.8 | 1240.74 | 9575.9 | 14.58 | 1017.5 | 75.31 | 68.4 | 2417.74 |
| 128 | 61.1 | 3384.55 | 167.1 | 2577.76 | 9151.2 | 30.01 | 1018.1 | 143.59 | 69.4 | 2424.63 |
| 256 | 58.5 | 8711.67 | 161.3 | 7029.35 | 8462.2 | 64.67 | 1022.0 | 276.48 | 72.1 | 2357.89 |
| 512 | 55.0 | 8805.94 | 166.3 | 11127.86 | 6968.7 | 164.53 | 1020.3 | 545.98 | 57.9 | 3321.72 |

A2's levels c = 1, 2 and 4 are generator-limited in every block. A4's p99 from c = 32 includes the fast 503 responses only through the error count; goodput counts validated 200 responses only.

### S2.2 Error composition over the measurement windows (EXP-002, accepted runs, X1)

| Arm | Attempts | Validated 200 | HTTP 500 | HTTP 503 | Transport errors | Invalid bodies |
|---|---|---|---|---|---|---|
| A0 | 106824 | 101614 | 271 | 0 | 4939 | 0 |
| A1 | 251460 | 247960 | 1162 | 0 | 2338 | 0 |
| A2 | 19801735 | 19801632 | 0 | 0 | 103 | 0 |
| A3 | 887404 | 887404 | 0 | 0 | 0 | 0 |
| A4 | 11107543 | 109918 | 0 | 10996866 | 759 | 0 |

HTTP 500 first appears at c = 64 or 128 for A0 and at c = 32 or 64 for A1; transport errors appear only at c of 256 and above. The server's own count of internal errors, which includes warmups, is 334 (A0) and 1400 (A1). Every error level lies above every included arm's peak.

### S2.3 Mechanism descriptives (X2, medians over 10 blocks)

| Arm | c | Server CPU (cores) | Server CPU per validated response (ms) |
|---|---|---|---|
| A0 | 1 | 0.991 | 18.3 |
| A0 | 4 | 3.812 | 33.3 |
| A0 | 16 | 9.708 | 159.7 |
| A0 | 512 | 9.782 | 178.0 |
| A3 | 1 | 0.918 | 18.4 |
| A3 | 64 | 1.553 | 1.53 |
| A3 | 512 | 1.527 | 1.50 |
| A2 | 2 | 1.206 | 0.043 |
| A2 | 8 | 2.778 | 0.268 |

System time is 0.89 of A0's server CPU, 0.45 of A3's. A3's mean batch size is 15.97. A1's median hit ratio is 0.59.

## S3. Configurations and hashes

| Item | Path | SHA-256 (prefix) |
|---|---|---|
| Study protocol (frozen v1.0, after AM-5) | `research/protocol.md` | 5ea0c481 |
| EXP-001 protocol | `research/experiments/EXP-001/protocol.md` | 4af93dc2 |
| EXP-002 protocol | `research/experiments/EXP-002/protocol.md` | 8da83b07 |
| EXP-003 protocol | `research/experiments/EXP-003/protocol.md` | 82846c72 |
| EXP-004 protocol | `research/experiments/EXP-004/protocol.md` | f3c62a26 |
| EXP-001 config | `experiments/EXP-001.json` | 9f7b8d15 |
| EXP-002 config (completed by the pre-stated rules) | `experiments/EXP-002.json` | 09bf457c |
| Quiet-pilot config | `experiments/pilot-quiet.json` | ad73ae6e |
| EXP-002 run config hash (in every run) | `results/raw/EXP-002/EXP-002-M3/config.json` | 439fce64 |
| Raw-output checksums, EXP-001 | `results/raw/EXP-001/SHA256SUMS` | 8945e816 |
| Raw-output checksums, EXP-002 | `results/raw/EXP-002/SHA256SUMS` | de0e7fd1 |
| Raw-output checksums, PILOT-QUIET | `results/raw/PILOT-QUIET/SHA256SUMS` | 142966d6 |

Full hashes are in `research/freeze.json` and `research/publication/artifact_manifest.json`. Fixed design values (not measurements): N = 200,000 rows, 256-byte payload, Zipf exponent 0.99, 2 % writes, dataset seed 20261124, A1 capacity 10 % of N, A3 window 1 ms or 32 requests, A4 W = 8 and Q = 16, 5 s warmup and 15 s window, idle-probe threshold 15 %, generator-limited thresholds 50 % of C_gen and 85 % of generator cores, SLO 50 ms and 1 % errors, practical band [0.95, 1.05].

## S4. Robustness results

| Check | A1 | A3 | A4 | Source |
|---|---|---|---|---|
| Frozen primary, 98.75 % | 2.337 (2.254 to 2.435) | 9.005 (8.921 to 9.093) | 1.015 (1.000 to 1.030) | analysis.json |
| S3 (frozen sensitivity), 98.75 % | 2.606 (2.473 to 2.775) | 12.452 (12.012 to 12.936) | 1.161 (1.111 to 1.209) | analysis.json |
| G* over c up to 256 (X4) | | 8.99 (8.91 to 9.08) | | summary.json |
| Without blocks 8 and 9 (X5) | 2.37 (2.29 to 2.47) | 9.00 (8.90 to 9.11) | 1.018 (1.002 to 1.035) | summary.json |
| Closed-loop latency bound (X12) | 2.50 (2.26 to 2.92) | 3.95 (3.06 to 5.01) | 1.086 (1.001 to 1.248) | summary.json |
| Quiet pilot, unfiltered, 5 blocks (X10) | 2.29 | 8.72 | 1.002 | summary.json |

Rows other than the first are exploratory except S3, which is the frozen sensitivity analysis. A2 under the alternatives: S3 160.93 (155.28 to 166.99); unfiltered 246.8 (243.4 to 250.2); levels not flagged 90.8 (90.0 to 91.8); closed-loop latency bound 264.2 (243.5 to 304.7); pilot 242.1. Pairwise (X3, exploratory): R_A3 / R_A1 3.85 (3.72 to 3.99); R_A1 / R_A4 2.30 (2.24 to 2.37); R_A3 / R_A4 8.87 (8.74 to 8.98); under the latency bound R_A3 / R_A1 1.58 (1.25 to 1.92). Drift (frozen): -0.00039 per run (-0.00073 to 0.00010); -0.0030 per position (-0.0088 to 0.0016).

## S5. Experiment report links

- EXP-001: `research/experiments/EXP-001/report.md`
- EXP-002: `research/experiments/EXP-002/report.md`
- EXP-003 (not run): `research/experiments/EXP-003/report.md`
- EXP-004 (not run): `research/experiments/EXP-004/report.md`
- M4 re-analysis (exploratory): `results/exploratory/M4-REANALYSIS-20261125/summary.json`, journal J-0014
- Evidence audit: `research/publication/evidence_audit_M4.md`; second review pass: `research/publication/review_pass_2.md`

## S6. Deviations and owner decisions

| Item | Kind | Status |
|---|---|---|
| AM-1 to AM-4 (A4 queue 16, index wins by design, sweep extension, seed count after the pilot) | Amendments before the freeze | Owner-approved 2026-11-24 (D-009) |
| AM-5 (C_gen = median of the EXP-001 run ceilings) | Rule fixed before data | Owner-approved 2026-11-24 (D-011) |
| c_max = 512, n = 10, C_gen = 27919.4 | Application of pre-stated rules | D-013; not an amendment |
| D-012 analysis readings (generator-limited run G* undefined; arm-level exclusion) | Assistant reading before data | **Pending the owner** |
| 12 idle-probe exclusions, 7 cells re-attempted at the end | Protocol section 10 as written | D-014 |
| EXP-001 supplements run as exploratory | Outside the frozen config | D-014 |
| EXP-003 not run (connection count, seed, rung split, A2's centre unset) | Planned experiment not executed | **Pending the owner** |
| EXP-004 not run | Optional experiment | **Pending the owner** |
| M4 re-analysis X1 to X13 | Exploratory, chosen after the results were known; no new timing measurement | D-015 |

## S7. Changes made after the second review pass

Listed in `research/publication/review_pass_2.md`, section 3.
