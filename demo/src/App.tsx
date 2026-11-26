// SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
import { useEffect, useState } from "react";
import { EffectPlot, Explorer, Gauge } from "./charts";
import { Hero } from "./Hero";
import { fmtEstimate, fmtInterval, loadResults, ResultsError, type Estimate, type Results } from "./results";

type State = { kind: "loading" } | { kind: "error"; message: string } | { kind: "ready"; results: Results };

export function App() {
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    loadResults()
      .then((results) => setState({ kind: "ready", results }))
      .catch((e: unknown) =>
        setState({ kind: "error", message: e instanceof ResultsError ? e.message : "results could not be loaded" }),
      );
  }, []);

  const r = state.kind === "ready" ? state.results : null;
  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header className="bar">
        <div className="bar-in">
          <a className="brand" href="#main" aria-label="SCALE, back to the top">
            <img src="brand/scale-lockup.svg" alt="" width={112} height={32} />
          </a>
          <nav aria-label="Sections">
            <a href="#overview">Result</a>
            <a href="#results">Experiments</a>
            <a href="#explorer">Explorer</a>
            <a href="#exploratory">Exploratory</a>
            <a href="#assumptions">Assumptions</a>
            <a href="#method">Method</a>
            <a href="#reproduce">Reproduce</a>
          </nav>
        </div>
      </header>
      <main id="main" className="wrap">
        <Hero r={r} />
        {state.kind === "loading" && <p role="status">Loading the published results.</p>}
        {state.kind === "error" && (
          <div role="alert" className="panel error">
            <h2>Results unavailable</h2>
            <p>The published results file failed validation, so no numbers are shown.</p>
            <p><code>{state.message}</code></p>
          </div>
        )}
        {state.kind === "ready" && <Published r={state.results} />}
        <section id="reproduce" aria-labelledby="h-reproduce">
          <h2 id="h-reproduce">Reproduce</h2>
          <p>
            Every number on this page is read from <code>public/data/results.json</code>, which a script writes from the
            committed results; nothing is typed in by hand. From the repository root:
          </p>
          <pre className="cmd"><code>{`.venv/bin/python -I scripts/export_demo_data.py
cd demo && npm ci && npm test && npm run build`}</code></pre>
          <p>
            Re-running the benchmark needs the same quiet, single machine; the frozen protocol is{" "}
            <code>research/protocol.md</code> and the experiment reports are under <code>research/experiments/</code>.
          </p>
        </section>
      </main>
      <footer className="site">
        <div className="wrap">
          <div className="title-block" role="group" aria-label="Drawing title block">
            <div className="tb-mark"><img src="brand/scale-mark.svg" alt="" width={56} height={56} /></div>
            <div className="tb-cell tb-title"><span className="tb-k">Study</span><span className="tb-v">SCALE: single-machine server throughput</span></div>
            <div className="tb-cell"><span className="tb-k">Author</span><span className="tb-v">Mohamed Bechir Kefi, independent researcher</span></div>
            <div className="tb-cell"><span className="tb-k">Status</span><span className="tb-v">Preprint draft, not peer-reviewed</span></div>
            <div className="tb-cell"><span className="tb-k">Data revision</span><span className="tb-v"><code>{r ? r.code_revision.slice(0, 7) : "not loaded"}</code></span></div>
            <div className="tb-cell"><span className="tb-k">Licence</span><span className="tb-v">SCALE Source-Available Non-Commercial Research License v1.0</span></div>
          </div>
          <ul className="foot-links">
            <li><a href="https://github.com/mohamedbechirkefi/scale-single-machine-throughput">Source repository on GitHub</a></li>
            <li><a href="https://github.com/mohamedbechirkefi/scale-single-machine-throughput/blob/main/research/paper/manuscript.md">Manuscript (preprint draft, not peer-reviewed)</a></li>
            <li><a href="https://labs.kefimohamedbechir.workers.dev">All lab studies</a></li>
          </ul>
          <p>
            Runs offline after the first load. No data about visitors is collected or sent anywhere. This page runs no
            benchmark, no inference and no timing of its own, and contacts no local or remote service.
          </p>
          <p>
            AI assistance: an AI system (Claude, Anthropic) was used as a research and development assistant for code,
            protocol drafting, analysis and text; it is not an author.
          </p>
          <p>
            Type: Barlow Condensed (Jeremy Tribby) and Source Serif 4 (Frank Grie&szlig;hammer, Adobe), both under the SIL
            Open Font License 1.1, served from this site.
          </p>
        </div>
      </footer>
    </>
  );
}

