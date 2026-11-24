<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE roadmap

Status values: `done`, `in progress`, `planned`, `blocked(<reason>)`, `gated(<gate>)`. Effort is a planning estimate in focused days (five-day target). Nothing is marked done unless its acceptance criteria were checked.

| Milestone | Priority | Effort | Depends on | Status | Blockers |
|---|---|---|---|---|---|
| M0 Bootstrap and feasibility | P0 | 0.5 d | none | done (2026-11-24; see progress.md) | none |
| M1 Research and preregistration | P0 | 0.5 d | M0 | in progress (drafts written; freeze pending) | gated(G-FREEZE): owner review and freeze of the protocol |
| M2 Core implementation | P0 | 1 d | M1 drafts (implementation may start before the freeze) | planned | none |
| M3 Experiments | P0 | 1 d (about 6 h machine time) | M2, owner freeze | planned | gated(G-FREEZE) for confirmatory runs |
| M4 Interpretation | P0 | 0.75 d | M3 | planned | none |
| M5 Interactive experience | P1 | 0.75 d | M4 | planned | none |
| M6 Release candidate | P0 | 0.5 d | M4, M5 | planned | gated(G-PUBLIC) for any publication |

## M0 Bootstrap and feasibility (done)

Acceptance criteria:
- [x] Control files of master prompt section 2 and the section 11.1 tree created (no placeholder results, no PDFs).
- [x] Feasibility audit with commands and outputs (`research/feasibility.md`).
- [x] Source audit with access levels and licences (`research/literature_review.md`, `data/manifest.json`).
- [x] Budget (zero cost), scope, exclusions and fallback written.
- [x] 11.6 M0/M1: registry initialised, manuscript skeleton created, zero-cost toolchain confirmed by an exploratory smoke compile (see progress.md).
- [x] Dependency lockfile produced or failure recorded.
- Gate: the owner can understand the question, cost and exclusions from README.md, `research/protocol.md` and `research/feasibility.md`.

## M1 Research and preregistration

Tasks: complete the literature search (open items in `research/literature_review.md` section 4); formal model and notation in the manuscript skeleton; finalise the EXP-001 to EXP-004 protocols; fixture manifest; owner freeze.
Acceptance criteria:
- [x] Draft study protocol with H0/H1, baseline, primary metric, units, seeds, sample-size rationale, uncertainty, exclusions, stopping, smoke and full matrices, sensitivity analyses.
- [x] Draft per-experiment protocols (11.2 structure) and registry rows.
- [ ] Literature open items resolved or explicitly left unverified.
- [ ] Smoke pilot run (exploratory) estimates the between-block SD of log R, to settle n before the freeze.
- [ ] Owner freeze recorded with protocol hashes (G-FREEZE). Confirmatory runs are not allowed before this.

## M2 Core implementation (11.6: schemas, manifests, report generators alongside the core)

Tasks: data generator; server with arms A0 to A4 behind one configuration switch; load generator (closed and open loop); metrics; runner; versioned JSON result schema with validation; run manifests (runtime, peak memory, OS, CPU, package versions, git revision, config hash); report generator (Markdown, figures, Typst PDF); CLI `scale smoke | exp | report | test`.
Acceptance criteria:
- [ ] Baseline A0 implemented first, then A1 to A4.
- [ ] Unit tests for deterministic functions, invalid inputs and edge cases; hand-computed metric examples; property tests (bounds, monotonic counts).
- [ ] Response equivalence across arms; cache invalidation; correctness under concurrency; generator cancellation and extreme parameters.
- [ ] Results validated against the schema at export and import.
- [ ] Test suite executed, actual counts recorded in progress.md.

## M3 Experiments (11.6: individual reports as experiments finish)

Order: smoke matrix, EXP-001, EXP-002, EXP-003, EXP-004 (optional).
Acceptance criteria:
- [ ] Smoke run validates metrics; labelled exploratory.
- [ ] Frozen full matrix complete, or failures documented; no silently dropped runs; generator-limited cells flagged.
- [ ] Raw machine-readable results retained (regenerable, out of git if large) with manifests and checksums.
- [ ] `research/experiments/EXP-NNN/report.md` written for each experiment as it finishes, including failed or abandoned ones.
- [ ] Journal entries in `research/experiment_journal.jsonl` for every run batch.

## M4 Interpretation (11.6: evidence audit, manuscript synthesis)

Acceptance criteria:
- [ ] Confounders inspected; sensitivity analyses reported, including contradictory results.
- [ ] Claims register complete; every numerical claim maps to result id, config and figure; every external claim to a verified source.
- [ ] Second review pass challenging the preferred hypothesis.
- [ ] Manuscript complete (3,000 to 6,000 words where justified); limitations updated.

## M5 Interactive experience (11.6: identical results and labels across outputs)

Static benchmark report plus an interactive resource and latency explorer of recorded runs (TypeScript, React, Vite, using Node read-only from the shared tools folder, unless a simpler static page is justified).
Acceptance criteria:
- [ ] Offline after initial load; fails closed on malformed results; keyboard usable; reduced motion; mobile layout; accessible contrast.
- [ ] Measured results, sandbox results and assumptions visibly distinguished; no fabricated data.
- [ ] Demo, paper, reports and articles use the same verified numbers and labels.

## M6 Release candidate (11.6: PDFs, clean-clone reproduction)

Acceptance criteria:
- [ ] Manuscript and report PDFs compiled with the Typst path and visually inspected; `manuscript.tex` generated.
- [ ] Clean clone into a separate directory: locked install, tests, smoke reproduction, demo build; actual outputs recorded.
- [ ] Data manifests, links and references verified; secret and licence scan.
- [ ] `research/publication/` checklists completed; owner review recorded.
- [ ] No push or publication without the owner's explicit approval (G-PUBLIC).

## Five-day plan (planning estimate)

| Day | Work |
|---|---|
| 1 | M0 (done), M1 drafts (done), literature open items |
| 2 | M2 core, tests, schemas, smoke pilot (exploratory); owner freeze requested |
| 3 | M3 runs after the freeze; per-experiment reports |
| 4 | M4 analysis, claims audit, manuscript |
| 5 | M5 demo, M6 release candidate |

Cut order if the target is threatened: EXP-004, then EXP-003 reduced to A0 plus the top two arms, then the demo reduced to a static page. Controls and reporting are never cut.
