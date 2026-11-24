<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE: how much work can one computer actually handle? (working title)

**Question.** What bottlenecks dominate local request throughput under different architecture choices?

**Status: M0 (bootstrap and feasibility), 2026-11-24.** No experiment has run. There are no findings. The study protocol is a draft awaiting the owner's freeze; until then any run is exploratory.

## Why it matters

Caching, database indexes, request batching and bounded concurrency are standard answers to "the server is slow". SCALE measures, on one machine and one controlled workload, how much each of them changes successful throughput when applied alone to a simple baseline, with paired replicates and uncertainty intervals, and checks whether the answer survives a different load model and different workload parameters.

## What is implemented

Nothing yet beyond the control files and draft protocols. Implementation starts at M2 (`roadmap.md`).

## Planned design (draft)

- One Python standard-library HTTP server with SQLite on `127.0.0.1`; synthetic, seeded data.
- Baseline A0 versus A1 cache, A2 index, A3 batching, A4 bounded concurrency, one factor at a time.
- Primary metric: peak goodput over a closed-loop concurrency sweep; latency p50/p95/p99, errors, CPU and memory as secondary metrics.
- Details: [`research/protocol.md`](research/protocol.md), [`research/feasibility.md`](research/feasibility.md).

## Experiments

| ID | Title | Status |
|---|---|---|
| EXP-001 | Load-generator and measurement validation | planned (protocol draft, awaiting owner freeze) |
| EXP-002 | One-factor-at-a-time comparison (primary) | planned (protocol draft, awaiting owner freeze) |
| EXP-003 | Open-loop SLO goodput (sensitivity) | planned (protocol draft, awaiting owner freeze) |
| EXP-004 | Workload sensitivity (optional) | planned (protocol draft, awaiting owner freeze) |

Registry: [`research/experiment_registry.csv`](research/experiment_registry.csv).

## Data

No external dataset. All data are synthetic and regenerated from recorded seeds ([`data/manifest.json`](data/manifest.json)).

## Scope and limitations

Localhost only, one laptop, one implementation. No claim about production traffic or other hardware. See [`research/limitations.md`](research/limitations.md).

## Quick start

Not available yet (M2). The dependency lockfile is `uv.lock`.

## Licence

SCALE Source-Available Non-Commercial Research License v1.0 (`LicenseRef-SCALE-NC-Research-1.0`); see [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md). This is a custom source-available licence, not an OSI-approved open-source licence. Third-party material keeps its own terms.

## Citation

See [`CITATION.cff`](CITATION.cff). This is an independent research project, not peer reviewed.
