import { describe, expect, it } from "vitest";

import {
  dataLabelsConfigFromPreset,
  formatSeriesChartDataLabelText,
  matchDataLabelsPreset,
  mergeSeriesChartDataLabels,
  resolveSeriesChartDataLabels,
  shouldHideDataLabel,
} from "./seriesChartDataLabels";

describe("seriesChartDataLabels", () => {
  it("legado showDataLabels sem config → valor no centro", () => {
    const resolved = resolveSeriesChartDataLabels({ showDataLabels: true });
    expect(resolved).toMatchObject({
      showValue: true,
      showCategoryName: false,
      showPercentage: false,
      position: "center",
    });
  });

  it("desligado retorna null", () => {
    expect(resolveSeriesChartDataLabels({ showDataLabels: false })).toBeNull();
  });

  it("preset categoria+% formata como PPT", () => {
    const { dataLabels } = dataLabelsConfigFromPreset("categoryPercent");
    const config = mergeSeriesChartDataLabels(dataLabels);
    const text = formatSeriesChartDataLabelText({
      config,
      categoryLabel: "Pontual",
      value: 57,
      total: 100,
      valueFormat: "number",
    });
    expect(text).toBe("Pontual 57%");
    expect(config.showLeaderLines).toBe(true);
    expect(config.position).toBe("outsideEnd");
    expect(config.colorFromCategory).toBe(true);
  });

  it("hideBelowPercent oculta fatias mínimas", () => {
    const config = mergeSeriesChartDataLabels({ hideBelowPercent: 0.05 });
    expect(shouldHideDataLabel({ config, value: 2, total: 100 })).toBe(true);
    expect(shouldHideDataLabel({ config, value: 12, total: 100 })).toBe(false);
  });

  it("matchDataLabelsPreset reconhece categoryPercent", () => {
    const next = dataLabelsConfigFromPreset("categoryPercent");
    expect(matchDataLabelsPreset(next.showDataLabels, next.dataLabels)).toBe("categoryPercent");
  });
});
