<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE study protocol

| Field | Value |
|---|---|
| Status | **FROZEN v1.0 (owner-approved 2026-11-24).** Two EXP-002 values (sweep top c_max, block count n) are set later by the pre-stated rule of section 7.1 from a quiet-machine pilot. |
| Date | 2026-11-24 |
| Authority | `master_prompt.md` section 10; experiment protocols in `research/experiments/EXP-NNN/protocol.md` |
| Freeze record | `research/freeze.json` (owner approval, common decisions C1 to C4, SHA-256 of this file, of each EXP protocol and of each confirmatory config, git revision) and D-009 in `research/decision_log.md`. The CLI checks it before any confirmatory run. |

Runs made before the freeze are **exploratory** and labelled as such. Numeric parameters below are fixed design values, not measurements, unless a journal entry is cited. Changes made at the freeze are listed in section 15.

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
| A4 bounded concurrency | Request-level admission limit: at most W = 8 requests in database work and a bounded queue of Q = 16 waiting requests (W + Q = 24, below the largest concurrency level, so the limiter can reject); overflow returns HTTP 503 | oversubscription, lock and scheduler contention |

The baseline is the simplest configuration and the primary comparator for every arm.

**The index wins by design.** A0 answers each lookup with a full scan of N = 200,000 rows, and A2 replaces that scan with an index lookup. Against a full-scan baseline the index is therefore expected to dominate by construction, not as a discovery (the exploratory pilot J-0005 saw within-block ratios near 250). A finding that A2 has the largest R_j is reported as this designed expectation; the informative comparisons are the sizes and ordering of R_A1, R_A3 and R_A4, and whether anything other than A2 comes close. One-factor-at-a-time designs cannot estimate interactions; this is a stated limitation (`research/limitations.md`), not a hidden one.

## 4. Load generation

- Separate generator process or processes on the same machine, keep-alive HTTP/1.1 connections, monotonic clock (`time.perf_counter_ns`).
- **Closed loop (primary, EXP-002):** c connections, each sending its next request as soon as the previous response arrives, zero think time. Concurrency sweep c in {1, 2, 4, ..., c_max} (doubling), extended beyond 64 until A1 and A3 peak inside the range: c_max is one of 128, 256, 512 or 1024, set by the rule of section 7.1 from the quiet-machine pilot. The server's listen backlog is set to max(128, c_max) (the kernel may cap it; macOS `kern.ipc.somaxconn` is 128 on this machine). Per level: 5 s warmup (discarded), then 15 s measurement window.
- **Open loop (sensitivity, EXP-003):** requests scheduled at a constant offered rate; latency measured from the *intended* send time, correcting coordinated omission as described in the wrk2 README (Tene, accessed 2026-11-24).
- The generator's own ceiling is measured in EXP-001 and cross-checked against ApacheBench 2.3 (preinstalled at `/usr/sbin/ab`). Any measurement cell whose goodput exceeds 50 % of the generator ceiling, or whose generator CPU exceeds 85 % of its allotted cores, is flagged generator-limited and excluded from confirmatory comparison (reported, not dropped). The ceiling used by EXP-002 is the median of the EXP-001 ceiling runs (AM-5, section 15).

## 5. Hypotheses

For each treatment arm j in {A1, A2, A3, A4}, with R_j defined in section 6:

- **H0_j:** the change does not alter peak goodput: R_j = 1.
- **H1_j:** R_j differs from 1 (nondirectional test).

Recorded directional expectations, used for interpretation only and not for the test: R_A1 > 1, R_A2 > 1, R_A3 > 1; A4 indeterminate for peak goodput, expected to lower p99 latency at high concurrency at the price of a non-zero 503 rate. R_A2 is expected to be the largest by design (section 3), so a dominance claim for A2 confirms the construction of the baseline, not a property of real systems.

**Dominance question.** The dominant bottleneck of the baseline configuration is the mechanism whose relief yields the largest R_j. A dominance claim is made only if, for the top arm t and every other arm k, the bootstrap confidence interval of R_t / R_k excludes 1. Otherwise the ranking is reported as unresolved.

**What contradicts the hypotheses.** Every interval for R_j includes 1 (no factor changes peak goodput in this setup, for example because HTTP parsing or the generator is the ceiling); or the top two arms are not separable; or the ranking reverses under the EXP-003 open-loop metric or the EXP-004 workload variants.

## 6. Metrics

Per run and concurrency level c, over the measurement window of length T (seconds):

- **Goodput** G(c) = (number of HTTP 200 responses whose body passes validation) / T, in requests per second.
- **Primary metric: peak goodput** G* = max over c of G(c) (ties resolve to the smallest c), in requests per second, one value per run. Justification: throughput is the quantity named by the research question; the peak over a fixed sweep captures saturation capacity without assuming where the knee lies; counting only validated 200 responses prevents an arm from gaining throughput by failing fast (A4) or serving stale data (A1).
- **Primary effect:** R_j = G*_j / G*_A0 within a block. Summary: geometric mean of R_j over blocks.
- Secondary metrics, per level: latency p50, p95, p99 (milliseconds, from send to full response, closed loop); error rate (non-200 responses plus transport errors, divided by attempts); server CPU utilisation (process CPU seconds per wall second, from `psutil`); server peak resident memory (MB); generator CPU utilisation; saturation concurrency c_sat = smallest c with G(c) >= 0.95 G*.
- Saturation is reported as the full G(c) curve with per-level intervals; a Universal Scalability Law fit (Gunther, arXiv:0808.1431) is an exploratory descriptive summary, not a test.

