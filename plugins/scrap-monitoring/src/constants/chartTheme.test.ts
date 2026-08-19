import { describe, expect, it } from "vitest";

import {
  PIE_COLORS,
  assignDistinctPieColors,
  resolveMotivoChartHeight,
  resolveMotivoPieRadii,
  resolveRankingChartHeight,
} from "./chartTheme";

describe("assignDistinctPieColors", () => {
  it("não começa com uma rampa de azuis nos primeiros índices", () => {
    expect(PIE_COLORS[0]).not.toBe(PIE_COLORS[1]);
    expect(PIE_COLORS[1]).toBe("#f59e0b");
    expect(PIE_COLORS[2]).toBe("#16a34a");
    expect(PIE_COLORS[3]).toBe("#e11d48");
  });

  it("atribui cores distintas para os motivos do ranking", () => {
    const keys = ["FM", "FP", "FH", "M3", "RB", "F1"];
    const colors = assignDistinctPieColors(keys);
    expect(new Set(colors).size).toBe(keys.length);
  });

  it("é estável para o mesmo código na mesma ordem", () => {
    const keys = ["FM", "FP", "FH"];
    expect(assignDistinctPieColors(keys)).toEqual(assignDistinctPieColors(keys));
  });
});

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
