<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# EXP-004 protocol: workload sensitivity (table size and key skew)

| Field | Value |
|---|---|
| Status | DRAFT, not frozen; planned (protocol draft, awaiting owner freeze); optional, first to be cut if the budget is threatened |
| Version / date | v0.1, 2026-11-24 |
| Study protocol | `research/protocol.md` (draft v0.1), section 12 item 2 |
| Depends on | EXP-002 |

1. **Precise question.** Is the dominant bottleneck found in EXP-002 a property of the chosen workload parameters?
2. **Mechanism.** A smaller table shrinks full-scan cost (weakening A2 and A3); uniform keys reduce cache hit rate (weakening A1).
3. **Rationale.** mytkowicz2009 (abstract): setup choices can bias conclusions; this experiment varies the two setup parameters most likely to decide the answer.
4. **Competing explanations.** Changes in variance rather than in mean effects; reported with intervals.
5. **Hypotheses.** H0: the top arm under each variant equals the EXP-002 top arm. H1: it differs.
6. **Estimand.** R_j per variant, as in EXP-002.
7. **Experimental unit.** One run, as in EXP-002.
8. **Scope.** Variant V1: N = 10,000 rows, Zipf s = 0.99. Variant V2: N = 200,000 rows, uniform keys (s = 0). Other parameters as EXP-002.
9. **Variables.** Independent: variant, arm, concurrency. Dependent: as EXP-002.
10. **Treatment and control.** As EXP-002, within each variant.
11. **Baseline.** A0 of the same variant.
12. **Sampling and seeds.** 5 blocks per variant, block seeds distinct from EXP-002.
13. **Sample-size rationale.** Sensitivity; master-prompt minimum of 5 runs per arm.
14. **Compute budget.** About 150 s per run, 50 runs, about 2.1 h (planning estimate).
15. **Metric formulas.** As EXP-002.
16. **Uncertainty.** As EXP-002, 95 % intervals only (no confirmatory family).
17. **Exclusion and stopping.** As protocol section 10.
18. **Failure modes.** At N = 10,000 all arms may hit the HTTP ceiling (then no ranking; reported as such).
19. **Sensitivity.** None beyond the two variants.
20. **What contradicts the main interpretation.** A different top arm in either variant; the main finding is then reported as workload-conditional.
21. **Reproduction.** `uv run scale exp EXP-004` (to be implemented at M2); raw results `results/raw/EXP-004/`.
