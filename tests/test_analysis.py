# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Frozen EXP-001 / EXP-002 analysis (scale.analysis, D-012) on hand-built results,
and the protocol section 10 re-attempts of the runner."""

import math

import pytest

from scale import analysis as an
from scale import runner
from scale.config import parse_config

LADDER = (1, 2, 4, 8, 16, 32, 64, 128)


def _lv(c, g, lim=False, p99=1.0, ab=None):
    return {"concurrency": c, "goodput_rps": g, "generator_limited": lim, "p99_ms": p99,
            "error_rate": 0.0, "server_cpu_util": 1.0, "generator_cpu_util": 0.3, "ab_rps": ab}


def _run(arm, b, peak, peak_c=8, lim_at_peak=False, status="ok", rid_suffix="", pos=0):
    levels = [_lv(c, peak * (1.0 if c == peak_c else 0.5), lim=(lim_at_peak and c == peak_c))
              for c in LADDER]
    res = {"run_id": f"EXP-002-b{b:02d}-{arm}-deadbeef{rid_suffix}", "arm": arm, "block": b,
           "arm_position": pos, "status": status, "failure": None if status == "ok" else "x",
           "levels": levels, "summary": {"c_sat": peak_c}, "server_stats": {}}
    man = {"started_utc": f"2026-11-25T00:{b:02d}:{pos:02d}{rid_suffix}"}
    return res, man


def _matrix(ratios_by_arm, blocks=10, a0=100.0, **kw):
    runs = []
    for b in range(blocks):
        runs.append(_run("A0", b, a0, pos=0))
        for i, (arm, rs) in enumerate(ratios_by_arm.items()):
            runs.append(_run(arm, b, a0 * rs[b], pos=i + 1, **kw.get(arm, {})))
    return runs


def test_ratio_and_verdicts_hand_example():
    lr = [math.log(2.0)] * 10
    s = an.ratio_summary(lr)
    assert s["ratio"] == pytest.approx(2.0) and s["ci9875"] == pytest.approx([2.0, 2.0])
    assert an.verdict(s) == "H0 rejected: R > 1"
    assert an.verdict({"ci9875": [0.5, 0.8]}) == "H0 rejected: R < 1"
    assert an.verdict({"ci9875": [0.97, 1.02]}).startswith("no meaningful effect")
    assert an.verdict({"ci9875": [0.90, 1.02]}).startswith("inconclusive")


def test_exp002_primary_dominance_and_s3():
    r = {"A1": [1.5 + 0.01 * b for b in range(10)], "A2": [200.0 + b for b in range(10)],
         "A3": [10.0 + 0.1 * b for b in range(10)], "A4": [1.0 + 0.001 * (b % 3 - 1) for b in range(10)]}
    out = an.analyse_exp002(_matrix(r), 10, ["A0", "A1", "A2", "A3", "A4"])
    est = out["confirmatory"]
    assert all(est[a]["included"] for a in an.TREATMENTS)
    gm = math.exp(sum(math.log(x) for x in r["A2"]) / 10)
    assert est["A2"]["ratio"] == pytest.approx(gm)
    assert est["A2"]["verdict"] == "H0 rejected: R > 1"
    assert est["A4"]["verdict"].startswith("no meaningful effect")
    assert out["dominance"]["status"] == "dominance claimed" and out["dominance"]["top_arm"] == "A2"
    assert out["ranking"] == ["A2", "A3", "A1", "A4"]
    # S3 uses levels 16, 32, 64 where every arm is at half its peak, so the ratios are equal
    assert out["sensitivity_s3"]["ranking_equal_to_primary"] is True
    assert out["cells_ok"] == 50 and out["missing_cells"] == []


def test_generator_limited_peak_excludes_the_arm():
    r = {a: [2.0] * 10 for a in an.TREATMENTS}
    out = an.analyse_exp002(_matrix(r, A2={"lim_at_peak": True}), 10, ["A0", "A1", "A2", "A3", "A4"])
    assert out["confirmatory"]["A2"]["included"] is False
    assert out["confirmatory"]["A2"]["undefined_blocks"] == list(range(10))
    assert out["dominance"]["status"] == "unresolved"
    # exploratory alternatives still estimate A2
    assert out["exploratory"]["gstar_unfiltered"]["A2"]["ratio"] == pytest.approx(2.0)
    assert out["exploratory"]["gstar_over_unlimited_levels"]["A2"]["ratio"] == pytest.approx(1.0)


def test_reattempt_cell_selection_and_missing():
    runs = _matrix({a: [2.0] * 3 for a in an.TREATMENTS}, blocks=3)
    runs = [rm for rm in runs if not (rm[0]["block"] == 1 and rm[0]["arm"] == "A3")]
    runs.append(_run("A3", 1, 0.0, status="excluded"))
    runs.append(_run("A3", 1, 300.0, rid_suffix="-r1"))
    runs = [rm for rm in runs if not (rm[0]["block"] == 2 and rm[0]["arm"] == "A4")]
    runs.append(_run("A4", 2, 0.0, status="failed"))
    out = an.analyse_exp002(runs, 3, ["A0", "A1", "A2", "A3", "A4"])
    assert out["confirmatory"]["A3"]["included"] and out["confirmatory"]["A3"]["log_ratios"][1] == pytest.approx(math.log(3.0))
    assert out["missing_cells"] == [(2, "A4")]
    assert out["confirmatory"]["A4"]["included"] is False
    assert {d["status"] for d in out["not_ok_runs"]} == {"excluded", "failed"}


def test_exp001_table_and_gate():
    runs = []
    for b in range(5):
        lv = [_lv(1, 20000.0 + b, ab=20000.0), _lv(8, 28000.0, ab=28000.0), _lv(32, 26000.0, ab=31000.0)]
        runs.append(({"run_id": f"EXP-001-b{b:02d}-A0-x", "arm": "A0", "block": b, "status": "ok",
                      "failure": None, "levels": lv}, {}))
    out = an.analyse_exp001(runs)
    assert out["levels"][1]["c_gen_median"] == 20002.0
    assert out["levels"][32]["ratio_median"] == pytest.approx(26000 / 31000)
    assert out["gate_exp002_may_start"] is False and out["h0_ratio_median_in_band_all_levels"] is False


def test_runner_reattempts_confirmatory_cells(monkeypatch, tmp_path):
    calls = []

    def fake_run_one(cfg, arm, block, pos, out_dir, root, command, log, attempt=0):
        calls.append((block, arm, attempt))
        status = "excluded" if (block, arm) == (0, "A2") and attempt < 2 else "ok"
        res = {"run_id": f"x-{block}-{arm}-r{attempt}", "status": status, "failure": None,
               "summary": {"peak_goodput_rps": 1.0}}
        return res, {"runtime_s": 0.1}

    monkeypatch.setattr(runner, "run_one", fake_run_one)
    base = {"experiment_id": "T", "arms": ["A0", "A2"], "concurrency": [1], "blocks": 2,
            "idle_probe_enforce": True}
    batch = runner.run_experiment(parse_config({**base, "label": "confirmatory"}), str(tmp_path / "c"),
                                  str(tmp_path), ["t"], log=lambda s: None)
    assert [c for c in calls if c[2] > 0] == [(0, "A2", 1), (0, "A2", 2)]
    assert len(batch["runs"]) == 6 and batch["runs"][-1]["status"] == "ok"
    calls.clear()
    runner.run_experiment(parse_config({**base, "label": "exploratory"}), str(tmp_path / "e"),
                          str(tmp_path), ["t"], log=lambda s: None)
    assert all(c[2] == 0 for c in calls) and len(calls) == 4
