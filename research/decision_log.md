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

## D-009 (2026-11-24): Owner freeze of protocol v1.0 with amendments AM-1 to AM-4 (G-FREEZE)

- **Decided by:** the owner (approvals of 2026-11-24, `labs/_shared/owner-approvals-2026-11-24.md`, SCALE section, answering D-008). Applied by the AI assistant in the freeze session.
- **Approval (quoted).** Owner answers: "2. yes 3. yes 4. yes", "yes for all others". SCALE section: "Make A4's queue smaller than the maximum concurrency so that it can reject." "State that the index wins by design against a full-scan baseline." "Extend the concurrency sweep beyond 64 until A1 and A3 peak inside the range." "Set the seed count only after a quiet-machine pilot (a separate step, run later)." "Keep the other draft parameters." Coordinator instruction for this session: freeze everything else and record the seed count as "to be set by the pre-stated rule from the quiet pilot", with the rule written into the frozen protocol.
- **Amendments applied** (`research/protocol.md` section 15): AM-1 A4 queue Q = 16 (W = 8; W + Q = 24); AM-2 the index wins by design against the full-scan baseline (sections 3, 5; limitation 10); AM-3 sweep 1 to c_max by doubling, c_max in {128, 256, 512, 1024}; AM-4 n in {10, 20}. AM-3 and AM-4 are set by the pre-stated rule of protocol section 7.1 from the quiet pilot (`experiments/pilot-quiet.json`, `src/scale/pilotrule.py`, `scale resolve-pilot`). The rule reads only A1/A3 peak locations and the SD of log R, never effect sizes.
- **Note on AM-3.** The approved criterion ("until A1 and A3 peak inside the range") needs a measurement, so c_max is resolved by the same quiet pilot as n rather than fixed today. Q = 16 is the value named in D-008 item 1.
- **Common decisions.** C1 synthetic data only; C2 PDFs with pandoc and Typst (Libertinus Serif); C3 author "Mohamed Bechir Kefi", no affiliation, AI disclosed as a research and development assistant (manuscript metadata and section 11 updated, `manuscript.tex` regenerated; `CITATION.cff` already matched); C4 exploratory primary-contrast values seen before the freeze are listed in `research/freeze.json` (J-0004, J-0005, J-0008 with paths).
- **Freeze record.** `research/freeze.json`: git revision 9471b588002cc384c607ec01f325c1e6c3957698; SHA-256 of `research/protocol.md` 18dd4f8dd888fd9aa61718cf17ae2485dfd87453cd39693d55df156b1d634b1f; SHA-256 of the four EXP protocols, of `experiments/EXP-001.json`, of the pilot config and of the rule module. EXP-002's config is a template with `blocks`, `concurrency` and `generator_ceiling_rps` unset (deferred); its hash is appended at resolution.
- **Guard.** `scale run` (`src/scale/freeze.py`) accepts a confirmatory config only if the protocol status says FROZEN, the protocol, EXP protocol and config file hashes match the freeze record, and no value is deferred. Tested both ways (`tests/test_freeze.py`).
- **Consequences.** Confirmatory runs may start once the coordinator schedules a quiet machine: EXP-001, then the quiet pilot and its resolution, then EXP-002. Runtime grows to about 2.3 h to 6.2 h for EXP-002 depending on the rule. Open point for the resolution step: EXP-001 item 21 gives a per-level C_gen table while the config takes one `generator_ceiling_rps`; how the table becomes one number must be stated (as a dated note) before EXP-001 output is seen.

## D-010 (2026-11-24): Ratified follow-on choice, A4 queue = 16

- **Decided by:** the owner (second-round approvals of 2026-11-24, `labs/_shared/owner-approvals-2026-11-24b.md`, section 3). The owner answered "Approve all" (2026-11-24) to the coordinator's list.
- **Choice ratified.** "A4 queue = 16."
- **Consequences.** The value is already in the frozen text (AM-1, D-009; `src/scale/config.py`), so no file hash changes. Recorded in `research/freeze.json` under `amendments` (RATIFY-SCALE-1).

## D-011 (2026-11-24): Generator-ceiling rule fixed before data (AM-5)

