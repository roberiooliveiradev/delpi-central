import { describe, expect, it } from "vitest";

import { inferDefaultChartAxes } from "./chartAxisSelection";

describe("chartAxisSelection", () => {
  const rows = [
    {
      nome_operador: "Operador A",
      qtd_apontada: 1.8,
      tempo_real_horas: 0.5,
      eficiencia_percentual: 147.87,
    },
    {
      nome_operador: "Operador B",
      qtd_apontada: 6,
      tempo_real_horas: 3.7,
      eficiencia_percentual: 54.45,
    },
  ];

  it("prioriza eficiência no eixo Y em dispersão", () => {
    const axes = inferDefaultChartAxes(rows, "scatter", {
      xAxis: "tempo_real_horas",
      yAxis: ["tempo_previsto_horas"],
    });

    expect(axes.yKey).toBe("eficiencia_percentual");
    expect(axes.xKey).toBe("qtd_apontada");
  });

  it("usa categoria no eixo X em barras", () => {
    const axes = inferDefaultChartAxes(rows, "bar", {});

    expect(axes.xKey).toBe("nome_operador");
    expect(axes.yKey).toBe("eficiencia_percentual");
  });
});
