// SPDX-License-Identifier: LicenseRef-SCALE-NC-Research-1.0
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { ResultsError, validateResults } from "./results";

const good = () => JSON.parse(readFileSync("public/data/results.json", "utf8"));

describe("validateResults", () => {
  it("accepts the exported results file", () => {
    const r = validateResults(good());
    expect(r.experiments.map((e) => e.id)).toEqual(["EXP-001", "EXP-002", "EXP-003", "EXP-004"]);
    expect(r.pending_owner_decisions.length).toBe(4);
    expect(r.explorer.arms.length).toBe(5);
  });
  it("rejects a wrong schema name", () => {
    expect(() => validateResults({ ...good(), schema: "other" })).toThrow(ResultsError);
  });
  it("rejects an unsupported major version", () => {
    expect(() => validateResults({ ...good(), schema_version: "2.0.0" })).toThrow(ResultsError);
  });
  it("rejects a missing estimate", () => {
    const r = good();
    delete r.experiments[0].estimates[0].estimate;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a non-finite number", () => {
    const r = good();
    r.experiments[0].estimates[0].estimate = "NaN";
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a half-open interval", () => {
    const r = good();
    r.experiments[0].estimates[0].ci_high = null;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a malformed source hash", () => {
    expect(() => validateResults({ ...good(), sources: [{ path: "a", sha256: "zz" }] })).toThrow(ResultsError);
  });
  it("rejects an estimate without a kind label", () => {
    const r = good();
    delete r.experiments[1].estimates[0].kind;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects an interval without its kind", () => {
    const r = good();
    r.experiments[1].estimates[0].interval_kind = null;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a non-exploratory estimate in the exploratory block", () => {
    const r = good();
    r.exploratory.groups[0].estimates[0].kind = "confirmatory";
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a missing pending-decision list", () => {
    const r = good();
    r.pending_owner_decisions = [];
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects an explorer median outside its range", () => {
    const r = good();
    r.explorer.arms[0].levels[0].goodput_median = r.explorer.arms[0].levels[0].goodput_max + 1;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects an explorer level that does not match the concurrency list", () => {
    const r = good();
    r.explorer.arms[0].levels[1].c = 3;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
  it("rejects a missing explorer", () => {
    const r = good();
    delete r.explorer;
    expect(() => validateResults(r)).toThrow(ResultsError);
  });
});
