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

  it("indicadores aninhados: Score usa IDD do KPI, não média das notas", () => {
    const departmentIndicators: ComunicadoDataResolved = {
      kpi: { value: 3.25, label: "score" },
      kpiMetrics: [
        { field: "score", value: 3.25, label: "IDD" },
        { field: "idd", value: 3.25, label: "IDD" },
      ],
      table: {
        columns: [
          { key: "name", label: "Indicador" },
          { key: "score", label: "Score" },
        ],
        rows: [
          { name: "PPM interno", score: 1.23 },
          { name: "PPM externo", score: 10 },
          { name: "Kaizen ideias", score: 0 },
          { name: "Kaizen financeiro", score: 0 },
          { name: "Auditoria 5S", score: 0 },
        ],
      },
    };
    expect(extractProjectionFieldValues(departmentIndicators, "score")).toEqual([3.25]);
    expect(suggestDefaultAggregationForField(departmentIndicators, "score")).toBe("first");
    const avg = resolveProjectedField(departmentIndicators, "score", "avg");
    expect(avg.kind).toBe("scalar");
    expect(avg.scalar).toBe(3.25);
  });

  it("indicadores aninhados: list também é KPI único (não 10\\n0,84…)", () => {
    const departmentIndicators: ComunicadoDataResolved = {
      kpi: { value: 6.57, label: "IDD" },
      kpiMetrics: [
        { field: "idd", value: 6.57, label: "IDD" },
      ],
      table: {
        columns: [
          { key: "name", label: "Indicador" },
          { key: "score", label: "Score" },
        ],
        rows: [
          { name: "PPM externo", score: 10 },
          { name: "Refugo", score: 0.84 },
          { name: "Retrabalho", score: 0.22 },
        ],
      },
    };
    // Binding `score` com métrica só em `idd` — alias departamental.
    expect(extractProjectionFieldValues(departmentIndicators, "score")).toEqual([6.57]);
    const listed = resolveProjectedField(departmentIndicators, "score", "list");
    expect(listed.kind).toBe("list");
    expect(listed.values).toEqual([6.57]);
  });
});
