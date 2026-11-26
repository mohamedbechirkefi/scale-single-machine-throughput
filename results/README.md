<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# results/

Machine-readable experiment outputs.

- `results/exploratory/`: runs made while the protocol is unfrozen. **Exploratory, never findings.** Each directory holds `config.json`, `batch.json`, `runs/<run_id>.json` (result schema 1.0.0), `runs/<run_id>.manifest.json` (manifest schema 1.0.0), and, after `scale report`, `report.md`, `summary.json` and `figures/`.
- `results/confirmatory/`: created only after an owner-recorded freeze. Empty.
- `results/raw/`: raw outputs. The folder is listed in `.gitignore`, but the M3 outputs (EXP-001, the quiet pilot, EXP-002) were added explicitly and are tracked; they stay tracked (owner, 2026-11-26, decision sheet; D-017).

Per-request latencies are not stored; each level stores counts, goodput, percentiles and resource use.
