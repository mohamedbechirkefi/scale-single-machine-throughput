# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
import json

import pytest

from scale.config import ARMS, ConfigError, config_hash, derive_seed, load_config, parse_config

BASE = {"experiment_id": "X", "label": "exploratory", "arms": ["A0", "A2"],
        "concurrency": [1, 8], "warmup_s": 1, "measure_s": 1, "idle_probe_enforce": False}


def test_valid_config_parses():
    cfg = parse_config(BASE)
    assert cfg.arms == ("A0", "A2") and cfg.concurrency == (1, 8)
    assert cfg.workload.rows == 200_000


@pytest.mark.parametrize("patch,msg", [
    ({"label": "final"}, "label"),
    ({"arms": ["A9"]}, "unknown arm"),
    ({"arms": ["A0", "A0"]}, "repeat"),
    ({"arms": []}, "arms"),
    ({"concurrency": [8, 1]}, "increasing"),
    ({"concurrency": [0]}, "concurrency"),
    ({"concurrency": [True]}, "concurrency"),
    ({"measure_s": 0}, "measure_s"),
    ({"warmup_s": -1}, "warmup_s"),
    ({"blocks": 0}, "blocks"),
    ({"kind": "batch"}, "kind"),
    ({"endpoint": "admin"}, "endpoint"),
    ({"bogus": 1}, "unknown config keys"),
    ({"workload": {"rows": 0}}, "rows"),
    ({"workload": {"zipf_s": -0.1}}, "zipf_s"),
    ({"workload": {"write_fraction": 1.5}}, "write_fraction"),
    ({"workload": {"nope": 1}}, "unknown workload keys"),
    ({"kind": "open_ladder"}, "rates_rps"),
    ({"stall_period_s": 1.0, "stall_ms": 1500}, "stall_ms"),
    ({"generator_processes": 4}, "generator_processes"),
    ({"label": "confirmatory", "idle_probe_enforce": False}, "idle probe"),
])
def test_invalid_configs_raise(patch, msg):
    raw = dict(BASE)
    raw.update(patch)
    with pytest.raises(ConfigError, match=msg):
        parse_config(raw)


def test_missing_required_key():
    with pytest.raises(ConfigError, match="experiment_id"):
        parse_config({"label": "exploratory"})


def test_config_hash_stable_and_sensitive():
    a, b = parse_config(BASE), parse_config(dict(BASE))
    assert config_hash(a) == config_hash(b)
    assert len(config_hash(a)) == 64
    assert config_hash(a) != config_hash(parse_config({**BASE, "measure_s": 2}))


def test_derive_seed_deterministic_and_distinct():
    assert derive_seed(1, "requests", 0) == derive_seed(1, "requests", 0)
    assert derive_seed(1, "requests", 0) != derive_seed(1, "requests", 1)
    assert 0 <= derive_seed("x") < 2**63


def test_arm_factors_one_at_a_time():
    assert ARMS["A0"].factor == "baseline"
    assert [ARMS[a].factor for a in ("A1", "A2", "A3", "A4")] == [
        "cache", "index", "batching", "bounded_concurrency"]
    for a in ("A1", "A2", "A3", "A4"):  # each arm changes exactly one field from A0
        diff = [k for k, v in vars(ARMS[a]).items() if k != "name" and v != vars(ARMS["A0"])[k]]
        group = {"index": 1, "cache_capacity_fraction": 2, "batch_max": 3, "batch_window_ms": 3,
                 "workers": 4, "queue": 4}
        assert len({group[k] for k in diff}) == 1


def test_load_config_rejects_bad_json(tmp_path):
    p = tmp_path / "c.json"
    p.write_text("{not json")
    with pytest.raises(ConfigError, match="invalid JSON"):
        load_config(str(p))


def test_repository_configs_parse():
    import glob
    import os

    root = os.path.join(os.path.dirname(__file__), "..", "experiments")
    paths = glob.glob(os.path.join(root, "*.json"))
    assert paths
    deferred = {"EXP-002.json": {"blocks", "concurrency", "generator_ceiling_rps"}}
    for p in paths:
        name = os.path.basename(p)
        if name in deferred:  # values left unset on purpose until the quiet-pilot rule (protocol 7.1)
            raw = json.load(open(p))
            assert {k for k, v in raw.items() if v is None} == deferred[name]
            assert raw["label"] == "confirmatory"
            with pytest.raises(ConfigError):
                load_config(p)
            continue
        cfg = load_config(p)
        if cfg.experiment_id.startswith("EXP-"):
            assert cfg.label == "confirmatory"
        else:
            assert cfg.label == "exploratory"
        json.dumps(cfg.to_dict())
