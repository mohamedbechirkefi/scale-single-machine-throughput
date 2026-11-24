<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Progress journal (append-only)

## 2026-11-24: Session M0 (bootstrap and feasibility, M1 drafts)

**Milestone:** M0, plus the M1 drafts that M0 asks for. **Next bounded task at start:** create the control files and propose the protocol.

### Starting state
`git status`: `On branch main`, `nothing to commit, working tree clean`. One commit, `2861fa5` (master prompt and the owner's licence package). `master_prompt.md` read in full and left unchanged.

### Decisions
D-001 licence chosen by the owner (recorded first); D-002 zero-cost Typst toolchain; D-003 standard-library Python stack (proposal); D-004 primary metric and design (proposal); D-005 dependency cut-off 2026-11-10. See `research/decision_log.md`.

### Commands and actual outputs (trimmed only where marked)
- `sysctl -n machdep.cpu.brand_string hw.ncpu hw.memsize hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu` gave `Apple M1 Pro`, `10`, `17179869184`, `8`, `2`.
- `sw_vers` gave `ProductVersion: 15.3.1`, `BuildVersion: 24D70`.
- `df -h /Users/bechir/research/labs` gave `460Gi 311Gi 129Gi 71%`.
- `/usr/local/bin/python3 --version` gave `Python 3.12.1`; `sqlite3.sqlite_version` gave `3.43.1`.
- `uv --version` gave `uv 0.9.5 (d5f39331a 2025-10-21)`. `ls .tools/py/bin` showed no `typst` executable; the `typst` Python module imports as version `0.15.0`, with `pypdf 6.20.0` and `pillow 11.3.0`.
- `pandoc --version` gave `pandoc 3.6.3`; `node --version` gave `v22.23.3`; `git --version` gave `git version 2.42.1`.
- `which wrk ab hey oha k6 locust`: only `/usr/sbin/ab` found (`ApacheBench, Version 2.3 <$Revision: 1913912 $>`).
- `ulimit -n` gave `1048576`; `launchctl limit maxfiles` gave soft `256`; `kern.ipc.somaxconn` gave `128`.
- Literature: Crossref API lookups for six DOIs returned the metadata recorded in `research/paper/references.bib`; ACM and INFORMS publisher pages returned HTTP 403 (not read). Sources opened and access levels: `research/literature_review.md`.
- `uv lock` gave `Using CPython 3.12.1 interpreter at: /Library/Frameworks/Python.framework/Versions/3.12/bin/python3` and `Resolved 26 packages in 154ms`; locked versions include numpy 2.5.4, psutil 7.2.2, jsonschema 4.26.0, matplotlib 3.11.2, pytest 9.2.0, hypothesis 6.170.15.
- Toolchain smoke (exploratory, J-0001): first `typst.compile` failed with `typst.TypstError: font fallback list must not be empty`. With `-V mainfont="Libertinus Serif"` it compiled a 3-page skeleton PDF; page 1 inspected as PNG. The PDF stays in the session scratchpad and is not committed. `pandoc -t latex` produced `research/paper/manuscript.tex` (exit 0, not compiled).

### Files created
`CLAUDE.md`, `roadmap.md`, `progress.md`, `README.md`, `CITATION.cff`, `pyproject.toml`, `uv.lock`; `research/` (`decision_log.md`, `literature_review.md`, `protocol.md`, `feasibility.md`, `limitations.md`, `claims_register.csv` (header only), `experiment_journal.jsonl` (J-0001), `experiment_registry.csv` (EXP-001 to EXP-004), `experiments/EXP-00{1,2,3,4}/protocol.md`, `paper/manuscript.md` (headings only), `paper/manuscript.tex` (generated), `paper/references.bib`, `paper/supplementary.md`, `paper/figures/README.md`, `publication/` checklists and `artifact_manifest.json`); `data/manifest.json`; READMEs in `results/`, `src/`, `tests/`, `experiments/`, `demo/`, `articles/`. `CONTRIBUTING.md`: development commands appended (section 6). Licence files unchanged.

### Not done, and why
- No tests exist or were run: no code yet (M2).
- No experiment run; no confirmatory work (G-FREEZE).
- The smoke pilot that estimates the between-block SD (needed to settle n) requires the M2 harness.
- `pyproject.toml` sets `package = false`, so the `scale` CLI named in the protocols does not exist yet; it is added at M2 together with a build backend.
- `.gitignore` belongs to the owner's committed package and was not changed; generated `manuscript.typ` and PDFs must be kept out of commits by hand until the owner decides.

### Outstanding risks
Generator and server share the CPU; the workload parameters may decide the answer; closed-loop bias; thermal drift. See `research/feasibility.md` section 7.

### Owner decisions requested
1. Review and freeze the protocol (`research/protocol.md`, EXP-001 to EXP-004), or request changes. In particular: N = 200,000 rows, Zipf s = 0.99, 2 % writes, SLO 50 ms, 10 blocks, the practical threshold [0.95, 1.05].
2. Confirm the standard-library server and Python generator (D-003), or approve a free compiled generator.
3. Approve author metadata and the AI-assistance disclosure wording before any manuscript text is written.
4. Decide whether `.gitignore` may be extended for generated paper artifacts.

### Next action
M2: implement the data generator and baseline A0, the closed-loop generator, the result schema and the first tests; then the exploratory smoke pilot.
