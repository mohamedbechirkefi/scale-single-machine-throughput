<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Second review pass (M4): arguing against the preferred reading

| Field | Value |
|---|---|
| Date | 2026-11-25 |
| Object | `research/paper/manuscript.md` and `supplementary.md` (M4 draft), the EXP-001 to EXP-004 reports, the claims register |
| Preferred reading under challenge | "On this system, batching is the largest measurable remedy for peak goodput, caching second, admission control null; the index cannot be measured." |
| Nature | Internal quality control by the AI assistant that wrote the draft. It is not peer review and not independent. |

## 1. Challenges

Each challenge states the strongest alternative reading, the evidence that bears on it, and whether it holds (the manuscript must change) or fails (the text stands, with the reason).

| # | Challenge | Evidence | Holds? |
|---|---|---|---|
| 1 | **"Preregistered" overclaims.** The protocol was frozen and hashed locally by the owner; nothing was lodged with an external registry, so a reader would infer more independence than exists. | `research/freeze.json`; no registry entry exists | **Holds.** Title, abstract and keywords reworded. |
| 2 | **Batching wins by design, like the index.** With no index, the batched `IN (...)` query can share one scan among about 16 lookups; the ninefold gain may be an artifact of the full-scan baseline, not a property of batching. | Mean batch size 15.97; per-response CPU 1.5 ms against 18.3 ms; query plan `SCAN items` for both the single and the batched lookup (X13) | **Holds.** Section 6.1, the abstract's conclusion, limitation 3 and limitation 19 now say the A3 effect is conditional on the full-scan baseline. |
| 3 | **The ranking A3 > A1 > A4 is not tested.** The frozen analysis has no pairwise test, and the abstract's "outranks" reads as a tested ordering. | Exploratory pairwise intervals exclude 1 (X3) but are post hoc | **Holds.** The abstract and conclusion now say "point estimates order", with the exploratory intervals labelled. |
| 4 | **The batching advantage is a closed-loop artifact of high-latency levels.** A3 reaches its plateau at c = 64 with p99 near 75 ms; under a latency objective its advantage could vanish. | Closed-loop 50 ms p99 bound (X12): R_A3 3.95, R_A1 2.50, R_A3 / R_A1 1.58 (1.25 to 1.92) | **Partly holds.** The ordering survives, the size shrinks by more than half. Reported in 5.5, 6.2, 6.4 and limitation 21. Without EXP-003 the open-loop question stays open. |
| 5 | **The A4 null is not informative.** Both arms peak at c = 4, below W = 8; equal peaks follow from the design, not from a measured absence of effect. Also, the 95 % interval excludes 1. | X6: A4/A0 1.001 to 1.014 at c <= 4, no 503 below c = 32; 95 % interval 1.003 to 1.027 | **Holds.** Section 6.1 and limitation 20 say the null is structural and note the 95 % interval. The confirmatory verdict is unchanged, because the frozen rule uses the 98.75 % interval. |
| 6 | **The A2 exclusion hides the headline.** Under any plain reading the index is about 90 to 250 times the baseline; excluding it lets a smaller effect (A3) look like the winner. | Exploratory R_A2 246.8 (unfiltered), 90.8 (levels not flagged), 160.93 (S3) | **Fails as a reason to change the verdict, holds as a disclosure point.** The frozen rule decides, and the manuscript says in the abstract and in 5.2 that dominance is unresolved, never that A3 dominates. The D-012 reading is disclosed as pending with what it rests on. |
| 7 | **The "generator ceiling" is not the generator.** Four generator processes do not raise the null ceiling, so the 50 % rule may exclude A2 for the wrong reason. | GP4 supplement (J-0011); A2's drop at c = 8 while server CPU rises | **Holds as stated, without changing the verdict.** Section 5.2 now names the shared HTTP and loopback path as the likely limit, and says this changes the name of the limit, not the fact that A2's peak sits on it. |
| 8 | **The intervals overstate precision.** All 50 confirmatory runs came from one three-hour session; the between-block SD of log R (0.013 to 0.052) describes restarts within that session. | Run timestamps; quiet-pilot agreement (X10) is from the same day | **Holds.** Limitation 1 (manuscript) and 18 (living list) added; section 6.4 says what the intervals describe. |
| 9 | **The cache bound comparison is loose.** The hit ratio counts warmups and every level, not the peak level, so "close to its bound" may be a coincidence. | Hit ratio is a whole-run counter (`server_stats`) | **Holds.** Section 6.1 now states the scope and calls the comparison approximate. |
| 10 | **Unsupported mechanism claim.** "SQLite releases the interpreter lock during a query" is stated without a read source. | Not in the literature review | **Holds.** Removed; replaced by the measured fact that server CPU exceeds one core (audit F-6). |
| 11 | **Overgeneralisation in the practical lesson.** "The remedy that wins is the one that removes the dominant cost" reads as a general rule. | One system | **Holds.** Section 6.3 restricted to this system; the speculation that an indexed baseline "would very likely" reorder the arms softened to "might; not tested". |
| 12 | **Leakage from the pilot.** Pilot effect sizes were visible before EXP-002, and the analyst could have tuned the analysis. | C4 disclosure; analysis-1.0 committed at 6c3af82 before the EXP-002 runs at 3fb0c66; the pilot rule reads only peak locations and spreads | **Fails.** The analysis and its readings predate the confirmatory output, and no parameter was set from effect sizes. Disclosed as limitation 12. |
| 13 | **Forking paths in M4.** The exploratory checks were chosen after the results were known; X12 was added after inspecting per-level latencies. | Session record (J-0014) | **Holds.** Limitation 13 (manuscript) and 24 (living list) added; all checks labelled exploratory. |
| 14 | **Missing failed runs.** Twelve excluded runs, earlier noisy exploratory runs and the harness check with errors at c = 1024 could be omitted. | `analysis.json` `not_ok_runs`; supplementary S1 lists every exploratory directory | **Fails.** All are listed in S1, the EXP-002 report and the journal. |
| 15 | **Stale figures.** Figures from M3 might not match the current analysis. | Figures and `analysis.json` were written together by `scale analyse` at M3 and are unchanged; figure hashes in the manifest | **Fails.** No figure is stale; M6 can detect a change by hash. |
| 16 | **Errors hide correctness failures.** HTTP 500 responses could mask failed writes or stale reads. | No invalid body in any accepted run (X1); the 500 exception type is not logged; the final database state is not re-checked in confirmatory runs | **Partly holds.** Reads are validated, so no stale or wrong read was counted as goodput. Write correctness under load rests on the pre-run tests; stated in limitation 8 (manuscript) and 22. |
| 17 | **EXP-001 c = 1 shortfall.** The SCALE generator is about 6 % below ab at c = 1, so A0's c = 1 values may be understated. | Ratios 0.924 to 0.951 (X11); A0's peak is at c = 4, where goodput is about 115 rps, far below any generator limit | **Fails** for the conclusions; the c = 1 shortfall is reported in 5.1. |

