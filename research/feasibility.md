<!-- SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0 -->
# Feasibility audit (M0, 2026-11-24)

All values below were read from the machine with the commands shown; outputs are copied verbatim or trimmed only where marked.

## 1. Hardware

| Item | Command | Output |
|---|---|---|
| CPU | `sysctl -n machdep.cpu.brand_string` | `Apple M1 Pro` |
| Logical cores | `sysctl -n hw.ncpu` | `10` |
| Performance / efficiency cores | `sysctl -n hw.perflevel0.physicalcpu hw.perflevel1.physicalcpu` | `8`, `2` |
| Memory | `sysctl -n hw.memsize` | `17179869184` (16 GiB) |
| OS | `sw_vers` | macOS `15.3.1`, build `24D70` |
| Free disk | `df -h /Users/bechir/research/labs` | `460Gi` size, `311Gi` used, `129Gi` available (the brief's "about 127 GB" is consistent) |
| File descriptors | `ulimit -n` (session shell) | `1048576`; `launchctl limit maxfiles` soft limit `256` (the generator must raise or respect it) |
| Listen backlog | `sysctl kern.ipc.somaxconn` | `128` |
| Ephemeral ports | `sysctl net.inet.ip.portrange.first/last` | `49152` to `65535` |

Consequence for the design: generator and server share one machine with 8 performance and 2 efficiency cores. The macOS scheduler decides core placement; this cannot be pinned and is recorded as a limitation. Keep-alive connections avoid ephemeral-port exhaustion at c <= 64.

## 2. Tools

| Tool | Location | Version (command output) | Use |
|---|---|---|---|
| Python | `/usr/local/bin/python3` | `Python 3.12.1`; `sqlite3.sqlite_version` = `3.43.1` | interpreter for server, generator, analysis |
| uv | `/Users/bechir/research/labs/.tools/py/bin/uv` | `uv 0.9.5 (d5f39331a 2025-10-21)` | lockfile and environment |
| typst (Python package) | `/Users/bechir/research/labs/.tools/py/bin/python` | `typst 0.15.0` (module import; there is no `typst` executable in that folder) | PDF compilation |
| pypdf, pillow | same environment | `pypdf 6.20.0`, `pillow 11.3.0` | PDF inspection, figure checks |
| pandoc | `/Users/bechir/research/labs/.tools/pandoc` | `pandoc 3.6.3` | Markdown to Typst and LaTeX |
| Node | `/Users/bechir/research/helix/.tools/node/bin/node` | `v22.23.3` | demo build at M5 (read-only use of that folder) |
| git | system | `git version 2.42.1` | version control |
| ApacheBench | `/usr/sbin/ab` | `Version 2.3 <$Revision: 1913912 $>` | differential check of the load generator (EXP-001) |
| SQLite CLI | system | `3.43.2 2023-10-10` | inspection only |
| wrk, wrk2, hey, oha, k6, locust | `which` | not found | not used; no installation planned (a C load generator would need a build toolchain decision by the owner) |

No TeX distribution is installed. Decision D-002: PDFs are produced by pandoc to Typst, compiled with the `typst` Python package; `manuscript.tex` is generated from Markdown by pandoc as a source artifact only. A toolchain smoke check is recorded in `progress.md` (exploratory).

## 3. Time budget

Five focused development days (master prompt section 1). Planned machine time for all experiments is under 6 hours (protocol section 13, planning estimate). Day plan in `roadmap.md`.

## 4. Cost

Zero. No paid API, inference, dataset, cloud compute or hosting. All data are synthetic and generated locally from recorded seeds. The only external traffic is literature lookup during M0/M1.

## 5. Sources and licences

- **Data:** no external dataset is required. The workload is synthetic (section 2 of the protocol). Generator version, parameters and seed go to `data/manifest.json`. Synthetic data are the owner's original material under the project licence.
- **Software dependencies:** recorded in `pyproject.toml` and `uv.lock`; each keeps its own licence. SQLite is public domain (https://www.sqlite.org/copyright.html, accessed 2026-11-24). Python's `sqlite3` and `http.server` are part of the Python standard library (PSF licence; not re-verified this session, labelled unverified).
- **Reference tools:** wrk2 is Apache-2.0 (LICENSE file at https://raw.githubusercontent.com/giltene/wrk2/master/LICENSE, accessed 2026-11-24); it is cited for its method, not used or redistributed. HdrHistogram's site states the original work is placed in the public domain under CC0 1.0 (https://hdrhistogram.github.io/HdrHistogram/, accessed 2026-11-24); not a dependency at present.

## 6. Scope and fallback

- **In scope:** one server engine, five arms, closed-loop sweep, open-loop sensitivity, workload sensitivity, static report and explorer of recorded runs.
- **Excluded:** production traffic, other machines, remote targets, multi-process server farms, other databases, TLS, HTTP/2.
- **Fallback if the budget is threatened:** drop EXP-004, then reduce EXP-003 to the top two arms plus A0, then cut the demo to a static page of recorded figures. Scientific reporting, controls and truthfulness are never cut.
- **Fallback if the Python generator saturates before the server** (EXP-001): reduce the maximum concurrency, run the generator with more processes, or ask the owner to approve a free compiled generator; the confirmatory comparison is restricted to non-generator-limited cells, as the protocol states.

## 7. Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Generator and server share the CPU | Measured ceilings partly reflect the generator | EXP-001 ceiling, generator CPU recorded, ab cross-check |
| Workload parameters decide the answer | "Dominant bottleneck" is an artifact of N and skew | EXP-004; claims stated as conditional |
| Closed-loop bias | Latency understated, rankings may shift | EXP-003 open loop with intended-time latency |
| Thermal and background noise | Inflated variance, drift | Idle probe, randomised order, position check, 10 blocks |
| Python GIL | Thread arms limited by interpreter | Recorded as part of the system under test; not generalised |
| SQLite write locking under WAL | Errors in write-heavy cells | 2 % writes, busy timeout recorded, errors counted |
