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
