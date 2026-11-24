<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Release checklist (M6)

Status at M0: nothing checked. Publication requires the owner's explicit approval (G-PUBLIC).

- [ ] Owner approved the frozen protocol before confirmatory runs (hash recorded).
- [ ] Every registered experiment has a truthful standalone report, including failed or exploratory ones.
- [ ] Integrated manuscript complete; abstract written after analysis.
- [ ] Manuscript and report PDFs compiled (Typst path) and visually inspected; `manuscript.tex` generated.
- [ ] Clean clone in a separate directory: `uv sync --locked`, tests, smoke reproduction, demo build; outputs recorded.
- [ ] Artifact manifest maps every number to experiment, run ids, result path, script, hash and revision.
- [ ] Claims audit complete; no unsupported claim remains.
- [ ] References verified against sources actually accessed.
- [ ] Data manifest and licences verified; no non-redistributable data bundled.
- [ ] Secret and personal-data scan clean.
- [ ] README, demo, paper, reports and articles use identical numbers and labels.
- [ ] Licence files unchanged since the owner's decision (D-001).
- [ ] Owner review recorded in `author_review.md`.
- [ ] Owner explicitly approved any push, release or preprint.
