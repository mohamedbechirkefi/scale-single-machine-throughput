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
