<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# EXP-002 report: one-factor-at-a-time comparison, closed-loop concurrency sweep (primary)

| Field | Value |
|---|---|
| Status | Complete (confirmatory), M3, 2026-11-25. Planned matrix complete: 50 of 50 cells. |
| Protocol | `research/experiments/EXP-002/protocol.md` (frozen v1.0, sha256 8da83b07...); study protocol sha256 5ea0c481... |
| Config | `experiments/EXP-002.json` (sha256 09bf457c...), completed by the pre-stated rules (D-013): blocks 10, c in {1, 2, 4, ..., 512}, generator ceiling 27919.4 rps |
| Runs | 62 runs in `results/raw/EXP-002/EXP-002-M3` (50 accepted, 12 excluded by the idle probe and re-attempted); hashes in `results/raw/EXP-002/SHA256SUMS` |
| Revision | `3fb0c66` (clean tree in every manifest); dataset sha256 7a0c2b88f5e3... (matches `data/manifest.json`) |
| Analysis | `scale analyse EXP-002` (analysis-1.0, committed before any EXP-002 output, D-012) -> `analysis.json`, `metrics.csv`, `figures/exp002_goodput.*`, `figures/exp002_ratios.*` |
| Journal | J-0013 |

## 1. Hypotheses

For j in {A1, A2, A3, A4}, H0_j: R_j = 1, where R_j = G*_j / G*_A0 within a block. The test is nondirectional, with Bonferroni-adjusted 98.75 % intervals. Recorded expectations: R_A1, R_A2, R_A3 > 1; A4 indeterminate; A2 largest by design (AM-2). A dominance claim requires every R_t / R_k interval of the top arm to exclude 1.

## 2. What was run

- **Matrix.** 5 arms x 10 concurrency levels x 10 blocks. Each run had a fresh server and database, arm order was seeded within each block, and each level had a 5 s warmup and a 15 s window. One generator process. Jobs ran under `nice -n 10`.
- **Timing.** 03:44:21Z to 06:40:02Z, 10540.9 s, about 207 to 220 s per accepted run (206.9 to 219.7 s; corrected at M4, was printed as 207 to 216).
- **Quiet machine.** Checked before the start (probes 3.8, 3.1, 5.1 %; `results/raw/quiet-checks-exp002.jsonl`). The probe was enforced per run: accepted runs 1.9 % to 10.0 %. The 1-min load average at run start was 1.9 to 142; the high values come from the previous run's own threads. AC power throughout.

## 3. Deviations

- **Idle-probe exclusions.** 12 runs were excluded by the idle probe (16.2 % to 35.4 %) in one burst from 06:15:22Z to 06:15:34Z. The source was not identified. The runner does not wait between attempts, so the burst also used the first re-attempt of five cells.
- **Re-attempts.** As protocol section 10 requires, the cells were re-attempted at the end of the sequence, at most twice per cell. All 7 affected cells (block 8: A3, A4; block 9: all arms) completed, so **no cell is missing**. The excluded files are kept. These cells are paired with their block in request sequence, not in time (D-014).
- No other deviation. Protocol, configs, seeds and analysis were unchanged after the first output.

## 4. Results

### 4.1 Peak goodput per arm (median over 10 blocks, min to max)

| arm | G* (rps) | c at peak | generator-limited peak cells |
|---|---|---|---|
| A0 | 114.6 (111.2 to 116.1) | 4 in all blocks | 0 |
| A1 | 265.1 (246.5 to 286.6) | 4 in all blocks | 0 |
| A2 | 28131.4 (27586.5 to 28633.9) | 2 in all blocks | 10 of 10 |
| A3 | 1025.3 (1019.1 to 1037.6) | 128 (2), 256 (5), 512 (3) | 0 |
| A4 | 115.3 (113.6 to 119.7) | 4 in all blocks | 0 |

### 4.2 Confirmatory estimates (geometric mean of within-block R, percentile bootstrap over blocks, 10,000 resamples, seed 20261124)

| arm | R | 95 % interval | 98.75 % interval | SD of log R | verdict |
|---|---|---|---|---|---|
| A1 cache | 2.337 | [2.269, 2.413] | [2.254, 2.435] | 0.052 | H0 rejected, R > 1 |
| A2 index | excluded | | | | peak generator-limited in every block (G* above 50 % of the 27919.4 rps ceiling) |
| A3 batching | 9.005 | [8.937, 9.075] | [8.921, 9.093] | 0.013 | H0 rejected, R > 1 |
| A4 bounded concurrency | 1.015 | [1.003, 1.027] | [1.000, 1.030] | 0.020 | no meaningful effect (98.75 % interval inside [0.95, 1.05]) |

