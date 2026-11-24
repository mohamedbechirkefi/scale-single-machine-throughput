# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Versioned JSON result and manifest schemas; validation at export and import.

A result that fails validation is never written, and a file that fails
validation is never read into a report (fail closed).
"""

from __future__ import annotations

import json
import os
from typing import Any

import jsonschema

RESULT_SCHEMA_VERSION = "1.0.0"
MANIFEST_SCHEMA_VERSION = "1.0.0"


class SchemaError(ValueError):
    pass


_num_or_null = {"type": ["number", "null"]}

LEVEL_SCHEMA = {
    "type": "object",
    "required": ["concurrency", "window_s", "attempts", "validated_ok", "invalid_body",
                 "transport_errors", "status_counts", "goodput_rps", "error_rate",
                 "p50_ms", "p95_ms", "p99_ms", "max_ms", "server_cpu_util",
                 "server_rss_mb", "generator_cpu_util", "generator_limited",
                 "generator_limited_reasons", "connections_finished"],
    "properties": {
        "concurrency": {"type": "integer", "minimum": 1},
        "offered_rate_rps": _num_or_null,
        "window_s": {"type": "number", "exclusiveMinimum": 0},
        "attempts": {"type": "integer", "minimum": 0},
        "validated_ok": {"type": "integer", "minimum": 0},
        "invalid_body": {"type": "integer", "minimum": 0},
        "transport_errors": {"type": "integer", "minimum": 0},
        "status_counts": {"type": "object", "additionalProperties": {"type": "integer", "minimum": 0}},
        "goodput_rps": {"type": "number", "minimum": 0},
        "error_rate": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "p50_ms": _num_or_null, "p95_ms": _num_or_null, "p99_ms": _num_or_null,
        "max_ms": _num_or_null,
        "lag_p99_ms": _num_or_null,
        "server_cpu_util": {"type": "number", "minimum": 0},
        "server_rss_mb": {"type": "number", "minimum": 0},
        "generator_cpu_util": {"type": "number", "minimum": 0},
        "generator_limited": {"type": "boolean"},
        "generator_limited_reasons": {"type": "array", "items": {"type": "string"}},
        "connections_finished": {"type": "integer", "minimum": 0},
        "ab_rps": _num_or_null,
    },
    "additionalProperties": False,
}

RESULT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "SCALE run result",
    "type": "object",
    "required": ["schema_version", "run_id", "experiment_id", "label", "kind", "arm",
                 "factor", "block", "arm_position", "config_hash", "seeds", "endpoint",
                 "levels", "summary", "server_stats", "status", "failure"],
    "properties": {
        "schema_version": {"const": RESULT_SCHEMA_VERSION},
        "run_id": {"type": "string", "pattern": "^[A-Za-z0-9_.-]+$"},
        "experiment_id": {"type": "string", "minLength": 1},
        "label": {"enum": ["exploratory", "confirmatory"]},
        "kind": {"enum": ["closed_sweep", "open_ladder"]},
        "arm": {"enum": ["A0", "A1", "A2", "A3", "A4"]},
        "factor": {"type": "string"},
        "block": {"type": "integer", "minimum": 0},
        "arm_position": {"type": "integer", "minimum": 0},
        "config_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "seeds": {
            "type": "object",
            "required": ["study", "dataset", "requests", "permutation"],
            "properties": {k: {"type": "integer", "minimum": 0}
                           for k in ("study", "dataset", "requests", "permutation")},
        },
        "endpoint": {"enum": ["item", "null"]},
        "levels": {"type": "array", "items": LEVEL_SCHEMA},
        "summary": {
            "type": "object",
            "required": ["peak_goodput_rps", "c_at_peak", "c_sat"],
            "properties": {
                "peak_goodput_rps": _num_or_null,
                "c_at_peak": {"type": ["integer", "null"]},
                "c_sat": {"type": ["integer", "null"]},
                "slo_goodput_rps": _num_or_null,
                "generator_limited_levels": {"type": "array", "items": {"type": "integer"}},
            },
        },
        "server_stats": {"type": "object"},
        "status": {"enum": ["ok", "failed", "excluded"]},
        "failure": {"type": ["string", "null"]},
    },
    "additionalProperties": False,
}

MANIFEST_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "SCALE run manifest",
    "type": "object",
    "required": ["schema_version", "run_id", "label", "config_hash", "config", "seeds",
                 "git", "versions", "platform", "cpu", "started_utc", "finished_utc",
                 "runtime_s", "server_peak_rss_mb", "runner_peak_rss_mb", "dataset_sha256",
                 "idle_probe", "load_average", "command"],
    "properties": {
        "schema_version": {"const": MANIFEST_SCHEMA_VERSION},
        "run_id": {"type": "string"},
        "label": {"enum": ["exploratory", "confirmatory"]},
        "config_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "config": {"type": "object"},
        "seeds": {"type": "object"},
        "git": {"type": "object", "required": ["revision", "dirty"],
                "properties": {"revision": {"type": ["string", "null"]},
                               "dirty": {"type": ["boolean", "null"]}}},
        "versions": {"type": "object"},
        "platform": {"type": "object"},
        "cpu": {"type": "object"},
        "started_utc": {"type": "string"},
        "finished_utc": {"type": "string"},
        "runtime_s": {"type": "number", "minimum": 0},
        "server_peak_rss_mb": _num_or_null,
        "runner_peak_rss_mb": _num_or_null,
        "dataset_sha256": {"type": ["string", "null"]},
        "idle_probe": {"type": "object", "required": ["cpu_pct", "threshold_pct", "passed", "enforced"]},
        "load_average": {"type": "array"},
        "command": {"type": "array", "items": {"type": "string"}},
        "power": {"type": ["string", "null"]},
    },
    "additionalProperties": False,
}


def _validate(obj: Any, schema: dict[str, Any], what: str) -> None:
    try:
        jsonschema.Draft202012Validator(schema).validate(obj)
    except jsonschema.ValidationError as exc:
        path = "/".join(str(p) for p in exc.absolute_path)
        raise SchemaError(f"{what} invalid at '{path}': {exc.message}") from exc


def validate_result(obj: Any) -> None:
    _validate(obj, RESULT_SCHEMA, "result")


def validate_manifest(obj: Any) -> None:
    _validate(obj, MANIFEST_SCHEMA, "manifest")


def _write(path: str, obj: Any) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)


def write_result(path: str, obj: Any) -> None:
    validate_result(obj)
    _write(path, obj)


def write_manifest(path: str, obj: Any) -> None:
    validate_manifest(obj)
    _write(path, obj)


def _read(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise SchemaError(f"{path}: unreadable: {exc}") from exc


def read_result(path: str) -> dict[str, Any]:
    obj = _read(path)
    validate_result(obj)
    return obj


def read_manifest(path: str) -> dict[str, Any]:
    obj = _read(path)
    validate_manifest(obj)
    return obj
