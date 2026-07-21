import { describe, expect, it } from "vitest";

import type { ComunicadoDataResolved } from "./comunicadoTypes";
import {
  extractProjectionFieldValues,
  resolveProjectedField,
  suggestDefaultAggregationForField,
  suggestPreferredProjectionField,
} from "./fieldValueProjection";
import { discoverResolvedFieldOptions } from "./viewProjection";

const oeeSeries: ComunicadoDataResolved = {
  kpi: { value: 80, label: "value" },
  kpiMetrics: [{ field: "value", value: 80, label: "value" }],
  table: {
    columns: [
      { key: "periodo", label: "Período" },
      { key: "value", label: "OEE — série temporal" },
    ],
    rows: [
      { periodo: "01/07/26", value: 70 },
      { periodo: "02/07/26", value: 80 },
      { periodo: "03/07/26", value: 90 },
    ],
  },
};

describe("fieldValueProjection", () => {
  it("série tabular: value usa todas as linhas (não só KPI)", () => {
    expect(extractProjectionFieldValues(oeeSeries, "value")).toEqual([70, 80, 90]);
  });

  it("média da série value", () => {
    const projected = resolveProjectedField(oeeSeries, "value", "avg");
    expect(projected.kind).toBe("scalar");
    expect(projected.scalar).toBe(80);
  });

  it("lista sem agregar", () => {
    const projected = resolveProjectedField(oeeSeries, "value", "list");
    expect(projected.kind).toBe("list");
    expect(projected.values).toEqual([70, 80, 90]);
  });

  it("agregação numérica em Período não inventa número", () => {
    const projected = resolveProjectedField(oeeSeries, "periodo", "avg");
    expect(projected.kind).toBe("empty");
  });

  it("SI campo/valor: value vem do KPI, não da coluna vazia", () => {
    const si: ComunicadoDataResolved = {
      kpi: { value: 1100, label: "value" },
      kpiMetrics: [{ field: "value", value: 1100, label: "value" }],
      table: {
        columns: [
          { key: "campo", label: "Campo" },
          { key: "valor", label: "Valor" },
        ],
        rows: [
          { campo: "name", valor: "PPM" },
          { campo: "value", valor: 1100 },
        ],
      },
    };
    expect(extractProjectionFieldValues(si, "value")).toEqual([1100]);
  });

  it("default prefere value numérico da série, não Período", () => {
    const fields = discoverResolvedFieldOptions(oeeSeries);
    expect(suggestPreferredProjectionField(oeeSeries, fields)).toBe("value");
    expect(suggestDefaultAggregationForField(oeeSeries, "value")).toBe("avg");
  });

  it("não interpreta data dd/mm/aa como número (10.726)", () => {
    const projected = resolveProjectedField(oeeSeries, "periodo", "first");
    expect(projected.kind).toBe("scalar");
    expect(projected.scalar).toBe("01/07/26");
  });
});
