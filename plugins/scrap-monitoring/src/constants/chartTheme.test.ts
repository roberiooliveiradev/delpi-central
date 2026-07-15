import { describe, expect, it } from "vitest";

import {
  resolveMotivoChartHeight,
  resolveMotivoPieRadii,
  resolveRankingChartHeight,
} from "./chartTheme";

describe("chartTheme responsive heights", () => {
  it("aumenta altura do Motivo conforme itens da legenda", () => {
    const few = resolveMotivoChartHeight(3);
    const many = resolveMotivoChartHeight(10);
    expect(many).toBeGreaterThan(few);
    expect(resolveMotivoChartHeight(0)).toBeGreaterThanOrEqual(260);
    expect(resolveMotivoChartHeight(50)).toBeLessThanOrEqual(560);
  });

  it("escala raios da rosca com a altura", () => {
    const small = resolveMotivoPieRadii(260);
    const large = resolveMotivoPieRadii(480);
    expect(large.outerRadius).toBeGreaterThanOrEqual(small.outerRadius);
    expect(large.innerRadius).toBeLessThan(large.outerRadius);
  });

  it("ajusta altura dos rankings pelo número de barras", () => {
    expect(resolveRankingChartHeight(10, "product")).toBeGreaterThan(
      resolveRankingChartHeight(3, "product"),
    );
  });
});
