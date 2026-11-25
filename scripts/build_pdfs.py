# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""M6: build the manuscript, supplementary and experiment-report PDFs with the
repository builder (scale.report.build_pdf: pandoc to Typst, typst Python package),
regenerate manuscript.tex with pandoc, and check each PDF's metadata with pypdf
(title set, no e-mail address, no local path, size under 5 MB).

Usage: .venv/bin/python -I scripts/build_pdfs.py [--typ-dir DIR]
Outside labs/, set SCALE_PANDOC and SCALE_TYPST_PYTHON (see scale.report).
(pypdf and typst are read from the shared tools Python, scale.report.TYPST_PY.)
The intermediate .typ files go to --typ-dir (default: a temporary directory that is
removed). Exit 1 on any build or metadata failure. Never writes a PDF on failure."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from scale.report import PANDOC, TYPST_PY, build_pdf, escape_star_notation  # noqa: E402

DOCS = [
    "research/paper/manuscript.md",
    "research/paper/supplementary.md",
    "research/experiments/EXP-001/report.md",
    "research/experiments/EXP-002/report.md",
    "research/experiments/EXP-003/report.md",
    "research/experiments/EXP-004/report.md",
]
MAX_BYTES = 5 * 1024 * 1024
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
LOCAL = re.compile(r"(/Users/|/home/|/private/|/tmp/|[A-Z]:\\\\)")


_META = ("import json, sys, pypdf; r = pypdf.PdfReader(sys.argv[1]); "
         "print(json.dumps({'pages': len(r.pages), 'meta': {k: str(v) for k, v in (r.metadata or {}).items()}}))")


def read_pdf(path: str) -> dict:
    out = subprocess.run([TYPST_PY, "-I", "-c", _META, path], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def check_pdf(path: str, info: dict) -> list[str]:
    problems = []
    meta = info["meta"]
    if not meta.get("/Title", "").strip():
        problems.append("title not set")
    for key, text in meta.items():
        if EMAIL.search(text):
            problems.append(f"e-mail address in {key}")
        if LOCAL.search(text):
            problems.append(f"local path in {key}")
    if os.path.getsize(path) >= MAX_BYTES:
        problems.append("size 5 MB or more")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--typ-dir", default=None)
    a = ap.parse_args(argv)
    tmp = None
    typ_dir = a.typ_dir
    if typ_dir is None:
        tmp = tempfile.TemporaryDirectory()
        typ_dir = tmp.name
    os.makedirs(typ_dir, exist_ok=True)
    failures = 0
    with open(os.path.join(ROOT, "research/paper/manuscript.md"), encoding="utf-8") as fh:
        source = escape_star_notation(fh.read())
    r = subprocess.run([PANDOC, "-f", "markdown", "-s", "-t", "latex", "-o", "research/paper/manuscript.tex"],
                       input=source, cwd=ROOT, capture_output=True, text=True)
    if r.returncode == 0:  # SPDX header on the generated LaTeX source (M6)
        tex = os.path.join(ROOT, "research/paper/manuscript.tex")
        with open(tex, encoding="utf-8") as fh:
            body = fh.read()
        with open(tex, "w", encoding="utf-8") as fh:
            fh.write("% SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0\n"
                     "% Generated from manuscript.md by pandoc (scripts/build_pdfs.py); never hand-edited.\n" + body)
    print(f"manuscript.tex: pandoc exit {r.returncode}")
    failures += r.returncode != 0
    for rel in DOCS:
        md = os.path.join(ROOT, rel)
        pdf = md[: -len(".md")] + ".pdf"
        stem = rel.replace("/", "_")[: -len(".md")]
        ok, msg = build_pdf(md, pdf, typ_path=os.path.join(typ_dir, stem + ".typ"))
        if not ok:
            print(f"FAIL {rel}: {msg}")
            failures += 1
            continue
        info = read_pdf(pdf)
        pages, title = info["pages"], info["meta"].get("/Title")
        problems = check_pdf(pdf, info)
        status = "PASS" if not problems else "FAIL " + "; ".join(problems)
        print(f"{status} {os.path.relpath(pdf, ROOT)}: {pages} pages, {os.path.getsize(pdf)} bytes, title {title!r}")
        failures += bool(problems)
    if tmp is not None:
        tmp.cleanup()
    print("PDF-BUILD PASS" if not failures else f"PDF-BUILD FAIL ({failures})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
