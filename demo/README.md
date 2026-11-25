<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# demo/

Static benchmark report and resource and latency explorer of the recorded EXP-002 runs (M5), built from the shared lab template (TypeScript, React and Vite, pinned versions, `package-lock.json`).

**What it shows.** The published results exactly as the manuscript prints them, each labelled confirmatory, frozen sensitivity, descriptive or exploratory, with its interval and interval type; an effect plot in which the excluded index arm (A2) has its own row; EXP-003 and EXP-004, which did not run, with panels of the same weight; the four pending owner decisions with each reading the manuscript reports (none chosen); the design values; the limitations of manuscript section 7; and an explorer of per-level medians and ranges (goodput, p99 latency, server CPU, error rate, server memory).

**What it does not do.** It runs no benchmark, no simulation, no inference and no browser timing; it has no sandbox (decision D-016). It makes no request to any host or local service, uses no font, image or script from a CDN, and collects nothing about visitors. It works offline after the first load. Demo URL: [placeholder: demo URL, not published; publication requires the owner's approval].

**Data.** `public/data/results.json` is written by `.venv/bin/python -I scripts/export_demo_data.py` (repository root) from committed results only, and is checked by `tests/test_demo_export.py`. `src/results.ts` validates it and fails closed: on any malformed field the page shows no numbers.

**Commands** (Node from `/Users/bechir/research/helix/.tools/node/bin`):

    npm ci && npm test && npm run build && npm run preview
    node tools/a11y_check.mjs dist --screenshots <dir>    # offline and accessibility check; prints A11Y-CHECK PASS or FAIL
