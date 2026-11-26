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

## 2026-11-24: Session M2 (core implementation while the freeze is pending)

**Milestone:** M2. **Next bounded task at start:** implement the data generator, baseline A0, generator, schema and tests, then the exploratory smoke pilot (previous entry's next action). Brief: `labs/_shared/M2-brief.md`.

### Starting state
`git status`: `On branch main`, `nothing to commit, working tree clean`; HEAD `98e5c77`. Protocol `research/protocol.md` still DRAFT v0.1, not frozen.

### Implemented
- Package `scale` in `src/scale/` (see `src/README.md`): `config` (typed validated configs, arms A0 to A4), `data` (dataset `items-v1.0`, response encoding, SQLite build, Zipf sampler, request streams), `server` (A0 first, then A1 to A4), `loadgen` (closed and open loop), `metrics` (pure functions), `schema` (result and manifest schema 1.0.0, validated at export and import), `manifest`, `runner`, `report`, `cli` (`scale smoke | run | report | test`).
- Configs in `experiments/`: exploratory `smoke`, `smoke-null`, `smoke-null-gp2`, `pilot`, `stall-open`, `stall-closed`; confirmatory `EXP-001`, `EXP-002` with draft values, refused by the CLI while unfrozen.
- Build backend and entry point (D-007). Operational choices left open by the draft protocol recorded as D-006.

### Commands and actual outputs (trimmed only where marked)
- `uv lock` gave `Resolved 26 packages`; `uv sync --locked` installed `scale-single-machine-throughput==0.1.0` (editable). No third-party dependency added or upgraded.
- `.venv/bin/scale run experiments/EXP-002.json` gave `REFUSED: EXP-002 is confirmatory and research/protocol.md is not frozen (owner decision, G-FREEZE).`, exit code 3.
- First full pytest run: `2 failed, 94 passed`. (1) `test_transport_errors_counted_not_crashing`: a refused connection raised `ConnectionRefusedError` outside the client's error handling and killed the generator thread; fixed in `loadgen.HttpClient.request`. (2) `test_cache_invalidation_under_concurrent_readers`: the test's oracle flagged reads that returned a value newer than the last acknowledgement (committed but not yet acknowledged), which is not staleness; the oracle was corrected to flag only older values.
- Mutation checks (temporary edits to `server.py`, reverted from a backup, `git diff` clean afterwards): removing A1 invalidation failed 3 tests; removing the generation guard failed the concurrent-readers test. The concurrent-readers test alone initially missed the no-invalidation mutant (original prices were above the written values); the written values were moved above every generated price and the mutant is now caught by it too.
- Exploratory runs (all labelled exploratory, J-0002 to J-0007, outputs in `results/exploratory/`). The machine was shared with other agents' workloads throughout: 1-minute load average 10.9 to 82.9, idle probe 22.6 % to 100 % (every run would have failed the 15 % probe). All throughput numbers are noisy.
  - `scale smoke --config experiments/smoke-null.json`: ab cross-check returned nothing and the run took 70.4 s; ab output `apr_pollset_poll: The timeout specified has expired (70007)`. Cause: ApacheBench `-k` speaks HTTP/1.0 and waits for `Connection: keep-alive` in the response. Fixed in `server.py`, regression test added; the failed run is kept (J-0002).
  - Rerun (J-0003): c=1 SCALE 21426.3 rps vs ab 21640.97 rps (ratio 0.990); c=8 19594.0 vs 20680.54 (0.947).
  - `scale smoke` (J-0004): A2 G* 9192.3 rps, A0 G* 73.3 rps, zero errors, about 20 s per run.
  - `scale smoke --config experiments/pilot.json` (J-0005): 15 runs, all ok, 291.1 s; 18.9 to 19.9 s per run. Geometric mean within-block R (SD of log R): A1 1.711 (0.092), A2 248.975 (0.248), A3 12.844 (0.043), A4 1.014 (0.045).
  - Stall check (J-0006): open loop intended-time p99 191.66 ms; closed loop p99 0.85 ms for the same injected 200 ms pause every 2 s.
  - Two generator processes on /null at c=8 (J-0007): 27666.0 rps.
- `scale report <dir>` for every exploratory directory: Markdown, `summary.json`, PNG/SVG figure. `scale report <copy> --pdf` in the session scratchpad: 7-page PDF, figure page inspected as PNG; the PDF and `.typ` are not committed (M0 `.gitignore` question still open).
- `uv run scale test -q` first failed with `scale: error: unrecognized arguments: -q` (argparse did not pass leading options to pytest); fixed in `cli.main`, test added. Then `100 passed in 23.97s`. After the last edit (tools path in `report.py`, PDF rebuilt successfully) the final run before committing gave `100 passed in 23.59s` (0 failed).

### Smoke-run measurements for the owner (exploratory, noisy)
- **Runtime per run:** 18.9 to 20.3 s for 3 levels of 2 s + 3 s; worst overhead outside measurement windows 4.0 s.
- **Projected full matrix:** EXP-002 about 146 s per run, 50 runs about 2.03 h (planning value 2.1 h); with n = 20 blocks about 4.1 h.
- **Seed spread:** SD of log R from 3 blocks: A1 0.092, A2 0.248, A3 0.043, A4 0.045. A1 and A2 exceed the 0.07 trigger, under heavy background load. The planned n = 10 cannot be confirmed from this pilot.
- **Degenerate cases:** A4 never rejected a request (W + Q = 72 > c max 64); A1 cache hit ratio 0.34 to 0.36 (cold); A1 and A3 peak at the top of the sweep (G* truncated); A2 peaks at c = 1 and falls with c; A2's peak exceeds 50 % of the null ceiling, so the draft generator-limited rule would exclude it.

### Proposed amendments (owner decision; protocol not changed)
D-008 in `research/decision_log.md`: (1) A4 queue size or sweep range; (2) baseline full scan makes the index dominant almost by construction; (3) sweep range truncates G*; (4) cold A1 cache, warmup by request count; (5) generator-limited rule versus A2's peak, more generator processes; (6) repeat the pilot on a quiet machine before choosing n; (7) idle probe needs a quiet machine; (8) runtime as planned.

### Files changed
New: `src/scale/*.py`, `tests/*.py`, `experiments/*.json`, `results/exploratory/` (7 run directories). Modified: `pyproject.toml`, `uv.lock`, `README.md`, `CONTRIBUTING.md` (development commands appended), `roadmap.md`, `data/manifest.json`, `research/decision_log.md` (D-006 to D-008), `research/experiment_journal.jsonl` (J-0002 to J-0007), `research/experiment_registry.csv` (statuses), READMEs of `src/`, `tests/`, `experiments/`, `results/`. Licence files and `master_prompt.md` unchanged.

### Not done, and why
- No confirmatory run and no freeze (G-FREEZE).
- EXP-003 open-loop ladder runs only as a mechanism check (stall configs); no EXP-003 or EXP-004 config yet, because their ladders and variants depend on owner decisions (D-008).
- No per-experiment `report.md`: no registered experiment has run; the exploratory runs are smoke checks recorded in the journal and in `results/exploratory/*/report.md`.
- Generated PDFs not committed (open `.gitignore` question from M0).

### Outstanding risks
Background load from other workloads on this machine; the dominance of the index by construction; generator ceiling close to A2's peak.

### Next action
Owner: decide on D-008 and freeze the protocol. Then M3: EXP-001 on a quiet machine, then EXP-002.

## 2026-11-24: Session FREEZE (owner-approved amendments and protocol freeze)

**Milestone:** M1 gate (G-FREEZE). **Brief:** `labs/_shared/FREEZE-brief.md`; authority: SCALE section of `labs/_shared/owner-approvals-2026-11-24.md`; coordinator instruction: freeze everything else and record the seed count as "to be set by the pre-stated rule from the quiet pilot".

### Starting state
`git status`: clean on `main`, HEAD `a725d3f`.

### Amendments applied (protocol section 15, D-009)
- AM-1: A4 queue Q = 16 (was 64), W = 8 (`src/scale/config.py`).
- AM-2: protocol sections 3 and 5, EXP-002 items 2, 4, 5, limitation 10 state that the index wins by design against the full-scan baseline.
- AM-3: sweep 1 to c_max by doubling, c_max in {128, 256, 512, 1024}; listen backlog max(128, c_max) (`server.listen_backlog`, `--backlog`).
- AM-4: n in {10, 20}. AM-3 and AM-4 are set by the pre-stated rule of protocol section 7.1 from a quiet pilot (`experiments/pilot-quiet.json`, `src/scale/pilotrule.py`, `scale resolve-pilot`).
- Everything else kept as in draft v0.1. EXP-001, EXP-003, EXP-004 protocols unchanged in content apart from status and an amendments note.

### Freeze record and guard
- `research/freeze.json`: approval quote, C1 to C4, C4 disclosure (J-0004, J-0005, J-0008 with paths and values), SHA-256 of `research/protocol.md` (18dd4f8dd888fd9aa61718cf17ae2485dfd87453cd39693d55df156b1d634b1f), of EXP-001 to EXP-004 protocols, of `experiments/EXP-001.json`, of the pilot config and the rule module; git revision 9471b588002cc384c607ec01f325c1e6c3957698. EXP-002 is listed as deferred (template hash recorded).
- `src/scale/freeze.py`; `scale run` now checks the record.

### Commands and actual outputs
- `scale run <scratchpad>/mech.json` (config copied to `experiments/mech-hiconc.json`, results to `results/exploratory/MECH-HICONC-20261124`; exploratory harness check J-0008, N = 2,000): 4 runs ok, 51.8 s; all 1024 connections served; A4 rejected 196,114 requests with Q = 16; error rates at c = 1024 of 0.044 (A0) and 0.014 (A1), not diagnosed.
- First `pytest` after the config change: `1 failed, 27 passed` (stopped at first failure): `test_repository_configs_parse` could not parse the deferred EXP-002 template; the test now checks the template explicitly. Then `UnboundLocalError` from a local `import json` in that test; removed.
- `.venv/bin/python -m pytest -q` before the freeze record existed: 7 freeze-guard tests failed as expected (no record). After writing `research/freeze.json`: `114 passed in 23.77s`.
- `scale run experiments/EXP-002.json`: `REFUSED: EXP-002 is confirmatory and its values blocks, concurrency, generator_ceiling_rps are to be set by the pre-stated quiet-machine pilot rule ...`, exit 3.
- `scale run <copy of EXP-001.json with blocks 6>`: `REFUSED: EXP-001 is confirmatory and config file is not in the freeze record (changed since the freeze, or never frozen).`, exit 3.
- `cli.freeze_status(EXP-001)`: `(True, 'frozen')`. `scale run experiments/EXP-001.json` was not executed (no confirmatory run in this session); acceptance by `cmd_run` is tested with a stubbed runner.
- `pandoc research/paper/manuscript.md -s -t latex` regenerated `manuscript.tex` (exit 0) after the C3 author update.

### Not done, and why
- No confirmatory run (brief; quiet machine needed).
- EXP-003 and EXP-004 configs not written: they depend on EXP-002 results and on c_max (recorded in the freeze record).
- Open point: EXP-001 item 21 gives a per-level C_gen table, the config takes one ceiling; the reduction must be stated before EXP-001 output is seen.

### Next action
Coordinator: schedule a quiet window. Then `scale run experiments/EXP-001.json`, `scale smoke --config experiments/pilot-quiet.json` (or `scale run`), `scale resolve-pilot <dir>`, append the resolution and the completed EXP-002 config hash to `research/freeze.json`, then EXP-002.

## 2026-11-24: Session RATIFY (owner second-round decisions, pre-M3 fix)

**Brief:** `labs/_shared/RATIFY-brief.md`; authority: `labs/_shared/owner-approvals-2026-11-24b.md` (owner: "Approve all").

### Starting state
`git status`: clean on `main`, HEAD `2ca4107`.

### Done
- Ratification (D-010): "A4 queue = 16" recorded; already frozen (AM-1), no hash change. Added to `research/freeze.json` `amendments`.
- New pre-data rule AM-5 (D-011): the generator ceiling used by EXP-002 is the median of the EXP-001 ceiling runs. Protocol section 15 (dated amendment) and a pointer in section 4. Code `src/scale/ceiling.py`, `scale resolve-ceiling`; tests `tests/test_ceiling.py` (11 tests).
- Freeze record: protocol hash now 5ea0c481132059752d4923c0518ebe9e22a56924959bd13146c41bfab372712e; old hash 18dd4f8d... kept under `superseded_hashes` with the reason; `ceiling.py` hash 0ecd6026... recorded; EXP-002 deferred rule text updated. No config changed.

### Commands and actual outputs
- `.venv/bin/python -m pytest -q tests/test_ceiling.py`: `10 passed in 0.21s` (before the freeze-record test was added).
- `.venv/bin/python -m pytest -q` (dev dependencies installed): `125 passed in 24.02s`.

### Not done
- No confirmatory run (brief).

### Next action
Coordinator: quiet window. `scale run experiments/EXP-001.json`, then `scale resolve-ceiling <EXP-001 dir>`, the quiet pilot and `scale resolve-pilot <dir>`; complete the EXP-002 config from both outputs and append its hash to `research/freeze.json`.

## 2026-11-25: M3 done with documented gaps (coordinator, quiet window)

The owner approved the experiment reports (owner, 2026-11-25, "approve all recommendations, RIGGED A", item 4). Subagents may not write report files, so the reports were composed by the M3 session from committed results only and written by the coordinator: 4 report(s). The coordinator checked that every decimal number in them appears in a committed file. EXP-001 and EXP-002 ran in full in an exclusive quiet-machine window (EXP-002: 50 of 50 cells). EXP-003 was not run because its frozen text leaves four parameters unset (D-014), and EXP-004 (optional) has no frozen config; both are documented failures under the M3 gate. The exclusion of A2 as generator-limited (D-012 reading) awaits the owner. M3 is **done** with these gaps. Next: owner decisions on D-012, EXP-003 and EXP-004, then M4.

## 2026-11-25: Session M4 (interpretation, evidence audit, manuscript, review pass 2)

**Milestone:** M4. **Authority:** owner, 2026-11-25, "Next" (`labs/_shared/owner-approvals-2026-11-25d.md`); brief `labs/_shared/M4-brief.md`. The SCALE sections of `owner-approvals-2026-11-24.md` and `-24b.md` were read; `owner-approvals-2026-11-25.md`, `-25b.md` and `-25c.md` have no SCALE section.

### Starting state
`git status`: `On branch main`, `nothing to commit, working tree clean`; HEAD `b9047ab`.

### Constraint
Other lab agents were running, so the machine was not quiet. No timing or throughput measurement was made, exploratory or otherwise. Sensitivity and confounder work re-analyses the recorded M3 outputs only.

### Done
- `scripts/m4_exploratory_confounders.py` (exploratory, J-0014): checksums of 219 raw files verified (0 mismatches), then checks X1 to X13 written to `results/exploratory/M4-REANALYSIS-20261125/summary.json`. X13 asks SQLite for query plans on a temporary 100-row database (no timing).
- `scripts/m4_evidence_manifest.py`: `research/publication/artifact_manifest.json` rebuilt (535 entries, 0 mismatches, 0 uncovered numeric tokens over manuscript, supplementary, claims register and the four reports).
- Corrections to M3 reports (no verdict changed): EXP-001 generator CPU at c = 8 (0.66 to 0.65); EXP-002 per-run duration (207 to 220 s), scope of the 503 count, error composition at high concurrency.
- `research/paper/manuscript.md` (about 5,700 words, abstract to conclusion) and `supplementary.md`; `manuscript.tex` regenerated with pandoc. `research/publication/evidence_audit_M4.md`, `review_pass_2.md` (17 challenges, 8 changes), `claims_audit.md`. Claims register restructured (C-001 to C-012, E-001 to E-008). Limitations 18 to 25. D-015.

### Commands and actual outputs
- `.venv/bin/python scripts/m4_exploratory_confounders.py`: exit 0 (first X13 attempt failed with `sqlite3.OperationalError: no such table: items` because `build_database` returns a hash, not a path; fixed in the script. That failed attempt left an empty file named after the hash in the repository root, created by this session and deleted before the commit).
- `.venv/bin/python scripts/m4_evidence_manifest.py`: first run `entries 520, mismatches 0, uncovered 58` (section numbers, versions, and three real findings: 0.66, 207 to 216, and the rounded 42,000 and 28,000 without entries); after the fixes `entries 535, mismatches 0, uncovered 0`. One intermediate run found `MISMATCH 1.04` and `0.99` for a Little's-law range drafted by the assistant; the recorded range is 0.89 to 1.05 (audit F-5).
- `/Users/bechir/research/labs/.tools/pandoc research/paper/manuscript.md -s -t latex -o research/paper/manuscript.tex`: exit 0.
- `.venv/bin/python -m pytest -q`: `132 passed in 25.17s`.

### Report files refused to the subagent
The Write tool refused `results/exploratory/M4-REANALYSIS-20261125/report.md`; its text was returned to the coordinator. The same content is in `summary.json`, the manuscript section 5.5 and J-0014.

### Owner decisions still pending (disclosed in the manuscript and review pass, not decided)
1. D-012 reading that excludes A2 from the confirmatory comparison.
2. EXP-003's four unset parameters (EXP-003 not run).
3. Whether EXP-004 runs (not run).
4. Whether `results/raw/` (about 1.5 MB) is committed at M6.

### Owner placeholders for M5
1. Manuscript front matter: the author line is `[placeholder: author line, to be confirmed by the owner. Common decision C3 of 2026-11-24 records "Mohamed Bechir Kefi", no affiliation]`.
2. Manuscript section 10: the repository URL is `[placeholder: repository URL, not published; publication requires the owner's approval]`.
3. Manuscript section 11: funding `[placeholder: funding statement, to be supplied by the owner]`.
4. Manuscript section 11: competing interests `[placeholder: competing-interests statement, to be supplied by the owner]`.
5. Manuscript section 11: "the owner's review of this manuscript is pending".

### Next action
M5 (interactive explorer of the recorded runs), with the placeholders and pending decisions above put to the owner.

## 2026-11-25: Session M5 (interactive experience)

**Milestone:** M5. **Authority:** owner, 2026-11-25, "Next" (second) (`labs/_shared/owner-approvals-2026-11-25e.md`), stack as in `-25d`; briefs `labs/_shared/M5-brief.md` and `M5-timing-addendum.md`. Decision D-016.

### Starting state
`git status`: `On branch main`, `nothing to commit, working tree clean`; HEAD `08eae92`.

### Done
- `demo/` from the shared template (no version changed, no dependency added; sandbox files removed, D-016). Page: overview with status label and the four pending owner decisions (each reading shown, none chosen); published results with labels, intervals and interval types; an effect plot of R with 98.75 % intervals in which A2 has its own "no confirmatory estimate" row; EXP-003 and EXP-004 panels; the resource and latency explorer of recorded EXP-002 runs (goodput, p99, server CPU, error rate, server memory; arm toggles; concurrency selector with a readout table; generator ceiling and 50 % threshold; generator-limited cells as open markers); the exploratory M4 re-analysis in its own dashed section; design values; limitations from manuscript section 7; source hashes.
- `scripts/export_demo_data.py` writes `demo/public/data/results.json` (committed inputs only; nothing from `results/raw/`); `tests/test_demo_export.py` (3 tests: fresh export identical; every display string verbatim in the manuscript, no exceptions; every registered experiment and pending decision exported).
- `demo/src/results.ts` validation extended (estimate kind and interval type, pending decisions, excluded arms, exploratory block, explorer) and fails closed; 14 vitest tests.
- `tools/a11y_check.mjs` step 7 drives the explorer offline (D-016).
- README (status, key results, pending decisions, demo quick start, `docs/demo.png` with alt text, 184232 bytes), `CITATION.cff` (`date-released` removed), `articles/medium.md` and `articles/linkedin.md` (new drafts), `articles/README.md`, `demo/README.md`.
- Screenshots inspected (desktop light, desktop dark, mobile). Fixed after inspection: a 3 px horizontal overflow at 360 px (long select), cramped interval-type column, and the threshold label overlapping the A2 line (halo added).

### Commands and actual outputs
- `npm ci --prefer-offline`: `added 53 packages in 1s`.
- `.venv/bin/python -I scripts/export_demo_data.py`: `wrote demo/public/data/results.json (52094 bytes)`; `--check`: `EXPORT-CHECK PASS`.
- `npm test`: `Test Files 1 passed (1)`, `Tests 14 passed (14)`.
- `npm run build`: `built`, no error.
- First checker run: `FAIL keyboard reaches every focusable element: 14 reached of 24` (key collisions between unlabelled checkboxes and table regions; ids added) and `FAIL no horizontal page scroll at 360 px: overflow 3px` (fixed). Final run of `node tools/a11y_check.mjs dist --screenshots <scratchpad>/shots`:

```
PASS results render (no fail-closed panel): 4 experiment panels
PASS text contrast, light scheme (WCAG AA)
PASS text contrast, dark scheme (WCAG AA)
PASS keyboard reaches every focusable element: 24 reached of 24
PASS visible focus indicator
PASS no horizontal page scroll at 360 px: overflow 0px
PASS reduced motion: no running animations: 0 running
PASS no request leaves the local origin
PASS offline after first load: results stay, explorer responds: Recorded values at c = 256: Goodput (validated responses per second)ArmMedian (r
A11Y-CHECK PASS
```

- Fail-closed check: with one explorer median set to -1 in `dist/data/results.json`, the checker printed `FAIL results render (no fail-closed panel): 0 experiment panels` and `A11Y-CHECK FAIL (2)`; `dist` was then rebuilt.
- `.venv/bin/python -m pytest -q`: `135 passed in 25.30s`.

### Owner placeholders (unchanged, still visible)
Author line and affiliation, repository URL, demo URL, funding, competing interests. No SCALE item is in the post-M4 approvals (`-25c`), so no SCALE title or statement is recorded as owner-approved. `author_review.md`: no box ticked.

### Next action
M6 (release candidate) on the owner's word, with the four pending decisions on the owner review checklist.

## 2026-11-25: Session M6 (release candidate)

**Milestone:** M6. **Authority:** owner, 2026-11-25, "Push and next" (`labs/_shared/owner-approvals-2026-11-25f.md`); briefs `labs/_shared/M6-brief.md` and `labs/_shared/M6-timing-addendum.md` (the addendum takes precedence). `owner-approvals-2026-11-25e.md` was read for the pending SCALE decisions. Decision D-017.

### Starting state
`git status`: `On branch main`, `nothing to commit, working tree clean`; HEAD `24a4de2` (M5, pushed).

### Constraint
The machine was shared with other lab sessions (load average 2.18, 1.97, 1.70 at the first clone). No timing measurement and no harness smoke were made. Reproduction re-ran the frozen analysis and the scripts on committed recorded outputs.

### Clean clone 1 (HEAD 24a4de2, before any M6 change)
- `git clone -q <repo> <scratch>/clone`: 451 tracked files. `uv sync --frozen --all-groups --all-extras`: environment created (`Audited 25 packages` on a second run).
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: `135 passed in 29.76s`.
- `scale analyse EXP-001 results/raw/EXP-001/EXP-001-M3 --out-dir <scratch>/an-EXP-001` and the same for EXP-002: `analysis.json` and `metrics.csv` byte-identical to `research/experiments/EXP-00N/`; the 3 PNG figures identical; the 3 SVG figures differ only in the `dc:date` stamp and random element ids (identical after normalising).
- `shasum -a 256 -c SHA256SUMS`: EXP-001 36 OK, EXP-002 126 OK, PILOT-QUIET 57 OK, 0 failures.
- `scripts/m4_exploratory_confounders.py`: exit 0, output differs only in `code_revision_at_run`. `scripts/m4_evidence_manifest.py`: `entries 535, mismatches 0, uncovered 0`, output differs only in revision fields and one digest.
- `scale report results/exploratory/SMOKE-M3-20261125`: unchanged except the SVG stamp and ids.
- `scripts/export_demo_data.py`: `wrote demo/public/data/results.json (52094 bytes)`; `--check`: `EXPORT-CHECK PASS`; `git status` clean.
- Demo: `npm ci --prefer-offline` `added 53 packages in 626ms`; `npm test` `Tests 14 passed (14)`; `npm run build` `built in 282ms`; `node tools/a11y_check.mjs dist` 9 PASS lines and `A11Y-CHECK PASS`.

### Findings and fixes
1. **Raw outputs tracked.** `git ls-files results/raw | wc -l` gives 226, although `.gitignore` lists the folder (added in `3fb0c66` and `1558fee`, pushed on 2026-11-25). Statements that said otherwise corrected (D-017); no file added or removed; the owner decision stays open.
2. **PDF builder** (found by visual inspection of every page at 60 ppi): a sentence of manuscript section 4.5 rendered as a numbered list (pandoc line wrapping; fixed with `--wrap=none`); two italic spans in sections 5.2 and 5.3 from paired G* (asterisk escaped before pandoc); the supplementary matrix table could not break across pages and left a near-empty first page (figures made breakable); narrow table cells justified with wide gaps (justification off in tables); reports and supplementary had no PDF title (first heading promoted). Final: `.venv/bin/python -I scripts/build_pdfs.py --typ-dir <scratch>/typ` printed `PDF-BUILD PASS`: manuscript 14 pages (184132 bytes), supplementary 6, EXP-001 3, EXP-002 5, EXP-003 1, EXP-004 1. The first build attempt failed with `RuntimeError: input file must be contained in project root` (intermediate file placed outside the Typst root); fixed by compiling beside the source and moving the intermediate file to scratch.
3. **References:** 2 uncited bib entries removed; 4 sources' full texts obtained and claims checked; 3 not obtainable free (labels kept). `evidence_audit_M6.md` section 1.
4. **Links:** `scripts/check_links.py` first run `LINK-CHECK FAIL (14)` (12 placeholder or base-folder paths, 2 uncited bib entries); final `LINK-CHECK PASS` over 54 Markdown files.
5. **Scan:** 0 tokens, 0 private keys, 0 `.env` files; 1 non-personal e-mail address (commit-trailer rule); 22 lines with home-directory paths in 6 files, replaced in 4 files. Note for this journal: entries above (lines 17 and 180) quote two absolute home-directory paths; they are kept because this file is append-only, and later text uses relative paths.
6. **SPDX:** 91 of 94 new files with headers; `demo/.npmrc` fixed, `manuscript.tex` now generated with the header, `manuscript.md` keeps it after the YAML block.
7. **Data manifest:** dataset rebuilt from its seed, SHA-256 `7a0c2b88...` equal to the record. Artifact manifest: 25 paths exist, 4 of 4 input digests match.
8. **CITATION.cff:** version `0.1.0-rc1`; title copied from the manuscript, pending the owner; no `date-released`; structure check `CFF-STRUCTURE PASS` (Ruby YAML parser, keys and types of CFF 1.2.0).

### Working repository checks
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: `139 passed in 25.13s` (135 plus 3 link tests plus 1 README and article number test).
- Demo: `npm test` `Tests 14 passed (14)`; `npm run build` built; `node tools/a11y_check.mjs dist` `A11Y-CHECK PASS`.

### Not done
- No box of `author_review.md` ticked (none had been ticked). No timing run. No push, tag or release.

### Next action
The owner's review of `research/publication/author_review.md` (section "Prepared for the owner") and the G-PUBLIC decision.

### Re-check in a fresh clone (HEAD 91fbb13)
Tests `139 passed in 30.75s`; frozen analyses byte-identical; manifest `entries 535, mismatches 0, uncovered 0`; export `EXPORT-CHECK PASS` with a clean tree; `LINK-CHECK PASS`; `build_pdfs.py` needed `SCALE_PANDOC` and `SCALE_TYPST_PYTHON` outside `labs/` (first attempt `FileNotFoundError`), then `PDF-BUILD PASS` with identical page counts, sizes and extracted text and a byte-identical `manuscript.tex`; demo `Tests 14 passed (14)`, built, `A11Y-CHECK PASS`. Both clones deleted. Details: `research/publication/reproducibility_report.md` section 3.

## 2026-11-26: Owner answers of the decision sheet applied

**Authority:** owner, 2026-11-26, decision sheet (`labs/_shared/owner-decision-sheet-2026-11-26.md`, `labs/_shared/owner-approvals-2026-11-26.md`); brief `labs/_shared/OWNER-ANSWERS-brief.md`. Decision D-018.

### Starting state
`git status --short`: empty (clean tree); HEAD `8c12866` (M6, local).

### Constraint
Timing project on a shared machine (load average 9.96, 11.50, 7.08 at the checks): no benchmark, load test or harness smoke was run.

### Changes (wording and configuration only)
Manuscript (author line, status paragraph, D-012 and EXP-003/EXP-004 wording, repository URL, funding, competing interests, raw outputs), supplementary, limitations 23 and 25, EXP-002 report (limitation line, new section 9), EXP-003 and EXP-004 reports (new owner-answer sections), registry status text of EXP-003 and EXP-004, README, articles, `CITATION.cff`, `.gitignore` comment, `CLAUDE.md`, `results/README.md`, `roadmap.md`, `author_review.md`, `release_checklist.md`, `reproducibility_report.md`, demo README, footer and owner-decision panel, `scripts/export_demo_data.py`; new `demo/wrangler.jsonc`. Details in D-018.

### Commands and outputs
- `git ls-files -z | xargs -0 grep -a -l '/Users/'`: `progress.md`, `scripts/build_pdfs.py` (both kept; `reproducibility_report.md` section 4).
- `.venv/bin/python -I scripts/export_demo_data.py`: `wrote demo/public/data/results.json (52296 bytes)`; `--check`: `EXPORT-CHECK PASS`.
- `.venv/bin/python -m pytest -q -p no:cacheprovider`: `139 passed in 25.12s`.
- `.venv/bin/python -I scripts/m4_evidence_manifest.py`: `entries 535, mismatches 0, uncovered 0`; the only change to `artifact_manifest.json` was `audit_head_revision`, restored with `git checkout`.
- `.venv/bin/python -I scripts/check_links.py`: `checked 54 Markdown files`, `LINK-CHECK PASS`.
- `.venv/bin/python -I scripts/build_pdfs.py --typ-dir <scratch>/typ`: `PDF-BUILD PASS` (manuscript 14 pages, supplementary 6, EXP-001 3, EXP-002 5, EXP-003 2, EXP-004 1). EXP-001's source did not change, so its PDF was restored with `git checkout`. A first build used a scratch folder shared with other sessions; it was repeated in a private folder with identical sizes. Manuscript pages 1 and 13 (author line, owner-decision paragraph, data availability, funding and competing interests), EXP-002 page 5 and EXP-003 page 2 rendered with Ghostscript at 60 to 80 ppi and inspected: text correct, no layout fault.
- Demo (Node 22 from the shared read-only folder, npm cache in scratch): `npm ci --prefer-offline` `added 53 packages in 6s`; `npm test` `Tests 14 passed (14)`; `npm run build` `built in 628ms`; `node tools/a11y_check.mjs dist` 9 PASS lines (keyboard 25 of 25, one more focusable element: the footer repository link; "no request leaves the local origin") and `A11Y-CHECK PASS`. The built page loads only `./assets/` files; the only absolute URLs in the bundle are XML namespaces, React's error-page base and the footer link.

### Not done
No box of `author_review.md` ticked. No push, deploy or tag. No timing run.

### Next action
The owner's full-text review and sign-off (B16), the article drafts (B15), and the EXP-003 and EXP-004 parameters (G-FREEZE) when the owner sets them. The coordinator pushes and deploys.
