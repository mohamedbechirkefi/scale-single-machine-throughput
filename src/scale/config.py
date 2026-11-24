# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Typed, validated experiment configuration.

Units are explicit in field names: ``_s`` seconds, ``_ms`` milliseconds,
``_bytes`` bytes, ``_rps`` requests per second. Every invalid input raises
``ConfigError`` with a message naming the field.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

CONFIG_VERSION = "1.0"
LABELS = ("exploratory", "confirmatory")
KINDS = ("closed_sweep", "open_ladder")
ENDPOINTS = ("item", "null")


class ConfigError(ValueError):
    """Raised for any invalid configuration value."""


@dataclass(frozen=True)
class ArmSpec:
    """One architecture arm. A0 is the baseline; each other arm changes one factor."""

    name: str
    index: bool = False
    cache_capacity_fraction: float = 0.0
    batch_max: int = 0
    batch_window_ms: float = 0.0
    workers: int = 0
    queue: int = 0

    @property
    def factor(self) -> str:
        if self.index:
            return "index"
        if self.cache_capacity_fraction > 0:
            return "cache"
        if self.batch_max > 0:
            return "batching"
        if self.workers > 0:
            return "bounded_concurrency"
        return "baseline"


# Values from research/protocol.md section 3 (frozen v1.0, owner-approved 2026-11-24).
# A4: W = 8 workers, Q = 16 queue slots (amendment AM-1: W + Q = 24 is below the
# largest concurrency level, so the limiter can reject; draft v0.1 had Q = 64).
ARMS: dict[str, ArmSpec] = {
    "A0": ArmSpec("A0"),
    "A1": ArmSpec("A1", cache_capacity_fraction=0.10),
    "A2": ArmSpec("A2", index=True),
    "A3": ArmSpec("A3", batch_max=32, batch_window_ms=1.0),
    "A4": ArmSpec("A4", workers=8, queue=16),
}


@dataclass(frozen=True)
class Workload:
    rows: int = 200_000
    payload_bytes: int = 256
    zipf_s: float = 0.99
    write_fraction: float = 0.02
    dataset_seed: int = 20261124

    def validate(self) -> None:
        if not isinstance(self.rows, int) or self.rows < 1:
            raise ConfigError("workload.rows must be an integer >= 1")
        if self.rows > 10_000_000:
            raise ConfigError("workload.rows must be <= 10,000,000")
        if not isinstance(self.payload_bytes, int) or not 1 <= self.payload_bytes <= 65_536:
            raise ConfigError("workload.payload_bytes must be an integer in [1, 65536]")
        if not isinstance(self.zipf_s, (int, float)) or not 0.0 <= self.zipf_s <= 5.0:
            raise ConfigError("workload.zipf_s must be a number in [0, 5]")
        if not isinstance(self.write_fraction, (int, float)) or not 0.0 <= self.write_fraction <= 1.0:
            raise ConfigError("workload.write_fraction must be a number in [0, 1]")
        if not isinstance(self.dataset_seed, int) or self.dataset_seed < 0:
            raise ConfigError("workload.dataset_seed must be a non-negative integer")


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    label: str
    kind: str = "closed_sweep"
    endpoint: str = "item"
    arms: tuple[str, ...] = ("A0",)
    concurrency: tuple[int, ...] = (1,)
    rates_rps: tuple[float, ...] = ()
    warmup_s: float = 5.0
    measure_s: float = 15.0
    blocks: int = 1
    study_seed: int = 1
    generator_processes: int = 1
    workload: Workload = field(default_factory=Workload)
    idle_probe_threshold_pct: float = 15.0
    idle_probe_enforce: bool = True
    generator_ceiling_rps: float | None = None
    stall_period_s: float = 0.0
    stall_ms: float = 0.0
    ab_crosscheck: bool = False
    slo_p99_ms: float = 50.0
    slo_max_error_rate: float = 0.01
    protocol_path: str | None = None
    protocol_sha256: str | None = None
    description: str = ""
    config_version: str = CONFIG_VERSION

    def validate(self) -> None:
        if not self.experiment_id or not isinstance(self.experiment_id, str):
            raise ConfigError("experiment_id must be a non-empty string")
        if self.label not in LABELS:
            raise ConfigError(f"label must be one of {LABELS}, got {self.label!r}")
        if self.kind not in KINDS:
            raise ConfigError(f"kind must be one of {KINDS}, got {self.kind!r}")
        if self.endpoint not in ENDPOINTS:
            raise ConfigError(f"endpoint must be one of {ENDPOINTS}, got {self.endpoint!r}")
        if not self.arms:
            raise ConfigError("arms must not be empty")
        for a in self.arms:
            if a not in ARMS:
                raise ConfigError(f"unknown arm {a!r}; known arms: {sorted(ARMS)}")
        if len(set(self.arms)) != len(self.arms):
            raise ConfigError("arms must not repeat")
        if not self.concurrency:
            raise ConfigError("concurrency must not be empty")
        for c in self.concurrency:
            if not isinstance(c, int) or isinstance(c, bool) or not 1 <= c <= 1024:
                raise ConfigError("every concurrency level must be an integer in [1, 1024]")
        if list(self.concurrency) != sorted(set(self.concurrency)):
            raise ConfigError("concurrency levels must be strictly increasing")
        if self.kind == "open_ladder":
            if not self.rates_rps:
                raise ConfigError("rates_rps must not be empty for kind open_ladder")
            if len(self.concurrency) != 1:
                raise ConfigError("open_ladder uses exactly one concurrency (connection pool size)")
        for r in self.rates_rps:
            if not isinstance(r, (int, float)) or r <= 0:
                raise ConfigError("every rate in rates_rps must be > 0")
        if not isinstance(self.warmup_s, (int, float)) or self.warmup_s < 0:
            raise ConfigError("warmup_s must be >= 0")
        if not isinstance(self.measure_s, (int, float)) or self.measure_s <= 0:
            raise ConfigError("measure_s must be > 0")
        if self.measure_s > 600:
            raise ConfigError("measure_s must be <= 600")
        if not isinstance(self.blocks, int) or not 1 <= self.blocks <= 1000:
            raise ConfigError("blocks must be an integer in [1, 1000]")
        if not isinstance(self.study_seed, int) or self.study_seed < 0:
            raise ConfigError("study_seed must be a non-negative integer")
        if not isinstance(self.generator_processes, int) or not 1 <= self.generator_processes <= 64:
            raise ConfigError("generator_processes must be an integer in [1, 64]")
        if min(self.concurrency) < self.generator_processes:
            raise ConfigError("every concurrency level must be >= generator_processes")
        if not 0 <= self.idle_probe_threshold_pct <= 100:
            raise ConfigError("idle_probe_threshold_pct must be in [0, 100]")
        if self.generator_ceiling_rps is not None and self.generator_ceiling_rps <= 0:
            raise ConfigError("generator_ceiling_rps must be > 0 when given")
        if self.stall_period_s < 0 or self.stall_ms < 0:
            raise ConfigError("stall_period_s and stall_ms must be >= 0")
        if self.stall_ms > 0 and self.stall_ms >= self.stall_period_s * 1000:
            raise ConfigError("stall_ms must be shorter than stall_period_s")
        if self.slo_p99_ms <= 0 or not 0 <= self.slo_max_error_rate <= 1:
            raise ConfigError("slo_p99_ms must be > 0 and slo_max_error_rate in [0, 1]")
        if self.label == "confirmatory" and not self.idle_probe_enforce:
            raise ConfigError("a confirmatory config must enforce the idle probe")
        if self.config_version != CONFIG_VERSION:
            raise ConfigError(f"config_version must be {CONFIG_VERSION!r}")
        self.workload.validate()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["arms"] = list(self.arms)
        d["concurrency"] = list(self.concurrency)
        d["rates_rps"] = list(self.rates_rps)
        return d


