import { describe, expect, it } from "vitest";

import { applyDataParamRawUpdates, parseDataParamRaw } from "./applyDataParamUpdates";
import { buildExpressionParamValue } from "./paramExpressions";

const EXPR = buildExpressionParamValue({
  kind: "call",
  value: "Date.AddMonths",
  children: [
    { kind: "identifier", value: "today" },
    { kind: "literal", value: -12 },
  ],
});

describe("applyDataParamRawUpdates", () => {
  it("aplica dateRangePreset e limpa competence no mesmo patch", () => {
    const next = applyDataParamRawUpdates(
      { dateRangePreset: "this_month", competence: "2026-06", branch: "01" },
      { dateRangePreset: "this_year", competence: "" },
      {
        competence: { type: "string" },
        branch: { type: "string" },
      },
    );
    expect(next).toEqual({
      dateRangePreset: "this_year",
      branch: "01",
    });
    expect(next).not.toHaveProperty("competence");
  });

  it("parseia inteiros do schema", () => {
    expect(parseDataParamRaw("periodDays", "15", { periodDays: { type: "integer" } })).toBe(15);
    expect(parseDataParamRaw("excludeWeekends", "true", {})).toBe(true);
    expect(parseDataParamRaw("excludeWeekends", "", {})).toBeUndefined();
  });

  it("rejeita data com ano absurdo (ex.: 0026)", () => {
    expect(
      parseDataParamRaw("start_date", "0026-07-01", {
        start_date: { type: "string", format: "date" },
        end_date: { type: "string", format: "date" },
      }),
    ).toBeUndefined();
    expect(
      parseDataParamRaw("start_date", "2026-07-01", {
        start_date: { type: "string", format: "date" },
        end_date: { type: "string", format: "date" },
      }),
    ).toBe("2026-07-01");
  });

  it("preserva ExpressionSpec intacto no mapa de params", () => {
    const next = applyDataParamRawUpdates(
      { branch: "01" },
      { start_date: EXPR },
      undefined,
    );
    expect(next.start_date).toEqual(EXPR);
    expect(next.branch).toBe("01");
  });

  it("ExpressionSpec existente não é restringido pelo schema parse", () => {
    const next = applyDataParamRawUpdates(
      { start_date: EXPR },
      { end_date: "2026-09-29" },
      { end_date: { type: "string", format: "date" } },
    );
    expect(next.start_date).toEqual(EXPR);
    expect(next.end_date).toBe("2026-09-29");
  });

  it("string vazia remove a chave (inclui ExpressionSpec)", () => {
    const next = applyDataParamRawUpdates(
      { start_date: EXPR, branch: "01" },
      { start_date: "" },
      undefined,
    );
    expect(next).not.toHaveProperty("start_date");
    expect(next.branch).toBe("01");
  });

  it("entries undefined/null do mapa atual são descartadas", () => {
    const next = applyDataParamRawUpdates(
      { a: undefined, b: null, c: "x" },
      {},
      undefined,
    );
    expect(next).toEqual({ c: "x" });
  });
});
