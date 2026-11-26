<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# demo/

Static benchmark report and resource and latency explorer of the recorded EXP-002 runs (M5), built from the shared lab template (TypeScript, React and Vite, pinned versions, `package-lock.json`).

**What it shows.** The published results exactly as the manuscript prints them, each labelled confirmatory, frozen sensitivity, descriptive or exploratory, with its interval and interval type; an effect plot in which the excluded index arm (A2) has its own row; EXP-003 and EXP-004, which did not run, with panels of the same weight; the four owner decisions of 2026-11-26 with each reading the manuscript reports; the design values; the limitations of manuscript section 7; and an explorer of per-level medians and ranges (goodput, p99 latency, server CPU, error rate, server memory).

**What it does not do.** It runs no benchmark, no simulation, no inference and no browser timing; it has no sandbox (decision D-016). It makes no request to any host or local service, uses no font, image or script from a CDN, and collects nothing about visitors. It works offline after the first load.

**Hosting.** Demo URL: <https://scale-single-machine-throughput.kefimohamedbechir.workers.dev>. The built page (`dist/`) is hosted as Cloudflare Workers static assets on the free plan, configured by `wrangler.jsonc` (assets only, no Worker script). It is deployed by the coordinator, not by any script of this repository.

**Data.** `public/data/results.json` is written by `.venv/bin/python -I scripts/export_demo_data.py` (repository root) from committed results only, and is checked by `tests/test_demo_export.py`. `src/results.ts` validates it and fails closed: on any malformed field the page shows no numbers.

**Commands** (Node 22; the development machine uses a shared, read-only Node folder outside this repository):

    npm ci && npm test && npm run build && npm run preview
    node tools/a11y_check.mjs dist --screenshots <dir>    # offline and accessibility check; prints A11Y-CHECK PASS or FAIL

**Design.** On 2026-11-26 the page received its own brand identity, motion and layout at the owner's request: the plan is `DESIGN.md`, and the logo, favicon and Open Graph image are in `public/brand/`, drawn for this repository and covered by its licence. No result, data file, test expectation or label changed.

## Third-party notes

- **Antonio** by Vernon Adams: package `@fontsource-variable/antonio`, version v5.3.0, pinned exactly; only the latin subset of the variable weight axis is bundled. Licence: SIL Open Font License (OFL-1.1).
- **Literata** by TypeTogether: package `@fontsource-variable/literata`, version v5.3.0, pinned exactly; only the latin subset of the variable weight axis (default optical size) is bundled. Licence: SIL Open Font License (OFL-1.1).

Both are self-hosted in the built page; nothing is loaded from another origin. They are the only dependencies added; the other pinned versions are unchanged.
