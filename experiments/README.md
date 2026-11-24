<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# experiments/

Experiment configurations consumed by `scale run` / `scale smoke`. Protocols, reports and per-experiment outputs live in `research/experiments/EXP-NNN/`; the registry is `research/experiment_registry.csv`.

| Config | Label | Use |
|---|---|---|
| `smoke.json` | exploratory | Smoke matrix of protocol section 11: A0 and A2, c in {1, 8, 64}, 1 block, 2 s + 3 s |
| `smoke-null.json` | exploratory | Null-endpoint generator check at c in {1, 8} with the ApacheBench cross-check |
| `pilot.json` | exploratory | All five arms, c in {1, 8, 64}, 3 blocks: runtime and between-block spread for the sample-size decision |
| `stall-open.json`, `stall-closed.json` | exploratory | Coordinated-omission check with an injected 200 ms pause every 2 s |
| `pilot-quiet.json` | exploratory | Quiet-machine pilot of protocol section 7.1 (all arms, c = 1 to 1024, 5 blocks, 5 s + 15 s); its only use is `scale resolve-pilot`, which sets EXP-002's c_max and n |
| `EXP-001.json` | confirmatory | Frozen v1.0 (owner-approved 2026-11-24); SHA-256 in `research/freeze.json`; `scale run` accepts it and refuses any changed copy |
| `EXP-002.json` | confirmatory | Frozen v1.0 except `blocks`, `concurrency` (quiet-pilot rule) and `generator_ceiling_rps` (EXP-001), left unset; `scale run` refuses it until the resolution is appended to `research/freeze.json` |

Keys starting with `_comment` are ignored by the parser; any other unknown key is an error.
