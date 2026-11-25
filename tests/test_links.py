# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""M6: relative links, quoted repository paths and citation keys resolve
(scripts/check_links.py), and the checker itself detects a broken link."""

from __future__ import annotations

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location("check_links", ROOT / "scripts" / "check_links.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_links_and_quoted_paths_resolve():
    mod = _load()
    assert mod.check_links(mod.tracked_markdown()) == []


def test_every_citation_resolves_and_every_bib_entry_is_cited():
    assert _load().check_citations() == []


def test_checker_reports_a_missing_target(tmp_path, monkeypatch):
    mod = _load()
    (tmp_path / "a.md").write_text("[x](missing.md) and `docs/none.txt` and [y](b.md#nope)\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Present\n", encoding="utf-8")
    monkeypatch.setattr(mod, "ROOT", str(tmp_path))
    problems = mod.check_links(["a.md"])
    assert len(problems) == 3
