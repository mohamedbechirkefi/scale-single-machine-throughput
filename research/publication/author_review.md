<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Author review (owner)

Status at M0: no review requested yet.

- [ ] Author list and metadata approved by the owner (no invented affiliation).
- [ ] AI-assistance disclosure reviewed and accurate.
- [ ] Funding and competing-interest statements reviewed.
- [ ] Claims and limitations reviewed.
- [ ] Publication decision recorded (date, scope).

No box above was ticked by an agent at any milestone up to M6; none was unticked.

## Prepared for the owner (M6, 2026-11-25)

M6 prepared a release candidate. Nothing was released or tagged, and no box above is ticked: only the owner signs off. The repository is public at <https://github.com/mohamedbechirkefi/scale-single-machine-throughput> since the push of 2026-11-25 (state of M5); the M6 commits are local until the coordinator pushes them (owner-approved, B17, 2026-11-26).

### What to read for each box

1. **Author list and metadata.** `research/paper/manuscript.md` front matter (author line "Mohamed Bechir Kefi, independent researcher" since 2026-11-26); `CITATION.cff` (authors with affiliation "Independent researcher", title, `repository-code`, version `0.1.0-rc1`, no `date-released`); `README.md` section "Citation"; PDF metadata of `research/paper/manuscript.pdf`.
2. **AI-assistance disclosure.** `research/paper/manuscript.md` section 11, paragraph "AI assistance"; limitation 14 in section 7; `articles/medium.md` last paragraph.
3. **Funding and competing interests.** `research/paper/manuscript.md` section 11 (both statements, filled 2026-11-26); `README.md` section "Citation"; `articles/medium.md` last paragraph.
4. **Claims and limitations.** `research/paper/manuscript.md` abstract and sections 5 to 7; `research/claims_register.csv`; `research/publication/claims_audit.md`; `research/publication/review_pass_2.md`; `research/publication/evidence_audit_M4.md` and `evidence_audit_M6.md`; the PDFs in `research/paper/` and the four report PDFs (`research/experiments/EXP-001/report.pdf` to `research/experiments/EXP-004/report.pdf`).
5. **Publication decision.** `research/publication/release_checklist.md`; `research/publication/reproducibility_report.md`; `research/publication/dependency_licences.md`.

### Open decisions for this repository (as listed at M6; answers of 2026-11-26 in the section below)

1. **D-012 reading that excludes A2.** The manuscript reports the frozen-rule reading as applied (A2 has no confirmatory estimate and dominance is unresolved) and two exploratory alternatives that are not verdicts: the unfiltered within-block ratio 246.8 (98.75 % interval 243.4 to 250.2) and G* over the levels not flagged, 90.8 (90.0 to 91.8).
2. **EXP-003 parameters.** The owner has not set the four parameters the frozen text leaves open (open-loop connection count, study seed, warmup and measurement split of each rung, and which G* centres A2's ladder), so EXP-003 did not run.
3. **EXP-004.** The owner has not decided whether the optional workload experiment runs; it did not run.
4. **`results/raw/`.** The owner has not decided whether the raw outputs stay committed; M6 found that the 226 M3 raw files are already tracked and were pushed on 2026-11-25, although `.gitignore` lists the folder (D-017).
5. **Manuscript title.** The title "Cache, index, batching or admission control? A one-factor-at-a-time throughput study with a frozen protocol of one Python and SQLite server on one laptop" is not owner-approved, and `CITATION.cff` now carries the same title, copied at M6 and pending approval (the previous title is kept in a comment).
6. **Funding statement.** It is a placeholder for the owner to supply.
7. **Competing-interests statement.** It is a placeholder for the owner to supply.
8. **AI-use statement.** The wording in manuscript section 11 is a draft that the owner has not approved.
9. **Author line and affiliation.** The manuscript, README, articles and `CITATION.cff` carry the C3 name as a placeholder to be confirmed, with no affiliation.
10. **Repository URL and demo URL.** Both are placeholders until the owner decides to publish.
11. **Assistant readings and deviations for review.** D-012 (analysis readings), D-014 (M3 deviations and experiments not run), D-015 (M4 interpretation), D-016 (M5 demo without a sandbox) and D-017 (M6 release candidate) were decided by the AI assistant within its briefs and await the owner's review.
12. **Release.** Any tag, GitHub release, preprint or article publication needs the owner's explicit approval (G-PUBLIC); the push of 2026-11-25 was not a release.

### Remaining owner placeholders (file and line)

Updated 2026-11-26: none remain. The author line, repository URL, demo URL, funding and competing-interests placeholders listed at M6 (`research/paper/manuscript.md` lines 3, 254, 258 and 260; `README.md` lines 80 and 90; `articles/medium.md` lines 6, 29 and 31; `articles/linkedin.md` line 12; `demo/README.md` line 8; `CITATION.cff` lines 5 and 12) were filled from the owner's answers of 2026-11-26, and `manuscript.tex` and the PDFs were regenerated from the manuscript.

## Owner answers recorded (2026-11-26)

Source: owner, 2026-11-26, decision sheet (`labs/_shared/owner-decision-sheet-2026-11-26.md`, answers in `labs/_shared/owner-approvals-2026-11-26.md`). Applied as wording and configuration only (D-018); no result, analysis, figure, config, seed, frozen protocol or checksummed output changed. No box above is ticked by this round.

- **A1.** Out-of-date "not pushed" statements corrected in this file, `release_checklist.md`, `roadmap.md` and the README (append-only records left as written).
- **B1.** Repository URL `https://github.com/mohamedbechirkefi/scale-single-machine-throughput` in the manuscript, README, articles and `CITATION.cff` (`repository-code`).
- **B2.** Demo URL `https://scale-single-machine-throughput.kefimohamedbechir.workers.dev` in the README and `demo/README.md`; `demo/wrangler.jsonc` added (Cloudflare Workers static assets, free plan, assets only, deployed by the coordinator).
- **B3.** Author line "Mohamed Bechir Kefi, independent researcher" in the manuscript, README, `articles/medium.md` and the demo footer; `CITATION.cff` affiliation "Independent researcher". The frozen record `research/freeze.json` (C3, "no affiliation") is not edited.
- **B4.** Funding: "No funding was received." Competing interests: "The author declares no competing interests."
- **B5.** The AI-use statement of manuscript section 11 is owner-approved as drafted.
- **B6, B7.** The manuscript title is owner-approved; `CITATION.cff` carries it, old-title comment removed; "working title" removed from the README heading. The article titles stay drafts (B15).
- **B8.** `0.1.0-rc1` and no `date-released` kept; the release step is recorded in `release_checklist.md`.
- **B9.** No editable file needed scrubbing; what remains and why is in `reproducibility_report.md` section 4.
- **B11, B13, B14.** Release-note sentences added to `release_checklist.md`; source labels accepted.
- **R-SCALE-1.** `results/raw/` stays tracked; README, `.gitignore` comment, `CLAUDE.md`, `results/README.md` and limitation 25 agree.
- **R-SCALE-2.** A2 per the frozen rule as applied (no confirmatory estimate, dominance unresolved); the alternatives 246.8 and 90.8 stay exploratory.
- **R-SCALE-3, R-SCALE-4.** EXP-003 and EXP-004: not run; to run later after the owner sets the parameters.

Still open (owner only): **B15** article drafts and titles; **B16** full-text review and sign-off of each box above; **B18** release, tag, DOI or preprint; the **freezes** of the EXP-003 parameters and of the EXP-004 config (G-FREEZE); **R-SCALE-5**, the review of the assistant decisions D-012 and D-014 to D-017 as a whole (not answered on 2026-11-26).
