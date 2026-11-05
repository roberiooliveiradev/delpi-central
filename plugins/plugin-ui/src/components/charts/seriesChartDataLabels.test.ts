import { describe, expect, it } from "vitest";

import {
  formatSeriesChartDataLabelText,
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

  it("categoria + percentual do total compõe o texto sem preset", () => {
    const config = mergeSeriesChartDataLabels({
      showCategoryName: true,
      showValue: false,
      showPercentage: true,
      position: "outsideEnd",
    });
    const text = formatSeriesChartDataLabelText({
      config,
      categoryLabel: "Pontual",
      value: 57,
      total: 100,
      valueFormat: "number",
    });
    expect(text).toBe("Pontual 57%");
    expect(config.position).toBe("outsideEnd");
  });

  it("valor pronto do backend não é reformatado no rótulo", () => {
    const config = mergeSeriesChartDataLabels({ showValue: true, showPercentage: false });
    const text = formatSeriesChartDataLabelText({
      config,
      value: 85,
      total: 100,
      valueFormat: "number",
      displayValue: "85,0%",
    });
    expect(text).toBe("85,0%");
  });

  it("hideBelowPercent oculta fatias mínimas", () => {
    const config = mergeSeriesChartDataLabels({ hideBelowPercent: 0.05 });
    expect(shouldHideDataLabel({ config, value: 2, total: 100 })).toBe(true);
    expect(shouldHideDataLabel({ config, value: 12, total: 100 })).toBe(false);
  });

});
