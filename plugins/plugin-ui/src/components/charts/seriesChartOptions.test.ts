import { describe, expect, it } from "vitest";

import {
  DEFAULT_SERIES_CHART_OPTIONS,
  SERIES_CHART_CHROME_VERSION,
  formatSeriesChartCategoryLabel,
  formatSeriesChartValue,
  migrateSeriesChartOptionsOnLoad,
  resolveSeriesChartDisplayOptions,
  resolveSeriesChartLegendLayout,
  resolveSeriesChartLegendSort,
  resolveSeriesChartTicks,
} from "./seriesChartOptions";

describe("seriesChartOptions — títulos de eixo", () => {
  it("liga títulos de eixo por padrão", () => {
    expect(DEFAULT_SERIES_CHART_OPTIONS.showXAxisTitle).toBe(true);
    expect(DEFAULT_SERIES_CHART_OPTIONS.showYAxisTitle).toBe(true);
    expect(DEFAULT_SERIES_CHART_OPTIONS.legendLayout).toBe("auto");
    expect(DEFAULT_SERIES_CHART_OPTIONS.legendSort).toBe("auto");
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

  it("resolveSeriesChartDisplayOptions não infere formato — escolha do usuário", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      { valueFormat: "auto" },
      {
        label: "Relatório operacional — Refugos rankings",
        table: {
          columns: [
            { key: "code", label: "Código" },
            { key: "value", label: "Valor (R$)" },
          ],
        },
      },
    );
    expect(resolved.valueFormat).toBe("auto");
  });

  it("resolveSeriesChartDisplayOptions preserva formato explícito do usuário", () => {
    const resolved = resolveSeriesChartDisplayOptions(
      { valueFormat: "currency" },
      {
        table: {
          columns: [
            { key: "code", label: "Código" },
            { key: "sharePct", label: "Participação (%)" },
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

describe("formatSeriesChartValue / category label", () => {
  it("compact formata em notação curta pt-BR", () => {
    const formatted = formatSeriesChartValue(28000, "compact");
    expect(formatted.toLowerCase()).toMatch(/28/);
    expect(formatted.toLowerCase()).toMatch(/mil|k/);
  });

  it("autoDate encurta ISO date", () => {
    expect(formatSeriesChartCategoryLabel("2026-07-01", "autoDate")).toMatch(/jul/i);
  });

  it("defaults de label format preservam playlists antigas", () => {
    expect(DEFAULT_SERIES_CHART_OPTIONS.categoryLabelRotation).toBe("auto");
    expect(DEFAULT_SERIES_CHART_OPTIONS.categoryLabelOverflow).toBe("skip");
    expect(DEFAULT_SERIES_CHART_OPTIONS.categoryLabelFormat).toBe("raw");
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

describe("legenda — layout e ordenação automáticos", () => {
  it("auto: laterais em coluna; top/bottom em linha com poucas categorias", () => {
    expect(
      resolveSeriesChartLegendLayout({
        position: "right",
        layout: "auto",
        itemCount: 5,
        usesCategoryLegend: true,
      }),
    ).toBe("column");
    expect(
      resolveSeriesChartLegendLayout({
        position: "bottom",
        layout: "auto",
        itemCount: 2,
        usesCategoryLegend: true,
      }),
    ).toBe("row");
  });

  it("auto: top/bottom em coluna com ≥4 categorias (padrão de ajuste)", () => {
    expect(
      resolveSeriesChartLegendLayout({
        position: "bottom",
        layout: "auto",
        itemCount: 5,
        usesCategoryLegend: true,
      }),
    ).toBe("column");
  });

  it("força linha mesmo à direita", () => {
    expect(
      resolveSeriesChartLegendLayout({
        position: "right",
        layout: "row",
        itemCount: 5,
        usesCategoryLegend: true,
      }),
    ).toBe("row");
  });

  it("auto: pizza/funil ordenam por valor ↓", () => {
    expect(
      resolveSeriesChartLegendSort({
        chartType: "pie",
        sort: "auto",
        usesCategoryLegend: true,
      }),
    ).toBe("valueDesc");
    expect(
      resolveSeriesChartLegendSort({
        chartType: "line",
        sort: "auto",
        usesCategoryLegend: false,
      }),
    ).toBe("data");
  });
});
