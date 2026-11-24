<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# tests/

pytest suite (M2). Run with `uv run pytest` or `uv run scale test`. The latest real pass/fail count is recorded in `progress.md`.

| File | Covers |
|---|---|
| `test_config.py` | Valid and invalid configs (21 invalid cases), config hash, seeds, one-factor-at-a-time arm definitions, repository configs |
| `test_data.py` | Hand-written golden response bytes, constant body length (property), hand-computed Zipf CDF, sampler properties, request mix, database build, full-scan query plan for A0 |
| `test_metrics.py` | Textbook nearest-rank percentiles, goodput and error rate, peak and saturation golden example, generator-limited rule, protocol planning half-width (0.0358), bootstrap determinism, properties (bounds, monotonicity) |
| `test_server.py` | Response equivalence across all arms; read-after-acknowledged-write per arm; cache invalidation under concurrent readers; deterministic stale-reinsert interleaving; LRU bound; no lost writes under concurrency per arm; batching correctness; admission limiter and HTTP 503; differential test of every arm against a dictionary reference model |
| `test_loadgen.py` | Response parsing, loopback-only client, validation, transport errors without crashes, cancellation, extreme parameters (128 connections, 1 ms window), coordinated-omission check under an injected stall, ApacheBench output parsing, HTTP/1.0 keep-alive for ApacheBench |
| `test_pipeline.py` | Config to runner (real server subprocess) to validated results to report; fail-closed report on a malformed result; schema rejection; hand-computed pilot analysis and runtime projection; CLI refusal of confirmatory configs; freeze-hash check |
