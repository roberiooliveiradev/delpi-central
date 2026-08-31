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
  normalizeTableProjection,
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

  it("anexa coluna nova da fonte que ainda não está na projeção", () => {
    const next = applyViewProjection(sampleResolved, {
      tableProjection: {
        columns: [
          { key: "periodo", visible: true },
          { key: "oee", visible: true },
        ],
      },
    });
    expect(next?.table?.columns?.map((col) => col.key)).toEqual([
      "periodo",
      "oee",
      "otd",
    ]);
  });

  it("oculta sáb./dom. nos pontos do gráfico quando excludeWeekends", () => {
    const daily: ComunicadoDataResolved = {
      table: {
        columns: [
          { key: "periodo", label: "Período" },
          { key: "oee", label: "OEE" },
        ],
        rows: [
          { periodo: "2026-08-08", oee: 70 },
          { periodo: "2026-08-10", oee: 80 },
        ],
      },
      chart: {
        points: [
          { label: "2026-08-08", value: 70 },
          { label: "2026-08-10", value: 80 },
        ],
        chartType: "bar",
      },
    };
    const next = applyViewProjection(daily, {
      chartProjection: {
        categoryField: "periodo",
        series: [{ field: "oee", label: "OEE" }],
      },
      chartType: "bar",
      excludeWeekends: true,
    });
    expect(next?.chart?.points?.map((item) => item.label)).toEqual(["2026-08-10"]);
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
      chartType: "line",
    });
    expect(next?.chart?.series).toHaveLength(2);
    expect(next?.chart?.series?.[0]?.points?.[0]).toMatchObject({ label: "Jan", value: 80 });
    expect(next?.chart?.series?.[1]?.points?.[1]).toMatchObject({ label: "Fev", value: 95 });
  });

  it("categoria/legenda usam o valor cru da coluna escolhida (como na API)", () => {
    const ranking: ComunicadoDataResolved = {
      table: {
        columns: [
          { key: "code", label: "Código" },
          { key: "label", label: "Descrição" },
          { key: "value", label: "Valor" },
        ],
        rows: [
          { code: "FM", label: "FM - Falha de material", value: 102.04 },
          { code: "FH", label: "FH - Falha humana", value: 41.91 },
          {
            code: "10070821",
            label: "CABO PP CIRCULAR PVC/PVC 4X1.5MM2",
            value: 41.65,
          },
        ],
      },
    };
    const byCode = applyViewProjection(ranking, {
      chartType: "doughnut",
      chartProjection: {
        categoryField: "code",
        series: [{ field: "value", label: "Valor", aggregation: "sum" }],
      },
    });
    expect(byCode?.chart?.points?.map((p) => p.label)).toEqual([
      "FM",
      "FH",
      "10070821",
    ]);

    const byLabel = applyViewProjection(ranking, {
      chartType: "bar",
      chartProjection: {
        categoryField: "label",
        series: [{ field: "value", label: "Valor", aggregation: "sum" }],
      },
    });
    expect(byLabel?.chart?.points?.map((p) => p.label)).toEqual([
      "FM - Falha de material",
      "FH - Falha humana",
      "CABO PP CIRCULAR PVC/PVC 4X1.5MM2",
    ]);
  });

  it("pizza agrupa por categoria (TIPO) e conta linhas quando medida ausente", () => {
    const lmpResolved: ComunicadoDataResolved = {
      table: {
        columns: [
          { key: "tipo", label: "Tipo" },
          { key: "ov", label: "OV" },
        ],
        rows: [
          { tipo: "LMP", ov: "1" },
          { tipo: "LMP", ov: "2" },
          { tipo: "AMOSTRA", ov: "3" },
          { tipo: "OUTRO", ov: "4" },
          { tipo: "LMP", ov: "5" },
        ],
      },
    };
    const next = applyViewProjection(lmpResolved, {
      chartType: "pie",
      chartProjection: {
        categoryField: "tipo",
        series: [{ field: "total_items", label: "total items", aggregation: "first" }],
      },
    });
    const points = next?.chart?.points ?? [];
    expect(points).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ label: "LMP", value: 3 }),
        expect.objectContaining({ label: "AMOSTRA", value: 1 }),
        expect.objectContaining({ label: "OUTRO", value: 1 }),
      ]),
    );
    expect(points).toHaveLength(3);
  });

  it("com serverProjectionApplied ainda agrupa pizza (não confia no bake rowwise)", () => {
    const bakedWrong: ComunicadoDataResolved = {
      serverProjectionApplied: true,
      chart: {
        chartType: "line",
        points: [
          { label: "LMP", value: 1 },
          { label: "LMP", value: 1 },
          { label: "AMOSTRA", value: 1 },
          { label: "LMP", value: 1 },
        ],
        series: [
          {
            name: "Dashboard de LMPs",
            points: [
              { label: "LMP", value: 1 },
              { label: "LMP", value: 1 },
              { label: "AMOSTRA", value: 1 },
              { label: "LMP", value: 1 },
            ],
          },
        ],
      },
      table: {
        columns: [
          { key: "tipo", label: "Tipo" },
          { key: "ov", label: "OV" },
        ],
        rows: [
          { tipo: "LMP", ov: "1" },
          { tipo: "LMP", ov: "2" },
          { tipo: "AMOSTRA", ov: "3" },
          { tipo: "LMP", ov: "4" },
        ],
      },
    };
    const next = applyViewProjection(bakedWrong, {
      chartType: "doughnut",
      chartProjection: {
        categoryField: "tipo",
        series: [{ field: "tipo", aggregation: "count", label: "Contagem" }],
      },
    });
    const points = next?.chart?.points ?? [];
    expect(points).toHaveLength(2);
    expect(points).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ label: "LMP", value: 3 }),
        expect.objectContaining({ label: "AMOSTRA", value: 1 }),
      ]),
    );
    expect(next?.chart?.chartType).toBe("doughnut");
  });

  it("com serverProjectionApplied ainda re-agrega KPI do bloco (não confia no bake)", () => {
    const bakedWrong: ComunicadoDataResolved = {
      serverProjectionApplied: true,
      kpi: { value: 99, label: "bake errado" },
      kpiMetrics: [{ field: "oee", value: 99, label: "bake errado" }],
      table: {
        columns: [
          { key: "periodo", label: "Período" },
          { key: "oee", label: "OEE" },
        ],
        rows: [
          { periodo: "a", oee: 60 },
          { periodo: "b", oee: 80 },
          { periodo: "c", oee: 100 },
        ],
      },
    };
    const next = applyViewProjection(bakedWrong, {
      kpiProjection: {
        metrics: [{ field: "oee", aggregation: "avg", label: "OEE médio" }],
      },
    });
    expect(next?.kpiMetrics?.[0]?.value).toBe(80);
    expect(next?.kpi?.label).toBe("OEE médio");
  });

  it("barra agrupa soma por categoria", () => {
    const next = applyViewProjection(
      {
        table: {
          columns: [
            { key: "filial", label: "Filial" },
            { key: "qtd", label: "Qtd" },
          ],
          rows: [
            { filial: "01", qtd: 10 },
            { filial: "01", qtd: 5 },
            { filial: "02", qtd: 3 },
          ],
        },
      },
      {
        chartType: "bar",
        chartProjection: {
          categoryField: "filial",
          series: [{ field: "qtd", aggregation: "sum" }],
        },
      },
    );
    expect(next?.chart?.points).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ label: "01", value: 15 }),
        expect.objectContaining({ label: "02", value: 3 }),
      ]),
    );
  });

  it("linha não agrupa (um ponto por linha)", () => {
    const next = applyViewProjection(sampleResolved, {
      chartType: "line",
      chartProjection: {
        categoryField: "periodo",
        series: [{ field: "oee" }],
      },
    });
    expect(next?.chart?.points).toHaveLength(2);
  });

  it("preserva plotOn secondary na série do chart", () => {
    const next = applyViewProjection(sampleResolved, {
      chartType: "line",
      chartProjection: {
        categoryField: "periodo",
        series: [
          { field: "oee", label: "OEE", plotOn: "primary" },
          { field: "otd", label: "OTD", plotOn: "secondary" },
        ],
      },
    });
    expect(next?.chart?.series?.[1]?.plotOn).toBe("secondary");
  });

  it("suggestDefaultProjections pizza sugere count na categoria", () => {
    const suggested = suggestDefaultProjections(
      {
        table: {
          columns: [
            { key: "tipo", label: "Tipo" },
            { key: "qtd", label: "Qtd" },
          ],
          rows: [
            { tipo: "LMP", qtd: 1 },
            { tipo: "OUTRO", qtd: 2 },
          ],
        },
      },
      { tipo: "string", qtd: "number" },
      "pie",
    );
    expect(suggested.chartProjection?.categoryField).toBe("tipo");
    expect(suggested.chartProjection?.series?.[0]?.aggregation).toBe("sum");
    expect(suggested.chartProjection?.series?.[0]?.field).toBe("qtd");
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

  it("descobre value a partir do KPI escalar sem kpiMetrics", () => {
    const fields = discoverResolvedFieldOptions({
      kpi: { value: 5.43, label: "PPM" },
    });
    expect(fields.some((item) => item.field === "value")).toBe(true);
  });

  it("catálogo curado sobrescreve humanize fraco do runtime", () => {
    const fields = discoverResolvedFieldOptions(
      {
        kpiMetrics: [{ field: "scrap_cost_pct", value: 0.57, label: "scrap cost pct" }],
      },
      [{ field: "scrap_cost_pct", label: "Custo de refugo / ROL (%)" }],
    );
    expect(fields.find((item) => item.field === "scrap_cost_pct")?.label).toBe(
      "Custo de refugo / ROL (%)",
    );
  });

  it("rótulo PT do kpiMetrics prevalece sobre chave crua do catálogo", () => {
    const fields = discoverResolvedFieldOptions(
      {
        kpiMetrics: [
          { field: "scrap_cost_pct", value: 0.57, label: "Custo de refugo / ROL (%)" },
        ],
      },
      [{ field: "scrap_cost_pct", label: "scrap_cost_pct" }],
    );
    expect(fields.find((item) => item.field === "scrap_cost_pct")?.label).toBe(
      "Custo de refugo / ROL (%)",
    );
  });

  it("humaniza chaves descobertas sem catálogo (picker Campo)", () => {
    const fields = discoverResolvedFieldOptions({
      table: {
        columns: [
          { key: "month", label: "month" },
          { key: "gross_savings_month", label: "gross_savings_month" },
        ],
        rows: [{ month: "2026-01", gross_savings_month: 1 }],
      },
    });
    expect(fields.find((item) => item.field === "month")?.label).toBe("Mês");
    expect(fields.find((item) => item.field === "gross_savings_month")?.label).toBe(
      "Economia bruta (mês)",
    );
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

  it("não sugere série numérica declarada sem amostra finita nas linhas", () => {
    const resolved: ComunicadoDataResolved = {
      ...sampleResolved,
      table: {
        columns: [
          { key: "periodo", label: "Período" },
          { key: "oee_filial_01", label: "OEE 01" },
          { key: "quantidade", label: "Quantidade" },
        ],
        rows: [
          { periodo: "Jan", oee_filial_01: 80, quantidade: null },
          { periodo: "Fev", oee_filial_01: 70 },
        ],
      },
      kpiMetrics: [{ field: "oee_filial_01", label: "OEE 01", value: 80 }],
    };
    const suggested = suggestDefaultProjections(resolved, {
      periodo: "date",
      oee_filial_01: "number",
      quantidade: "number",
    });
    expect(suggested.chartProjection?.series?.map((s) => s.field)).toEqual(["oee_filial_01"]);
    expect(suggested.kpiProjection?.metrics?.map((m) => m.field)).toEqual(["oee_filial_01"]);
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

describe("normalizeTableProjection", () => {
  it("preserva widthPct das colunas", () => {
    const projection = normalizeTableProjection({
      columns: [
        { key: "oee", visible: true, widthPct: 40 },
        { key: "otd", visible: true, widthPct: 200 },
      ],
    });
    expect(projection?.columns?.[0]?.widthPct).toBe(40);
    expect(projection?.columns?.[1]?.widthPct).toBe(100);
  });
});

describe("bubble projection", () => {
  it("mapeia 2ª série como size no ponto e legenda de 1 série", () => {
    const resolved: ComunicadoDataResolved = {
      table: {
        columns: [
          { key: "periodo", label: "Período" },
          { key: "economia", label: "Economia" },
          { key: "investimento", label: "Investimento" },
        ],
        rows: [
          { periodo: 1, economia: 100, investimento: 10 },
          { periodo: 2, economia: 200, investimento: 40 },
        ],
      },
    };
    const next = applyViewProjection(resolved, {
      chartType: "bubble",
      chartProjection: {
        categoryField: "periodo",
        series: [
          { field: "economia", aggregation: "first" },
          { field: "investimento", aggregation: "first" },
        ],
      },
    });
    expect(next?.chart?.series).toHaveLength(1);
    expect(next?.chart?.points?.[0]).toMatchObject({
      label: "1",
      value: 100,
      size: 10,
    });
    expect(next?.chart?.points?.[1]).toMatchObject({
      label: "2",
      value: 200,
      size: 40,
    });
  });
});

describe("maxCategories / Outros", () => {
  it("barra de CT não agrega em Outros (sem teto na policy)", () => {
    const rows = Array.from({ length: 25 }, (_, index) => ({
      work_center: `CT-${String(index + 1).padStart(2, "0")}`,
      oee: 70 + index,
    }));
    const next = applyViewProjection(
      {
        table: {
          columns: [
            { key: "work_center", label: "CT" },
            { key: "oee", label: "OEE" },
          ],
          rows,
        },
      },
      {
        chartType: "bar",
        chartProjection: {
          categoryField: "work_center",
          series: [{ field: "oee", aggregation: "sum" }],
        },
      },
    );
    const labels = next?.chart?.points?.map((point) => point.label) ?? [];
    expect(labels).toHaveLength(25);
    expect(labels).not.toContain("Outros");
  });

  it("pizza ainda compacta categorias excedentes em Outros", () => {
    const rows = Array.from({ length: 12 }, (_, index) => ({
      work_center: `CT-${index + 1}`,
      oee: 10,
    }));
    const next = applyViewProjection(
      {
        table: {
          columns: [
            { key: "work_center", label: "CT" },
            { key: "oee", label: "OEE" },
          ],
          rows,
        },
      },
      {
        chartType: "pie",
        chartProjection: {
          categoryField: "work_center",
          series: [{ field: "oee", aggregation: "sum" }],
        },
      },
    );
    const labels = next?.chart?.points?.map((point) => point.label) ?? [];
    expect(labels).toContain("Outros");
    expect(labels.length).toBeLessThanOrEqual(8);
  });

  it("chartProjection.maxCategories=0 desliga o teto também na pizza", () => {
    const rows = Array.from({ length: 12 }, (_, index) => ({
      work_center: `CT-${index + 1}`,
      oee: 10,
    }));
    const next = applyViewProjection(
      {
        table: {
          columns: [
            { key: "work_center", label: "CT" },
            { key: "oee", label: "OEE" },
          ],
          rows,
        },
      },
      {
        chartType: "pie",
        chartProjection: {
          categoryField: "work_center",
          series: [{ field: "oee", aggregation: "sum" }],
          maxCategories: 0,
        },
      },
    );
    expect(next?.chart?.points).toHaveLength(12);
    expect(next?.chart?.points?.some((point) => point.label === "Outros")).toBe(false);
  });
});

describe("encoding vazio — não troca coluna por cobertura", () => {
  it("bar com projection e rows vazias não pinta buckets_count", () => {
    const next = applyViewProjection(
      {
        serverProjectionApplied: true,
        kpiMetrics: [
          { field: "buckets_count", label: "Buckets quantidade", value: 5 },
          { field: "customers_count", label: "Customers quantidade", value: 0 },
        ],
        chart: {
          points: [
            { label: "Buckets quantidade", value: 5 },
            { label: "Customers quantidade", value: 0 },
          ],
          chartType: "bar",
        },
        table: { columns: [], rows: [] },
      },
      {
        chartType: "bar",
        chartProjection: {
          categoryField: "periodo",
          series: [{ field: "total_qty", label: "Quantidade total", aggregation: "sum" }],
        },
      },
    );
    expect(next?.chart?.points ?? []).toEqual([]);
    expect(next?.chart?.series ?? []).toEqual([]);
  });

  it("gauge só usa kpiMetrics do field escolhido", () => {
    const next = applyViewProjection(
      {
        kpi: { value: 5, label: "Buckets quantidade" },
        kpiMetrics: [{ field: "buckets_count", label: "Buckets quantidade", value: 5 }],
        table: { columns: [], rows: [] },
      },
      {
        chartType: "gauge",
        chartProjection: {
          series: [{ field: "otd_pct", label: "OTD (%)", aggregation: "first" }],
        },
      },
    );
    expect(next?.chart?.points ?? []).toEqual([]);
    expect(next?.kpi?.value).toBeNull();
  });

  it("suggestDefaultProjections ignora buckets_count", () => {
    const suggested = suggestDefaultProjections({
      kpiMetrics: [
        { field: "buckets_count", label: "Buckets quantidade", value: 5 },
        { field: "otd_pct", label: "OTD (%)", value: 98 },
      ],
      table: { columns: [], rows: [] },
    });
    const fields = suggested.chartProjection?.series?.map((s) => s.field) ?? [];
    expect(fields).not.toContain("buckets_count");
    expect(fields).toContain("otd_pct");
  });
});
