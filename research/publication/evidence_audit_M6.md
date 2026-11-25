<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Evidence audit, M6 (release candidate, 2026-11-25)

Companion to `research/publication/evidence_audit_M4.md`. This audit covers the references, links, manifests and repository scans checked at M6. Every count below comes from a command recorded in `progress.md` (entry "Session M6") and `research/publication/reproducibility_report.md`.

## 1. References

`research/paper/references.bib` had 11 entries; the manuscript cites 9. The two uncited entries (georges2007, gan2019) were removed from the bib file and stay in `research/literature_review.md`. `scripts/check_links.py` now checks that every citation key of the manuscript resolves in the bib file and that every bib entry is cited (`tests/test_links.py`).

Access level of each cited source after the M6 access check. "Claim checked in full text" means the full text was obtained legally and free of charge and the cited claim was checked against the location given; it does not mean the whole source was read line by line.

| Key | Label at M6 | Where the cited claim was checked | Claim in the manuscript |
|---|---|---|---|
| kalibera2013 | Read in full (accepted manuscript, M1) | Whole paper | Unchanged |
| tene-wrk2 | Read in full (project page, the whole source) | README of the repository | Unchanged |
| schroeder2006 | Claim checked in full text (USENIX HTML, downloaded at M6) | Abstract and section 1: open-model mean response time can exceed the closed-model one "by an order of magnitude or more"; the two models "respond fundamentally differently ... to resource allocation (scheduling) policies" | Supported; label updated |
| kalibera2020 | Claim checked in full text (arXiv PDF, 55 pages) | Abstract and section 1, pp. 1 to 3: a model to "quantify uncertainty in the ratio of (execution time) means", effect size confidence intervals | Supported; label updated |
| gunther2008 | Claim checked in full text (arXiv PDF; the current arXiv revision is dated 2024) | Section 2.3, p. 3: USL with contention-limited (sigma) and coherency-limited (kappa) regimes | Supported; label updated, revision noted |
| gunther2011 | Claim checked in full text (arXiv PDF) | Section 27.5.2, Definition 1, p. 9: USL with contention (alpha) and coherency (beta) parameters | Supported; label updated |
| mytkowicz2009 | Abstract only (abstract and author page) | Full text not obtained: ACM page and the author-group PDF URLs tried returned HTTP 403 | Already limited to motivation; unchanged |
| dean2013 | Abstract only | Full text not obtained: ACM and CACM pages returned HTTP 403; the Google Research listing gives no PDF | Already limited to motivation; unchanged |
| little1961 | Unverified (bibliographic metadata only) | No free copy found; publisher page only | Already limited to the identity named in the title; unchanged |

Counts: read in full 2 (kalibera2013, tene-wrk2); claim checked in full text 4 (schroeder2006, kalibera2020, gunther2008, gunther2011); abstract only 2 (mytkowicz2009, dean2013); unverified 1 (little1961). No claim needed further qualification: the three sources not obtained were already cited with their access level and only for motivation or a named identity. No paid access, login or shadow library was used.

## 2. Links and quoted paths

`.venv/bin/python -I scripts/check_links.py` checks 52 tracked Markdown files (the master prompt is excluded because it is never edited): every relative link and anchor, every repository path quoted in backticks (journals exempt, because they record paths as they were), and the citation keys. First run: 14 problems (12 quoted paths that were placeholders such as `EXP-NNN`, journal paths written relative to another folder, or demo paths written relative to `demo/`; and the 2 uncited bib entries). The checker was given those placeholder and base-folder rules and the bib entries were removed; final run `LINK-CHECK PASS`.

## 3. Numbers in the README, articles and demo

`tests/test_demo_export.py` (M5) checks that every display string of the demo is printed in the manuscript. M6 added `test_readme_and_article_numbers_are_in_the_manuscript`: every number in `README.md` and `articles/*.md` appears in the manuscript, except the structural token "11.7" (a master prompt section). It passes.

## 4. Manifests

- `data/manifest.json`: the synthetic dataset items-v1 (200,000 rows, seed 20261124) was rebuilt in the scratch folder with `scale.data.build_database`; its logical SHA-256 equals the recorded `7a0c2b88...`.
- `research/publication/artifact_manifest.json`: all 25 distinct repository paths it names exist; the 4 analysis inputs under `inputs_sha256` match their recorded digests; the 219 files listed in the three `SHA256SUMS` files hash correctly in a clean clone (36, 126 and 57 OK, 0 failures). `scripts/m4_evidence_manifest.py` re-run in a clean clone printed `entries 535, mismatches 0, uncovered 0`; the regenerated manifest differs from the committed one only in the code-revision fields.

## 5. Finding: raw outputs are tracked although the ignore rule lists them

`.gitignore` lists `results/raw/`, and the M4 audit, limitation 25, the manuscript (sections 4.6 and 10), the results README, `CLAUDE.md` and the demo text said the raw outputs were outside git. In fact the 226 files under `results/raw/` (EXP-001, EXP-002, the quiet pilot, two logs and two quiet-check files) were added explicitly in the M3 commits `3fb0c66` and `1558fee` and are tracked; they were therefore on the remote after the push of 2026-11-25. The statements were corrected at M6 without deciding the owner question (D-017). Whether the files stay tracked remains the owner's decision; removing them from the current tree would not remove them from the history.

## 6. Secret, identifier and licence scan

Scope: the 460 tracked and new files (`git ls-files` plus untracked, not ignored).

| Check | Hits | Action |
|---|---|---|
| E-mail addresses | 1 (the Anthropic no-reply address in the commit-trailer rule of `CLAUDE.md`; not personal) | Kept |
| Tokens and keys (GitHub, OpenAI-style, AWS, Slack, Google API key patterns) | 0 | None |
| Private key headers | 0 | None |
| `.env` files | 0 | None |
| Absolute home-directory paths | 22 lines in 6 files: `CONTRIBUTING.md` 10, `research/feasibility.md` 5, `CLAUDE.md` 3, `progress.md` 2, `demo/README.md` 1, `scripts/build_pdfs.py` 1 (a regular-expression pattern, not a path) | Replaced in `CONTRIBUTING.md`, `research/feasibility.md` (with a dated note), `CLAUDE.md` and `demo/README.md`; `progress.md` is append-only and gets a note instead; the pattern stays |
| Home paths in `results/raw/` | 0 | None |

Git history was not rewritten; earlier commits keep the old text. Dependency licences: `research/publication/dependency_licences.md` (no flag).

## 7. SPDX headers

Of the files added since the initial commit whose format allows a comment, 91 carried the header and 3 did not: `demo/.npmrc` (header added), `research/paper/manuscript.tex` (generated; `scripts/build_pdfs.py` now writes the header) and `research/paper/manuscript.md` (the header follows the YAML front matter, which must come first; kept).
