<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Reproducibility report

Status at M6 (2026-11-25): clean-clone reproduction recorded below. The machine was shared with other lab sessions, so, under the M6 timing addendum, no new timing measurement was made and no timing was compared with the published results. Reproduction means re-running the frozen analysis and the report, audit and export scripts on the committed recorded outputs and comparing the results byte for byte.

Environment: macOS 15.3.1, Apple M1 Pro, Python 3.12.1 (project `.venv`), uv 0.9.5, pandoc 3.6.3, typst 0.15.0 (Python package), Node 22.23.3. Load average at the start of clone 1: 2.18, 1.97, 1.70 (shared machine).

## 1. Clean clone 1 (HEAD `24a4de2`, before the M6 changes)

Commands run in `<scratch>/clone`, a local `git clone -q` of the working repository (no network). Nothing was committed before the clone.

| Step | Command | Actual output |
|---|---|---|
| Clone | `git clone -q <repo> <scratch>/clone` | HEAD `24a4de2`; 451 tracked files |
| Locked install | `uv sync --frozen --all-groups --all-extras` | environment created; a second run printed `Audited 25 packages` |
| Tests | `.venv/bin/python -m pytest -q -p no:cacheprovider` | `135 passed in 29.76s` |
| Frozen analysis, EXP-001 | `scale analyse EXP-001 results/raw/EXP-001/EXP-001-M3 --out-dir <scratch>/an-EXP-001` | `analysis.json` and `metrics.csv` identical (`cmp`) to `research/experiments/EXP-001/`; `exp001_ceiling.png` identical; `exp001_ceiling.svg` differs only in the `dc:date` stamp and matplotlib's random element ids (identical after normalising both) |
| Frozen analysis, EXP-002 | `scale analyse EXP-002 results/raw/EXP-002/EXP-002-M3 --out-dir <scratch>/an-EXP-002` | `analysis.json` and `metrics.csv` identical; both PNG figures identical; both SVG figures identical after normalising date and ids |
| Raw checksums | `shasum -a 256 -c SHA256SUMS` in `results/raw/{EXP-001,EXP-002,PILOT-QUIET}` | 36, 126 and 57 OK; 0 failures |
| M4 re-analysis | `.venv/bin/python -I scripts/m4_exploratory_confounders.py` | exit 0; `summary.json` differs from the commit only in `code_revision_at_run` |
| Evidence manifest | `.venv/bin/python -I scripts/m4_evidence_manifest.py` | `entries 535, mismatches 0, uncovered 0`; `artifact_manifest.json` differs only in `audit_head_revision`, `code_revision` fields and the digest of the re-written `summary.json` |
| Exploratory report | `scale report results/exploratory/SMOKE-M3-20261125` | `report.md`, `summary.json` and the PNG unchanged; the SVG identical after normalising date and ids |
| Demo export (determinism) | `.venv/bin/python -I scripts/export_demo_data.py`, then `--check` | `wrote demo/public/data/results.json (52094 bytes)`, `EXPORT-CHECK PASS`; `git status` clean |
| Demo install | `npm ci --prefer-offline` | `added 53 packages in 626ms` |
| Demo tests | `npm test` | `Test Files 1 passed (1)`, `Tests 14 passed (14)` |
| Demo build | `npm run build` | `built in 282ms`, no error |
| Accessibility check | `node tools/a11y_check.mjs dist` | 9 PASS lines (contrast light and dark, keyboard 24 of 24, focus, no overflow at 360 px, reduced motion, no external request, offline explorer) and `A11Y-CHECK PASS` |

The two re-analysis scripts stamp the current git revision into their outputs, so a re-run on a later commit differs in those fields only; this is the documented tolerance for them. After each re-run the clone was restored with `git checkout --` on the files the script had written (inside the clone only), and `git status` was clean before the next step.

### Raw outputs and the clean clone

The M6 timing addendum notes that whether `results/raw/` is committed is an open owner question. The clean clone showed that the M3 raw outputs are already tracked (226 files), although `.gitignore` lists the folder; this is why the frozen analysis could be reproduced from a clean clone at all. Finding and correction of the statements that said otherwise: `research/publication/evidence_audit_M6.md` section 5, D-017. No raw file was added or removed.

### Harness smoke

No harness smoke run was made: the frozen analysis and the report scripts were reproduced from recorded outputs, the test suite already starts the server and the load generator on localhost, and the machine was shared. No timing number was produced.

### Findings in clone 1

1. SVG figures are not byte-reproducible (matplotlib writes the date and random ids). The PNG figures and every number are. Not changed, because `src/scale/analysis.py` is frozen; recorded here as the tolerance for SVG files.
2. The raw outputs are tracked although the ignore rule lists them (above).

## 2. PDFs

`.venv/bin/python -I scripts/build_pdfs.py --typ-dir <scratch>/typ` (repository builder `scale.report.build_pdf`, pandoc to Typst, typst Python package) built six PDFs and regenerated `research/paper/manuscript.tex`; every PDF passed the metadata check (title set, no e-mail address, no local path, under 5 MB). Page counts: manuscript 14, supplementary 6, EXP-001 report 3, EXP-002 report 5, EXP-003 report 1, EXP-004 report 1. Every page was rendered to PNG at 60 ppi and inspected; the fixes made to the builder are listed in `progress.md` (Session M6) and D-017.
