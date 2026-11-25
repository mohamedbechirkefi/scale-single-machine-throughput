<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Limitations (living document)

Status at M0: no experiment has run. These are limitations known by design; results-dependent limitations will be added at M4.

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
15. **Errors at high concurrency.** A0 and A1 lose up to 42 % and 17 % of attempts at c = 512 (cause not diagnosed; candidates are client timeouts and the listen backlog, which the kernel caps at 128). Goodput counts only validated responses, so this lowers G(c) at those levels but not G*, which lies at c = 4.
16. **Re-attempted cells are not adjacent in time.** Seven EXP-002 cells (blocks 8 and 9) ran at the end of the sequence after idle-probe exclusions, as protocol section 10 requires; their pairing with the other arms of the block is in request sequence, not in time.
17. **EXP-003 and EXP-004 did not run** (no frozen config). The closed-loop ranking is therefore not tested against an open-loop load model or other workload parameters.
