// SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
// Hand-written SVG charts: the confirmatory effect plot and the resource and
// latency explorer of recorded EXP-002 runs. Nothing here measures or simulates
// anything in the browser; every mark is a value from results.json.
import { useEffect, useId, useRef, useState, type RefObject } from "react";
import { fixed, type Estimate, type ExcludedArm, type Explorer as ExplorerData, type Level, type LevelField } from "./results";

const SERIES = ["s0", "s1", "s2", "s3", "s4"];
const DASH = ["", "6 3", "2 3", "8 3 2 3", "1 2"];

function useWidth<T extends HTMLElement>(fallback = 640): [RefObject<T | null>, number] {
  const ref = useRef<T | null>(null);
  const [w, setW] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      const cw = Math.floor(entries[0].contentRect.width);
      if (cw > 0) setW(cw);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

function Marker({ i, x, y, open }: { i: number; x: number; y: number; open: boolean }) {
  const cls = `mark ${SERIES[i % 5]}${open ? " open" : ""}`;
  const s = 4.5;
  switch (i % 5) {
    case 1:
      return <rect className={cls} x={x - s} y={y - s} width={2 * s} height={2 * s} />;
    case 2:
      return <polygon className={cls} points={`${x},${y - s - 1} ${x + s + 1},${y + s} ${x - s - 1},${y + s}`} />;
    case 3:
      return <polygon className={cls} points={`${x},${y - s - 1} ${x + s + 1},${y} ${x},${y + s + 1} ${x - s - 1},${y}`} />;
    case 4:
      return <rect className={cls} x={x - s + 1} y={y - s + 1} width={2 * s - 2} height={2 * s - 2} transform={`rotate(45 ${x} ${y})`} />;
    default:
      return <circle className={cls} cx={x} cy={y} r={s} />;
  }
}

/* ---------------- Confirmatory effect plot ---------------- */

const LOG_MIN = Math.log(0.8);
const LOG_MAX = Math.log(12);
const pctN = (v: number) => ((Math.log(v) - LOG_MIN) / (LOG_MAX - LOG_MIN)) * 100;
const pct = (v: number) => `${pctN(v).toFixed(2)}%`;

export function EffectPlot({ rows, excluded }: { rows: { name: string; e: Estimate }[]; excluded: ExcludedArm[] }) {
  const ticks = [1, 2, 5, 10];
  return (
    <figure className="effect" aria-labelledby="effect-cap">
      <figcaption id="effect-cap">
        <strong>Figure: confirmatory effects (EXP-002, measured).</strong> Ratio R of each arm's peak goodput to the
        baseline's, geometric mean over 10 blocks, with the Bonferroni 98.75 % interval, on a log scale. The shaded band is
        the practical-equivalence band [0.95, 1.05]. An arm without a confirmatory estimate is shown on its own row with the
        same weight.
      </figcaption>
      <ul className="effect-rows">
        {rows.map((r) => (
          <li key={r.name} className="effect-row">
            <span className="effect-name">{r.name}</span>
            <svg className="effect-strip" width="100%" height="30" role="img"
              aria-label={`${r.name}: R ${r.e.display}, 98.75 % interval ${r.e.interval_display}`}>
              <rect className="band" x={pct(0.95)} y="2" width={`${(pctN(1.05) - pctN(0.95)).toFixed(2)}%`} height="26" />
              <line className="ref" x1={pct(1)} x2={pct(1)} y1="0" y2="30" />
              <line className="ci" x1={pct(r.e.ci_low!)} x2={pct(r.e.ci_high!)} y1="15" y2="15" />
              <line className="ci" x1={pct(r.e.ci_low!)} x2={pct(r.e.ci_low!)} y1="9" y2="21" />
              <line className="ci" x1={pct(r.e.ci_high!)} x2={pct(r.e.ci_high!)} y1="9" y2="21" />
              <circle className="pt" cx={pct(r.e.estimate)} cy="15" r="5" />
            </svg>
            <span className="effect-val">
              {r.e.display} <span className="meta">[{r.e.interval_display}]</span>
            </span>
          </li>
        ))}
        {excluded.map((x) => (
          <li key={x.arm} className="effect-row excluded">
            <span className="effect-name">{x.name}</span>
            <svg className="effect-strip" width="100%" height="30" role="img" aria-label={`${x.name}: no confirmatory estimate. ${x.verdict}`}>
              <rect className="excl" x="0" y="4" width="100%" height="22" />
              <text className="excl-text" x="50%" y="19" textAnchor="middle">no confirmatory estimate</text>
            </svg>
            <span className="effect-val">{x.verdict}</span>
          </li>
        ))}
        <li className="effect-row axis" aria-hidden="true">
          <span className="effect-name" />
          <svg className="effect-strip" width="100%" height="22">
            {ticks.map((t) => (
              <g key={t}>
                <line className="tick" x1={pct(t)} x2={pct(t)} y1="0" y2="6" />
                <text className="tick-label" x={pct(t)} y="18" textAnchor="middle">{t}</text>
              </g>
            ))}
          </svg>
          <span className="effect-val meta">R (log scale)</span>
        </li>
      </ul>
    </figure>
  );
}

/* ---------------- Resource and latency explorer ---------------- */

type Metric = {
  key: string;
  label: string;
  unit: string;
  med: LevelField;
  lo?: LevelField;
  hi?: LevelField;
  log: boolean;
  digits: number;
  scale?: number;
};

const METRICS: Metric[] = [
  { key: "goodput", label: "Goodput (validated responses per second)", unit: "rps", med: "goodput_median", lo: "goodput_min", hi: "goodput_max", log: true, digits: 1 },
  { key: "p99", label: "p99 latency, closed loop", unit: "ms", med: "p99_median_ms", lo: "p99_min_ms", hi: "p99_max_ms", log: true, digits: 2 },
  { key: "cpu", label: "Server CPU (cores busy, median)", unit: "cores", med: "server_cpu_median", log: false, digits: 2 },
  { key: "err", label: "Error rate (share of attempts, median)", unit: "%", med: "error_rate_median", hi: "error_rate_max", log: false, digits: 1, scale: 100 },
  { key: "mem", label: "Server memory (resident set)", unit: "MB", med: "server_rss_mb_median", lo: "server_rss_mb_min", hi: "server_rss_mb_max", log: true, digits: 1 },
];

function niceLogTicks(lo: number, hi: number): number[] {
  const out: number[] = [];
  for (let e = Math.floor(Math.log10(lo)); e <= Math.ceil(Math.log10(hi)); e++) {
    for (const m of [1, 3]) {
      const v = m * 10 ** e;
      if (v >= lo * 0.999 && v <= hi * 1.001) out.push(v);
    }
  }
  return out;
}

function niceLinTicks(hi: number): number[] {
  const step = hi <= 1.2 ? 0.25 : hi <= 5 ? 1 : hi <= 12 ? 2 : hi <= 120 ? 20 : 10 ** Math.floor(Math.log10(hi));
  const out: number[] = [];
  for (let v = 0; v <= hi * 1.0001; v += step) out.push(Number(v.toFixed(6)));
  return out;
}

function tickText(v: number): string {
  if (v >= 1000) return `${v / 1000}k`;
  return String(v);
}

export function Explorer({ data }: { data: ExplorerData }) {
  const [metricKey, setMetricKey] = useState("goodput");
  const [shown, setShown] = useState<Set<string>>(() => new Set(data.arms.map((a) => a.arm)));
  const [cSel, setCSel] = useState<number>(4);
  const [wrapRef, width] = useWidth<HTMLDivElement>();
  const ids = useId();
  const m = METRICS.find((x) => x.key === metricKey)!;
  const sc = m.scale ?? 1;
  const val = (l: Level, f: LevelField) => l[f] * sc;

  const arms = data.arms.map((a, i) => ({ ...a, i })).filter((a) => shown.has(a.arm));
  const all: number[] = [];
  for (const a of arms) for (const l of a.levels) {
    all.push(val(l, m.med));
    if (m.lo) all.push(val(l, m.lo));
    if (m.hi) all.push(val(l, m.hi));
  }
  if (m.key === "goodput") all.push(data.generator_ceiling_rps);
  const positive = all.filter((v) => v > 0);
  let yLo = m.log ? Math.min(...(positive.length ? positive : [1])) / 1.3 : 0;
  let yHi = Math.max(...(all.length ? all : [1])) * (m.log ? 1.3 : 1.08);
  if (!m.log && yHi <= 0) yHi = 1;
  if (m.log && yLo <= 0) yLo = 0.01;

  const H = width < 480 ? 300 : 360;
  const pad = { l: width < 480 ? 44 : 60, r: 12, t: 14, b: 40 };
  const pw = Math.max(50, width - pad.l - pad.r);
  const ph = H - pad.t - pad.b;
  const cs = data.concurrency;
  const xOf = (c: number) => pad.l + (Math.log2(c) - Math.log2(cs[0])) / (Math.log2(cs[cs.length - 1]) - Math.log2(cs[0])) * pw;
  const yOf = (v: number) => {
    if (m.log) {
      const t = (Math.log(Math.max(v, yLo)) - Math.log(yLo)) / (Math.log(yHi) - Math.log(yLo));
      return pad.t + ph - t * ph;
    }
    return pad.t + ph - (v / yHi) * ph;
  };
  const yTicks = m.log ? niceLogTicks(yLo, yHi) : niceLinTicks(yHi);
  const toggle = (arm: string) =>
    setShown((s) => {
      const n = new Set(s);
      if (n.has(arm)) n.delete(arm);
      else n.add(arm);
      return n;
    });

  const fmt = (v: number) => fixed(v, m.digits);
  const range = (l: Level) =>
    m.lo && m.hi ? `${fmt(val(l, m.lo))} to ${fmt(val(l, m.hi))}` : m.hi ? `max ${fmt(val(l, m.hi))}` : "";

  return (
    <div className="explorer">
      <p className="label-measured">
        <span className="badge kind-measured">measured</span> Recorded EXP-002 runs. Medians over the {data.n_runs_per_cell} accepted
        runs per cell; bands and ranges are the minimum to maximum over those runs, not confidence intervals. These are
        recorded per-level values, not confirmatory estimates. Source: <code>{data.source}</code>.
      </p>
      <div className="controls" role="group" aria-label="Explorer controls">
        <label>
          Metric{" "}
          <select id={`${ids}-metric`} value={metricKey} onChange={(e) => setMetricKey(e.target.value)}>
            {METRICS.map((x) => (
              <option key={x.key} value={x.key}>{x.label}</option>
            ))}
          </select>
        </label>
        <label>
          Concurrency level{" "}
          <select id="explorer-c" value={cSel} onChange={(e) => setCSel(Number(e.target.value))}>
            {cs.map((c) => (
              <option key={c} value={c}>c = {c}</option>
            ))}
          </select>
        </label>
        <fieldset className="arm-toggles">
          <legend>Arms shown</legend>
          {data.arms.map((a, i) => (
            <label key={a.arm} className="arm-toggle">
              <input type="checkbox" id={`arm-${a.arm}`} checked={shown.has(a.arm)} onChange={() => toggle(a.arm)} />
              <svg width="26" height="14" aria-hidden="true">
                <line className={`line ${SERIES[i]}`} x1="1" x2="25" y1="7" y2="7" strokeDasharray={DASH[i]} />
                <Marker i={i} x={13} y={7} open={false} />
              </svg>
              {a.name}
            </label>
          ))}
        </fieldset>
      </div>

      <div ref={wrapRef} className="chart-wrap">
        <svg width={width} height={H} role="img" aria-labelledby={`${ids}-cap`} className="chart">
          {yTicks.map((t) => (
            <g key={t}>
              <line className="grid" x1={pad.l} x2={pad.l + pw} y1={yOf(t)} y2={yOf(t)} />
              <text className="tick-label" x={pad.l - 6} y={yOf(t) + 4} textAnchor="end">{tickText(t)}</text>
            </g>
          ))}
          {cs.map((c) => (
            <text key={c} className="tick-label" x={xOf(c)} y={pad.t + ph + 16} textAnchor="middle">
              {width < 480 && [2, 8, 32, 128].includes(c) ? "" : c}
            </text>
          ))}
          <text className="axis-label" x={pad.l + pw / 2} y={H - 4} textAnchor="middle">Concurrent connections c (log scale)</text>
          <line className="sel" x1={xOf(cSel)} x2={xOf(cSel)} y1={pad.t} y2={pad.t + ph} />
          {m.key === "goodput" && (
            <>
              <line className="limit" x1={pad.l} x2={pad.l + pw} y1={yOf(data.generator_ceiling_rps)} y2={yOf(data.generator_ceiling_rps)} />
              <text className="limit-label" x={pad.l + pw - 4} y={yOf(data.generator_ceiling_rps) - 5} textAnchor="end">
                generator ceiling C_gen {fixed(data.generator_ceiling_rps, 1)}
              </text>
              <line className="limit thr" x1={pad.l} x2={pad.l + pw} y1={yOf(data.generator_limited_threshold_rps)} y2={yOf(data.generator_limited_threshold_rps)} />
              <text className="limit-label" x={pad.l + pw - 4} y={yOf(data.generator_limited_threshold_rps) + 14} textAnchor="end">
                50 % threshold {data.generator_limited_threshold_display}
              </text>
            </>
          )}
          {arms.map((a) => {
            const pts = a.levels.map((l) => [xOf(l.c), yOf(val(l, m.med))] as const);
            const band =
              m.lo && m.hi
                ? a.levels.map((l) => `${xOf(l.c)},${yOf(val(l, m.hi!))}`).join(" ") + " " +
                  [...a.levels].reverse().map((l) => `${xOf(l.c)},${yOf(val(l, m.lo!))}`).join(" ")
                : null;
            return (
              <g key={a.arm}>
                {band && <polygon className={`bandfill ${SERIES[a.i]}`} points={band} />}
                <polyline className={`line ${SERIES[a.i]}`} points={pts.map((p) => p.join(",")).join(" ")} strokeDasharray={DASH[a.i]} />
                {a.levels.map((l, j) => (
                  <Marker key={l.c} i={a.i} x={pts[j][0]} y={pts[j][1]} open={l.generator_limited_runs > 0} />
                ))}
              </g>
            );
          })}
          <rect className="frame" x={pad.l} y={pad.t} width={pw} height={ph} />
        </svg>
        <p id={`${ids}-cap`} className="note">
          {m.label} ({m.unit}) against concurrency, {m.log ? "log" : "linear"} vertical scale. Open markers: the cell was
          flagged generator-limited in at least one run (A2 at c = 1, 2 and 4).
          {m.key === "goodput" && " Horizontal lines: the measured generator ceiling and the frozen 50 % threshold."}
        </p>
      </div>

      <div className="readout" aria-live="polite" id="explorer-readout">
        <h4>Recorded values at c = {cSel}: {m.label}</h4>
        <div className="table-scroll" role="region" aria-label={`Values at c = ${cSel}`} tabIndex={0} id="t-readout">
          <table>
            <thead>
              <tr>
                <th scope="col">Arm</th>
                <th scope="col">Median ({m.unit})</th>
                <th scope="col">{m.lo ? "Range over runs" : m.hi ? "Maximum over runs" : "Range"}</th>
                <th scope="col">Flagged generator-limited</th>
              </tr>
            </thead>
            <tbody>
              {data.arms.map((a) => {
                const l = a.levels.find((x) => x.c === cSel)!;
                return (
                  <tr key={a.arm}>
                    <th scope="row">{a.name}</th>
                    <td>{fmt(val(l, m.med))}</td>
                    <td>{range(l) || "not recorded"}</td>
                    <td>{l.generator_limited_runs} of {data.n_runs_per_cell}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ---------------- Key result: the load gauge ---------------- */

/** Reveal once when scrolled into view; immediate under reduced motion or without IntersectionObserver. */
export function useReveal<T extends Element>() {
  const ref = useRef<T>(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduce = typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce || typeof IntersectionObserver === "undefined") {
      setShown(true);
      return;
    }
    const io = new IntersectionObserver((es) => {
      if (es.some((e) => e.isIntersecting)) {
        setShown(true);
        io.disconnect();
      }
    }, { threshold: 0.2 });
    io.observe(el);
    // Safety net: never leave data hidden if the observer does not report.
    const t = setTimeout(() => setShown(true), 2500);
    return () => {
      io.disconnect();
      clearTimeout(t);
    };
  }, []);
  return [ref, shown] as const;
}

const G_MIN = Math.log(0.8);
const G_MAX = Math.log(12);
/** Dial angle in degrees (SVG, 180 = left, 270 = up, 360 = right) for a ratio on the log scale. */
const gAngle = (v: number) => 180 + ((Math.log(v) - G_MIN) / (G_MAX - G_MIN)) * 180;

/** Confirmatory ratios R as needles on a log-scale load gauge; excluded arms listed with the same weight. */
export function Gauge({ rows, excluded }: { rows: { name: string; e: Estimate }[]; excluded: ExcludedArm[] }) {
  const [ref, shown] = useReveal<HTMLElement>();
  const W = 560, CX = 280, CY = 292, R = 236;
  const p = (deg: number, r: number) => [CX + r * Math.cos((deg * Math.PI) / 180), CY + r * Math.sin((deg * Math.PI) / 180)];
  const arc = (a1: number, a2: number, r: number) => {
    const [x1, y1] = p(a1, r), [x2, y2] = p(a2, r);
    return `M${x1.toFixed(2)} ${y1.toFixed(2)} A${r} ${r} 0 ${a2 - a1 > 180 ? 1 : 0} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
  };
  const minor = [0.8, 0.9, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12];
  const major = [1, 2, 5, 10];
  const desc =
    "Load gauge of the confirmatory effects, EXP-002: ratio R of each arm's peak goodput to the baseline's on a log scale. " +
    rows.map((r) => `${r.name}: R ${r.e.display}, 98.75 % interval ${r.e.interval_display}`).join("; ") +
    ". " + excluded.map((x) => `${x.name}: no confirmatory estimate (${x.verdict})`).join("; ") + ".";
  const ordered = [...rows].sort((a, b) => a.e.estimate - b.e.estimate);
  useEffect(() => {
    if (!shown || !ref.current) return;
    if (typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    ref.current.querySelectorAll<SVGGElement>(".needle").forEach((el, i) => {
      const to = el.style.transform;
      const from = el.dataset.from;
      if (!from || typeof el.animate !== "function") return;
      el.animate([{ transform: from }, { transform: to }],
        { duration: 1100, delay: i * 80, easing: "cubic-bezier(0.23, 1, 0.32, 1)", fill: "backwards" });
    });
  }, [shown, ref]);
  return (
    <figure className="gauge" ref={ref} data-shown={shown ? "true" : "false"} aria-labelledby="gauge-cap">
      <div className="gauge-body">
        <svg viewBox={`0 0 ${W} 370`} role="img" aria-label={desc} className="gauge-svg">
          <path className="dial-face" d={`${arc(180, 360, R)} L${CX} ${CY} Z`} />
          <path className="dial-rim" d={arc(180, 360, R)} />
          <path className="dial-band" d={arc(gAngle(0.95), gAngle(1.05), R - 14)} />
          {minor.map((v) => {
            const [x1, y1] = p(gAngle(v), R), [x2, y2] = p(gAngle(v), R - (major.includes(v) ? 22 : 11));
            return <line key={v} className={major.includes(v) ? "tick-major" : "tick-minor"} x1={x1} y1={y1} x2={x2} y2={y2} />;
          })}
          {major.map((v) => {
            const [x, y] = p(gAngle(v), R - 40);
            return <text key={v} className="dial-num" x={x} y={y + 6} textAnchor="middle">{v}</text>;
          })}
          {ordered.map((r, i) => {
            const a = gAngle(r.e.estimate);
            const from = gAngle(1);
            const [lx, ly] = p(a, R + 16);
            return (
              <g key={r.name}>
                <path className={`ci-arc n${i}`} d={arc(gAngle(r.e.ci_low!), gAngle(r.e.ci_high!), R - 6)} />
                <g className={`needle n${i}`}
                  data-from={`translate(${CX}px, ${CY}px) rotate(${from}deg)`}
                  style={{ transform: shown ? `translate(${CX}px, ${CY}px) rotate(${a}deg)` : `translate(${CX}px, ${CY}px) rotate(${from}deg)` }}>
                  <path d={`M-14 -5 L${R - 30} -1.5 L${R - 30} 1.5 L-14 5 Z`} />
                </g>
                <text className="needle-label" x={lx} y={ly + 6}
                  textAnchor={a > 300 ? "start" : a < 240 ? "end" : "middle"}>{r.name.split(" ")[0]}</text>
              </g>
            );
          })}
          <rect className="hub" x={CX - 16} y={CY - 16} width={32} height={32} />
          <text className="dial-caption" x={CX} y={CY + 42} textAnchor="middle">R, peak goodput against the baseline</text>
          <text className="dial-caption small" x={CX} y={CY + 70} textAnchor="middle">log scale, 1 = no change</text>
        </svg>
        <ul className="gauge-legend">
          {[...rows].sort((a, b) => b.e.estimate - a.e.estimate).map((r) => (
            <li key={r.name}>
              <span className="gl-name">{r.name}</span>
              <span className="gl-val num">{r.e.display}</span>
              <span className="meta">98.75 % interval {r.e.interval_display}</span>
            </li>
          ))}
          {excluded.map((x) => (
            <li key={x.arm} className="gl-excluded">
              <span className="gl-name">{x.name}</span>
              <span className="gl-val">no needle</span>
              <span className="meta">{x.verdict}</span>
            </li>
          ))}
        </ul>
      </div>
      <figcaption id="gauge-cap">
        <span className="badge kind-confirmatory">confirmatory</span> EXP-002, ten paired blocks. Each needle is the
        geometric mean ratio of the arm's peak goodput to the baseline's; the thick arc under it is its Bonferroni
        98.75 % interval, and the shaded strip near 1 is the practical-equivalence band [0.95, 1.05]. The index arm has no
        needle because its peak reached the measurement ceiling; it is listed with the same weight.
      </figcaption>
    </figure>
  );
}
