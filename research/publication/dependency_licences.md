<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Dependency licences (M6, 2026-11-25)

Read from the installed package metadata: Python from `.venv` (`importlib.metadata`, after `uv sync --frozen --all-groups --all-extras`), npm from `demo/node_modules/*/package.json` (after `npm ci --prefer-offline`). Licences as declared by each package; not legal advice. Flag rule: anything that is not MIT, BSD, ISC, Apache-2.0, PSF, MPL-2.0 or similarly permissive.

**Result: no dependency is flagged.** No dependency is bundled into the repository; the demo build (`demo/dist/`, not committed) contains React and React DOM (MIT) only.

## Python, runtime (pyproject `dependencies` and their dependencies)

| Package | Version | Licence |
|---|---|---|
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| psutil | 7.2.2 | BSD-3-Clause |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| referencing | 0.37.0 | MIT |
| rpds-py | 2026.9.1 | MIT |
| attrs | 26.1.0 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| matplotlib | 3.11.2 | Python Software Foundation License (matplotlib licence, PSF-based) |
| contourpy | 1.4.0 | BSD-3-Clause |
| cycler | 0.12.1 | BSD |
| fonttools | 4.68.0 | MIT |
| kiwisolver | 1.5.1 | BSD |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pillow | 13.0.0 | MIT-CMU (HPND-style, permissive) |
| pyparsing | 3.3.3 | MIT |
| python-dateutil | 4.0.0 | BSD-3-Clause |
| tzdata | 2026.6 | Apache-2.0 |

## Python, development group

| Package | Version | Licence |
|---|---|---|
| pytest | 9.2.0 | MIT |
| pluggy | 1.7.0 | MIT |
| iniconfig | 2.3.1 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| hypothesis | 6.170.15 | MPL-2.0 |
| sortedcontainers | 2.4.0 | Apache-2.0 |

The project itself (`scale-single-machine-throughput` 0.1.0) declares no licence field; its licence is the custom `LicenseRef-SCALE-NC-Research-1.0` (`LICENSE`).

## npm (demo), 53 installed packages

Runtime: react 19.3.1 (MIT), react-dom 19.3.1 (MIT), scheduler 0.28.0 (MIT).

Build and test: MIT for all packages except: detect-libc 2.1.2 (Apache-2.0), expect-type 1.4.0 (Apache-2.0), typescript 5.9.3 (Apache-2.0), lightningcss 1.33.0 and lightningcss-darwin-arm64 1.33.0 (MPL-2.0), picocolors 1.1.1 (ISC), siginfo 2.0.0 (ISC), source-map-js 1.2.4 (BSD-3-Clause). The MIT packages are: @jridgewell/sourcemap-codec, @oxc-project/types, @rolldown/binding-darwin-arm64, @rolldown/pluginutils, @standard-schema/spec, @types/chai, @types/deep-eql, @types/estree, @types/react, @types/react-dom, @vitejs/plugin-react, @vitest/expect, @vitest/mocker, @vitest/pretty-format, @vitest/runner, @vitest/snapshot, @vitest/spy, @vitest/utils, assertion-error, chai, convert-source-map, csstype, es-module-lexer, estree-walker, fdir, fsevents, magic-string, nanoid, obug, pathe, picomatch, postcss, rolldown, stackback, std-env, tinybench, tinyexec, tinyglobby, tinyrainbow, vite, vitest, why-is-node-running.

The demo package (`lab-demo`) declares `SEE LICENSE IN ../LICENSE`.

## External tools (used read-only, not dependencies, not distributed)

| Tool | Version | Licence | Note |
|---|---|---|---|
| pandoc | 3.6.3 | GPL-2.0-or-later | Run as a separate program to convert Markdown; not linked or distributed. Its output is not covered by its licence. Noted for information, not flagged. |
| typst (Python package) | 0.15.0 | Apache-2.0 | PDF compilation |
| pypdf | 6.20.0 | BSD-3-Clause | PDF metadata check |
| uv | 0.9.5 | MIT OR Apache-2.0 | Environment and lockfile |
| Node | 22.23.3 | MIT | Demo build |
| ApacheBench | 2.3 | Apache-2.0 | Bundled with macOS; EXP-001 cross-check |
| SQLite | 3.43.1 | Public domain | Via the Python standard library |
