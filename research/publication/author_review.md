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

M6 prepared a release candidate. Nothing was released, tagged or published, and no box above is ticked: only the owner signs off.

### What to read for each box

1. **Author list and metadata.** `research/paper/manuscript.md` front matter (author placeholder quoting common decision C3); `CITATION.cff` (authors, title, version `0.1.0-rc1`, no `date-released`); `README.md` section "Citation"; PDF metadata of `research/paper/manuscript.pdf` (its Author field carries the placeholder).
2. **AI-assistance disclosure.** `research/paper/manuscript.md` section 11, paragraph "AI assistance"; limitation 14 in section 7; `articles/medium.md` last paragraph.
3. **Funding and competing interests.** `research/paper/manuscript.md` section 11 (both placeholders); `README.md` section "Citation"; `articles/medium.md` last paragraph.
4. **Claims and limitations.** `research/paper/manuscript.md` abstract and sections 5 to 7; `research/claims_register.csv`; `research/publication/claims_audit.md`; `research/publication/review_pass_2.md`; `research/publication/evidence_audit_M4.md` and `evidence_audit_M6.md`; the PDFs in `research/paper/` and the four report PDFs (`research/experiments/EXP-001/report.pdf` to `research/experiments/EXP-004/report.pdf`).
5. **Publication decision.** `research/publication/release_checklist.md`; `research/publication/reproducibility_report.md`; `research/publication/dependency_licences.md`.

### Open decisions for this repository (none chosen at M6)

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

- `research/paper/manuscript.md` line 3: author line.
- `research/paper/manuscript.md` line 254: repository URL.
- `research/paper/manuscript.md` line 258: funding statement.
- `research/paper/manuscript.md` line 260: competing-interests statement.
- `README.md` line 80: demo URL.
- `README.md` line 90: author line and affiliation, repository URL, funding and competing interests.
- `articles/medium.md` line 6: author line.
- `articles/medium.md` line 29: repository URL.
- `articles/medium.md` line 31: funding and competing-interests statements.
- `articles/linkedin.md` line 12: repository URL.
- `demo/README.md` line 8: demo URL.
- `CITATION.cff` line 5: repository URL (comment; no `repository-code` key); line 12: author line (comment "to be confirmed by the owner").
- `research/paper/manuscript.tex` and the PDFs repeat the manuscript placeholders, because they are generated from it.
