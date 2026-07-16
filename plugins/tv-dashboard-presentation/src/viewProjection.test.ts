import { describe, expect, it } from "vitest";

import {
  parseComunicadoConfig,
  serializeComunicadoConfig,
} from "./comunicadoHelpers";
import {
  aggregateValues,
  applyViewProjection,
  discoverResolvedFieldOptions,
  kpiProjectionFromSelectedFields,
  suggestDefaultProjections,
} from "./viewProjection";
import type { ComunicadoDataResolved } from "./comunicadoTypes";

const sampleResolved: ComunicadoDataResolved = {
  kpi: { value: 10, label: "A" },
  kpiMetrics: [
    { field: "a", label: "A", value: 10 },
    { field: "b", label: "B", value: 20 },
  ],
  table: {
    columns: [
      { key: "periodo", label: "Período" },
      { key: "oee", label: "OEE" },
      { key: "otd", label: "OTD" },
    ],
    rows: [
      { periodo: "Jan", oee: 80, otd: 90 },
      { periodo: "Fev", oee: 70, otd: 95 },
    ],
  },
  chart: {
    points: [
      { label: "Jan", value: 80 },
      { label: "Fev", value: 70 },
    ],
    chartType: "line",
  },
};

describe("aggregateValues", () => {
  it("soma, média e contagem", () => {
    expect(aggregateValues([1, 2, 3], "sum")).toBe(6);
    expect(aggregateValues([1, 2, 3], "avg")).toBe(2);
    expect(aggregateValues([1, 2, 3], "count")).toBe(3);
    expect(aggregateValues([1, 2, 3], "min")).toBe(1);
    expect(aggregateValues([1, 2, 3], "max")).toBe(3);
  });
});

describe("applyViewProjection", () => {
  it("agrega coluna da tabela em KPI", () => {
    const next = applyViewProjection(sampleResolved, {
      kpiProjection: {
        metrics: [{ field: "oee", aggregation: "avg", label: "OEE médio" }],
      },
    });
    expect(next?.kpiMetrics).toHaveLength(1);
    expect(next?.kpiMetrics?.[0]?.value).toBe(75);
    expect(next?.kpi?.label).toBe("OEE médio");
  });

  it("filtra colunas da tabela pela projeção", () => {
    const next = applyViewProjection(sampleResolved, {
      tableProjection: {
        columns: [
          { key: "periodo", visible: true },
          { key: "oee", visible: true },
          { key: "otd", visible: false },
        ],
      },
    });
    expect(next?.table?.columns?.map((col) => col.key)).toEqual(["periodo", "oee"]);
    expect(Object.keys(next?.table?.rows?.[0] ?? {})).toEqual(["periodo", "oee"]);
  });

  it("monta multi-série a partir da tabela", () => {
    const next = applyViewProjection(sampleResolved, {
      chartProjection: {
        categoryField: "periodo",
        series: [
          { field: "oee", label: "OEE" },
          { field: "otd", label: "OTD" },
        ],
      },
    });
    expect(next?.chart?.series).toHaveLength(2);
    expect(next?.chart?.series?.[0]?.points?.[0]).toMatchObject({ label: "Jan", value: 80 });
    expect(next?.chart?.series?.[1]?.points?.[1]).toMatchObject({ label: "Fev", value: 95 });
  });

  it("migra selectedValueFields para kpiProjection helper", () => {
    expect(kpiProjectionFromSelectedFields(["a", "b"])?.metrics?.map((m) => m.field)).toEqual([
      "a",
      "b",
    ]);
  });

  it("descobre campos do resolved", () => {
    const fields = discoverResolvedFieldOptions(sampleResolved);
    expect(fields.some((item) => item.field === "oee")).toBe(true);
    expect(fields.some((item) => item.field === "a")).toBe(true);
  });

  it("sugere projeções default ao conectar fonte", () => {
    const suggested = suggestDefaultProjections(sampleResolved);
    expect(suggested.kpiProjection?.metrics?.some((m) => m.field === "oee")).toBe(true);
    expect(suggested.chartProjection?.categoryField).toBe("periodo");
    expect(suggested.chartProjection?.series?.length).toBeGreaterThan(0);
    expect(suggested.tableProjection?.columns?.length).toBeGreaterThan(0);
  });

  it("respeita valueFieldTypes para eixo X vs Y", () => {
    const suggested = suggestDefaultProjections(sampleResolved, {
      periodo: "date",
      oee: "number",
      otd: "number",
      a: "number",
      b: "number",
    });
    expect(suggested.chartProjection?.categoryField).toBe("periodo");
    expect(suggested.chartProjection?.series?.every((s) => s.field !== "periodo")).toBe(true);
  });
});

describe("persistência sem selectedValueFields", () => {
  it("migra legado no load e não regrava selectedValueFields", () => {
    const parsed = parseComunicadoConfig({
      blocks: [
        {
          id: "c1",
          type: "chart_view",
          chartType: "bar",
          selectedValueFields: ["oee", "otd"],
          frame: { x: 0, y: 0, w: 40, h: 30 },
        },
      ],
    });
    const chart = parsed.blocks.find((b) => b.type === "chart_view");
    expect(chart?.type).toBe("chart_view");
    if (chart?.type !== "chart_view") return;
    expect(chart.chartProjection?.series?.map((s) => s.field)).toEqual(["oee", "otd"]);
    expect("selectedValueFields" in chart).toBe(false);
    const serialized = serializeComunicadoConfig(parsed) as { blocks: Array<Record<string, unknown>> };
    const out = serialized.blocks.find((b) => b.type === "chart_view");
    expect(out?.selectedValueFields).toBeUndefined();
    expect(out?.chartProjection).toBeTruthy();
  });
});
