<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# EXP-001 protocol: load-generator and measurement validation

| Field | Value |
|---|---|
| Status | FROZEN v1.0 (owner-approved 2026-11-24); not yet run |
| Version / date | v1.0, 2026-11-24 (draft v0.1 unchanged in content except as listed under "Amendments before freeze") |
| Study protocol | `research/protocol.md` (frozen v1.0) |
| Depends on | M2 harness (server, generator, schemas) |
| Gates | EXP-002, EXP-003, EXP-004 |

1. **Precise question.** Up to what request rate, and with what timing accuracy, can the SCALE load generator measure the SCALE server on this machine without itself being the bottleneck or hiding stalls?
2. **Mechanism.** A Python generator on the same machine consumes CPU and may saturate before the server; a closed-loop generator stops sending while waiting and hides stalls (coordinated omission, wrk2 README).
3. **Rationale from verified sources.** tene-wrk2 (read, page); schroeder2006 (read); kalibera2013 (read). See `research/literature_review.md`.
4. **Competing explanations.** A low measured ceiling can come from the generator, the server's HTTP parsing, the loopback stack or the shared CPU; the ApacheBench cross-check separates the generator from the rest.
5. **Hypotheses.** H0: the SCALE generator and ApacheBench 2.3 obtain the same throughput on `GET /null` at c in {1, 8, 32} (ratio within [0.9, 1.1]). H1: they differ. Stall check: with an injected 200 ms server pause every 2 s, the open-loop generator's intended-time p99 is at least 150 ms, while the closed-loop p99 may be lower (expected coordinated omission). Timer: `time.perf_counter_ns` resolution is at most 1 microsecond.
6. **Estimand.** Generator ceiling C_gen (requests per second) per concurrency level; ratio SCALE/ab; corrected versus uncorrected p99 under stall.
7. **Experimental unit.** One fresh server process plus one generator invocation per level.
8. **Scope.** Localhost only; `GET /null` and `GET /health`; no database work.
9. **Variables.** Independent: generator (SCALE, ab), concurrency, generator process count (1, 2, 4), stall injection (off, on). Dependent: throughput, p50/p95/p99, generator CPU, server CPU.
10. **Treatment and control.** Control: ApacheBench 2.3 (`ab -k -c <c> -t 10 http://127.0.0.1:<port>/null`). Treatment: SCALE generator with matching settings.
11. **Baseline.** ab.
12. **Sampling and seeds.** 5 repeats per cell, fresh server per repeat; generator seed recorded (only affects schedule jitter).
13. **Sample-size rationale.** Validation, not inference about the factors; 5 repeats give a range adequate to detect a generator shortfall larger than 10 %.
14. **Compute budget.** About 30 minutes.
15. **Metric formulas.** Throughput = completed 200 responses / window (req/s). Intended-time latency = completion time minus scheduled send time (ms). Generator CPU = generator process CPU seconds / wall seconds.
16. **Uncertainty.** Median and range over 5 repeats; no inferential test.
17. **Exclusion and stopping.** Harness failures re-attempted twice. If the ratio is below 0.9 at c = 32, EXP-002 is not started until the generator is fixed or the owner accepts a lower confirmatory concurrency range.
18. **Failure modes.** ab single-threaded ceiling below the server's (then ab is not a valid upper reference: report it); file-descriptor soft limit 256 (raise inside the generator process or stay below it).
19. **Sensitivity.** Generator process count 1 versus 4.
20. **What contradicts.** SCALE/ab ratio outside [0.9, 1.1], or corrected p99 under stall below 150 ms (the correction does not work).
21. **Outputs.** `C_gen` table used by EXP-002 to flag generator-limited cells (goodput > 50 % of C_gen or generator CPU > 85 %).
22. **Reproduction.** `uv run scale exp EXP-001` (command to be implemented at M2); raw results in `results/raw/EXP-001/`, summaries in `research/experiments/EXP-001/metrics.csv`.


## Amendments before freeze (owner-approved 2026-11-24)

None to this protocol. The study-level amendments AM-1 to AM-4 (`research/protocol.md` section 15) do not touch EXP-001. Config: `experiments/EXP-001.json`; run with `uv run scale run experiments/EXP-001.json`.
