// SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
// Published results: loaded from public/data/results.json, which
// scripts/export_demo_data.py writes from committed results only.
// Validation fails closed: any missing or malformed field means no numbers are shown.

export const SCHEMA = "lab-demo-results";
export const SCHEMA_MAJOR = 1;

export const KINDS = ["confirmatory", "frozen sensitivity", "descriptive", "exploratory"] as const;
export type Kind = (typeof KINDS)[number];

export interface Estimate {
  label: string;
  kind: Kind;
  estimate: number;
  ci_low: number | null;
  ci_high: number | null;
  ci_level: number | null;
  unit: string;
  /** Exact text the manuscript prints for the estimate and interval; shown verbatim when present. */
  display: string | null;
  interval_display: string | null;
  /** What the interval is: a bootstrap interval or a range over repeats. Present exactly when an interval is. */
  interval_kind: string | null;
  /** The unadjusted 95 % interval, where the manuscript prints one beside the 98.75 % interval. */
  interval95_display: string | null;
}

export interface Experiment {
  id: string;
  title: string;
  status: string;
  verdict: string;
  estimates: Estimate[];
  claim_ids: string[];
  report_path: string;
  notes: string[];
}

export interface Assumption {
  name: string;
  value: string;
  source: string;
}

export interface Source {
  path: string;
  sha256: string;
}

export interface Reading {
  label: string;
  text: string;
  estimates: Estimate[];
}

export interface PendingDecision {
  id: string;
  title: string;
  readings: Reading[];
}

export interface ExcludedArm {
  arm: string;
  name: string;
  verdict: string;
  reason: string;
}

export interface ExploratoryGroup {
  title: string;
  estimates: Estimate[];
}

export interface Exploratory {
  id: string;
  title: string;
  label: "exploratory";
  note: string;
  claim_ids: string[];
  report_path: string;
  groups: ExploratoryGroup[];
}

export const LEVEL_FIELDS = [
  "goodput_median", "goodput_min", "goodput_max",
  "p99_median_ms", "p99_min_ms", "p99_max_ms",
  "server_cpu_median", "error_rate_median", "error_rate_max",
  "server_rss_mb_median", "server_rss_mb_min", "server_rss_mb_max",
  "generator_limited_runs",
] as const;
export type LevelField = (typeof LEVEL_FIELDS)[number];
export type Level = { c: number } & Record<LevelField, number>;

export interface ExplorerArm {
  arm: string;
  name: string;
  levels: Level[];
}

export interface Explorer {
  label: string;
  source: string;
  n_runs_per_cell: number;
  concurrency: number[];
  generator_ceiling_rps: number;
  generator_limited_threshold_rps: number;
  generator_limited_threshold_display: string;
  arms: ExplorerArm[];
}

export interface Results {
  schema: string;
  schema_version: string;
  project: string;
  question: string;
  status_label: string;
  code_revision: string;
  sources: Source[];
  experiments: Experiment[];
  assumptions: Assumption[];
  limitations: string[];
  pending_owner_decisions: PendingDecision[];
  excluded_arms: ExcludedArm[];
  exploratory: Exploratory;
  explorer: Explorer;
}

export class ResultsError extends Error {}

type Obj = Record<string, unknown>;

function obj(v: unknown, where: string): Obj {
  if (typeof v !== "object" || v === null || Array.isArray(v)) {
    throw new ResultsError(`${where}: expected an object`);
  }
  return v as Obj;
}

function str(o: Obj, k: string, where: string): string {
  const v = o[k];
  if (typeof v !== "string" || v.length === 0) {
    throw new ResultsError(`${where}.${k}: expected a non-empty string`);
  }
  return v;
}

function optStr(o: Obj, k: string, where: string): string | null {
  const v = o[k];
  if (v === null || v === undefined) return null;
  if (typeof v !== "string" || v.length === 0) throw new ResultsError(`${where}.${k}: expected a string or null`);
  return v;
}

function num(o: Obj, k: string, where: string, nullable = false): number | null {
  const v = o[k];
  if (nullable && v === null) return null;
  if (typeof v !== "number" || !Number.isFinite(v)) {
    throw new ResultsError(`${where}.${k}: expected a finite number`);
  }
  return v;
}

function arr(o: Obj, k: string, where: string): unknown[] {
  const v = o[k];
  if (!Array.isArray(v)) throw new ResultsError(`${where}.${k}: expected an array`);
  return v;
}

function strArr(o: Obj, k: string, where: string): string[] {
  return arr(o, k, where).map((v, i) => {
    if (typeof v !== "string") throw new ResultsError(`${where}.${k}[${i}]: expected a string`);
    return v;
  });
}

