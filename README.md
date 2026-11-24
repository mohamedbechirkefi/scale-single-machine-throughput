<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE: how much work can one computer actually handle? (working title)

**Question.** What bottlenecks dominate local request throughput under different architecture choices?

**Status: M2 (core implementation) done, 2026-11-24.** No confirmatory experiment has run. There are no findings. The study protocol is a draft awaiting the owner's freeze; until then every run is exploratory. Exploratory smoke and pilot runs (harness checks, planning values) are under `results/exploratory/` and are not results.

## Why it matters

Caching, database indexes, request batching and bounded concurrency are standard answers to "the server is slow". SCALE measures, on one machine and one controlled workload, how much each of them changes successful throughput when applied alone to a simple baseline, with paired replicates and uncertainty intervals, and checks whether the answer survives a different load model and different workload parameters.

## What is implemented

- The `scale` Python package (`src/scale/`): synthetic dataset and request streams, the HTTP server with arms A0 to A4, closed-loop and open-loop load generator, metrics, runner, versioned result schema with run manifests, report generator and CLI. See `src/README.md`.
- A pytest suite (`tests/`, see `tests/README.md`); the latest real count is in `progress.md`.
- Experiment configs (`experiments/`). Confirmatory configs are refused until the owner freezes the protocol.
- No demo yet (M5).

## Planned design (draft)

- One Python standard-library HTTP server with SQLite on `127.0.0.1`; synthetic, seeded data.
- Baseline A0 versus A1 cache, A2 index, A3 batching, A4 bounded concurrency, one factor at a time.
- Primary metric: peak goodput over a closed-loop concurrency sweep; latency p50/p95/p99, errors, CPU and memory as secondary metrics.
- Details: [`research/protocol.md`](research/protocol.md), [`research/feasibility.md`](research/feasibility.md).

## Experiments

| ID | Title | Status |
|---|---|---|
| EXP-001 | Load-generator and measurement validation | exploratory smoke checks only (2026-11-24); confirmatory run awaits owner freeze |
| EXP-002 | One-factor-at-a-time comparison (primary) | planned (protocol draft, awaiting owner freeze) |
| EXP-003 | Open-loop SLO goodput (sensitivity) | planned (protocol draft, awaiting owner freeze) |
| EXP-004 | Workload sensitivity (optional) | planned (protocol draft, awaiting owner freeze) |

Registry: [`research/experiment_registry.csv`](research/experiment_registry.csv).

## Data

No external dataset. All data are synthetic and regenerated from recorded seeds ([`data/manifest.json`](data/manifest.json)).

## Scope and limitations

Localhost only, one laptop, one implementation. No claim about production traffic or other hardware. See [`research/limitations.md`](research/limitations.md).

## Quick start

    uv sync --locked                      # environment from uv.lock
    uv run scale test -q                  # test suite
    uv run scale smoke                    # exploratory smoke matrix (about 40 s)
    uv run scale report results/exploratory/<dir> [--pdf]

`uv run scale run experiments/EXP-002.json` refuses to start while the protocol is unfrozen.

## Licence

SCALE Source-Available Non-Commercial Research License v1.0 (`LicenseRef-SCALE-NC-Research-1.0`); see [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md). This is a custom source-available licence, not an OSI-approved open-source licence. Third-party material keeps its own terms.

## Citation

See [`CITATION.cff`](CITATION.cff). This is an independent research project, not peer reviewed.
