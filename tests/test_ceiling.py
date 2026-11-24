# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Pre-stated generator-ceiling rule (protocol section 15, AM-5): the ceiling used by
EXP-002 is the median of the EXP-001 ceiling runs."""

import json

import pytest

from scale import ceiling as cr
from scale import cli


def _exp001(peaks, ok=True, probe=True, label="confirmatory", endpoint="null", ladder=cr.EXP001_LADDER):
    runs = []
    for b, peak in enumerate(peaks):
        res = {"run_id": f"E1-{b}", "experiment_id": "EXP-001", "label": label, "endpoint": endpoint,
               "status": "ok" if ok else "excluded", "block": b, "arm": "A0",
               "levels": [{"concurrency": c, "goodput_rps": peak * (0.5 if c != 8 else 1.0)} for c in ladder]}
        runs.append((res, {"idle_probe": {"enforced": True, "passed": probe}}))
    return runs


def test_ceiling_is_median_of_run_peaks():
    out = cr.resolve_ceiling(_exp001([20000.0, 18000.0, 25000.0, 21000.0, 19000.0]))
    assert out["generator_ceiling_rps"] == 20000.0
    assert out["run_ceilings_rps"] == [20000.0, 18000.0, 25000.0, 21000.0, 19000.0]
    assert out["n_runs"] == 5 and out["rule_version"] == "ceiling-rule-1.0"


def test_run_ceiling_is_peak_over_ladder():
    res = {"levels": [{"concurrency": 1, "goodput_rps": 5.0}, {"concurrency": 8, "goodput_rps": 9.0},
                      {"concurrency": 32, "goodput_rps": 7.0}]}
    assert cr.run_ceiling(res) == 9.0


@pytest.mark.parametrize("bad", [
    _exp001([1.0] * 5, ok=False), _exp001([1.0] * 5, probe=False), _exp001([1.0] * 5, label="exploratory"),
    _exp001([1.0] * 5, endpoint="item"), _exp001([1.0] * 5, ladder=(1, 8)), _exp001([1.0] * 4),
    _exp001([1.0] * 5) + _exp001([1.0]),
])
def test_invalid_exp001_sets_no_value(bad):
    with pytest.raises(cr.CeilingRuleError):
        cr.resolve_ceiling(bad)


def test_cli_resolve_ceiling(monkeypatch, capsys):
    import scale.report as rep
    monkeypatch.setattr(rep, "load_runs", lambda d: _exp001([3.0, 1.0, 2.0, 5.0, 4.0]))
    assert cli.main(["resolve-ceiling", "x"]) == 0
    assert json.loads(capsys.readouterr().out)["generator_ceiling_rps"] == 3.0
    monkeypatch.setattr(rep, "load_runs", lambda d: _exp001([3.0] * 4))
    assert cli.main(["resolve-ceiling", "x"]) == 1


def test_rule_inputs_and_am5_recorded_in_freeze_record():
    import os

    from scale import freeze
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    rec = freeze.load_record(root)
    for e in rec["pre_stated_rule_inputs"]:
        assert freeze.sha256_file(os.path.join(root, e["path"])) == e["sha256"], e["path"]
    assert {a["id"] for a in rec["amendments"]} >= {"AM-5", "RATIFY-SCALE-1"}
    old = [s["sha256"] for s in rec["superseded_hashes"] if s["path"] == "research/protocol.md"]
    assert old and rec["protocol"]["sha256"] not in old
    assert "AM-5" in open(os.path.join(root, "research", "protocol.md"), encoding="utf-8").read()
