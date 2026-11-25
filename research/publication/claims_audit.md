<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Claims audit (M4, 2026-11-25)

Each row of `research/claims_register.csv` was checked: the evidence path exists, every number in the claim is a manifest entry that matches the recorded value (`scripts/m4_evidence_manifest.py`: 535 entries, 0 mismatches), the scope stays inside the claims boundary (one machine, localhost, this workload), and external claims map to a source with its access level stated. Details: `research/publication/evidence_audit_M4.md`.

| claim_id | evidence checked | number matches raw | scope OK | verdict |
|---|---|---|---|---|
| C-001 | EXP-001 runs EXP-001-b00..b04-A0-549fdc85 (research/experiments/EXP-001/analysis.json) | yes | yes | supported (confirmatory) |
| C-002 | EXP-002 (50 accepted runs, RS-EXP-002) (analysis.json confirmatory.A1) | yes | yes | supported (confirmatory) |
| C-003 | EXP-002 (RS-EXP-002) (analysis.json confirmatory.A3) | yes | yes | supported (confirmatory) |
| C-004 | EXP-002 (RS-EXP-002) (analysis.json confirmatory.A4) | yes | yes | supported (confirmatory) |
| C-005 | EXP-002 (RS-EXP-002) (analysis.json confirmatory.A2 and dominance) | yes | yes | supported under the D-012 reading; D-012 pending the owner |
| C-006 | EXP-002 (RS-EXP-002) (analysis.json ranking and sensitivity_s3) | yes | yes | supported (frozen sensitivity) |
| C-007 | M4-REANALYSIS-20261125 X3 on RS-EXP-002 (results/exploratory/M4-REANALYSIS-20261125/summary.json X3) | yes | yes | exploratory |
| C-008 | M4-REANALYSIS-20261125 X3, X12 (summary.json X12) | yes | yes | exploratory |
| C-009 | M4-REANALYSIS-20261125 X6 (summary.json X6) | yes | yes | exploratory |
| C-010 | M4-REANALYSIS-20261125 X4 (summary.json X4) | yes | yes | exploratory |
| C-011 | M4-REANALYSIS-20261125 X1 (summary.json X1) | yes | yes | exploratory |
| C-012 | M4-REANALYSIS-20261125 X13 (summary.json X13) | yes | yes | exploratory |
| E-001 | mytkowicz2009 (research/literature_review.md (abstract and author page read)) | n/a (no number) | yes | abstract read |
| E-002 | kalibera2013 (literature_review.md (full text read)) | n/a (no number) | yes | read |
| E-003 | kalibera2020 (literature_review.md (abstract read)) | n/a (no number) | yes | abstract read |
| E-004 | schroeder2006 (literature_review.md (full text read through a summarising fetch)) | n/a (no number) | yes | read (summarising fetch) |
| E-005 | tene-wrk2 (literature_review.md (project page read)) | n/a (no number) | yes | read (page) |
| E-006 | little1961 (literature_review.md, metadata only) | n/a (no number) | yes | metadata only |
| E-007 | gunther2008; gunther2011 (literature_review.md (abstracts read)) | n/a (no number) | yes | abstract read |
| E-008 | dean2013 (literature_review.md (abstract read)) | n/a (no number) | yes | abstract read |

Qualified at M4: C-003 (conditional on the full-scan baseline), C-004 (structural null), C-005 (D-012 pending the owner). No claim was removed; no claim without a row appears in the manuscript.
