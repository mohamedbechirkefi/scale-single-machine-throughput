<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# EXP-003 protocol: open-loop SLO goodput (sensitivity to the load model)

| Field | Value |
|---|---|
| Status | DRAFT, not frozen; planned (protocol draft, awaiting owner freeze) |
| Version / date | v0.1, 2026-11-24 |
| Study protocol | `research/protocol.md` (draft v0.1), section 12 item 1 |
| Depends on | EXP-001, EXP-002 (rate ladder centred on EXP-002 results; ladder fixed before EXP-003 runs) |

1. **Precise question.** Does the ranking of arms by closed-loop peak goodput (EXP-002) hold when capacity is measured as the highest open-loop offered rate that meets a latency objective?
2. **Mechanism.** In an open system, arrivals do not wait for completions; queues build when the offered rate approaches capacity, and latency must be measured from the intended send time (coordinated-omission correction).
3. **Rationale.** schroeder2006 (read): closed and open models can differ by an order of magnitude in response time and change the benefit of scheduling; tene-wrk2 (read, page).
4. **Competing explanations.** A ranking change may come from latency variability (A3 batching window, A4 shedding) rather than capacity; both are reported.
5. **Hypotheses.** H0: the arm ranking by SLO goodput equals the EXP-002 ranking. H1: it differs. Per arm: H0_j: S_j / S_A0 = 1.
6. **Estimand.** SLO goodput S = highest offered rate on the ladder at which intended-time p99 <= 50 ms and error rate <= 1 %, per run (planning SLO values, fixed at freeze).
7. **Experimental unit.** One run = fresh server, one arm, the whole rate ladder ascending.
8. **Scope.** Same workload as EXP-002.
9. **Variables.** Independent: arm, offered rate (8 rungs, geometric, from 10 % to 150 % of the arm's EXP-002 median G*, fixed before the run). Dependent: intended-time p50/p95/p99, achieved goodput, error rate, CPU.
10. **Treatment and control.** As EXP-002. Control A0.
11. **Baseline.** A0.
12. **Sampling and seeds.** 5 blocks, randomised arm order, constant-rate schedule (no random inter-arrival), request sequence seed per block.
13. **Sample-size rationale.** Sensitivity experiment; 5 runs per arm is the master-prompt minimum. The outcome of interest is a ranking change, judged by the rank of point estimates and by whether intervals overlap.
14. **Compute budget.** About 20 s per rung, 8 rungs, 25 runs, about 1.2 h (planning estimate).
15. **Metric formulas.** Intended-time latency = completion time minus scheduled time (ms). S in req/s, discretised by the ladder (resolution reported). Ratio S_j / S_A0.
16. **Uncertainty.** Bootstrap over blocks of mean log(S_j / S_A0); with a discrete ladder, also the full per-run S table.
17. **Exclusion and stopping.** As protocol section 10. A run stops ascending after two consecutive rungs fail the SLO.
18. **Failure modes.** Generator cannot sustain the offered rate (detected by schedule lag; the rung is marked generator-limited).
19. **Sensitivity.** SLO 100 ms instead of 50 ms.
20. **What contradicts the main interpretation.** A different top arm than EXP-002, with non-overlapping intervals; then the main finding is qualified as load-model dependent.
21. **Reproduction.** `uv run scale exp EXP-003` (to be implemented at M2); raw results `results/raw/EXP-003/`.