## 7. Design, units, seeds and sample size

- **Experimental unit:** one run = a fresh server process on a freshly built database, one arm, one full concurrency sweep. Requests within a run are correlated and are never treated as independent observations.
- **Block:** one execution of all five arms in a seeded random order. Blocks are the independent replicates; arms within a block are paired (same request sequence seed, adjacent in time).
- **Seeds:** dataset seed fixed for the study; request-sequence seed and arm-order seed derived from the block index. At least 5 independent runs per arm. **The number of blocks n is to be set by the pre-stated rule of section 7.1 from the quiet pilot** (n = 10 or n = 20).
- **Sample-size rationale.** Kalibera and Jones (ISMM 2013) argue that repetition should be spent at the level with the largest variance; for a server benchmark this is process restart, hence one replicate per fresh process. With paired blocks, the half-width of a 95 % interval on log R is about t(0.975, n-1) x s_d / sqrt(n), where s_d is the between-block standard deviation of the log ratio. If s_d is near 0.05 (planning guess, not a measurement), n = 10 gives a half-width of about 3.6 %, enough to resolve the 5 % practical threshold below. The quiet-machine pilot (exploratory, section 7.1) estimates s_d and sets n by the rule below. n is fixed before any confirmatory EXP-002 run and never changed after seeing confirmatory data.
- **Practical threshold:** |log R_j| < log 1.05 is treated as practically negligible. "No meaningful effect" is claimed only if the whole interval lies within [0.95, 1.05]; otherwise a non-significant result is reported as inconclusive, never as equivalence.

### 7.1 Quiet-machine pilot and the pre-stated rule for c_max and n

The owner approved setting the seed count only after a quiet-machine pilot run as a separate, later step; the sweep top depends on the same measurement. Everything else is frozen now. The rule is fixed here and implemented in `src/scale/pilotrule.py` (`scale resolve-pilot <dir>`, rule version `pilot-rule-1.0`).

