# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""M5 consistency (master prompt 11.6): the demo shows the manuscript's numbers.

1. Re-running the export in memory reproduces the committed
   demo/public/data/results.json byte for byte.
2. Every display string in it appears verbatim in research/paper/manuscript.md,
   unless it is a documented exception below (there are none at M5).
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPLAY_KEYS = {"display", "interval_display", "interval95_display", "generator_limited_threshold_display"}

# Documented exceptions: display string -> reason. Empty at M5.
EXCEPTIONS: dict[str, str] = {}


def _export():
    spec = importlib.util.spec_from_file_location("export_demo_data", ROOT / "scripts" / "export_demo_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _displays(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in DISPLAY_KEYS and isinstance(v, str):
                yield v
            elif k == "display_values":
                yield from v
            else:
                yield from _displays(v)
    elif isinstance(o, list):
        for v in o:
            yield from _displays(v)


def test_committed_results_json_equals_fresh_export():
    mod = _export()
    fresh = mod.render(mod.build(ROOT))
    committed = (ROOT / "demo" / "public" / "data" / "results.json").read_text(encoding="utf-8")
    assert fresh == committed


def test_every_display_string_is_in_the_manuscript():
    data = json.loads((ROOT / "demo" / "public" / "data" / "results.json").read_text(encoding="utf-8"))
    manuscript = (ROOT / "research" / "paper" / "manuscript.md").read_text(encoding="utf-8")
    shown = list(_displays(data))
    assert len(shown) > 50
    missing = [s for s in shown if s not in manuscript and s not in EXCEPTIONS]
    assert missing == []


def test_every_registered_experiment_is_exported_with_status_and_verdict():
    data = json.loads((ROOT / "demo" / "public" / "data" / "results.json").read_text(encoding="utf-8"))
    ids = [e["id"] for e in data["experiments"]]
    assert ids == ["EXP-001", "EXP-002", "EXP-003", "EXP-004"]
    for e in data["experiments"]:
        assert e["status"] and e["verdict"]
    assert {d["id"] for d in data["pending_owner_decisions"]} == {"D-012", "EXP-003 parameters", "EXP-004", "results/raw"}
    assert all(not s["path"].startswith("results/raw") for s in data["sources"])


# M6: the README and the article drafts quote the manuscript's numbers too.
# Structural tokens that are not results: "11.7" is the master prompt section on the release package.
STRUCTURAL_TOKENS = {"11.7"}


def test_readme_and_article_numbers_are_in_the_manuscript():
    import re

    manuscript = (ROOT / "research" / "paper" / "manuscript.md").read_text(encoding="utf-8")
    number = re.compile(r"(?<![\w.-])\d[\d,]*(?:\.\d+)?(?![\w])")
    docs = [ROOT / "README.md", *sorted((ROOT / "articles").glob("*.md"))]
    missing = {}
    for doc in docs:
        tokens = set(number.findall(doc.read_text(encoding="utf-8")))
        bad = sorted(t for t in tokens if t not in manuscript and t not in STRUCTURAL_TOKENS)
        if bad:
            missing[doc.name] = bad
    assert missing == {}
