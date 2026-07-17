import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { describe, expect, it } from "vitest";

import {
  applyDataTransformSteps,
  applyDataTransformToPayload,
  coercePayloadToTable,
  dataTransformStepLabel,
  evaluateSafeArithmeticExpr,
  evaluateSafeColumnExpr,
  isDataTransformV1,
  normalizeDataTransform,
} from "./dataTransform";

type SharedOperationFixture = {
  name: string;
  input: { columns: string[]; rows: Array<Record<string, unknown>> };
  legacySteps: Parameters<typeof applyDataTransformSteps>[1];
  siblingTables?: NonNullable<Parameters<typeof applyDataTransformSteps>[2]>["siblingTables"];
  expected: { columns: string[]; rows: Array<Record<string, unknown>> };
  expectedTs?: { columns: string[]; rows: Array<Record<string, unknown>> };
  knownDrift?: string;
};

function loadSharedFixtures(): {
  operations: SharedOperationFixture[];
  previewByStep: {
    input: SharedOperationFixture["input"];
    legacySteps: SharedOperationFixture["legacySteps"];
    expectedStages: SharedOperationFixture["expected"][];
  };
} {
  const fixturePath = resolve(
    process.cwd(),
    "../../fixtures/tv-dashboard/m-query/v1-operations.json",
  );
  return JSON.parse(readFileSync(fixturePath, "utf8")) as ReturnType<typeof loadSharedFixtures>;
}

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
    const normalized = normalizeDataTransform({
      steps: [
        { op: "rename", from: "oee", to: "oee_pct" },
        { op: "bogus" },
        { op: "filter", column: "branch", cmp: "eq", value: "01" },
      ],
    });
    expect(isDataTransformV1(normalized) ? normalized.steps : undefined).toEqual([
      { op: "rename", from: "oee", to: "oee_pct" },
      { op: "filter", column: "branch", cmp: "eq", value: "01" },
    ]);
  });

  it("normaliza DTO v2 sem interpretar ou executar M", () => {
    const normalized = normalizeDataTransform({
      version: 2,
      language: "m-delpi-v1",
      script: "let\r\n    X = Fonte\r\nin\r\n    X\u0000",
      ast: { forbidden: true },
      rows: [{ secret: true }],
    });

    expect(normalized).toEqual({
      version: 2,
      language: "m-delpi-v1",
      script: "let\n    X = Fonte\nin\n    X",
    });
    expect(isDataTransformV1(normalized)).toBe(false);
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

  it("DSL if/concat/coalesce", () => {
    expect(evaluateSafeColumnExpr('if(oee >= meta, "ok", "nok")', { oee: 90, meta: 85 })).toBe(
      "ok",
    );
    expect(evaluateSafeColumnExpr('concat("F", branch)', { branch: "01" })).toBe("F01");
    expect(evaluateSafeColumnExpr("coalesce(gap, 0)", { gap: null })).toBe(0);
    expect(evaluateSafeColumnExpr("abs(meta - oee)", { meta: 85, oee: 90 })).toBe(5);
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

  it("groupBy + sort + replace", () => {
    const next = applyDataTransformSteps(
      {
        columns: ["branch", "oee"],
        rows: [
          { branch: "01", oee: 80 },
          { branch: "01", oee: 90 },
          { branch: "02", oee: 70 },
        ],
      },
      [
        { op: "replace", column: "branch", find: "0", replaceWith: "F" },
        {
          op: "groupBy",
          keys: ["branch"],
          aggregations: [{ column: "oee", fn: "sum", as: "oee_sum" }],
        },
        { op: "sort", column: "oee_sum", direction: "desc" },
      ],
    );
    expect(next.rows).toEqual([
      { branch: "F1", oee_sum: 170 },
      { branch: "F2", oee_sum: 70 },
    ]);
  });

  it("pivot e unpivot", () => {
    const pivoted = applyDataTransformSteps(
      {
        columns: ["periodo", "filial", "oee"],
        rows: [
          { periodo: "2024-01", filial: "01", oee: 80 },
          { periodo: "2024-01", filial: "02", oee: 90 },
        ],
      },
      [{ op: "pivot", column: "filial", valueColumn: "oee", aggregation: "sum" }],
    );
    expect(pivoted.columns).toEqual(["periodo", "_01", "_02"]);
    expect(pivoted.rows).toEqual([{ periodo: "2024-01", _01: 80, _02: 90 }]);

    const back = applyDataTransformSteps(pivoted, [
      { op: "unpivot", columns: ["_01", "_02"], nameColumn: "filial", valueColumn: "oee" },
    ]);
    expect(back.rows).toEqual([
      { periodo: "2024-01", filial: "_01", oee: 80 },
      { periodo: "2024-01", filial: "_02", oee: 90 },
    ]);
  });

  it("merge com siblingTables", () => {
    const left = {
      columns: ["code", "qty"],
      rows: [
        { code: "A", qty: 1 },
        { code: "B", qty: 2 },
      ],
    };
    const right = {
      columns: ["sku", "name"],
      rows: [
        { sku: "A", name: "Alpha" },
        { sku: "B", name: "Beta" },
      ],
    };
    const next = applyDataTransformSteps(
      left,
      [{ op: "merge", sourceId: "other", leftKey: "code", rightKey: "sku", join: "left" }],
      { siblingTables: { other: right } },
    );
    expect(next.rows).toEqual([
      { code: "A", qty: 1, name: "Alpha" },
      { code: "B", qty: 2, name: "Beta" },
    ]);
  });

  it("keepRows / fillDown / changeType", () => {
    const next = applyDataTransformSteps(
      {
        columns: ["g", "v"],
        rows: [
          { g: "x", v: "1" },
          { g: null, v: "2" },
          { g: "y", v: "3" },
        ],
      },
      [
        { op: "fillDown", column: "g" },
        { op: "changeType", column: "v", to: "number" },
        { op: "keepRows", count: 2, from: "top" },
      ],
    );
    expect(next.rows).toEqual([
      { g: "x", v: 1 },
      { g: "x", v: 2 },
    ]);
  });

  it("rótulos de etapa no estilo Power Query", () => {
    expect(dataTransformStepLabel({ op: "firstRowAsHeader" })).toBe("Cabeçalhos promovidos");
    expect(dataTransformStepLabel({ op: "addColumn", name: "gap", expr: "a-b" })).toBe(
      "Coluna personalizada «gap»",
    );
    expect(dataTransformStepLabel({ op: "merge", sourceId: "x", leftKey: "a", rightKey: "b", join: "left" })).toBe(
      "Consultas mescladas",
    );
  });

  it("coercePayloadToTable aceita envelope e objeto escalar textual", () => {
    expect(
      coercePayloadToTable({
        success: true,
        data: [{ status: "A" }, { status: "B" }],
      })?.rows,
    ).toHaveLength(2);
    expect(coercePayloadToTable({ status: "ATIVO", owner: "Ops" })?.rows).toEqual([
      { campo: "status", valor: "ATIVO" },
      { campo: "owner", valor: "Ops" },
    ]);
  });

  it("mantém paridade TS com as fixtures v1 e congela drifts conhecidos", () => {
    const fixture = loadSharedFixtures();
    expect(fixture.operations.map((item) => item.name)).toHaveLength(15);
    expect(fixture.operations.filter((item) => item.knownDrift).map((item) => item.name)).toEqual([
      "firstRowAsHeader",
    ]);

    for (const item of fixture.operations) {
      const actual = applyDataTransformSteps(item.input, item.legacySteps, {
        siblingTables: item.siblingTables,
      });
      expect(actual, item.name).toEqual(item.expectedTs ?? item.expected);
    }
  });

  it("mantém preview por etapa usando prefixos do mesmo plano legado", () => {
    const preview = loadSharedFixtures().previewByStep;

    preview.expectedStages.forEach((expected, index) => {
      expect(applyDataTransformSteps(preview.input, preview.legacySteps.slice(0, index + 1))).toEqual(
        expected,
      );
    });
  });
});
