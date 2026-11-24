<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE study protocol

| Field | Value |
|---|---|
| Status | **DRAFT v0.1, not frozen.** Awaiting the owner's review and freeze (G-FREEZE). |
| Date | 2026-11-24 |
| Authority | `master_prompt.md` section 10; experiment protocols in `research/experiments/EXP-NNN/protocol.md` |
| Freeze record | None. When the owner freezes, record the commit, the SHA-256 of this file and of each EXP protocol, and the owner's approval in `research/decision_log.md`. |

Until a freeze is recorded, every run in this repository is **exploratory** and labelled as such. All numeric parameters below are planning proposals, not measurements, unless a journal entry is cited.

## 1. Research question

**What bottlenecks dominate local request throughput under different architecture choices?**

Operational version: on one fixed machine (Apple M1 Pro, 10 cores, 16 GB, macOS 15.3.1), for one fixed local HTTP workload served by one Python process backed by SQLite, which single architecture change, applied one factor at a time to a simple baseline, produces the largest change in peak successful throughput: an in-process cache, a database index, request batching, or bounded concurrency?

The answer is conditional on the workload, the implementation and the machine. The claims boundary of the master prompt applies: no extrapolation to production traffic or other hardware, and no external load testing.

## 2. System under test (identical across arms)

- **Process.** One Python 3.12 server process using the standard library (`http.server`, `socketserver`, `sqlite3`), HTTP/1.1 with keep-alive, bound to `127.0.0.1` only.
- **Data.** A synthetic table `items(id INTEGER PRIMARY KEY, sku TEXT, category INTEGER, price_cents INTEGER, payload TEXT)` with N = 200,000 rows (planning value), a fixed 256-byte payload per row, generated deterministically from a recorded seed by `src/` (generator version and parameters recorded in `data/manifest.json`). SQLite file on local disk, WAL journal mode, rebuilt from the seed for every run.
- **Endpoints.**
  - Read: `GET /item?sku=<sku>` returns the row as JSON with a fixed byte layout.
  - Write: `POST /item/<sku>/price` sets a new price (deterministic from the request sequence).
  - Control (not measured): `GET /health`, `GET /null` (fixed 64-byte body, no database access; used only by EXP-001).
- **Request mix.** 98 % reads and 2 % writes (planning values). Keys follow a Zipf distribution with exponent s = 0.99 over a seeded permutation of the N keys. The request sequence for a block is generated from the block seed and is identical across the arms of that block (common random numbers).
- **Payload.** Fixed request and response sizes per endpoint; response equivalence across arms is tested (section 8).

## 3. Arms (one factor at a time)

| Arm | Change relative to A0 | Mechanism relieved |
|---|---|---|
| **A0 baseline** | Thread per connection (`ThreadingHTTPServer`), no index on `sku` (full table scan per lookup), no cache, one query per request, no admission limit | none |
| A1 cache | In-process LRU cache of read responses, capacity 10 % of N, write-through invalidation (entry deleted under a lock before the write is acknowledged) | repeated database work for hot keys |
| A2 index | `CREATE INDEX ix_items_sku ON items(sku)` built before the run | full-scan cost per lookup |
| A3 batching | Read micro-batching: pending lookups are collected for at most 1 ms or 32 requests, then served by one `SELECT ... WHERE sku IN (...)` | per-query fixed cost and scan amortisation |
| A4 bounded concurrency | Fixed worker pool W = 8 with a bounded queue of 64 requests; overflow returns HTTP 503 | oversubscription, lock and scheduler contention |

The baseline is the simplest configuration and the primary comparator for every arm. One-factor-at-a-time designs cannot estimate interactions; this is a stated limitation (`research/limitations.md`), not a hidden one.

## 4. Load generation

- Separate generator process or processes on the same machine, keep-alive HTTP/1.1 connections, monotonic clock (`time.perf_counter_ns`).
- **Closed loop (primary, EXP-002):** c connections, each sending its next request as soon as the previous response arrives, zero think time. Concurrency sweep c in {1, 2, 4, 8, 16, 32, 64}. Per level: 5 s warmup (discarded), then 15 s measurement window.
- **Open loop (sensitivity, EXP-003):** requests scheduled at a constant offered rate; latency measured from the *intended* send time, correcting coordinated omission as described in the wrk2 README (Tene, accessed 2026-11-24).
- The generator's own ceiling is measured in EXP-001 and cross-checked against ApacheBench 2.3 (preinstalled at `/usr/sbin/ab`). Any measurement cell whose goodput exceeds 50 % of the generator ceiling, or whose generator CPU exceeds 85 % of its allotted cores, is flagged generator-limited and excluded from confirmatory comparison (reported, not dropped).