**Dominance: unresolved.** A2 is excluded from the confirmatory comparison, so the top arm across all four treatments cannot be tested. Among the three included arms, the point estimates rank A3 > A1 > A4. The frozen analysis has no pairwise test among them.

### 4.3 Sensitivity (protocol section 12)

- **S3, mean goodput over c in {16, 32, 64}** (98.75 % intervals): A1 2.606 [2.473, 2.775], A2 160.93 [155.28, 166.99], A3 12.452 [12.012, 12.936], A4 1.161 [1.111, 1.209].
  - A2's cells at these levels are not generator-limited, so A2 enters S3 and ranks first.
  - The order of A3, A1 and A4 is unchanged.
  - Under S3, A4 is above 1 (about 16 %), unlike under G*.
- **Drift** (OLS of log G* on arm indicators plus run order, block bootstrap): slope -0.00039 per run, 95 % [-0.00073, 0.00010]. Per position in block: -0.0030, 95 % [-0.0088, 0.0016]. Both intervals include 0, so there is no evidence of a time trend.

### 4.4 Exploratory (beyond the frozen analysis)

- **A2, unfiltered G*:** R = 246.8, 98.75 % [243.4, 250.2].
- **A2, G* restricted to levels that are not generator-limited** (c >= 8): R = 90.8 [90.0, 91.8].
- **Other arms:** their peaks are not flagged, so their alternative estimates equal the confirmatory ones.

### 4.5 Descriptives

- **A1:** median cache hit ratio 0.59.
- **A4:** 14,737,227 HTTP 503 rejections counted by the server over the ten runs, including warmups; 10,996,866 of them fell in measurement windows (M4 re-analysis X1). Error rate about 0.99 at every c >= 32.
- **Errors at c = 512:** maximum error rate 0.42 for A0 and 0.17 for A1. Composition (M4 re-analysis X1, corrected at M4): the errors are HTTP 500 responses from the server's generic exception handler (from c = 64 or 128 for A0 and c = 32 or 64 for A1) plus transport errors (only at c = 256 and 512). The exception type is not logged, so the cause of the 500s is not identified (the 5 s SQLite busy timeout is a candidate only); client timeouts and the listen backlog, which the kernel caps at 128, remain candidates for the transport errors. No invalid body occurred in any accepted run.
- **A3:** zero errors at every level.
- **Per-level detail:** goodput and p99 latency per level, with medians and ranges, are in `analysis.json`.

## 5. Expected versus observed

- **A1 and A3:** above 1, as expected. A3's effect (about 9x) is much larger than A1's (about 2.3x).
- **A4:** indeterminate for peak goodput in advance; observed as practically null on G*, while it sheds almost all load from c = 32.
- **A2:** expected to be largest by design. Its peak is so fast that it reaches the generator/HTTP ceiling (28131 rps, above C_gen), so the frozen rule excludes it. This is the outcome D-008 item 5 anticipated.
- **What would contradict the hypotheses** (protocol item 20): all intervals containing 1 (not observed); the top arm not separable (dominance unresolved by exclusion, not by overlap); a ranking change under S3 (not for the included arms).

## 6. Verdict under the frozen decision rule

- H0 is rejected for A1 and A3, both with R > 1.
- A4 has no meaningful effect on peak goodput.
- A2 is excluded as generator-limited.
- The dominance question is **unresolved**.

## 7. Limitations

- One machine, one implementation, one workload.
- A3's G* may be truncated in the 3 blocks that peaked at c = 512.
- The exclusion of A2 rests on the reading fixed in D-012, which is pending the owner's review.
- The re-attempted cells are not adjacent in time.
- EXP-003 and EXP-004 did not run, so the ranking is not tested against open-loop arrivals or other workloads.
- See `research/limitations.md` items 12 to 17.

## 8. M4 addendum (2026-11-25)

- **Evidence audit.** Two statements of this report were corrected: the per-run duration range (above) and the 503 count, which is a server-side total including warmups. The error composition at high concurrency was added. No verdict changed. See `research/publication/evidence_audit_M4.md`.
- **Exploratory re-analysis** (`results/exploratory/M4-REANALYSIS-20261125/summary.json`, J-0014; no new measurement). It does not change any verdict. It finds that the A4 null is structural (both A4 and A0 peak at c = 4, below W = 8, where the limiter does not engage), that A3's G* is not materially truncated (R over c <= 256 is 8.99), and that the size of A3's advantage over A1 depends on the summary metric (exploratory R_A3 / R_A1 3.85 under G*, 1.58 under a closed-loop 50 ms p99 bound).
- **Pending the owner.** The D-012 reading that excludes A2 is still pending (owner, 2026-11-25, "Next", does not decide it).
