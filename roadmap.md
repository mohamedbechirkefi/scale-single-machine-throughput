<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE roadmap

Status values: `done`, `in progress`, `planned`, `blocked(<reason>)`, `gated(<gate>)`. Effort is a planning estimate in focused days (five-day target). Nothing is marked done unless its acceptance criteria were checked.

| Milestone | Priority | Effort | Depends on | Status | Blockers |
|---|---|---|---|---|---|
| M0 Bootstrap and feasibility | P0 | 0.5 d | none | done (2026-11-24; see progress.md) | none |
| M1 Research and preregistration | P0 | 0.5 d | M0 | gate passed: protocol frozen v1.0 (owner-approved 2026-11-24, D-009, `research/freeze.json`); literature open items remain | none for the freeze; EXP-002 c_max and n await the quiet-pilot rule (protocol 7.1) |
| M2 Core implementation | P0 | 1 d | M1 drafts (implementation may start before the freeze) | done (2026-11-24; see progress.md); amendments D-008 decided by the owner and applied (D-009) | none |
| M3 Experiments | P0 | 1 to 1.5 d (about 6 h to 11 h machine time) | M2, owner freeze (done) | done with documented gaps (2026-11-25) | EXP-001 and EXP-002 complete; EXP-003 not run (four unset parameters, D-014); EXP-004 optional, no frozen config; D-012 reading of the A2 exclusion awaits the owner |
| M4 Interpretation | P0 | 0.75 d | M3 | done (2026-11-25; D-015) | Pending owner decisions disclosed, not blocking: D-012 reading (A2 exclusion), EXP-003 parameters, EXP-004; owner-only placeholders listed in progress.md |
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
- [x] Smoke pilot run (exploratory) estimates the between-block SD of log R, to settle n before the freeze (J-0005, 3 blocks under heavy background load; SD above the 0.07 trigger for A1 and A2; repeat on a quiet machine recommended, D-008 item 6).
- [x] Owner decisions on the amendment proposals D-008 (2026-11-24): AM-1 to AM-4 applied, other draft parameters kept (D-009).
- [x] Owner freeze recorded with protocol hashes (G-FREEZE): `research/freeze.json`, git revision 9471b58. The EXP-002 block count and sweep top are to be set by the pre-stated quiet-pilot rule (protocol 7.1).

## M2 Core implementation (11.6: schemas, manifests, report generators alongside the core)

Tasks: data generator; server with arms A0 to A4 behind one configuration switch; load generator (closed and open loop); metrics; runner; versioned JSON result schema with validation; run manifests (runtime, peak memory, OS, CPU, package versions, git revision, config hash); report generator (Markdown, figures, Typst PDF); CLI `scale smoke | run | report | test` (the brief names the run command `run`; the protocols' `scale exp EXP-NNN` is `scale run experiments/EXP-NNN.json`).
Acceptance criteria (status 2026-11-24):
- [x] Baseline A0 implemented first, then A1 to A4 (`src/scale/server.py`).
- [x] Unit tests for deterministic functions, invalid inputs and edge cases; hand-computed metric examples; property tests (bounds, monotonicity).
- [x] Response equivalence across arms; cache invalidation; correctness under concurrency; differential test against a dictionary reference; generator cancellation and extreme parameters; coordinated-omission check.
- [x] Results validated against the schema at export and import (schema 1.0.0; report fails closed on malformed files).
- [x] Run manifests per run; `run` refuses confirmatory configs while the protocol is unfrozen (exit code 3).
- [x] Report generator: Markdown tables, PNG and SVG figure, pilot analysis, runtime projection, degenerate-case list; PDF through pandoc and Typst verified on the pilot report (7 pages, kept out of git).
- [x] Test suite executed, actual counts recorded in progress.md.
- [x] Exploratory smoke and pilot runs journaled (J-0002 to J-0007), outputs under `results/exploratory/`.

## M3 Experiments (11.6: individual reports as experiments finish)

Order: EXP-001, quiet pilot (`experiments/pilot-quiet.json`) and `scale resolve-pilot` (resolution appended to `research/freeze.json`), EXP-002, EXP-003, EXP-004 (optional). Quiet machine required (idle probe enforced).
Acceptance criteria:
- [ ] Smoke run validates metrics; labelled exploratory.
- [ ] Frozen full matrix complete, or failures documented; no silently dropped runs; generator-limited cells flagged.
- [ ] Raw machine-readable results retained (regenerable, out of git if large) with manifests and checksums.
- [ ] `research/experiments/EXP-NNN/report.md` written for each experiment as it finishes, including failed or abandoned ones.
- [ ] Journal entries in `research/experiment_journal.jsonl` for every run batch.

## M4 Interpretation (11.6: evidence audit, manuscript synthesis)

Acceptance criteria:
- [x] Confounders inspected; sensitivity analyses reported, including contradictory results (re-analysis of recorded runs only; no new measurement on a shared machine).
- [x] Claims register complete; every numerical claim maps to result id, config and figure; every external claim to a verified source (`research/publication/evidence_audit_M4.md`).
- [x] Second review pass challenging the preferred hypothesis (`research/publication/review_pass_2.md`).
- [x] Manuscript complete (about 5,700 words from abstract to conclusion); limitations updated (items 18 to 25).

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
