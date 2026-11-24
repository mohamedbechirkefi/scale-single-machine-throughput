<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Decision log

Append-only. Each entry: id, date, decision, decided by, context, alternatives, consequences.

## D-001 (2026-11-24): Licence chosen by the owner

- **Decided by:** the owner.
- **Decision:** all original material in this repository is licensed under the SCALE Source-Available Non-Commercial Research License v1.0 (SPDX `LicenseRef-SCALE-NC-Research-1.0`), with a CLA for contributions, from the first commit.
- **Context:** `master_prompt.md` section 2 asks for an "owner-approved permissive code license". On 2026-11-24 the owner chose this protective, non-permissive licence instead, for their own protection. The licence package (`LICENSE`, `NOTICE.md`, `LICENSE_HISTORY.md`, `CLA.md`, `CONTRIBUTING.md`, `.github/`) was committed in the initial commit.
- **Consequences:** the project is source-available, not OSI open source. README and CITATION.cff must not describe it as open source. Third-party data and dependencies keep their own licences, recorded separately. AI sessions do not change the licence files.

## D-002 (2026-11-24): Zero-cost publication toolchain

- **Decided by:** AI assistant, following the session brief; open to owner review.
- **Decision:** Markdown is the canonical source. PDFs are produced by pandoc 3.6.3 (`-t typst`) and compiled with the `typst` 0.15.0 Python package. `manuscript.tex` is generated from Markdown by pandoc (`-t latex -s`) as a source artifact; it is not compiled locally.
- **Context:** no TeX distribution is installed; installing one is not needed and would add maintenance cost.
- **Alternatives:** install TeX Live (large, not needed); Chrome headless HTML to PDF (less control over equations and references).
- **Consequences:** M6 must visually inspect the Typst-compiled PDFs. The `.tex` file is checked for well-formedness only and is never described as compiled.

## D-003 (2026-11-24): Stack and system under test (proposal)

- **Decided by:** AI assistant, proposal pending the owner's protocol freeze.
- **Decision:** Python 3.12 standard library server (`http.server`, `socketserver`, `sqlite3`) and a Python load generator, with ApacheBench 2.3 (preinstalled) as a differential reference. Analysis with numpy; figures with matplotlib; schemas with jsonschema; process metrics with psutil; tests with pytest and hypothesis.
- **Context:** master prompt section 4 prefers Python and minimal pinned dependencies. A standard-library server keeps the baseline simple and the mechanisms visible.
- **Alternatives:** asyncio or a third-party framework (adds a confound: the framework, not the factor, may dominate); a compiled generator such as wrk2 (not installed; would need a build toolchain).
- **Consequences:** results describe this Python implementation only. The generator ceiling must be measured (EXP-001).

## D-004 (2026-11-24): Primary metric and design (proposal)

- **Decided by:** AI assistant, proposal pending the owner's freeze.
- **Decision:** primary metric is peak goodput G* over a fixed closed-loop concurrency sweep; primary effect is the within-block ratio to the baseline, summarised by geometric mean with percentile bootstrap over 10 paired blocks; open-loop SLO goodput and workload variants are sensitivity experiments.
- **Context:** the research question is about throughput; goodput (validated HTTP 200 only) prevents fast failure or stale responses from counting as capacity.
- **Consequences:** latency, errors, CPU and memory are secondary and reported in full.

## D-005 (2026-11-24): Dependency resolution cut-off

- **Decided by:** AI assistant, following the brief.
- **Decision:** `pyproject.toml` sets `[tool.uv] exclude-newer = "2026-11-10T00:00:00Z"`, so every locked version was released at least two weeks before 2026-11-24.
- **Consequences:** upgrades require a dated decision entry.

## D-006 (2026-11-24): Operational details of the M2 implementation (proposal)

- **Decided by:** AI assistant at M2; open to owner review before the freeze. None of these changes the draft protocol's hypotheses, metrics or analysis.
- **Decisions.**
  1. *Response encoding.* Read responses are JSON with numbers right-aligned by spaces, so every body has the same length and stays valid JSON (zero padding would be invalid JSON). Writes are `POST /item/<sku>/price?cents=<n>`; the new price is in the query string.
  2. *A1 invalidation.* Write path: commit, then under the cache lock bump a per-key generation and drop the entry, then acknowledge. A reader inserts its database result only if the key's generation did not change during its read, so a read that started before a write cannot re-insert the old value after the write is acknowledged.
  3. *A3 batching.* One batcher thread collects reads for at most 1 ms or 32 requests and runs one `SELECT ... WHERE sku IN (...)` over distinct keys. Writes are not batched.
  4. *A4 bounded concurrency.* Connections keep one thread each (identical HTTP layer); the limit is applied per request: at most W = 8 requests do database work, at most Q = 64 more wait, any further request gets HTTP 503 at once. This is a request-level admission limiter, not a fixed pool of connection threads; the owner may prefer the latter before the freeze.
  5. *Listen backlog.* `request_queue_size = 128` for every arm (the standard-library default of 5 would refuse connection bursts at c = 64).
  6. *Generator.* Raw-socket keep-alive client, one thread per connection, in `generator_processes` spawned processes. A request counts toward a level if it completes inside the measurement window; latencies are recorded for validated 200 responses only. Generator CPU is the CPU time of the generator processes over the window divided by wall time.
  7. *Server CPU and memory.* Process CPU over the measurement window via psutil; RSS at the end of each level; peak RSS from `getrusage` at the end of the run.
  8. *Idle probe.* Recorded for every run; enforced (run excluded) only when the config says so. Confirmatory configs must enforce it (validated).
  9. *Confirmatory guard.* `scale run` refuses a confirmatory config unless the status row of `research/protocol.md` says FROZEN and the config's `protocol_sha256` matches the protocol file (exit code 3).
