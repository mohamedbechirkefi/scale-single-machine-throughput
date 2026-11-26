<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# SCALE: how every session works in this repository

SCALE asks: what bottlenecks dominate local request throughput under different architecture choices? `master_prompt.md` is the authority for the project. It is saved unchanged and must never be edited. If this file and the master prompt conflict, the master prompt wins; record the conflict in `progress.md`.

## 1. Reading order (before modifying anything)

1. `master_prompt.md` (sections 1 to 11).
2. `roadmap.md`: milestones, dependencies, acceptance criteria, status, blockers.
3. `progress.md`: append-only dated journal; read the latest entry and its "next action".
4. `research/protocol.md`: the study protocol and its freeze status.
5. `research/claims_register.csv`: every claim that may appear anywhere.
6. Then, as needed: `research/decision_log.md`, `research/experiment_registry.csv`, `research/experiments/EXP-NNN/protocol.md`, `research/feasibility.md`, `research/limitations.md`, `data/manifest.json`.

At session start: run `git status`, inspect existing files, never overwrite owner changes, state the current milestone and the next bounded task.

## 2. Mandatory requirements (master prompt section 11, all sessions)

- Every planned experiment is registered in `research/experiment_registry.csv` (stable id EXP-NNN, purpose, dependency, primary outcome, protocol hash, status, report location, planned analysis) before any confirmatory execution.
- Every registered experiment has `research/experiments/EXP-NNN/protocol.md` written before it runs (structure of 11.2), and a standalone `report.md` (structure of 11.3) once it ran, failed, was abandoned or stayed exploratory. Failed, null and exploratory experiments keep their reports, visibly labelled.
- One integrated manuscript: `research/paper/manuscript.md` is the canonical source; `manuscript.tex` and `manuscript.pdf` are generated from it with the zero-cost toolchain (pandoc to Typst, compiled with the `typst` Python package; pandoc to LaTeX for the `.tex` source). No TeX distribution is installed; see D-002 in `research/decision_log.md`.
- Never fabricate a PDF, a result, a citation, a test count or a placeholder number to fill the file tree. Generated tables and figures come from versioned raw results through scripts, and are reused by reports, manuscript, demo and articles.
- An artifact manifest maps every quantitative figure, table and claim to experiment id, run ids, metric definition, result path, generator script, config or protocol hash and code revision.
- Provenance is captured while experiments run (11.6, M3), never deferred to writing.
- A second review pass challenges the preferred hypothesis. AI review is internal quality control, not peer review.
- Milestone additions of 11.6 are tracked in `roadmap.md` (M0/M1 registry and skeleton, M2 schemas and report generators, M3 per-experiment reports, M4 evidence audit and manuscript, M5 consistency, M6 PDFs and clean-clone reproduction).

## 3. Rules (all sessions)

### Gates
- Never push, add a remote, create a GitHub repository or publish anything (G-PUBLIC).
- No paid service of any kind. The coding subscription is not an inference backend.
- Never freeze a protocol yourself. Freezing is the owner's decision (G-FREEZE). Until the owner records a freeze, every run is exploratory and labelled so.
- No confirmatory experiments without an owner-recorded freeze. Small exploratory smoke checks are allowed and labelled exploratory.

### Scope
- Work only inside this repository. Tools outside it are used read-only: `../.tools/` (the shared labs tools folder: uv, typst, pypdf, pillow, pandoc) and `helix/.tools/node/bin` under the research root (the parent of `labs/`) (Node; never modify that folder).
- Do not touch any other folder under the research root.
- Never kill processes you did not start. Never delete anything you did not create in the current session.
- Localhost only. No external load testing, no traffic to any remote host from the benchmark.

### Truthfulness
- Never fabricate results, citations, test counts or PDFs.
- Record the commands you ran and their actual outputs in `progress.md`.
- A source you did not open is labelled unverified and is not cited as read.
- No extrapolation to production traffic or other hardware (master prompt section 10, claims boundary).

### Files and style
- New text and code files start with `SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0` as a comment where the format allows. JSON, JSONL and CSV are covered by `NOTICE.md`.
- The licence files (`LICENSE`, `NOTICE.md`, `LICENSE_HISTORY.md`, `CLA.md`, `.github/`) are the owner's decision and are not changed. Development commands may be appended to `CONTRIBUTING.md`.
- English. No em dashes. Plain, formal register.
- No e-mail address, personal identifier or secret in any committed file (git author metadata excepted).
- Refer to the owner as "the owner"; use they/them if a pronoun is needed.

### Git
- Local commits only, with the owner's git identity passed through `git -c user.name=... -c user.email=... commit` exactly as given in the session brief (`labs/_shared/M0-brief.md` under the research root; the address is not repeated here, to keep e-mail addresses out of committed files); the message ends with a blank line and `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Run `git status` before and after committing. `results/raw/` is listed in `.gitignore`; the M3 raw outputs are nevertheless tracked (D-017) and stay tracked (owner, 2026-11-26, decision sheet). Do not add or remove raw files without an owner decision.

## 4. Session end

1. Append a dated entry to `progress.md`: decisions, commands, actual outputs, failures, changed files, risks, next action.
2. Update `roadmap.md` statuses. Never mark incomplete work done.
3. Append decisions to `research/decision_log.md` (next free id).
4. If code changed, run the test suite and record the real result, or record why it was not run.
