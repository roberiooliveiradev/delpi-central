import { describe, expect, it } from "vitest";

import {
  dualYAxisMargin,
  hasSecondaryYAxis,
  isSecondaryYSeries,
  resolveTooltipSeries,
} from "./multiTypeSeriesDualAxis";

const VALUE = {
  dataKey: "faturamento",
  name: "Faturamento · Bruto",
  axis: "primary" as const,
};
const QUANTITY = {
  dataKey: "quantidade",
  name: "Quantidade fornecida",
  axis: "secondary" as const,
  plotAs: "line" as const,
};

describe("multiTypeSeriesDualAxis", () => {
  it("positive: série com axis secondary usa o eixo direito", () => {
    expect(isSecondaryYSeries(QUANTITY)).toBe(true);
    expect(hasSecondaryYAxis([VALUE, QUANTITY])).toBe(true);
    expect(dualYAxisMargin(true, 16).right).toBeGreaterThanOrEqual(88);
  });

  it("sibling: secondaryDataKeys marca o eixo mesmo sem axis no spec", () => {
    const stripped = { dataKey: "quantidade", name: "Quantidade fornecida" };
    expect(isSecondaryYSeries(stripped)).toBe(false);
    expect(isSecondaryYSeries(stripped, ["quantidade"])).toBe(true);
    expect(hasSecondaryYAxis([VALUE, stripped], ["quantidade"])).toBe(true);
  });

  it("negative: só série primária ou plotAs line sem axis não abre eixo direito", () => {
    expect(isSecondaryYSeries(VALUE)).toBe(false);
    expect(
      isSecondaryYSeries({
        dataKey: "trendish",
        name: "Linha",
        plotAs: "line",
      }),
    ).toBe(false);
    expect(hasSecondaryYAxis([VALUE])).toBe(false);
    expect(hasSecondaryYAxis([VALUE], [])).toBe(false);
    expect(dualYAxisMargin(false, 16)).toEqual({});
  });

  it("tooltip resolve por dataKey e cai no nome quando o payload omite dataKey", () => {
    const series = [VALUE, QUANTITY];
    expect(
      resolveTooltipSeries(series, QUANTITY.name, { dataKey: "quantidade" })?.axis,
    ).toBe("secondary");
    expect(
      resolveTooltipSeries(series, QUANTITY.name, { payload: { dataKey: "quantidade" } })
        ?.dataKey,
    ).toBe("quantidade");
    expect(resolveTooltipSeries(series, QUANTITY.name, {})?.dataKey).toBe("quantidade");
    expect(resolveTooltipSeries(series, VALUE.name, null)?.dataKey).toBe("faturamento");
    expect(resolveTooltipSeries(series, "série desconhecida", null)).toBeUndefined();
  });
});