function estimate(v: unknown, where: string): Estimate {
  const o = obj(v, where);
  const kind = o.kind;
  if (typeof kind !== "string" || !(KINDS as readonly string[]).includes(kind)) {
    throw new ResultsError(`${where}.kind: expected one of ${KINDS.join(", ")}`);
  }
  const e: Estimate = {
    label: str(o, "label", where),
    kind: kind as Kind,
    estimate: num(o, "estimate", where) as number,
    ci_low: num(o, "ci_low", where, true),
    ci_high: num(o, "ci_high", where, true),
    ci_level: num(o, "ci_level", where, true),
    unit: typeof o.unit === "string" ? o.unit : "",
    display: optStr(o, "display", where),
    interval_display: optStr(o, "interval_display", where),
    interval_kind: optStr(o, "interval_kind", where),
    interval95_display: optStr(o, "interval95_display", where),
  };
  if ((e.ci_low === null) !== (e.ci_high === null)) {
    throw new ResultsError(`${where}: interval must have both bounds or neither`);
  }
  if (e.ci_low !== null && e.ci_high !== null && e.ci_low > e.ci_high) {
    throw new ResultsError(`${where}: ci_low exceeds ci_high`);
  }
  const hasInterval = e.ci_low !== null;
  if (hasInterval !== (e.interval_kind !== null) || hasInterval !== (e.interval_display !== null)) {
    throw new ResultsError(`${where}: an interval needs its kind and its display text, and only an interval has them`);
  }
  if (e.display === null) throw new ResultsError(`${where}.display: required (the manuscript's exact text)`);
  return e;
}

function estimates(o: Obj, k: string, where: string): Estimate[] {
  return arr(o, k, where).map((x, j) => estimate(x, `${where}.${k}[${j}]`));
}

function explorer(v: unknown): Explorer {
  const w = "explorer";
  const o = obj(v, w);
  const concurrency = arr(o, "concurrency", w).map((c, i) => {
    if (typeof c !== "number" || !Number.isInteger(c) || c < 1) throw new ResultsError(`${w}.concurrency[${i}]: expected a positive integer`);
    return c;
  });
  if (concurrency.length < 2) throw new ResultsError(`${w}.concurrency: too few levels`);
  const arms = arr(o, "arms", w).map((a, i) => {
    const aw = `${w}.arms[${i}]`;
    const ao = obj(a, aw);
    const levels = arr(ao, "levels", aw).map((l, j) => {
      const lw = `${aw}.levels[${j}]`;
      const lo = obj(l, lw);
      const c = num(lo, "c", lw) as number;
      if (c !== concurrency[j]) throw new ResultsError(`${lw}.c: does not match explorer.concurrency`);
      const level = { c } as Level;
      for (const f of LEVEL_FIELDS) {
        const x = num(lo, f, lw) as number;
        if (x < 0) throw new ResultsError(`${lw}.${f}: negative`);
        level[f] = x;
      }
      for (const [lo_, md, hi] of [
        ["goodput_min", "goodput_median", "goodput_max"],
        ["p99_min_ms", "p99_median_ms", "p99_max_ms"],
        ["server_rss_mb_min", "server_rss_mb_median", "server_rss_mb_max"],
      ] as const) {
        if (!(level[lo_] <= level[md] && level[md] <= level[hi])) throw new ResultsError(`${lw}: ${md} outside its range`);
      }
      if (level.error_rate_max > 1 || level.error_rate_median > level.error_rate_max) {
        throw new ResultsError(`${lw}: error rate out of range`);
      }
      return level;
    });
    if (levels.length !== concurrency.length) throw new ResultsError(`${aw}.levels: one entry per concurrency level expected`);
    return { arm: str(ao, "arm", aw), name: str(ao, "name", aw), levels };
  });
  if (arms.length === 0) throw new ResultsError(`${w}.arms: empty`);
  const ceiling = num(o, "generator_ceiling_rps", w) as number;
  const threshold = num(o, "generator_limited_threshold_rps", w) as number;
  if (!(threshold > 0 && threshold < ceiling)) throw new ResultsError(`${w}: threshold must lie below the ceiling`);
  return {
    label: str(o, "label", w),
    source: str(o, "source", w),
    n_runs_per_cell: num(o, "n_runs_per_cell", w) as number,
    concurrency,
    generator_ceiling_rps: ceiling,
    generator_limited_threshold_rps: threshold,
    generator_limited_threshold_display: str(o, "generator_limited_threshold_display", w),
    arms,
  };
}

