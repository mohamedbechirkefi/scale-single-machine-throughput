<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# experiments/

Experiment configurations consumed by `scale run` / `scale smoke`. Protocols, reports and per-experiment outputs live in `research/experiments/EXP-NNN/`; the registry is `research/experiment_registry.csv`.

| Config | Label | Use |
|---|---|---|
| `smoke.json` | exploratory | Smoke matrix of protocol section 11: A0 and A2, c in {1, 8, 64}, 1 block, 2 s + 3 s |
| `smoke-null.json` | exploratory | Null-endpoint generator check at c in {1, 8} with the ApacheBench cross-check |
| `pilot.json` | exploratory | All five arms, c in {1, 8, 64}, 3 blocks: runtime and between-block spread for the sample-size decision |
| `stall-open.json`, `stall-closed.json` | exploratory | Coordinated-omission check with an injected 200 ms pause every 2 s |
| `EXP-001.json`, `EXP-002.json` | confirmatory | Draft v0.1 values. `scale run` refuses them until the owner freezes the protocol and fills `protocol_sha256` (G-FREEZE) |

Keys starting with `_comment` are ignored by the parser; any other unknown key is an error.