1. **Pilot.** Config `experiments/pilot-quiet.json` (frozen with this protocol): experiment id PILOT-QUIET, label exploratory, all five arms, c in {1, 2, 4, ..., 1024}, 5 s warmup and 15 s measurement per level, 5 blocks, study seed 20261126 (distinct from every confirmatory seed), idle probe enforced. Run after EXP-001 on a quiet machine (section 8 environment conditions).
2. **Validity.** The rule applies only if all 25 runs have status ok with the idle probe enforced and passed, five complete blocks and the full ladder. Otherwise the whole pilot is repeated later; partial pilots are kept as exploratory and never used.
3. **c_max.** For each pilot block, find the concurrency at which A1 and at which A3 reach their peak goodput (ties to the smallest c). c_max is the smallest of 128, 256, 512, 1024 strictly greater than every such peak location. If a peak lies at 1024, c_max = 1024 and the truncation of G* for that arm is reported as a limitation.
4. **n.** With G* computed over levels c <= c_max, compute per block log R_j for j in {A1, A2, A3, A4} and the sample standard deviation s_d(j) over the 5 blocks. n = 10 if max_j s_d(j) <= 0.07, otherwise n = 20.
5. **What the rule may not use.** The rule reads only peak locations of A1 and A3 and the spread of log R. It never uses the size, sign or ranking of any effect. Pilot values are disclosed in the freeze resolution and never pooled with confirmatory data.
6. **Recording.** The resolution (the rule's JSON output, the pilot results path, the resulting EXP-002 config and its SHA-256) is appended to `research/freeze.json` and to the decision log. Applying the rule is not an amendment; any departure from it is.

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
| Quiet pilot (exploratory) | 5 arms x 11 levels (c = 1 to 1024) x 5 blocks = 25 runs | Sets c_max and n by section 7.1. Never confirmatory. |
| Full (EXP-002) | 5 arms x L concurrency levels x n blocks, with L = log2(c_max) + 1 (8 to 11) and n in {10, 20}: 50 or 100 runs | Primary confirmatory comparison |
| Sensitivity (EXP-003) | 5 arms x open-loop rate ladder x 5 blocks | Could invalidate the closed-loop ranking |
| Sensitivity (EXP-004) | 2 workload variants x 5 arms x 5 blocks | Could show the ranking is workload-specific |

## 12. Sensitivity analyses that could invalidate the main interpretation

1. **Workload model (EXP-003).** Closed-loop generators can understate response time and change conclusions relative to open-loop arrival (Schroeder, Wierman and Harchol-Balter, NSDI 2006). If the arm ranking by SLO-constrained open-loop goodput differs from the EXP-002 ranking, the closed-loop "dominant bottleneck" is a property of the load model, and the main interpretation must be qualified accordingly.
2. **Workload parameters (EXP-004).** The dominant bottleneck is partly set by the chosen table size and key skew. EXP-004 repeats the comparison with (a) N = 10,000 rows and (b) uniform keys (s = 0). A change of the top arm shows the finding is workload-conditional.
3. **Summary statistic (within EXP-002).** Replace G* by the mean goodput over c in {16, 32, 64}. A ranking change shows sensitivity to a single noisy level.
4. **Measurement bias.** Following Mytkowicz et al. (ASPLOS 2009), arm order is randomised within blocks, and the effect of time-of-run is checked by regressing G* on run position.

## 13. Compute budget and schedule

Planning estimate, not a measurement: quiet pilot about 25 x 224 s, about 1.6 h; EXP-002 about 8 to 11 levels x 20 s plus about 4 s overhead per run (164 to 224 s), 50 or 100 runs, about 2.3 h to 6.2 h depending on the section 7.1 rule; EXP-003 about 1.2 h; EXP-004 about 2.1 h; EXP-001 under 0.5 h. Total between about 6 h and 11 h of unattended machine time on the local laptop, at zero cost, depending on the section 7.1 rule. Fits the five-day target (`roadmap.md`).

## 14. Confounders

Thermal state and background load (idle probe, randomised order, position check); Python GIL and the interpreter build (recorded); SQLite version and page cache (fresh database per run, WAL mode); macOS scheduler placement between performance and efficiency cores (not controllable, recorded as a limitation); generator and server sharing the same CPU (EXP-001 ceiling, generator CPU recorded).

## 15. Amendments

### Amendments before freeze (owner-approved 2026-11-24)

Source: the owner's approvals of 2026-11-24 (`labs/_shared/owner-approvals-2026-11-24.md`, SCALE section), answering proposals D-008. Recorded in D-009.

- **AM-1 (A4 can reject).** A4's queue changed from Q = 64 to Q = 16 (W = 8 unchanged), so W + Q = 24 is below the largest concurrency level and the limiter can shed load. Q = 16 is the value named in D-008 item 1, chosen before any confirmatory run; it was not tuned on the primary contrast. Section 3 and `src/scale/config.py`.
- **AM-2 (index wins by design).** Section 3 and section 5 now state that the index is expected to dominate a full-scan baseline by construction.
- **AM-3 (sweep extended).** The sweep continues by doubling beyond 64 until A1 and A3 peak inside the range; c_max in {128, 256, 512, 1024} is set by the rule of section 7.1. The listen backlog follows the sweep (section 4).
- **AM-4 (seed count after a quiet pilot).** n is to be set by the pre-stated rule from the quiet pilot (section 7.1): n = 10 if every treatment arm's between-block SD of log R is at most 0.07, otherwise n = 20 (the trigger and both values are those of draft v0.1 and D-008 item 6).
- **Unchanged.** All other draft v0.1 parameters are kept as approved: N = 200,000, Zipf s = 0.99, 2 % writes, payload 256 B, A1 capacity 10 % with time-based warmup, A3 1 ms or 32 requests, 5 s + 15 s windows, 1 generator process, the 50 % and 85 % generator-limited rule, the 15 % idle probe, the 50 ms SLO, the [0.95, 1.05] threshold, bootstrap and Bonferroni analysis, EXP-003 and EXP-004 with 5 blocks.

### Amendment before confirmatory data (owner-approved 2026-11-24, second round)

Source: the owner's second-round approvals of 2026-11-24 (`labs/_shared/owner-approvals-2026-11-24b.md`, section 4, "Rules fixed before data"; the owner answered "Approve all"). Recorded in D-011. Made before any confirmatory run of any experiment: no EXP-001, pilot or EXP-002 output exists when this rule is written.

- **AM-5 (generator ceiling).** The generator ceiling used by EXP-002 (`generator_ceiling_rps`, the C_gen of EXP-001 item 21, used by the 50 % generator-limited rule of section 4) is the median of the EXP-001 ceiling runs. A ceiling run is one of the five EXP-001 repeats (config `experiments/EXP-001.json`: SCALE generator, `GET /null`, c in {1, 8, 32}); its ceiling is its peak goodput over those levels (ties to the smallest c). The rule applies only if all five repeats have status ok with the idle probe enforced and passed; otherwise no value is set and EXP-001 is repeated. The per-level C_gen table and the ApacheBench cross-check are still reported in full; the 85 % generator-CPU criterion is unchanged. The rule reads EXP-001 runs only, never a study arm. Implemented in `src/scale/ceiling.py` (`scale resolve-ceiling <dir>`, rule version `ceiling-rule-1.0`); its output is recorded with the section 7.1 resolution. This closes the open point of D-009 (how the per-level table becomes one number).

### After the freeze

Any amendment after the freeze is dated, justified, recorded in `research/decision_log.md`, and analysed separately from the frozen analysis. Applying the section 7.1 rule is not an amendment.
