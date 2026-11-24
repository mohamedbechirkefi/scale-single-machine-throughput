<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# src/

Python package `scale` (M2, 2026-11-24). Ingestion, simulation, metrics, runner and serialisation are separate modules (master prompt section 4):

| Module | Role |
|---|---|
| `config.py` | Typed, validated experiment configuration; arm definitions A0 to A4 (protocol draft v0.1 values); config hash; seed derivation |
| `data.py` | Ingestion: deterministic synthetic dataset (`items-v1.0`), fixed-length JSON response encoding, SQLite build (WAL), Zipf sampler, request streams |
| `server.py` | System under test: standard-library HTTP/1.1 server on loopback; backends for A0 (full scan), A1 (LRU cache with generation-guarded invalidation), A2 (index), A3 (read micro-batching), A4 (admission limiter, HTTP 503 on overflow) |
| `loadgen.py` | Closed-loop and open-loop (intended-time latency) load generator over raw keep-alive sockets, response validation |
| `metrics.py` | Pure functions: nearest-rank percentiles, goodput, peak goodput, saturation concurrency, generator-limited rule, ratios, bootstrap, t half-width |
| `schema.py` | Versioned JSON schemas (result 1.0.0, manifest 1.0.0); validation at export and import |
| `manifest.py` | Provenance: git revision and dirty flag, versions, platform, CPU, power state, idle probe, load average |
| `runner.py` | Blocks of arms in seeded random order; fresh database and server process per run; per-level CPU and memory sampling; ApacheBench cross-check |
| `report.py` | Tables, figures, pilot analysis, runtime projection, degenerate-case list, PDF through pandoc and Typst |
| `cli.py` | `scale smoke | run | report | test`; `run` refuses confirmatory configs while the protocol is unfrozen |

Operational details that the draft protocol leaves open are recorded in `research/decision_log.md` (D-006).
