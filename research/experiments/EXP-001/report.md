<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# EXP-001 report: load-generator and measurement validation

| Field | Value |
|---|---|
| Status | Complete (confirmatory), M3, 2026-11-25 |
| Protocol | `research/experiments/EXP-001/protocol.md` (frozen v1.0, sha256 4af93dc2...) |
| Config | `experiments/EXP-001.json` (frozen, sha256 9f7b8d15...) |
| Runs | 5 of 5 ok (`results/raw/EXP-001/EXP-001-M3`, run ids `EXP-001-b00..b04-A0-549fdc85`) |
| Revision | `6c3af82` (clean tree, `dirty = false` in every manifest) |
| Journal | J-0010 (confirmatory), J-0011 (exploratory supplements) |
| Analysis | `scale analyse EXP-001` -> `research/experiments/EXP-001/analysis.json`, `metrics.csv`, `figures/exp001_ceiling.{png,svg}` |

## 1. Hypothesis

H0: the SCALE generator and ApacheBench 2.3 get the same throughput on `GET /null` at c in {1, 8, 32}, meaning the SCALE/ab ratio lies within [0.9, 1.1]. H1: they differ. Item 17 gate: if the ratio at c = 32 is below 0.9, EXP-002 does not start. Item 21 output: the C_gen table. Under AM-5, EXP-002 uses the median of the five run ceilings.

## 2. What was run

The frozen config was run through the freeze guard. It has one generator process, c in {1, 8, 32}, a 2 s warmup and a 10 s window, and 5 repeats, each with a fresh server. After every SCALE level, `ab -k -c <c> -t 10` ran against the same server. The machine was quiet: AC power, idle probe 1.9 % to 2.5 % against a 15 % threshold, 1-min load average 2.76 to 4.05, and three 1 s probes all below 15 % before the start (`results/raw/quiet-checks.jsonl`). The jobs ran under `nice -n 10`. Runtime was 344.5 s.

## 3. Deviations

None from the frozen config. The protocol also names a stall check, a 1 versus 4 generator-process sensitivity and a timer-resolution check, which are not in the frozen config. They were run as **exploratory** supplements (section 6).

## 4. Results

| c | SCALE C_gen median (min to max), rps | ab median (min to max), rps | SCALE/ab median (min to max) | generator CPU median (max) |
|---|---|---|---|---|
| 1 | 26656.8 (26134.9 to 26820.5) | 28273.7 (28120.1 to 28406.5) | 0.942 (0.924 to 0.951) | 0.30 (0.30) |
| 8 | 27919.4 (27860.9 to 28657.0) | 27024.7 (26942.6 to 27076.2) | 1.034 (1.032 to 1.058) | 0.65 (0.68) |
| 32 | 27063.1 (25893.4 to 27531.8) | 26632.6 (26576.5 to 26666.3) | 1.015 (0.973 to 1.033) | 0.90 (1.40) |

Zero errors at every level. Run ceilings (peak over the ladder) were 27914.5, 27919.4, 27953.9, 27860.9 and 28657.0 rps. **The AM-5 ceiling is 27919.4 rps** (`scale resolve-ceiling`, ceiling-rule-1.0).

## 5. Expected versus observed, and verdict

- **H0 holds.** Every median ratio, and every single repeat, lies within [0.9, 1.1].
- **Gate passed.** The median ratio at c = 32 is 1.015, so EXP-002 may start.
- **c = 1.** The SCALE generator is about 6 % below ab here, still inside the band.
- **Generator CPU at c = 32.** It exceeds the 85 %-of-one-core criterion (median 0.90). In EXP-002 this criterion flagged no cell; only the 50 % goodput rule did.

## 6. Exploratory supplements (not confirmatory)

- **Stall check** (`experiments/stall-open.json` / `stall-closed.json`, one repeat each), with a 200 ms server pause every 2 s:
  - The open loop at 200 rps gave an intended-time p99 of 190.12 ms (at least 150 ms, so the correction exposes the stall).
  - The closed loop gave p99 0.91 ms, the expected coordinated omission.
- **Four generator processes** (`experiments/exp001-gp4.json`, 3 repeats, c in {8, 32}): G* was 27159.1, 27341.7 and 27079.9 rps, no higher than with one process. The ceiling near 28k rps is therefore the server and loopback path, not the generator alone.
- **Timer.** `perf_counter` resolution is 4.17e-08 s (mach_absolute_time), below 1 microsecond.

## 7. Limitations

One machine. The "generator ceiling" includes the server's HTTP path, so it caps any arm that serves requests as fast as `/null`, which matters for A2 in EXP-002. The stall check is a single repeat.

## 8. M4 evidence-audit correction (2026-11-25)

The median generator CPU at c = 8 was printed as 0.66 at M3; the recorded value is 0.6547 (`analysis.json` `levels.8.generator_cpu_median`), so the table now shows 0.65. No verdict depends on it. Audit: `research/publication/evidence_audit_M4.md`.
