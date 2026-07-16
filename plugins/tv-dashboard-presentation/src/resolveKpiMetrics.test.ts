import { describe, expect, it } from "vitest";

import {
  applyMetricSelectionToResolved,
  filterKpiMetrics,
  normalizeSelectedValueFields,
} from "./resolveKpiMetrics";
import type { ComunicadoDataResolved } from "./comunicadoTypes";

const sampleResolved: ComunicadoDataResolved = {
  label: "LMP",
  kpi: { value: 42, label: "Total de LMPs" },
  kpiMetrics: [
    { field: "total_lmps", value: 42, label: "Total de LMPs" },
    { field: "percent_dentro_prazo", value: 81.5, label: "% no prazo" },
    { field: "avg_lead_time", value: 3.2, label: "Lead time médio" },
  ],
  chart: {
    points: [
      { label: "Total de LMPs", value: 42 },
      { label: "% no prazo", value: 81.5 },
      { label: "Lead time médio", value: 3.2 },
    ],
    chartType: "bar",
  },
  table: {
    rows: [
      { metric: "Total de LMPs", field: "total_lmps", value: 42 },
      { metric: "% no prazo", field: "percent_dentro_prazo", value: 81.5 },
      { metric: "Lead time médio", field: "avg_lead_time", value: 3.2 },
    ],
    columns: [
      { key: "metric", label: "Indicador" },
      { key: "value", label: "Valor" },
    ],
  },
};

describe("resolveKpiMetrics", () => {
  it("normalizeSelectedValueFields limpa vazios", () => {
    expect(normalizeSelectedValueFields([" a ", "", "b"])).toEqual(["a", "b"]);
    expect(normalizeSelectedValueFields([])).toBeUndefined();
  });

  it("filterKpiMetrics respeita ordem da seleção", () => {
    const filtered = filterKpiMetrics(sampleResolved.kpiMetrics, {
      selectedValueFields: ["avg_lead_time", "total_lmps"],
    });
    expect(filtered.map((item) => item.field)).toEqual(["avg_lead_time", "total_lmps"]);
  });

  it("applyMetricSelectionToResolved atualiza kpi/chart/table", () => {
    const next = applyMetricSelectionToResolved(sampleResolved, {
      selectedValueFields: ["percent_dentro_prazo"],
    });
    expect(next?.kpi?.value).toBe(81.5);
    expect(next?.kpiMetrics).toHaveLength(1);
    expect(next?.chart?.points).toEqual([{ label: "% no prazo", value: 81.5 }]);
    expect(next?.table?.rows).toEqual([
      { metric: "% no prazo", field: "percent_dentro_prazo", value: 81.5 },
    ]);
  });

  it("preserva tabela textual quando a métrica é só contagem", () => {
    const resolved: ComunicadoDataResolved = {
      kpiMetrics: [{ field: "total_records", value: 2, label: "Quantidade" }],
      table: {
        rows: [
          { status: "APROVADO", owner: "Ana" },
          { status: "PENDENTE", owner: "Bruno" },
        ],
        columns: [
          { key: "status", label: "Status" },
          { key: "owner", label: "Responsável" },
        ],
      },
    };
    const next = applyMetricSelectionToResolved(resolved, {});
    expect(next?.table?.rows).toHaveLength(2);
    expect(next?.table?.rows?.[0]?.status).toBe("APROVADO");
  });
});