function KindBadge({ kind }: { kind: string }) {
  const cls = kind.replace(/\s+/g, "-");
  return <span className={`badge kind-${cls}`}>{kind}</span>;
}

function EstimateTable({ caption, rows }: { caption: string; rows: Estimate[] }) {
  const rid = "t-" + caption.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  const has95 = rows.some((r) => r.interval95_display !== null);
  return (
    <div className="table-scroll" role="region" aria-label={caption} tabIndex={0} id={rid}>
      <table className="stack">
        <thead>
          <tr>
            <th scope="col">Quantity</th>
            <th scope="col">Label</th>
            <th scope="col">Estimate</th>
            <th scope="col">Interval</th>
            {has95 && <th scope="col">95 % interval</th>}
            <th scope="col">Interval type</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((x) => (
            <tr key={x.label}>
              <th scope="row">{x.label}</th>
              <td data-label="Label"><KindBadge kind={x.kind} /></td>
              <td className="num" data-label="Estimate">{fmtEstimate(x)}{x.unit && x.unit !== "ratio" ? ` ${x.unit}` : ""}</td>
              <td className="num" data-label="Interval">{fmtInterval(x)}</td>
              {has95 && <td className="num" data-label="95 % interval">{x.interval95_display ?? ""}</td>}
              <td className="meta" data-label="Interval type">{x.interval_kind ?? "none reported"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Published({ r }: { r: Results }) {
  const exp002 = r.experiments.find((e) => e.id === "EXP-002");
  const effectRows = (exp002?.estimates ?? [])
    .filter((e) => e.kind === "confirmatory" && e.ci_low !== null)
    .map((e) => ({ name: e.label.replace(/^R, /, "").replace(/ \/ A0.*$/, ""), e }));

  return (
    <>
      <section id="overview" aria-labelledby="h-overview">
        <h2 id="h-overview">What the gauge reads</h2>
        <Gauge rows={effectRows} excluded={r.excluded_arms} />
        <p className="status-label">{r.status_label}</p>
        <p>{r.question}</p>
        <p>
          <strong>In short.</strong> Against a full-scan baseline, read batching raised peak goodput about ninefold and the
          cache about 2.3-fold; bounded concurrency left the peak unchanged. The index arm reached the measurement ceiling
          and has no confirmatory estimate, so which factor dominates is unresolved.
        </p>
        <div className="panel pending" role="region" aria-labelledby="h-pending">
          <h3 id="h-pending">Owner decisions</h3>
          <p className="note">
            The owner answered these on 2026-11-26. The page shows each reading the manuscript reports and labels the one
            the owner chose; the alternatives stay exploratory.
          </p>
          {r.pending_owner_decisions.map((d) => (
            <div key={d.id} className="decision">
              <h4>
                <span className="badge kind-pending">owner decision</span> {d.id}: {d.title}
              </h4>
              {d.readings.map((rd) => (
                <div key={rd.label} className="reading">
                  <p><strong>{rd.label}.</strong> {rd.text}</p>
                  {rd.estimates.length > 0 && <EstimateTable caption={`${d.id}: ${rd.label}`} rows={rd.estimates} />}
                </div>
              ))}
            </div>
          ))}
        </div>
      </section>

      <section id="results" aria-labelledby="h-results">
        <h2 id="h-results">Published results</h2>
        <p className="note">
          Measured results from the committed outputs at revision <code>{r.code_revision}</code>, printed exactly as the
          manuscript prints them. Every row carries its label: <strong>confirmatory</strong> (frozen analysis),{" "}
          <strong>frozen sensitivity</strong>, <strong>descriptive</strong> (ranges over runs) or{" "}
          <strong>exploratory</strong>. Experiments that did not run have the same panel as those that did.
        </p>
        <EffectPlot rows={effectRows} excluded={r.excluded_arms} />
        {r.experiments.map((e) => (
          <article key={e.id} className="panel" aria-labelledby={`h-${e.id}`}>
            <h3 id={`h-${e.id}`}>
              {e.id}: {e.title}
            </h3>
            <p>
              <span className="badge">{e.status}</span> <strong>Verdict under the frozen rule:</strong> {e.verdict}
            </p>
            {e.estimates.length > 0 ? (
              <EstimateTable caption={`${e.id} estimates`} rows={e.estimates} />
            ) : (
              <p className="none">No estimate: this experiment did not run.</p>
            )}
            {e.id === "EXP-002" &&
              r.excluded_arms.map((x) => (
                <p key={x.arm} className="panel excluded-note">
                  <strong>{x.name}: {x.verdict}.</strong> {x.reason}
                </p>
              ))}
            {e.notes.map((n, i) => (
              <p key={i} className="note">{n}</p>
            ))}
            <p className="meta">
              Report: <code>{e.report_path}</code>
              {e.claim_ids.length > 0 && <>; claims: {e.claim_ids.join(", ")}</>}
            </p>
          </article>
        ))}
      </section>

      <section id="explorer" aria-labelledby="h-explorer">
        <h2 id="h-explorer">Resource and latency explorer (recorded runs)</h2>
        <p>
          Choose a metric, a concurrency level and the arms to compare. Every value is a recorded EXP-002 measurement;
          nothing is computed from your settings.
        </p>
        <Explorer data={r.explorer} />
      </section>

      <section id="exploratory" aria-labelledby="h-exploratory">
        <h2 id="h-exploratory">Exploratory re-analysis (not confirmatory)</h2>
        <div className="panel exploratory-panel">
          <p>
            <KindBadge kind="exploratory" /> <strong>{r.exploratory.title}.</strong> {r.exploratory.note}
          </p>
          {r.exploratory.groups.map((g) => (
            <div key={g.title}>
              <h3 className="h-small">{g.title}</h3>
              <EstimateTable caption={g.title} rows={g.estimates} />
            </div>
          ))}
          <p className="meta">
            Report: <code>{r.exploratory.report_path}</code>; claims: {r.exploratory.claim_ids.join(", ")}
          </p>
        </div>
      </section>

      <section id="assumptions" aria-labelledby="h-assumptions">
        <h2 id="h-assumptions">Assumptions and design values</h2>
        <p className="note">
          <span className="badge kind-design">design value</span> These are settings fixed by the frozen protocol, not
          results.
        </p>
        <dl className="assumptions">
          {r.assumptions.map((a) => (
            <div key={a.name}>
              <dt>{a.name}</dt>
              <dd>
                {a.value} <span className="meta">({a.source})</span>
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section id="method" aria-labelledby="h-method">
        <h2 id="h-method">Method and limitations</h2>
        <p>
          One standard-library Python HTTP server backed by SQLite ran in five arms on one laptop: a full-scan,
          thread-per-connection baseline and four one-factor changes. A separate load generator on the same machine swept
          closed-loop concurrency; ten paired blocks were run under a protocol the owner froze before any confirmatory
          data. The primary metric is peak goodput; effects are within-block ratios to the baseline with percentile
          bootstrap intervals. The full method is in <code>research/paper/manuscript.md</code>.
        </p>
        <h3 className="h-small">Limitations (manuscript section 7)</h3>
        <ol>
          {r.limitations.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ol>
        <details>
          <summary>Source files and hashes</summary>
          <ul className="meta">
            {r.sources.map((s) => (
              <li key={s.path}>
                <code>{s.path}</code> <code>{s.sha256.slice(0, 12)}</code>
              </li>
            ))}
          </ul>
        </details>
      </section>
    </>
  );
}
