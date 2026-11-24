# SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
"""Freeze guard (G-FREEZE).

A confirmatory config may run only if all of these hold:

1. the status row of ``research/protocol.md`` says FROZEN;
2. ``research/freeze.json`` (the owner-approved freeze record) exists and the
   SHA-256 of ``research/protocol.md`` equals the recorded value;
3. the config's ``protocol_path`` file exists, its SHA-256 equals both the
   config's ``protocol_sha256`` and the value recorded in the freeze record;
4. the SHA-256 of the config file itself is listed in the freeze record's
   ``configs`` for the same experiment id.

An experiment listed under ``deferred`` with status other than ``resolved`` is
refused with the reason (EXP-002 awaits the quiet-machine pilot). A resolution
appends the resolved config's hash to ``configs``; nothing else changes.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

FREEZE_RECORD = os.path.join("research", "freeze.json")
FREEZE_SCHEMA = "scale-freeze-1"


def sha256_file(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_record(root: str) -> dict[str, Any] | None:
    path = os.path.join(root, FREEZE_RECORD)
    try:
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(rec, dict) or rec.get("schema") != FREEZE_SCHEMA:
        return None
    return rec


def protocol_is_marked_frozen(root: str) -> bool:
    try:
        text = open(os.path.join(root, "research", "protocol.md"), encoding="utf-8").read()
    except OSError:
        return False
    rows = [ln for ln in text.splitlines() if ln.startswith("| Status |")]
    return bool(rows) and "FROZEN" in rows[0] and "not frozen" not in rows[0].lower()


def deferred_reason(experiment_id: str, root: str) -> str | None:
    """Reason to refuse if the experiment still has deferred values, else None."""
    rec = load_record(root)
    if rec is None:
        return None
    for d in rec.get("deferred", []):
        if d.get("experiment_id") == experiment_id and d.get("status") != "resolved":
            return (f"its values {', '.join(d.get('values', []))} are to be set by the pre-stated "
                    f"quiet-machine pilot rule ({d.get('rule')}); status: {d.get('status')}")
    return None


def check(cfg: Any, config_path: str | None, root: str) -> tuple[bool, str]:
    """Return (allowed, reason) for a confirmatory config."""
    if not protocol_is_marked_frozen(root):
        return False, "research/protocol.md is not frozen (owner decision, G-FREEZE)"
    rec = load_record(root)
    if rec is None:
        return False, f"freeze record {FREEZE_RECORD} missing or invalid"
    proto = rec.get("protocol", {})
    if sha256_file(os.path.join(root, "research", "protocol.md")) != proto.get("sha256"):
        return False, "research/protocol.md changed since the freeze (hash mismatch)"
    if not cfg.protocol_path or not cfg.protocol_sha256:
        return False, "config lacks protocol_path or protocol_sha256"
    ppath = os.path.join(root, cfg.protocol_path)
    if not os.path.exists(ppath):
        return False, f"{cfg.protocol_path} not found"
    actual = sha256_file(ppath)
    if actual != cfg.protocol_sha256:
        return False, f"protocol hash mismatch: config {cfg.protocol_sha256[:12]}, file {actual[:12]}"
    recorded = {e["path"]: e["sha256"] for e in rec.get("experiment_protocols", [])}
    if recorded.get(cfg.protocol_path) != actual:
        return False, f"{cfg.protocol_path} is not recorded with this hash in the freeze record"
    why = deferred_reason(cfg.experiment_id, root)
    if why is not None:
        return False, why
    if config_path is None:
        return False, "config file path unknown"
    chash = sha256_file(config_path)
    for e in rec.get("configs", []):
        if e.get("experiment_id") == cfg.experiment_id and e.get("sha256") == chash:
            return True, "frozen"
    return False, "config file is not in the freeze record (changed since the freeze, or never frozen)"
