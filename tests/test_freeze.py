# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Freeze guard (research/freeze.json), the frozen arm values, the listen backlog
and the pre-stated quiet-pilot rule (protocol section 7.1)."""

import json
import os
import shutil

import pytest

from scale import cli, freeze
from scale import pilotrule as pr
from scale.config import ARMS, load_config
from scale.server import AdmissionLimiter, Overloaded, listen_backlog

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXP001 = os.path.join(ROOT, "experiments", "EXP-001.json")


def _copy_repo(tmp_path):
    """Minimal copy of the frozen files into a temporary root."""
    for rel in ("research/protocol.md", "research/freeze.json", "experiments/EXP-001.json",
                "experiments/EXP-002.json", "research/experiments/EXP-001/protocol.md",
                "research/experiments/EXP-002/protocol.md"):
        dst = tmp_path / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(os.path.join(ROOT, rel), dst)
    return tmp_path


def test_freeze_record_hashes_match_the_files():
    rec = freeze.load_record(ROOT)
    assert rec is not None and rec["status"] == "frozen"
    assert freeze.sha256_file(os.path.join(ROOT, rec["protocol"]["path"])) == rec["protocol"]["sha256"]
    for e in rec["experiment_protocols"] + rec["configs"]:
        assert freeze.sha256_file(os.path.join(ROOT, e["path"])) == e["sha256"], e["path"]
    assert freeze.protocol_is_marked_frozen(ROOT)


def test_frozen_exp001_is_accepted_by_the_guard_and_run(monkeypatch, capsys):
    cfg = load_config(EXP001)
    assert cli.freeze_status(cfg, ROOT, EXP001) == (True, "frozen")
    calls = []

    def fake_run(cfg, out_dir, root, command):  # no confirmatory run in tests
        calls.append(cfg.experiment_id)
        return {"runs": [], "runtime_s": 0.0}

    import scale.runner

    monkeypatch.setattr(scale.runner, "run_experiment", fake_run)
    assert cli.main(["run", EXP001, "--out", "/nonexistent-not-used"]) == 0
    assert calls == ["EXP-001"]


def test_changed_config_is_refused(tmp_path, capsys):
    raw = json.load(open(EXP001))
    raw["blocks"] = 6
    p = tmp_path / "EXP-001.json"
    p.write_text(json.dumps(raw))
    cfg = load_config(str(p))
    ok, why = cli.freeze_status(cfg, ROOT, str(p))
    assert not ok and "not in the freeze record" in why
    assert cli.main(["run", str(p)]) == cli.EXIT_REFUSED


def test_changed_protocol_is_refused(tmp_path):
    root = _copy_repo(tmp_path)
    cfg_path = str(root / "experiments" / "EXP-001.json")
    cfg = load_config(cfg_path)
    assert freeze.check(cfg, cfg_path, str(root)) == (True, "frozen")
    with open(root / "research" / "protocol.md", "a") as fh:
        fh.write("\nedited after the freeze\n")
    ok, why = freeze.check(cfg, cfg_path, str(root))
    assert not ok and "changed since the freeze" in why


def test_changed_experiment_protocol_is_refused(tmp_path):
    root = _copy_repo(tmp_path)
    cfg_path = str(root / "experiments" / "EXP-001.json")
    cfg = load_config(cfg_path)
    with open(root / "research" / "experiments" / "EXP-001" / "protocol.md", "a") as fh:
        fh.write("x")
    ok, why = freeze.check(cfg, cfg_path, str(root))
    assert not ok and "mismatch" in why


def test_missing_record_or_unfrozen_status_is_refused(tmp_path):
    root = _copy_repo(tmp_path)
    cfg_path = str(root / "experiments" / "EXP-001.json")
    cfg = load_config(cfg_path)
    os.remove(root / "research" / "freeze.json")
    ok, why = freeze.check(cfg, cfg_path, str(root))
    assert not ok and "freeze record" in why
    (root / "research" / "protocol.md").write_text("| Status | **DRAFT v0.1, not frozen.** |\n")
    assert freeze.check(cfg, cfg_path, str(root))[0] is False


def test_exp002_deferred_until_resolution(tmp_path):
    assert "quiet-machine pilot rule" in freeze.deferred_reason("EXP-002", ROOT)
    assert freeze.deferred_reason("EXP-001", ROOT) is None
    # A resolution (rule applied, config completed and hashed) makes it acceptable.
    root = _copy_repo(tmp_path)
    raw = json.load(open(root / "experiments" / "EXP-002.json"))
    raw.update(blocks=10, concurrency=[1, 2, 4, 8, 16, 32, 64, 128], generator_ceiling_rps=30000.0)
    cfg_path = root / "experiments" / "EXP-002.json"
    cfg_path.write_text(json.dumps(raw))
    rec = json.load(open(root / "research" / "freeze.json"))
    for d in rec["deferred"]:
        if d["experiment_id"] == "EXP-002":
            d["status"] = "resolved"
    rec["configs"].append({"experiment_id": "EXP-002", "path": "experiments/EXP-002.json",
                           "sha256": freeze.sha256_file(str(cfg_path))})
    (root / "research" / "freeze.json").write_text(json.dumps(rec))
    cfg = load_config(str(cfg_path))
    assert freeze.check(cfg, str(cfg_path), str(root)) == (True, "frozen")


def test_a4_values_and_rejection_possible():
    """AM-1: W = 8, Q = 16, so W + Q = 24 is below every possible top of the sweep and
    the 25th request in the system is rejected (the draft Q = 64 could never reject at c <= 64)."""
    import threading

    a4 = ARMS["A4"]
    assert (a4.workers, a4.queue) == (8, 16)
    assert a4.workers + a4.queue < 32 < min(pr.EXTENSION_CANDIDATES)
    lim = AdmissionLimiter(a4.workers, a4.queue)
    release = threading.Event()
    entered = threading.Semaphore(0)

    def hold():
        with lim:
            entered.release()
            release.wait(5)

    threads = [threading.Thread(target=hold, daemon=True) for _ in range(a4.workers)]
    for t in threads:
        t.start()
    for _ in range(a4.workers):
        assert entered.acquire(timeout=5)
    with lim._lock:  # 16 more requests waiting in the queue
        lim._in_system += a4.queue
    with pytest.raises(Overloaded):
        lim.__enter__()
    assert lim.rejected == 1
    with lim._lock:
        lim._in_system -= a4.queue
    release.set()
    for t in threads:
        t.join(5)


def test_listen_backlog_follows_sweep():
    assert listen_backlog(1) == 128
    assert listen_backlog(64) == 128
    assert listen_backlog(1024) == 1024
    with pytest.raises(ValueError):
        listen_backlog(0)


def test_pilot_config_matches_rule_constants():
    cfg = load_config(os.path.join(ROOT, "experiments", "pilot-quiet.json"))
    assert cfg.label == "exploratory" and cfg.experiment_id == pr.PILOT_EXPERIMENT_ID
    assert cfg.concurrency == pr.PILOT_LADDER and cfg.blocks == pr.PILOT_BLOCKS
    assert tuple(cfg.arms) == pr.PILOT_ARMS and cfg.idle_probe_enforce
    assert (cfg.warmup_s, cfg.measure_s) == (5.0, 15.0)
    assert cfg.study_seed != load_config(EXP001).study_seed
    assert cfg.study_seed != json.load(open(os.path.join(ROOT, "experiments", "EXP-002.json")))["study_seed"]


def test_choose_c_max():
    assert pr.choose_c_max([64, 32]) == (128, False)
    assert pr.choose_c_max([128]) == (256, False)  # a peak at 128 is not inside {.., 128}
    assert pr.choose_c_max([256, 8]) == (512, False)
    assert pr.choose_c_max([512]) == (1024, False)
    assert pr.choose_c_max([1024]) == (1024, True)
    with pytest.raises(pr.PilotRuleError):
        pr.choose_c_max([])


def test_choose_n():
    assert pr.choose_n({"A1": 0.07, "A2": 0.01}) == 10  # boundary: <= 0.07 gives 10
    assert pr.choose_n({"A1": 0.0701, "A2": 0.01}) == 20
    with pytest.raises(pr.PilotRuleError):
        pr.choose_n({"A1": float("nan")})


def _pilot(curves, ok=True, probe=True, blocks=5):
    """curves: arm -> function(block, c) -> goodput."""
    runs = []
    for b in range(blocks):
        for arm in pr.PILOT_ARMS:
            res = {"run_id": f"P-{b}-{arm}", "experiment_id": "PILOT-QUIET", "label": "exploratory",
                   "status": "ok" if ok else "excluded", "block": b, "arm": arm,
                   "levels": [{"concurrency": c, "goodput_rps": curves[arm](b, c)} for c in pr.PILOT_LADDER]}
            runs.append((res, {"idle_probe": {"enforced": True, "passed": probe}}))
    return runs


def _hump(peak, height):
    return lambda b, c: height * (1 + 0.01 * b) * (1.0 - abs(__import__("math").log2(c / peak)) / 20)


def test_resolve_pilot_hand_example():
    flat = lambda b, c: 100.0  # noqa: E731
    curves = {"A0": flat, "A1": _hump(64, 200.0), "A2": lambda b, c: 100.0 * (2.0 + 0.001 * b),
              "A3": _hump(256, 300.0), "A4": flat}
    out = pr.resolve_pilot(_pilot(curves))
    assert out["c_max"] == 512 and not out["truncated_at_cap"]
    assert out["concurrency"] == [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    assert out["peak_concurrency"] == {"A1": [64] * 5, "A3": [256] * 5}
    assert out["sd_log_ratio"]["A4"] == 0.0
    assert out["blocks"] == 10  # every SD is small


def test_resolve_pilot_large_spread_gives_20():
    flat = lambda b, c: 100.0  # noqa: E731
    curves = {"A0": flat, "A1": _hump(32, 200.0), "A2": lambda b, c: 100.0 * (1.0 + 0.5 * b),
              "A3": _hump(32, 300.0), "A4": flat}
    out = pr.resolve_pilot(_pilot(curves))
    assert out["c_max"] == 128 and out["blocks"] == 20


def test_resolve_pilot_rejects_invalid_pilots():
    flat = lambda b, c: 100.0  # noqa: E731
    curves = {a: flat for a in pr.PILOT_ARMS}
    for bad in (_pilot(curves, ok=False), _pilot(curves, probe=False), _pilot(curves, blocks=4),
                _pilot(curves)[:-1]):
        with pytest.raises(pr.PilotRuleError):
            pr.resolve_pilot(bad)
