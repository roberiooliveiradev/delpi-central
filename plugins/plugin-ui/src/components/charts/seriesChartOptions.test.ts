import { describe, expect, it } from "vitest";

import {
  DEFAULT_SERIES_CHART_OPTIONS,
  SERIES_CHART_CHROME_VERSION,
  migrateSeriesChartOptionsOnLoad,
  resolveSeriesChartDisplayOptions,
  resolveSeriesChartTicks,
} from "./seriesChartOptions";

describe("seriesChartOptions — títulos de eixo", () => {
  it("liga títulos de eixo por padrão", () => {
    expect(DEFAULT_SERIES_CHART_OPTIONS.showXAxisTitle).toBe(true);
    expect(DEFAULT_SERIES_CHART_OPTIONS.showYAxisTitle).toBe(true);
    expect(DEFAULT_SERIES_CHART_OPTIONS.chromeVersion).toBe(SERIES_CHART_CHROME_VERSION);
  });

  it("resolveSeriesChartDisplayOptions preenche eixos com dados da rota (como o título)", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      {},
      {
        label: "OEE — série temporal",
        kpi: { label: "OEE" },
        table: {
          columns: [
            { key: "periodo", label: "Período" },
            { key: "value", label: "OEE %" },
          ],
        },
      },
    );
    expect(resolved.title).toBe("OEE — série temporal");
    expect(resolved.xAxisTitle).toBe("Período");
    expect(resolved.yAxisTitle).toBe("OEE %");
    expect(resolved.showXAxisTitle).toBe(true);
    expect(resolved.showYAxisTitle).toBe(true);
  });

  it("resolveSeriesChartDisplayOptions infere moeda em ranking de valor (R$)", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      { valueFormat: "auto" },
      {
        label: "Relatório operacional — Refugos rankings",
        chart: { series: [{ field: "value", name: "Valor (R$)" }] },
        table: {
          columns: [
            { key: "code", label: "Código" },
            { key: "value", label: "Valor (R$)" },
          ],
        },
      },
    );
    expect(resolved.valueFormat).toBe("currency");
  });

  it("resolveSeriesChartDisplayOptions preserva override explícito dos eixos", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      { xAxisTitle: "Mês", yAxisTitle: "Índice", showXAxisTitle: false },
      {
        label: "OTD — série temporal",
        table: { columns: [{ key: "periodo", label: "Período" }] },
      },
    );
    expect(resolved.xAxisTitle).toBe("Mês");
    expect(resolved.yAxisTitle).toBe("Índice");
    expect(resolved.showXAxisTitle).toBe(false);
  });

  it("migrateSeriesChartOptionsOnLoad liga eixos em bloco legado sem chromeVersion", () => {
    const migrated = migrateSeriesChartOptionsOnLoad({
      showXAxisTitle: false,
      showYAxisTitle: false,
    });
    expect(migrated.showXAxisTitle).toBe(true);
    expect(migrated.showYAxisTitle).toBe(true);
    expect(migrated.chromeVersion).toBe(SERIES_CHART_CHROME_VERSION);
  });

  it("migrateSeriesChartOptionsOnLoad preserva eixos desligados após chromeVersion atual", () => {
    const migrated = migrateSeriesChartOptionsOnLoad({
      showXAxisTitle: false,
      showYAxisTitle: false,
      chromeVersion: SERIES_CHART_CHROME_VERSION,
    });
    expect(migrated.showXAxisTitle).toBe(false);
    expect(migrated.showYAxisTitle).toBe(false);
  });

  it("migrate v2 zera categoryPaddingPercent legado (extremos no eixo X)", () => {
    const migrated = migrateSeriesChartOptionsOnLoad({
      categoryPaddingPercent: 6,
      chromeVersion: 1,
    });
    expect(migrated.categoryPaddingPercent).toBe(0);
    expect(migrated.chromeVersion).toBe(SERIES_CHART_CHROME_VERSION);
  });
});

describe("resolveSeriesChartTicks — domínio cobre dataMax", () => {
  it("não trunca economia ~875 com piso ~100 (regressão clip no teto)", () => {
    const ticks = resolveSeriesChartTicks(100, 875);
    expect(ticks[0]!).toBeLessThanOrEqual(100);
    expect(ticks[ticks.length - 1]!).toBeGreaterThanOrEqual(875);
  });

  it("cobre max quando cai entre ticks nice", () => {
    const ticks = resolveSeriesChartTicks(0, 875);
    expect(ticks[ticks.length - 1]!).toBeGreaterThanOrEqual(875);
  });

  it("mantém ticks estáveis quando max já é nice", () => {
    const ticks = resolveSeriesChartTicks(0, 800);
    expect(ticks[0]).toBe(0);
    expect(ticks[ticks.length - 1]).toBe(800);
  });
});
