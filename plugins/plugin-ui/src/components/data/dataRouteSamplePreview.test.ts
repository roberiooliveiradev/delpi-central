import { describe, expect, it } from "vitest";

import {
  buildSampleDataRoutePreview,
  mapEnrichedBlockToDataRoutePreview,
} from "./dataRouteSamplePreview";

describe("buildSampleDataRoutePreview", () => {
  it("monta KPI, tabela e série com poucos dados", () => {
    expect(buildSampleDataRoutePreview({ id: "a", label: "OEE", kind: "kpi" })).toMatchObject({
      kind: "kpi",
      source: "sample",
      kpi: { label: "OEE", value: "87,4%" },
    });

    expect(
      buildSampleDataRoutePreview({ id: "summary", label: "Resumo LMP", kind: "kpi", kpiSummary: true }),
    ).toMatchObject({
      kind: "kpi",
      source: "sample",
      metrics: [
        { label: "Total", value: "128" },
        { label: "% no prazo", value: "87,4%" },
        { label: "Lead time", value: "3,2" },
      ],
    });

    const table = buildSampleDataRoutePreview({ id: "b", label: "Lista", kind: "table" });
    expect(table.table?.rows).toHaveLength(4);
    expect(table.table?.columns[0]?.key).toBe("code");

    const series = buildSampleDataRoutePreview({ id: "c", label: "Série", kind: "series" });
    expect(series.series?.points).toHaveLength(5);
  });
});

describe("mapEnrichedBlockToDataRoutePreview", () => {
  it("mapeia resolved.kpi / table / chart", () => {
    expect(
      mapEnrichedBlockToDataRoutePreview(
        { resolved: { kpi: { label: "OEE", value: 0.912 } } },
        "kpi",
      ),
    ).toMatchObject({
      kind: "kpi",
      source: "live",
      kpi: { label: "OEE", value: "0,91" },
    });

    const table = mapEnrichedBlockToDataRoutePreview(
      {
        resolved: {
          table: {
            columns: [{ key: "code", label: "Código" }],
            rows: [{ code: "A1" }, { code: "B2" }, { code: "C3" }, { code: "D4" }, { code: "E5" }, { code: "F6" }],
          },
        },
      },
      "table",
    );
    expect(table.table?.rows).toHaveLength(5);

    const series = mapEnrichedBlockToDataRoutePreview(
      {
        resolved: {
          chart: {
            points: [
              { label: "Jan", value: 10 },
              { label: "Fev", value: 12 },
            ],
          },
        },
      },
      "series",
    );
    expect(series.series?.points).toEqual([
      { label: "Jan", value: 10 },
      { label: "Fev", value: 12 },
    ]);

    const emptyTable = mapEnrichedBlockToDataRoutePreview({ resolved: { table: { rows: [] } } }, "table");
    expect(emptyTable.error).toMatch(/não retornou linhas/i);

    const metricsAsTable = mapEnrichedBlockToDataRoutePreview(
      {
        resolved: {
          kpiMetrics: [
            { label: "Total", value: 10 },
            { label: "Média", value: 5 },
          ],
        },
      },
      "table",
    );
    expect(metricsAsTable.kind).toBe("kpi");
    expect(metricsAsTable.metrics).toHaveLength(2);
  });

  it("mapeia kpi summary multi-métrica e cai em tabela quando não há KPI de negócio", () => {
    const summary = mapEnrichedBlockToDataRoutePreview(
      {
        resolved: {
          kpi: { label: "Total de LMPs", value: 42 },
          kpiMetrics: [
            { field: "total_lmps", label: "Total de LMPs", value: 42 },
            { field: "percent_dentro_prazo", label: "% no prazo", value: 81.5 },
            { field: "avg_lead_time", label: "Lead time médio", value: 3.2 },
          ],
        },
      },
      "kpi",
    );
    expect(summary.kind).toBe("kpi");
    expect(summary.metrics).toHaveLength(3);
    expect(summary.metrics?.[1]).toMatchObject({ label: "% no prazo", value: "81,5" });

    const playbook = mapEnrichedBlockToDataRoutePreview(
      {
        resolved: {
          kpi: { label: "total records", value: 10 },
          kpiMetrics: [],
          table: {
            columns: [
              { key: "item_code", label: "Código" },
              { key: "real_consumption_qty", label: "Consumo" },
            ],
            rows: [{ item_code: "A1", real_consumption_qty: 12 }],
          },
        },
      },
      "kpi",
    );
    expect(playbook.kind).toBe("table");
    expect(playbook.table?.rows).toHaveLength(1);
  });
});
