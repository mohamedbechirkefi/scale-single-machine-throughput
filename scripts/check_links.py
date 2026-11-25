# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""M6 link and reference check (master prompt 11.6).

1. Every relative Markdown link [text](target) in a tracked .md file resolves to an
   existing file, and its #anchor (if any) to a heading of the target.
2. Every repository path quoted in backticks in a tracked .md file (a path with a
   slash and a file extension, no placeholder or wildcard) exists; the append-only
   journals are exempt from this part, because they record paths as they were.
3. Every citation key [key] or [key; note] in the manuscript resolves to an entry
   of research/paper/references.bib, and every bib entry is cited.

Prints one line per problem and LINK-CHECK PASS or LINK-CHECK FAIL (n).
Usage: .venv/bin/python -I scripts/check_links.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)")
CODE_PATH = re.compile(r"`([A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+\.[A-Za-z0-9]+)`")
# Paths that the documents describe but that are not files of this repository:
# outputs of commands not run (EXP-003/EXP-004 raw folders), the shared briefs, and
# files that are generated locally and ignored by git.
NOT_IN_REPO = ("labs/_shared/", "results/raw/EXP-003", "results/raw/EXP-004",
               "results/confirmatory/", "demo/dist/", "demo/node_modules/", "dist/", "EXP-NNN")
# Quoted paths may be written relative to the repository root, the document, or the
# research/ and demo/ folders the surrounding text is about.
BASES = ("", "research", "demo")
# Append-only journals keep the paths as they were when written; only their links are checked.
JOURNALS = ("progress.md", "research/decision_log.md")
CITE = re.compile(r"\[([a-z][a-z0-9-]*\d{4}[a-z]?|tene-wrk2)(?:[;,\]])")
BIBKEY = re.compile(r"^@\w+\{([^,]+),", re.M)


def tracked_markdown() -> list[str]:
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [p for p in out.stdout.split() if p != "master_prompt.md"]


def slug(heading: str) -> str:
    text = re.sub(r"[`*_]", "", heading.strip().lower())
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: str) -> set[str]:
    with open(path, encoding="utf-8") as fh:
        return {slug(m.group(1)) for m in re.finditer(r"^#+\s+(.*)$", fh.read(), re.M)}


def check_links(files: list[str]) -> list[str]:
    problems = []
    for rel in files:
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            text = fh.read()
        for m in LINK.finditer(text):
            target = m.group(1) or m.group(2)
            if re.match(r"^[a-z]+:", target):
                continue
            path, _, anchor = target.partition("#")
            dest = os.path.normpath(os.path.join(ROOT, os.path.dirname(rel), path)) if path else os.path.join(ROOT, rel)
            if not os.path.exists(dest):
                problems.append(f"{rel}: link target missing: {target}")
            elif anchor and dest.endswith(".md") and anchor not in anchors(dest):
                problems.append(f"{rel}: anchor missing: {target}")
        for m in CODE_PATH.finditer(text if rel not in JOURNALS else ""):
            path = m.group(1)
            if any(path.startswith(p) or p in path for p in NOT_IN_REPO):
                continue
            here = os.path.normpath(os.path.join(ROOT, os.path.dirname(rel), path))
            if not (os.path.exists(here) or any(os.path.exists(os.path.join(ROOT, b, path)) for b in BASES)):
                problems.append(f"{rel}: quoted path missing: {path}")
    return problems


def check_citations() -> list[str]:
    with open(os.path.join(ROOT, "research/paper/manuscript.md"), encoding="utf-8") as fh:
        cited = set(CITE.findall(fh.read()))
    with open(os.path.join(ROOT, "research/paper/references.bib"), encoding="utf-8") as fh:
        keys = set(BIBKEY.findall(fh.read()))
    problems = [f"manuscript: citation key not in references.bib: {k}" for k in sorted(cited - keys)]
    problems += [f"references.bib: entry never cited in the manuscript: {k}" for k in sorted(keys - cited)]
    return problems


def main() -> int:
    files = tracked_markdown()
    problems = check_links(files) + check_citations()
    for p in problems:
        print(p)
    print(f"checked {len(files)} Markdown files")
    print("LINK-CHECK PASS" if not problems else f"LINK-CHECK FAIL ({len(problems)})")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
