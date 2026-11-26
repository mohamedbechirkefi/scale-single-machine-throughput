// SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
// Hero: the question, a one-sentence answer read from results.json, and the
// request-lane illustration (batching packs reads into one trip). The
// illustration carries no data and shows no number.
import type { Results } from "./results";


export function LaneIllustration() {
  const single = Array.from({ length: 6 }, (_, i) => i);
  return (
    <figure className="lanes" aria-labelledby="lanes-cap">
      <svg viewBox="0 0 540 300" className="lanes-svg" aria-hidden="true" focusable="false">
        {/* dimension line across the top, blueprint style */}
        <line className="dim" x1="20" x2="520" y1="22" y2="22" />
        <path className="dim-arrow" d="M20 22 l10 -5 v10 Z M520 22 l-10 -5 v10 Z" />
        <text className="lane-label" x="270" y="16" textAnchor="middle">one laptop, one server process</text>

        <text className="lane-label" x="20" y="62">one read per request</text>
        <line className="lane" x1="20" x2="520" y1="104" y2="104" />
        <rect className="gen" x="28" y="80" width="72" height="48" />
        <text className="server-label" x="64" y="152" textAnchor="middle">load generator</text>
        <rect className="server" x="236" y="72" width="64" height="64" />
        <text className="server-label" x="268" y="152" textAnchor="middle">server</text>
        {single.map((i) => (
          <rect key={i} className="req single" x={340 + i * 28} y={96} width={16} height={16}
            style={{ animationDelay: `${300 + (5 - i) * 260}ms` }} />
        ))}

        <text className="lane-label" x="20" y="190">reads packed into one batch</text>
        <line className="lane" x1="20" x2="520" y1="232" y2="232" />
        <rect className="gen" x="28" y="208" width="72" height="48" />
        <text className="server-label" x="64" y="280" textAnchor="middle">load generator</text>
        <rect className="server" x="236" y="200" width="64" height="64" />
        <text className="server-label" x="268" y="280" textAnchor="middle">server</text>
        {[0, 1].map((k) => (
          <g key={k} className="container" style={{ animationDelay: `${300 + (1 - k) * 300}ms` }}>
            <rect className="box" x={336 + k * 92} y={216} width={84} height={32} />
            {[0, 1, 2].map((j) => (
              <rect key={j} className="req" x={344 + k * 92 + j * 24} y={224} width={16} height={16} />
            ))}
          </g>
        ))}
      </svg>
      <figcaption id="lanes-cap">
        <span className="illus-label">Illustration, not study data.</span> Read batching sends several reads in one trip;
        the figure shows the mechanism only, with no measured value.
      </figcaption>
    </figure>
  );
}

export function Hero({ r }: { r: Results | null }) {
  const est = r?.experiments.find((e) => e.id === "EXP-002")?.estimates ?? [];
  const a3 = est.find((e) => e.kind === "confirmatory" && e.label.startsWith("R, A3"));
  const a1 = est.find((e) => e.kind === "confirmatory" && e.label.startsWith("R, A1"));
  const a4 = est.find((e) => e.kind === "confirmatory" && e.label.startsWith("R, A4"));
  return (
    <section className="hero" aria-labelledby="h-question">
      <div className="hero-text">
        <h1 id="h-question">Cache, index, batching or admission control: which change moves peak throughput most on one laptop?</h1>
        {a1 && a3 && a4 ? (
          <p className="answer">
            Read batching multiplied peak goodput by <span className="num">{a3.display}</span> against the full-scan
            baseline (Bonferroni 98.75 % interval <span className="num">{a3.interval_display}</span>) and the cache by{" "}
            <span className="num">{a1.display}</span>; bounded concurrency gave <span className="num">{a4.display}</span>,
            no meaningful effect. The index arm hit the measurement ceiling, so which change dominates is unresolved.{" "}
            <span className="badge kind-confirmatory">confirmatory</span>
          </p>
        ) : (
          <p className="answer muted">The answer appears here once the published results have loaded.</p>
        )}
        <p className="byline">Mohamed Bechir Kefi, independent researcher. A study with a protocol frozen before any confirmatory data.</p>
      </div>
      <LaneIllustration />
    </section>
  );
}
