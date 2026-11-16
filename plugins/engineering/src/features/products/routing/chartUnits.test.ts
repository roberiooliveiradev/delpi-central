import { describe, expect, it } from "vitest";

import { resolveChartTimeUnit, toChartValue } from "./chartUnits";

describe("resolveChartTimeUnit — unidade de exibição do gráfico", () => {
  it("mantém minutos quando há tempos >= 0,5 min", () => {
    const unit = resolveChartTimeUnit([0.0354, 2.0664, 4.929]);
    expect(unit.unit).toBe("min");
    expect(unit.factor).toBe(1);
    expect(unit.decimalPlaces).toBe(4);
  });

  it("converte para segundos quando todos os tempos são subminuto", () => {
    const unit = resolveChartTimeUnit([0.0012, 0.02, 0.4]);
    expect(unit.unit).toBe("s");
    expect(unit.factor).toBe(60);
    expect(unit.note).toContain("segundos");
  });

  it("sem valores positivos permanece em minutos (estado vazio)", () => {
    expect(resolveChartTimeUnit([]).unit).toBe("min");
    expect(resolveChartTimeUnit([0, Number.NaN]).unit).toBe("min");
  });

  it("exatamente 0,5 min não converte (limite exclusivo)", () => {
    expect(resolveChartTimeUnit([0.5]).unit).toBe("min");
    expect(resolveChartTimeUnit([0.499]).unit).toBe("s");
  });
});

describe("toChartValue — conversão apenas de exibição", () => {
  it("aplica o fator sobre o valor em minutos", () => {
    const seconds = resolveChartTimeUnit([0.0012]);
    expect(toChartValue(0.0012, seconds)).toBeCloseTo(0.072, 6);
  });

  it("preserva null/undefined — nunca plota como zero", () => {
    const unit = resolveChartTimeUnit([1]);
    expect(toChartValue(null, unit)).toBeNull();
    expect(toChartValue(undefined, unit)).toBeNull();
  });
});