## 5. Hypotheses

For each treatment arm j in {A1, A2, A3, A4}, with R_j defined in section 6:

- **H0_j:** the change does not alter peak goodput: R_j = 1.
- **H1_j:** R_j differs from 1 (nondirectional test).

Recorded directional expectations, used for interpretation only and not for the test: R_A1 > 1, R_A2 > 1, R_A3 > 1; A4 indeterminate for peak goodput, expected to lower p99 latency at c = 64 at the price of a non-zero 503 rate.

**Dominance question.** The dominant bottleneck of the baseline configuration is the mechanism whose relief yields the largest R_j. A dominance claim is made only if, for the top arm t and every other arm k, the bootstrap confidence interval of R_t / R_k excludes 1. Otherwise the ranking is reported as unresolved.

**What contradicts the hypotheses.** Every interval for R_j includes 1 (no factor changes peak goodput in this setup, for example because HTTP parsing or the generator is the ceiling); or the top two arms are not separable; or the ranking reverses under the EXP-003 open-loop metric or the EXP-004 workload variants.

## 6. Metrics

Per run and concurrency level c, over the measurement window of length T (seconds):

- **Goodput** G(c) = (number of HTTP 200 responses whose body passes validation) / T, in requests per second.
- **Primary metric: peak goodput** G* = max over c of G(c), in requests per second, one value per run. Justification: throughput is the quantity named by the research question; the peak over a fixed sweep captures saturation capacity without assuming where the knee lies; counting only validated 200 responses prevents an arm from gaining throughput by failing fast (A4) or serving stale data (A1).
- **Primary effect:** R_j = G*_j / G*_A0 within a block. Summary: geometric mean of R_j over blocks.
- Secondary metrics, per level: latency p50, p95, p99 (milliseconds, from send to full response, closed loop); error rate (non-200 responses plus transport errors, divided by attempts); server CPU utilisation (process CPU seconds per wall second, from `psutil`); server peak resident memory (MB); generator CPU utilisation; saturation concurrency c_sat = smallest c with G(c) >= 0.95 G*.
- Saturation is reported as the full G(c) curve with per-level intervals; a Universal Scalability Law fit (Gunther, arXiv:0808.1431) is an exploratory descriptive summary, not a test.

## 7. Design, units, seeds and sample size

- **Experimental unit:** one run = a fresh server process on a freshly built database, one arm, one full concurrency sweep. Requests within a run are correlated and are never treated as independent observations.
- **Block:** one execution of all five arms in a seeded random order. Blocks are the independent replicates; arms within a block are paired (same request sequence seed, adjacent in time).
- **Seeds:** dataset seed fixed for the study; request-sequence seed and arm-order seed derived from the block index. At least 5 independent runs per arm; the full matrix plans **10 blocks** (10 runs per arm).
- **Sample-size rationale.** Kalibera and Jones (ISMM 2013) argue that repetition should be spent at the level with the largest variance; for a server benchmark this is process restart, hence one replicate per fresh process. With paired blocks, the half-width of a 95 % interval on log R is about t(0.975, n-1) x s_d / sqrt(n), where s_d is the between-block standard deviation of the log ratio. If s_d is near 0.05 (planning guess, not a measurement), n = 10 gives a half-width of about 3.6 %, enough to resolve the 5 % practical threshold below. The smoke pilot (exploratory) estimates s_d; if it exceeds 0.07, the owner decides before the freeze whether to raise n to 20. n is fixed at the freeze and not changed after seeing confirmatory data.
- **Practical threshold:** |log R_j| < log 1.05 is treated as practically negligible. "No meaningful effect" is claimed only if the whole interval lies within [0.95, 1.05]; otherwise a non-significant result is reported as inconclusive, never as equivalence.

## 8. Controls and verification (before any confirmatory run)