_FIELDS = set(ExperimentConfig.__dataclass_fields__)
_WORKLOAD_FIELDS = set(Workload.__dataclass_fields__)


def parse_config(raw: dict[str, Any]) -> ExperimentConfig:
    """Build and validate a config from a JSON-like dict. Unknown keys are errors."""
    if not isinstance(raw, dict):
        raise ConfigError("config must be a JSON object")
    raw = {k: v for k, v in raw.items() if not k.startswith("_comment")}
    unknown = set(raw) - _FIELDS
    if unknown:
        raise ConfigError(f"unknown config keys: {sorted(unknown)}")
    for req in ("experiment_id", "label"):
        if req not in raw:
            raise ConfigError(f"missing required key {req!r}")
    wl_raw = raw.get("workload", {})
    if not isinstance(wl_raw, dict):
        raise ConfigError("workload must be an object")
    wl_unknown = set(wl_raw) - _WORKLOAD_FIELDS
    if wl_unknown:
        raise ConfigError(f"unknown workload keys: {sorted(wl_unknown)}")
    kwargs = dict(raw)
    kwargs["workload"] = Workload(**wl_raw)
    for key in ("arms", "concurrency", "rates_rps"):
        if key in kwargs:
            if not isinstance(kwargs[key], (list, tuple)):
                raise ConfigError(f"{key} must be a list")
            kwargs[key] = tuple(kwargs[key])
    cfg = ExperimentConfig(**kwargs)
    cfg.validate()
    return cfg


def load_config(path: str) -> ExperimentConfig:
    with open(path, encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"{path}: invalid JSON: {exc}") from exc
    return parse_config(raw)


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def config_hash(cfg: ExperimentConfig) -> str:
    """SHA-256 of the canonical JSON form of the config."""
    return hashlib.sha256(canonical_json(cfg.to_dict()).encode("ascii")).hexdigest()


def derive_seed(*parts: Any) -> int:
    """Deterministic 63-bit seed from any JSON-serialisable parts."""
    digest = hashlib.sha256(canonical_json(list(parts)).encode("ascii")).digest()
    return int.from_bytes(digest[:8], "big") >> 1