export function validateResults(raw: unknown): Results {
  const o = obj(raw, "results");
  if (o.schema !== SCHEMA) throw new ResultsError(`results.schema: expected "${SCHEMA}"`);
  const version = str(o, "schema_version", "results");
  if (Number(version.split(".")[0]) !== SCHEMA_MAJOR) {
    throw new ResultsError(`results.schema_version: unsupported major version ${version}`);
  }
  const experiments = arr(o, "experiments", "results").map((v, i) => {
    const w = `experiments[${i}]`;
    const e = obj(v, w);
    return {
      id: str(e, "id", w),
      title: str(e, "title", w),
      status: str(e, "status", w),
      verdict: str(e, "verdict", w),
      estimates: estimates(e, "estimates", w),
      claim_ids: strArr(e, "claim_ids", w),
      report_path: str(e, "report_path", w),
      notes: strArr(e, "notes", w),
    };
  });
  if (experiments.length === 0) throw new ResultsError("results.experiments: empty");

  const pending = arr(o, "pending_owner_decisions", "results").map((v, i) => {
    const w = `pending_owner_decisions[${i}]`;
    const p = obj(v, w);
    const readings = arr(p, "readings", w).map((r, j) => {
      const rw = `${w}.readings[${j}]`;
      const ro = obj(r, rw);
      return { label: str(ro, "label", rw), text: str(ro, "text", rw), estimates: estimates(ro, "estimates", rw) };
    });
    if (readings.length === 0) throw new ResultsError(`${w}.readings: empty`);
    return { id: str(p, "id", w), title: str(p, "title", w), readings };
  });
  if (pending.length === 0) throw new ResultsError("results.pending_owner_decisions: empty");

  const excluded = arr(o, "excluded_arms", "results").map((v, i) => {
    const w = `excluded_arms[${i}]`;
    const x = obj(v, w);
    return { arm: str(x, "arm", w), name: str(x, "name", w), verdict: str(x, "verdict", w), reason: str(x, "reason", w) };
  });

  const xo = obj(o.exploratory, "exploratory");
  if (xo.label !== "exploratory") throw new ResultsError(`exploratory.label: expected "exploratory"`);
  const groups = arr(xo, "groups", "exploratory").map((g, i) => {
    const w = `exploratory.groups[${i}]`;
    const go = obj(g, w);
    const es = estimates(go, "estimates", w);
    if (es.some((e) => e.kind !== "exploratory")) throw new ResultsError(`${w}: every estimate must be labelled exploratory`);
    if (es.length === 0) throw new ResultsError(`${w}.estimates: empty`);
    return { title: str(go, "title", w), estimates: es };
  });
  const exploratory: Exploratory = {
    id: str(xo, "id", "exploratory"),
    title: str(xo, "title", "exploratory"),
    label: "exploratory",
    note: str(xo, "note", "exploratory"),
    claim_ids: strArr(xo, "claim_ids", "exploratory"),
    report_path: str(xo, "report_path", "exploratory"),
    groups,
  };

  return {
    schema: SCHEMA,
    schema_version: version,
    project: str(o, "project", "results"),
    question: str(o, "question", "results"),
    status_label: str(o, "status_label", "results"),
    code_revision: str(o, "code_revision", "results"),
    sources: arr(o, "sources", "results").map((v, i) => {
      const s = obj(v, `sources[${i}]`);
      const sha = str(s, "sha256", `sources[${i}]`);
      if (!/^[0-9a-f]{64}$/.test(sha)) throw new ResultsError(`sources[${i}].sha256: not a sha256`);
      return { path: str(s, "path", `sources[${i}]`), sha256: sha };
    }),
    experiments,
    assumptions: arr(o, "assumptions", "results").map((v, i) => {
      const a = obj(v, `assumptions[${i}]`);
      return {
        name: str(a, "name", `assumptions[${i}]`),
        value: str(a, "value", `assumptions[${i}]`),
        source: str(a, "source", `assumptions[${i}]`),
      };
    }),
    limitations: strArr(o, "limitations", "results"),
    pending_owner_decisions: pending,
    excluded_arms: excluded,
    exploratory,
    explorer: explorer(o.explorer),
  };
}

export async function loadResults(url = "./data/results.json"): Promise<Results> {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new ResultsError(`could not load ${url} (HTTP ${res.status})`);
  let raw: unknown;
  try {
    raw = await res.json();
  } catch {
    throw new ResultsError(`${url} is not valid JSON`);
  }
  return validateResults(raw);
}

/** Fixed-point text for recorded per-level values (the explorer); no invented precision. */
export function fixed(x: number, digits: number): string {
  return x.toFixed(digits);
}

export function fmtEstimate(e: Estimate): string {
  return e.display ?? String(e.estimate);
}

export function fmtInterval(e: Estimate): string {
  return e.interval_display ?? "no interval";
}