- Response equivalence: for a fixed request list, every arm returns byte-identical bodies given the same database state.
- Cache invalidation: a read after an acknowledged write never returns the old value (A1), including under concurrent readers.
- Correctness under concurrency: final database state after a seeded concurrent write sequence equals the state produced by applying the writes serially in acknowledgment order; no lost writes.
- Load-generator limits: EXP-001 (ceiling, ApacheBench cross-check, injected-stall coordinated-omission check, timer resolution).
- Environment: AC power, low-power mode off, no other heavy applications; record `pmset -g batt`, load average, OS version, CPU model, package versions, git revision and config hash per run. A run starts only if system-wide CPU over a 1 s idle probe is below 15 %.

## 9. Uncertainty and analysis

- Per block: log R_j. Summary: mean of log R_j, back-transformed (geometric mean ratio).
- Interval: percentile bootstrap over blocks, 10,000 resamples, recorded seed. Confirmatory decisions use Bonferroni-adjusted 98.75 % intervals (four comparisons); 95 % intervals are also reported.
- Raw distributions (per-run G*, per-level G(c), latency histograms) are published alongside summaries.
- Latency percentiles are reported per run and summarised across runs by median and range; they are not pooled across runs as if independent.

## 10. Exclusion and stopping rules

- A run is excluded only for a harness failure (server fails the readiness check within 30 s, generator crash) or a failed idle probe. Excluded runs are kept in the raw log, reported with reasons, and re-attempted at the end of the sequence, at most twice per cell; cells still failing are reported missing.
- **Correctness failure** (response mismatch, stale cache read, lost write) suspends the experiment. The fix is recorded, the protocol amended and dated, and the experiment restarted from block 1. Results from before the fix are kept as exploratory.
- Generator-limited cells are flagged and excluded from the confirmatory comparison, and reported.
- The design is fixed-n. No early stopping for efficacy.

## 11. Smoke matrix and full matrix

| Matrix | Content | Use |
|---|---|---|
| Smoke (exploratory) | EXP-001 null-endpoint check at c in {1, 8}; arms A0 and A2; c in {1, 8, 64}; 1 block; 2 s warmup, 3 s measurement | Validates the harness, schema and metrics; estimates s_d for planning. Never confirmatory. |
| Full (EXP-002) | 5 arms x 7 concurrency levels x 10 blocks = 50 runs, 350 measurement cells | Primary confirmatory comparison |
| Sensitivity (EXP-003) | 5 arms x open-loop rate ladder x 5 blocks | Could invalidate the closed-loop ranking |
| Sensitivity (EXP-004) | 2 workload variants x 5 arms x 5 blocks | Could show the ranking is workload-specific |

## 12. Sensitivity analyses that could invalidate the main interpretation

1. **Workload model (EXP-003).** Closed-loop generators can understate response time and change conclusions relative to open-loop arrival (Schroeder, Wierman and Harchol-Balter, NSDI 2006). If the arm ranking by SLO-constrained open-loop goodput differs from the EXP-002 ranking, the closed-loop "dominant bottleneck" is a property of the load model, and the main interpretation must be qualified accordingly.
2. **Workload parameters (EXP-004).** The dominant bottleneck is partly set by the chosen table size and key skew. EXP-004 repeats the comparison with (a) N = 10,000 rows and (b) uniform keys (s = 0). A change of the top arm shows the finding is workload-conditional.
3. **Summary statistic (within EXP-002).** Replace G* by the mean goodput over c in {16, 32, 64}. A ranking change shows sensitivity to a single noisy level.
4. **Measurement bias.** Following Mytkowicz et al. (ASPLOS 2009), arm order is randomised within blocks, and the effect of time-of-run is checked by regressing G* on run position.

## 13. Compute budget and schedule

Planning estimate, not a measurement: EXP-002 about 150 s per run, 50 runs, about 2.1 h; EXP-003 about 1.2 h; EXP-004 about 2.1 h; EXP-001 under 0.5 h. Total under 6 h of unattended machine time on the local laptop, at zero cost. Fits the five-day target (`roadmap.md`).

## 14. Confounders

Thermal state and background load (idle probe, randomised order, position check); Python GIL and the interpreter build (recorded); SQLite version and page cache (fresh database per run, WAL mode); macOS scheduler placement between performance and efficiency cores (not controllable, recorded as a limitation); generator and server sharing the same CPU (EXP-001 ceiling, generator CPU recorded).

## 15. Amendments

None. Any amendment after a freeze is dated, justified, recorded in `research/decision_log.md`, and analysed separately from the frozen analysis.