- **Decided by:** the owner (second-round approvals of 2026-11-24, `labs/_shared/owner-approvals-2026-11-24b.md`, section 4, "Rules fixed before data"; the owner answered "Approve all", 2026-11-24). Applied by the AI assistant.
- **Rule (quoted).** "The generator ceiling used by EXP-002 is the median of the EXP-001 ceiling runs."
- **Made before any confirmatory data.** No EXP-001, quiet-pilot or EXP-002 run exists. This closes the open point of D-009 (how the per-level C_gen table of EXP-001 item 21 becomes the single `generator_ceiling_rps`).
- **Operational definition** (`research/protocol.md` section 15, AM-5, plus a pointer sentence in section 4). A ceiling run is one of the five confirmatory EXP-001 repeats (SCALE generator, `GET /null`, c in {1, 8, 32}); its ceiling is its peak goodput over those levels. The value is the median over the five. All five must have status ok with the idle probe enforced and passed, else no value is set. The rule reads no study arm.
- **Implementation.** `src/scale/ceiling.py` (rule version `ceiling-rule-1.0`), CLI `scale resolve-ceiling <dir>`, tests `tests/test_ceiling.py`.
- **Freeze record.** `research/protocol.md` re-hashed: 5ea0c481132059752d4923c0518ebe9e22a56924959bd13146c41bfab372712e (was 18dd4f8dd888fd9aa61718cf17ae2485dfd87453cd39693d55df156b1d634b1f, kept under `superseded_hashes` with the reason). `src/scale/ceiling.py` hash 0ecd60269a9e18855c53bc5c42b12eca69e4abd4dee5c3d2704fae1b9b1cd371 added to `pre_stated_rule_inputs`. No config changed; EXP protocols unchanged.

## D-012 (2026-11-25): Frozen-analysis implementation and section 10 re-attempts, written before any EXP-001 or EXP-002 output

- **Decided by:** AI assistant at M3, before any confirmatory run (no EXP-001, quiet-pilot or EXP-002 output existed). For owner review; flagged in the M3 report.
- **Context.** The frozen protocol defines the EXP-002 estimand, intervals, multiplicity correction, decision rule and sensitivity analyses, but the repository had no code for them, and the runner did not re-attempt excluded runs as protocol section 10 requires. The brief forbids any change to analysis code once confirmatory output exists, so both were written and tested first.
- **Implementation.** `src/scale/analysis.py` (`scale analyse EXP-001|EXP-002 <dir> --out-dir <dir>`), tests `tests/test_analysis.py`; runner re-attempts in `src/scale/runner.py` (confirmatory configs only, at most two per cell, at the end of the sequence, run ids suffixed `-r1`, `-r2`; the excluded run stays in place). Exploratory configs are never re-attempted, because the quiet-pilot rule requires a whole repeat.
- **Readings fixed here, where the frozen text is implicit.**
  1. *Generator-limited exclusion (section 4).* A run's confirmatory G* is undefined when the level attaining its peak is flagged generator-limited. This is the reading stated in D-008 item 5 ("those cells would be excluded and A2's G* would be undefined"), which the owner saw when keeping the 50 % rule and the single generator process.
  2. *Arm-level exclusion.* An arm enters the confirmatory comparison only if G* of the arm and of A0 are defined in every block; otherwise it is reported as excluded, because dropping single blocks would select blocks by outcome. Exploratory alternatives are reported beside it: G* over the levels that are not generator-limited, unfiltered G*, and the primary definition over the defined blocks only.
  3. *Decision intervals.* H0_j is rejected when the Bonferroni 98.75 % interval excludes 1; "no meaningful effect" requires the 98.75 % interval inside [0.95, 1.05]; dominance uses 98.75 % intervals of R_t / R_k and is attempted only if all four treatment arms are in the confirmatory comparison.
  4. *Bootstrap seed.* 20261124 (the EXP-002 study seed), 10,000 resamples.
  5. *S3 and drift.* S3 uses the mean goodput over c in {16, 32, 64}, undefined if any of the three cells is generator-limited. Drift: OLS of log G* on arm indicators plus run order (and, separately, position in block), slope intervals by a 2,000-resample block bootstrap; descriptive.
  6. *EXP-001.* Per-level median and range over the five repeats; the item 17 gate uses the median SCALE/ab ratio at c = 32.
- **Consequences.** Any later change to these readings is an amendment after the freeze and is analysed separately.

## D-013 (2026-11-25): EXP-002 values set by the pre-stated rules (resolution, not an amendment)

- **Decided by:** the frozen rules (protocol section 7.1, pilot-rule-1.0; section 15 AM-5, ceiling-rule-1.0), applied by the AI assistant at M3. No value was chosen by hand.
- **Inputs.** Confirmatory EXP-001 (`results/raw/EXP-001/EXP-001-M3`, 5 runs, all ok, idle probe 1.9 % to 2.5 %) and the exploratory quiet pilot (`results/raw/PILOT-QUIET/PILOT-QUIET-M3`, 25 runs, all ok, idle probe 2.0 % to 13.0 %, all passed).
- **Outputs.** `generator_ceiling_rps` = 27919.4 (median of run ceilings 27914.5, 27919.4, 27953.9, 27860.9, 28657.0). Pilot: A1 peaked at c = 4 in every block, A3 at c = 128 or 256, so c_max = 512 (not truncated); between-block SD of log R: A1 0.0208, A2 0.0135, A3 0.0125, A4 0.0103, all at most 0.07, so n = 10.
- **Effect.** `experiments/EXP-002.json` completed (blocks 10, c in {1, ..., 512}, ceiling 27919.4); its SHA-256 is appended to `research/freeze.json` `configs`, the deferral is marked resolved, and the rule outputs are recorded under `resolutions`. Tests that asserted the deferred state were updated to assert the resolved state.
- **Disclosure (C4).** The pilot shows effect sizes as a by-product (its per-run G* is in the pilot results). The rule used only peak locations and spreads. Pilot values are never pooled with EXP-002.

