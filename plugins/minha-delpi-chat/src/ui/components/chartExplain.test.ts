import { describe, expect, it } from "vitest";

import {
  buildChartExplanationFallback,
  getChartExplanationFromToolCalls,
  isExplainChartSuggestion,
} from "./chartExplain";

describe("chartExplain", () => {
  it("detecta chip de explicação inline", () => {
    expect(
      isExplainChartSuggestion({
        label: "Explique esse gráfico",
        inlineAction: "explain_chart",
      }),
    ).toBe(true);
  });

  it("lê chartExplanation do metadata", () => {
    const text = getChartExplanationFromToolCalls([
      {
        metadata: {
          presentation: { type: "chart", chartType: "bar", data: [{ a: 1, v: 2 }] },
          presentationDecision: {
            selected: "bar_chart",
            chartExplanation: "Texto pronto da API.",
          },
        },
      },
    ]);

    expect(text).toBe("Texto pronto da API.");
  });

  it("gera fallback quando não há chartExplanation", () => {
    const text = buildChartExplanationFallback({
      type: "chart",
      chartType: "horizontal_bar",
      data: [
        { nome: "A", valor: 10 },
        { nome: "B", valor: 5 },
      ],
      config: { xAxis: "nome", yAxis: ["valor"] },
    });

    expect(text).toContain("barras horizontais");
    expect(text).toContain("Nome");
  });
});
