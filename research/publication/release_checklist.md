<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Release checklist (M6)

Status at M0: nothing checked. Publication requires the owner's explicit approval (G-PUBLIC).

**Status, 2026-11-25 (M6):** release candidate prepared, awaiting the owner's review and G-PUBLIC. Items are ticked only where this session verified them; the evidence follows each item. The two owner items stay unticked. Nothing was released or tagged.

**Update, 2026-11-26 (owner answers, decision sheet).** The repository is public at <https://github.com/mohamedbechirkefi/scale-single-machine-throughput> since the push of 2026-11-25 (state of M5); the M6 commits and this update are local until the coordinator pushes them (push approved by the owner, B17). The owner's answers were applied as wording and configuration only (D-018); no box below was ticked or unticked in this round.

- [x] Owner approved the frozen protocol before confirmatory runs (hash recorded). Evidence: `shasum -a 256 research/protocol.md` gives `5ea0c481...`, equal to the study-protocol hash in `research/freeze.json`; owner approval recorded in D-009 and D-011 (2026-11-24), before the M3 runs of 2026-11-25.
- [x] Every registered experiment has a truthful standalone report, including failed or exploratory ones. Evidence: 4 experiments in `research/experiment_registry.csv` (EXP-001 to EXP-004), 4 `report.md` files and 4 report PDFs; EXP-003 and EXP-004 are labelled "not run" in their titles and status rows.
- [ ] Integrated manuscript complete; abstract written after analysis. Not ticked: the content is complete (abstract to conclusion, written at M4 after the analysis). Since 2026-11-26 the author line, repository URL, funding and competing-interest statements are filled and the title and AI-use statement are owner-approved; the owner's full-text review (B16) is still pending.
- [x] Manuscript and report PDFs compiled (Typst path) and visually inspected; `manuscript.tex` generated. Evidence: `.venv/bin/python -I scripts/build_pdfs.py` printed `PDF-BUILD PASS` (manuscript 14 pages, supplementary 6, EXP-001 3, EXP-002 5, EXP-003 1, EXP-004 1; titles set, no e-mail address or local path, each under 5 MB); every page rendered at 60 ppi and inspected; three builder fixes (progress.md, Session M6).
- [x] Clean clone in a separate directory: locked install, tests, smoke reproduction, demo build; outputs recorded. Evidence: `research/publication/reproducibility_report.md` (clone 1: 135 tests passed, frozen analyses byte-identical, `A11Y-CHECK PASS`, export deterministic; clone 2 after the M6 changes in the same report). `uv sync --frozen` was used, which installs the lockfile without re-resolving.
- [x] Artifact manifest maps every number to experiment, run ids, result path, script, hash and revision. Evidence: `scripts/m4_evidence_manifest.py` in a clean clone: `entries 535, mismatches 0, uncovered 0`; all 25 paths named in the manifest exist; 4 of 4 input digests match.
- [ ] Claims audit complete; no unsupported claim remains. Not ticked: the claims audit is from M4 (`claims_audit.md`) and was not redone at M6; M6 re-checked only the external-source claims (section 1 of `evidence_audit_M6.md`).
- [x] References verified against sources actually accessed. Evidence: `research/publication/evidence_audit_M6.md` section 1: 9 cited keys, all resolving (`LINK-CHECK PASS`); 2 read in full, 4 claims checked in full text, 2 abstract only, 1 metadata only, each labelled in the manuscript; 2 uncited bib entries removed.
- [x] Data manifest and licences verified; no non-redistributable data bundled. Evidence: the synthetic dataset rebuilt from its seed has the recorded SHA-256 `7a0c2b88...`; no external dataset; `research/publication/dependency_licences.md` flags nothing.
- [x] Secret and personal-data scan clean. Evidence: `evidence_audit_M6.md` section 6: 0 tokens, 0 private keys, 0 `.env` files, 1 non-personal e-mail address (commit-trailer rule), home-directory paths removed from current files (journal note appended); history not rewritten, so earlier commits keep the old paths.
- [x] README, demo, paper, reports and articles use identical numbers and labels. Evidence: `tests/test_demo_export.py` (4 tests, including the M6 README and article check) passes.
- [x] Licence files unchanged since the owner's decision (D-001). Evidence: `git log -- LICENSE NOTICE.md LICENSE_HISTORY.md CLA.md .github` shows only the initial commit and the owner's repository rename `98e5c77` (2026-11-24); no change since and no working-tree diff.
- [ ] Owner review recorded in `author_review.md`. Owner item.
- [ ] Owner explicitly approved any push, release or preprint. Owner item. The push of `main` was approved on 2026-11-25 ("Push and next"); no release, tag or preprint is approved.

## Version and date at the release (B8, owner, 2026-11-26)

Until the release, `CITATION.cff` keeps `version: 0.1.0-rc1` and has no `date-released`. At the release the version becomes `0.1.0` and `date-released` is set to the release day. `pyproject.toml` keeps its current version (`0.1.0`), because changing it would change the lockfile and the recorded environments.

## Release notes (draft)

- Figures: no SCALE figure was listed with small or clipped labels (B11 does not apply to this repository); the figures are kept as committed.
- Build and check tools: external tools are used but not redistributed: pandoc (GPL-2.0-or-later) for the PDF build, Google Chrome (headless) for the accessibility check, and the MPL-2.0 packages lightningcss (demo build) and hypothesis (tests), as listed in `dependency_licences.md`; the committed PDFs embed subsets of the fonts the Typst package ships (Libertinus Serif and DejaVu Sans Mono).
- Sources not read in full keep the labels stated in the manuscript (abstract only, metadata only, claim checked in full text); the owner accepted these labels (B14, 2026-11-26).