- **Consequences.** These choices are documented in `src/README.md` and tested in `tests/`. They can be changed before the freeze at no cost beyond re-running the exploratory smoke.

## D-007 (2026-11-24): Build backend and CLI entry point

- **Decided by:** AI assistant at M2.
- **Decision.** `pyproject.toml` now builds the `scale` package with `uv_build` (`>=0.9.5,<0.10`, the backend matching the installed uv 0.9.5, released 2025-10) and exposes the `scale` command. `package = false` was removed. `uv lock` changed only the project's own entry in `uv.lock` (version 0.0.1 to 0.1.0); no third-party dependency was added or upgraded.
- **Consequences.** `uv sync --locked` installs the package in editable mode; `uv run scale ...` works from the repository root.

## D-008 (2026-11-24): Proposed protocol amendments from the exploratory pilot (pending the owner)

- **Decided by:** nobody yet. These are AI-assistant proposals for the owner to accept, change or reject before the freeze (G-FREEZE). `research/protocol.md` and the EXP protocols were **not** changed.
- **Evidence.** Exploratory runs J-0002 to J-0007 (`research/experiment_journal.jsonl`, `results/exploratory/`), all made while other workloads loaded the machine (idle probe 22.6 % to 100 %, threshold 15 %). Planning input only, not findings.
- **Proposals.**
  1. *A4 cannot shed load in the planned sweep.* W + Q = 8 + 64 = 72 exceeds the largest closed-loop concurrency (64), so no request can ever be rejected; the pilot recorded 0 rejections and R_A4 about 1.01. Options: Q = 16 (W + Q = 24, so shedding is possible at c = 32 and 64), or extend the sweep beyond 72, or redefine A4 explicitly as "database concurrency cap only".
  2. *The baseline makes the index dominant almost by construction.* A0 scans 200,000 rows per lookup; the pilot's within-block ratio for A2 was about 249. Options: state this expectation in the protocol; promote EXP-004 V1 (N = 10,000) from optional to required; or register a second-stage experiment with A2 as the baseline for cache, batching and bounded concurrency (a new EXP id with its own hypotheses).
  3. *The concurrency sweep truncates G\* for several arms.* A1 and A3 peaked at c = 64 in every block (A3 still rising steeply), so G\* is the value at the top of the sweep, not a saturation peak. Options: extend to c in {..., 128, 256} (listen backlog is 128; raise it with the sweep), or keep the range and report G\* as "maximum over the fixed sweep" with the truncation flagged.
  4. *A1 is measured cold.* About 1,400 reads per pilot run against a 20,000-entry cache gave hit ratios of 0.34 to 0.36. With a time-based warmup, A1's effect depends on how many requests the warmup happens to contain. Options: warm up by request count (identical prefix for every arm), or a longer warmup for all arms, or keep and describe A1 as cold-start behaviour.
  5. *The generator-limited rule would exclude A2's peak.* A2's peak goodput (12,773 to 20,643 rps at c = 1) exceeds 50 % of the observed null-endpoint ceiling (19,594 to 27,666 rps), so under protocol section 4 those cells would be excluded and A2's G\* would be undefined. With 2 generator processes the null result rose from 19,594 to 27,666 rps (confounded by changing background load). Options: use 2 or 4 generator processes for EXP-002 and fix the count in EXP-001; revisit the 50 % threshold after EXP-001.
  6. *Between-block SD of log R exceeds the 0.07 trigger* for A1 (0.092) and A2 (0.248), from 3 blocks under heavy background load (A3 0.043, A4 0.045). Recommendation: repeat the pilot on a quiet machine before choosing n; if the SD stays above 0.07, n = 20 (projected EXP-002 time about 4.1 h instead of 2.0 h).
  7. *Idle probe.* Every exploratory run would have failed the 15 % probe. Confirmatory runs need a period without other agents' workloads; the runner enforces the probe for confirmatory configs.
  8. *Runtime is as planned.* Measured worst per-run overhead 4.0 s; projected EXP-002 run 146 s, 50 runs 2.03 h (planning value 150 s, 2.1 h). No amendment needed.
- **Consequences.** None until the owner decides. Any accepted change is made to the draft protocol before the freeze, with a dated note.