## 2. Overall assessment

The challenges do not overturn any frozen verdict: A1 and A3 raise peak goodput, A4 has no meaningful effect on it, A2 is excluded, and dominance is unresolved. They do narrow the interpretation. Both winning effects depend on the full-scan baseline; the A3 lead over A1 depends on the summary metric; the A4 null is structural; and the intervals describe one session. The open-loop and workload experiments, which were designed to challenge the ranking, did not run.

## 3. Changes made to the manuscript after this pass

1. Title, abstract and keywords: "preregistered" replaced by "frozen protocol" and "frozen by the owner before any confirmatory data (not registered with an external registry)" (challenge 1).
2. Abstract: the accepted-run count is given with the 12 excluded runs (challenge 14); "reached" the ceiling changed to "matched" (A2's median is 1.008 times C_gen).
3. Abstract conclusion: "point estimates order", exploratory pairwise intervals labelled, both winning effects stated as conditional on the full-scan baseline (challenges 2, 3).
4. Section 6.1: query-plan evidence added for the baseline and for A3 (X13); the unsupported interpreter-lock statement removed (challenge 10); the hit-ratio scope stated (challenge 9); the A4 95 % interval noted (challenge 5).
5. Section 6.3: the practical lesson restricted to this system; "would very likely reorder" softened (challenge 11).
6. Section 4.7 and limitation 13: the exploratory checks are stated as chosen after the results (challenge 13); X13 described as a query-plan request with no timing.
7. Section 5.5: X13 added.
8. Supplementary S1 and S6: X1 to X13 and their post hoc status.

No number changed in any of these revisions; every number in the revised text was re-checked by `scripts/m4_evidence_manifest.py` (535 entries, 0 mismatches, 0 uncovered).
