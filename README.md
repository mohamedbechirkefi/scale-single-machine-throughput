<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE: how much work can one computer actually handle? (working title)

**Question.** What bottlenecks dominate local request throughput under different architecture choices?

**Status: M2 (core implementation) done, 2026-11-24.** No confirmatory experiment has run. There are no findings. The study protocol is **frozen v1.0 (owner-approved 2026-11-24)**; freeze record `research/freeze.json`. The EXP-002 sweep top and block count are to be set by a pre-stated rule from a quiet-machine pilot (protocol section 7.1). Runs made before the freeze are exploratory. Exploratory smoke and pilot runs (harness checks, planning values) are under `results/exploratory/` and are not results.

## Why it matters

Caching, database indexes, request batching and bounded concurrency are standard answers to "the server is slow". SCALE measures, on one machine and one controlled workload, how much each of them changes successful throughput when applied alone to a simple baseline, with paired replicates and uncertainty intervals, and checks whether the answer survives a different load model and different workload parameters.

## What is implemented

- The `scale` Python package (`src/scale/`): synthetic dataset and request streams, the HTTP server with arms A0 to A4, closed-loop and open-loop load generator, metrics, runner, versioned result schema with run manifests, report generator and CLI. See `src/README.md`.
- A pytest suite (`tests/`, see `tests/README.md`); the latest real count is in `progress.md`.
- Experiment configs (`experiments/`). `scale run` accepts a confirmatory config only if its file and protocol hashes match the freeze record.
- No demo yet (M5).

## Design (frozen v1.0)

- One Python standard-library HTTP server with SQLite on `127.0.0.1`; synthetic, seeded data.
- Baseline A0 versus A1 cache, A2 index, A3 batching, A4 bounded concurrency (8 workers, queue 16), one factor at a time. Against the full-scan baseline the index is expected to win by design.
- Primary metric: peak goodput over a closed-loop concurrency sweep; latency p50/p95/p99, errors, CPU and memory as secondary metrics.
- Details: [`research/protocol.md`](research/protocol.md), [`research/feasibility.md`](research/feasibility.md).

## Experiments

| ID | Title | Status |
|---|---|---|
| EXP-001 | Load-generator and measurement validation | frozen (owner-approved 2026-11-24), not yet run |
| EXP-002 | One-factor-at-a-time comparison (primary) | frozen (owner-approved 2026-11-24), not yet run; c_max and n await the quiet pilot rule |
| EXP-003 | Open-loop SLO goodput (sensitivity) | frozen (owner-approved 2026-11-24), not yet run |
| EXP-004 | Workload sensitivity (optional) | frozen (owner-approved 2026-11-24), not yet run |

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

`uv run scale run experiments/EXP-001.json` is accepted (frozen config; confirmatory runs are scheduled separately on a quiet machine). `uv run scale run experiments/EXP-002.json` is refused until the quiet-pilot rule is applied (`uv run scale resolve-pilot <pilot results dir>`).

## Licence

SCALE Source-Available Non-Commercial Research License v1.0 (`LicenseRef-SCALE-NC-Research-1.0`); see [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md). This is a custom source-available licence, not an OSI-approved open-source licence. Third-party material keeps its own terms.

## Citation

See [`CITATION.cff`](CITATION.cff). This is an independent research project, not peer reviewed.
