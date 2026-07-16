import { describe, expect, it } from "vitest";

import {
  applyDataTransformSteps,
  applyDataTransformToPayload,
  evaluateSafeArithmeticExpr,
  normalizeDataTransform,
} from "./dataTransform";

describe("dataTransform", () => {
  const table = {
    columns: ["oee", "meta", "branch"],
    rows: [
      { oee: 80, meta: 85, branch: "01" },
      { oee: 90, meta: 85, branch: "02" },
      { oee: null, meta: 85, branch: "03" },
    ],
  };

  it("normaliza steps válidos", () => {
    expect(
      normalizeDataTransform({
        steps: [
          { op: "rename", from: "oee", to: "oee_pct" },
          { op: "bogus" },
          { op: "filter", column: "branch", cmp: "eq", value: "01" },
        ],
      })?.steps,
    ).toEqual([
      { op: "rename", from: "oee", to: "oee_pct" },
      { op: "filter", column: "branch", cmp: "eq", value: "01" },
    ]);
  });

  it("rename + select + filter + addColumn", () => {
    const next = applyDataTransformSteps(table, [
      { op: "rename", from: "oee", to: "oee_pct" },
      { op: "filter", column: "branch", cmp: "neq", value: "03" },
      { op: "addColumn", name: "gap", expr: "meta - oee_pct" },
      { op: "select", columns: ["branch", "gap"] },
    ]);
    expect(next.columns).toEqual(["branch", "gap"]);
    expect(next.rows).toEqual([
      { branch: "01", gap: 5 },
      { branch: "02", gap: -5 },
    ]);
  });

  it("expressão segura rejeita identificadores estranhos", () => {
    expect(evaluateSafeArithmeticExpr("oee + meta", { oee: 1, meta: 2 })).toBe(3);
    expect(evaluateSafeArithmeticExpr("oee + evil()", { oee: 1 })).toBeNull();
    expect(evaluateSafeArithmeticExpr("__proto__", { __proto__: 1 })).toBeNull();
  });

  it("aplica ao payload lista e marca applied", () => {
    const result = applyDataTransformToPayload(
      [
        { a: 1, b: 2 },
        { a: 3, b: 4 },
      ],
      { steps: [{ op: "addColumn", name: "c", expr: "a + b" }] },
    );
    expect(result.applied).toBe(true);
    expect(result.data).toEqual([
      { a: 1, b: 2, c: 3 },
      { a: 3, b: 4, c: 7 },
    ]);
  });
});
