<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Limitations (living document)

Status: items 1 to 11 were known by design at M0; items 12 to 17 were added at M3 and items 18 to 25 at M4 (2026-11-25).

1. **One machine.** All measurements come from one Apple M1 Pro laptop (macOS 15.3.1). No claim transfers to other hardware, operating systems or cloud instances.
2. **Not production traffic.** The workload is synthetic (fixed payloads, Zipf keys, 2 % writes). No claim is made about any real service or production traffic.
3. **One implementation.** A Python standard-library server with SQLite. The Python GIL, interpreter version and SQLite build are part of the system under test. Results describe this implementation, not caching, indexing, batching or admission control in general.
4. **One factor at a time.** The design does not estimate interactions between factors; combined configurations are out of scope.
5. **Shared CPU.** Load generator and server run on the same machine and compete for cores; the macOS scheduler's placement on performance or efficiency cores is not controllable.
6. **Workload dependence.** The "dominant bottleneck" depends on table size, key skew and read/write mix. EXP-004 probes two variants only.
7. **Load model.** Closed-loop capacity is the primary metric; open-loop behaviour is examined only as a sensitivity analysis (EXP-003).
8. **Localhost networking.** No real network latency, loss or bandwidth limits.
9. **Not peer reviewed.** All reports and the manuscript are independent research drafts.
10. **The index wins by design.** Baseline A0 answers each lookup with a full scan of 200,000 rows, so the index arm A2 is expected to dominate by construction (protocol section 3, amendment AM-2, owner-approved 2026-11-24). A finding that A2 has the largest effect reflects this designed baseline, not the value of indexing in real systems.
11. **Sweep top and block count set after the freeze by a pre-stated rule.** The owner approved setting the EXP-002 block count after a quiet-machine pilot; the top of the concurrency sweep is set by the same pilot (protocol section 7.1). The rule reads only peak locations and spread, never effect sizes, and is fixed in the frozen protocol.

## Results-dependent limitations (added at M3, 2026-11-25)

12. **The index arm is excluded by the generator-limited rule.** In every EXP-002 block A2's peak (c = 2, median 28131 rps) exceeds 50 % of the generator ceiling (27919.4 rps, EXP-001); it even exceeds the ceiling. Under the frozen rule and the reading of D-012, A2 has no confirmatory estimate and the dominance question is unresolved. The exploratory ratio near 247 measures how far the harness ceiling lies above the baseline, not the index alone.
13. **A3's peak may be truncated.** A3 peaked at the top of the sweep (c = 512) in 3 of 10 EXP-002 blocks, although the quiet pilot placed its peaks at 128 or 256; its R may be an underestimate.
14. **A4 sheds almost all load from c = 32.** With W + Q = 24 the limiter returns HTTP 503 to about 99 % of attempts at c >= 32; its peak goodput is set at c = 4, below the limit, so the A4 null result concerns peak goodput only.
15. **Errors at high concurrency.** A0 and A1 lose up to 42 % and 17 % of attempts at c = 512 (cause not diagnosed; candidates are client timeouts and the listen backlog, which the kernel caps at 128). Goodput counts only validated responses, so this lowers G(c) at those levels but not G*, which lies at c = 4. The candidate causes are incomplete; see item 22 (M4).
16. **Re-attempted cells are not adjacent in time.** Seven EXP-002 cells (blocks 8 and 9) ran at the end of the sequence after idle-probe exclusions, as protocol section 10 requires; their pairing with the other arms of the block is in request sequence, not in time.
17. **EXP-003 and EXP-004 did not run** (no frozen config). The closed-loop ranking is therefore not tested against an open-loop load model or other workload parameters.

## Limitations added at M4 (2026-11-25)

18. **One session.** All confirmatory EXP-002 runs were made in one window of about three hours on one machine. The intervals describe variation between process restarts within that window, not between days or machines.
19. **Batching also wins by design.** Without an index, SQLite plans the batched `IN (...)` lookup as one full scan (M4 re-analysis X13), so A3's ninefold gain is an amortisation of the baseline's scan. Like the index result (item 10), it does not measure batching in general.
20. **The A4 null is structural.** A0 and A4 both peak at c = 4, below the admission limit W = 8, where the limiter does not engage (X6). The null concerns peak goodput only; above the optimum A4 holds goodput up to about 26 % above A0. At the unadjusted 95 % level the A4 interval excludes 1.
21. **Metric dependence.** The A3 advantage over A1 is 3.85 under G* and 1.58 under a closed-loop 50 ms p99 bound (exploratory X3, X12). The ordering holds under every summary used, the size does not.
22. **Error causes not identified.** The server answers HTTP 500 from a generic exception handler without logging the exception type (A0 from c = 64, A1 from c = 32); transport errors at c >= 256 are unclassified. The confirmatory runs validate every read body (no invalid body occurred) but do not re-check the final database state after a run; write correctness rests on the pre-run tests. Item 15's candidate causes are therefore incomplete.
23. **D-012 is pending.** The exclusion of A2 rests on the assistant's reading of the frozen rule, made before data and not yet reviewed by the owner (owner, 2026-11-25, "Next", leaves it open).
24. **Post hoc exploratory checks.** The M4 checks X1 to X13 were chosen after the confirmatory results were known. They change no verdict and are hypothesis-generating only.
25. **Raw outputs outside git.** `results/raw/` is excluded by the repository's ignore rule; the recorded outputs are pinned by `SHA256SUMS` files whose digests are in the artifact manifest, but a reader of the repository alone cannot audit the per-run values without rerunning.
