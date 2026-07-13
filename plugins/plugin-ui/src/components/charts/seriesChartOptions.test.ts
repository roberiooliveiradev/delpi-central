import { describe, expect, it } from "vitest";

import {
  DEFAULT_SERIES_CHART_OPTIONS,
  SERIES_CHART_CHROME_VERSION,
  migrateSeriesChartOptionsOnLoad,
  resolveSeriesChartDisplayOptions,
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
});
