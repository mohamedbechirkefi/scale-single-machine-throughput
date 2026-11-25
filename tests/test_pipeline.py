# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Integration: config -> runner (real server subprocess) -> validated results ->
report; schema fail-closed behaviour; CLI refusal of confirmatory configs."""

import copy
import json
import os

import pytest

from scale import cli
from scale.config import parse_config
from scale.report import build_report, load_runs, pilot_analysis, project_runtime
from scale.runner import arm_order, connection_seeds, run_experiment
from scale.schema import SchemaError, read_result, validate_manifest, validate_result, write_result

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TINY = {"experiment_id": "TEST", "label": "exploratory", "arms": ["A0", "A2"],
        "concurrency": [1, 2], "warmup_s": 0.1, "measure_s": 0.3, "blocks": 2, "study_seed": 5,
        "idle_probe_enforce": False, "workload": {"rows": 1000, "payload_bytes": 32}}


@pytest.fixture(scope="module")
def tiny_run(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("run"))
    batch = run_experiment(parse_config(TINY), out, ROOT, ["pytest"], log=lambda s: None)
    return out, batch


def test_runner_produces_valid_results(tiny_run):
    out, batch = tiny_run
    assert len(batch["runs"]) == 4
    assert all(r["status"] == "ok" for r in batch["runs"])
    runs = load_runs(out)  # validates every result and manifest
    assert len(runs) == 4
    for res, man in runs:
        assert res["label"] == "exploratory"
        assert [lv["concurrency"] for lv in res["levels"]] == [1, 2]
        assert res["summary"]["peak_goodput_rps"] > 0
        assert all(lv["invalid_body"] == 0 and lv["error_rate"] == 0 for lv in res["levels"])
        assert man["git"]["revision"] is None or len(man["git"]["revision"]) == 40
        assert man["versions"]["sqlite"] and man["cpu"]["logical_cpus"] >= 1
        assert man["runtime_s"] > 0 and man["dataset_sha256"]
        assert man["server_peak_rss_mb"] > 0
    shas = {man["dataset_sha256"] for _, man in runs}
    assert len(shas) == 1  # same dataset for every arm and block


def test_report_from_results(tiny_run):
    out, _ = tiny_run
    s = build_report(out, full_levels=7, full_warmup_s=5, full_measure_s=15, full_runs=50)
    md = open(s["report_md"]).read()
    assert "EXPLORATORY" in md and "TEST-b00-A0" in md
    assert os.path.exists(os.path.join(out, "figures", "goodput_vs_concurrency.png"))
    assert set(s["pilot"]) == {"A2"} and s["pilot"]["A2"]["n_blocks"] == 2
    assert "sd_log_ratio" in s["pilot"]["A2"]
    assert s["projection_full_matrix"]["per_run_s"] > 7 * 20


def test_report_fails_closed_on_malformed_result(tiny_run, tmp_path):
    out, _ = tiny_run
    import shutil

    bad = tmp_path / "bad"
    shutil.copytree(out, bad)
    victim = sorted((bad / "runs").glob("*-A0-*[0-9a-f].json"))[0]
    obj = json.loads(victim.read_text())
    obj["levels"][0]["goodput_rps"] = -1
    victim.write_text(json.dumps(obj))
    with pytest.raises(SchemaError):
        load_runs(str(bad))
    assert cli.cmd_report(str(bad), False, 7, 5, 15, 50) == 1


def test_schema_rejects_and_write_refuses(tiny_run, tmp_path):
    out, _ = tiny_run
    p = sorted(x for x in os.listdir(os.path.join(out, "runs")) if not x.endswith("manifest.json"))[0]
    good = read_result(os.path.join(out, "runs", p))
    validate_result(good)
    for mutate in (lambda o: o.pop("run_id"), lambda o: o.update(label="final"),
                   lambda o: o.update(schema_version="0.9"), lambda o: o.update(extra=1),
                   lambda o: o["levels"][0].update(error_rate=2.0)):
        bad = copy.deepcopy(good)
        mutate(bad)
        with pytest.raises(SchemaError):
            validate_result(bad)
        target = tmp_path / "x.json"
        with pytest.raises(SchemaError):
            write_result(str(target), bad)
        assert not target.exists()
    with pytest.raises(SchemaError):
        validate_manifest({"schema_version": "1.0.0"})
    (tmp_path / "broken.json").write_text("{")
    with pytest.raises(SchemaError):
        read_result(str(tmp_path / "broken.json"))


def test_pilot_analysis_hand_example():
    def run(block, arm, g):
        return ({"status": "ok", "experiment_id": "E", "block": block, "arm": arm,
                 "summary": {"peak_goodput_rps": g}}, {})
    runs = [run(0, "A0", 100), run(0, "A1", 200), run(1, "A0", 100), run(1, "A1", 400)]
    p = pilot_analysis(runs)["A1"]
    assert p["log_ratios"] == pytest.approx([0.693147, 1.386294], abs=1e-6)
    assert p["geometric_mean_ratio"] == pytest.approx(2 ** 1.5)
    assert p["sd_log_ratio"] == pytest.approx(0.490129, abs=1e-6)


def test_projection_hand_example():
    res = {"levels": [{}, {}]}
    man = {"config": {"warmup_s": 1.0, "measure_s": 2.0}, "runtime_s": 10.0}
    # overhead = 10 - 2 * 3.3 = 3.4; per run = 3.4 + 7 * 20.3 = 145.5
    p = project_runtime([(res, man)], levels=7, warmup_s=5, measure_s=15, n_runs=50)
    assert p["per_run_s"] == pytest.approx(145.5)
    assert p["total_h"] == pytest.approx(145.5 * 50 / 3600)


def test_seed_plan_common_random_numbers():
    assert sorted(arm_order(("A0", "A1", "A2"), 1, 0)) == ["A0", "A1", "A2"]
    assert arm_order(("A0", "A1", "A2"), 1, 0) == arm_order(("A0", "A1", "A2"), 1, 0)
    orders = {tuple(arm_order(("A0", "A1", "A2", "A3", "A4"), 1, b)) for b in range(10)}
    assert len(orders) > 1  # order is randomised across blocks
    assert connection_seeds(7, 8, 8) == connection_seeds(7, 8, 8)
    assert len(set(connection_seeds(7, 8, 8))) == 8


def test_exp002_accepted_by_guard_after_resolution():
    from scale.config import load_config
    path = os.path.join(ROOT, "experiments", "EXP-002.json")
    assert cli.freeze_status(load_config(path), ROOT, path) == (True, "frozen")


def test_cli_rejects_invalid_config(tmp_path, capsys):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({**TINY, "arms": ["A7"]}))
    assert cli.main(["run", str(p)]) == 2


def test_degenerate_case_flags():
    from scale.report import degenerate_cases

    def lv(c, g):
        return {"concurrency": c, "validated_ok": 1, "invalid_body": 0, "error_rate": 0.0,
                "generator_limited": False, "connections_finished": c, "status_counts": {}}

    def res(arm, peak_c, stats):
        return ({"run_id": f"R-{arm}", "status": "ok", "failure": None, "kind": "closed_sweep",
                 "arm": arm, "levels": [lv(1, 1), lv(8, 2), lv(64, 3)],
                 "summary": {"c_at_peak": peak_c}, "server_stats": stats}, {})

    notes = degenerate_cases([res("A3", 64, {}), res("A2", 1, {}),
                              res("A4", 8, {"rejected_503": 0}),
                              res("A1", 8, {"cache_hits": 1, "cache_misses": 3})])
    text = "\n".join(notes)
    assert "R-A3: peak at the highest" in text
    assert "R-A2: peak at the lowest" in text
    assert "R-A4: A4 admission limit never triggered" in text
    assert "R-A1: A1 cache hit ratio 0.25" in text
    assert degenerate_cases([res("A0", 8, {})]) == []


def test_cli_test_command_passes_options(monkeypatch):
    calls = []
    monkeypatch.setattr(cli.subprocess, "call", lambda cmd, cwd: calls.append(cmd) or 0)
    assert cli.main(["test", "-q", "-k", "x"]) == 0
    assert calls[0][-3:] == ["-q", "-k", "x"]