## D-014 (2026-11-25): M3 deviations and experiments not run

- **Decided by:** AI assistant at M3, under the M3 briefs; for owner review.
- **EXP-002 idle-probe exclusions.** 12 runs were excluded by the idle probe (16.2 % to 35.4 %) in one 12 s burst (06:15:22Z to 06:15:34Z); the source was not identified (no process of this session other than the runner was active). The runner moves to the next run at once after an exclusion, so the burst also consumed the first re-attempt of five cells. Every cell completed on re-attempt 1 or 2 (protocol section 10), so no cell is missing. The excluded files stay in `results/raw/EXP-002/EXP-002-M3/runs`. A wait-for-quiet step between attempts would avoid burning re-attempts in a burst; it is not added, because the analysis and runner are frozen once confirmatory output exists.
- **EXP-001 supplements.** The stall check, the 4-process sensitivity and the timer resolution of the EXP-001 protocol are not in the frozen EXP-001 config; they were run as exploratory supplements (J-0011, `experiments/exp001-gp4.json` new).
- **EXP-003 not run.** No frozen config. Its protocol fixes the ladder rule (8 geometric rungs from 10 % to 150 % of each arm's EXP-002 median G*) and 5 blocks, but not the open-loop connection count, the study seed or the warmup/measure split of the 20 s rung, and not which G* (A2's is generator-limited) centres A2's ladder. Choosing them would be a design decision after EXP-002 output; the owner decides.
- **EXP-004 not run.** Optional and without a frozen config (its study seed and config were to be written after c_max); under the M3 brief it is not run.

## D-015 (2026-11-25): M4 interpretation, evidence audit and manuscript

- **Authority:** owner, 2026-11-25, "Next" (`labs/_shared/owner-approvals-2026-11-25d.md`), which starts M4 in SCALE. Brief: `labs/_shared/M4-brief.md`. Decided by the AI assistant within that brief; for owner review.
- **No new measurement.** Other lab agents were running, so the machine was not quiet; no timing or throughput run was made, exploratory or otherwise. The confounder and sensitivity review is a read-only re-analysis of the recorded M3 outputs (`scripts/m4_exploratory_confounders.py`, checks X1 to X13, `results/exploratory/M4-REANALYSIS-20261125/summary.json`, J-0014; checksums of 219 raw files verified first). X13 asks SQLite for query plans on a temporary 100-row database and measures nothing.
- **Frozen verdicts unchanged.** A1 and A3: H0 rejected; A4: no meaningful effect on G*; A2: excluded; dominance unresolved. The exploratory checks were chosen after the results were known and are labelled so.
- **Interpretation narrowed.** A3's gain is an amortisation of the full scan (query plan X13) and is conditional on the baseline, like A2's (limitation 19). The A4 null is structural (limitation 20). The A3 lead over A1 is metric-dependent (limitation 21). The intervals describe one session (limitation 18).
- **Evidence audit.** `scripts/m4_evidence_manifest.py` writes `research/publication/artifact_manifest.json` (535 entries, 0 mismatches, 0 uncovered tokens). Four M3 report statements corrected (generator CPU 0.66 to 0.65; per-run duration; scope of the 503 count; error composition). See `research/publication/evidence_audit_M4.md`.
- **Claims register.** Columns result id, config hash, figure or table and section added; C-007 to C-012 (exploratory) and E-001 to E-008 (external) added; C-003, C-004, C-005 qualified.
- **Manuscript.** `research/paper/manuscript.md` and `supplementary.md` written to master prompt 11.4; second review pass `research/publication/review_pass_2.md` (17 challenges, 8 changes).
- **Author line.** Kept as a visible placeholder that quotes C3, on the coordinator's instruction that owner-only facts stay placeholders until the owner confirms them.
- **Still pending the owner (not decided here):** the D-012 reading that excludes A2; EXP-003's four unset parameters (EXP-003 not run); whether EXP-004 runs (not run); repository URL, funding, competing interests and the author line; whether `results/raw/` (about 1.5 MB) is committed at M6.
