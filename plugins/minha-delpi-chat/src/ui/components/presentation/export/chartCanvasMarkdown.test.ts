import { describe, expect, it } from "vitest";

import {
  chartPresentationToCanvasMarkdown,
  presentationToCanvasPayload,
} from "./chartCanvasMarkdown";

describe("chartCanvasMarkdown", () => {
  it("gera markdown com título e tabela", () => {
    const markdown = chartPresentationToCanvasMarkdown({
      type: "chart",
      title: "Vendas por mês",
      chartType: "line",
      data: [
        { mes: "2026-01", valor: 10 },
        { mes: "2026-02", valor: 12 },
      ],
      config: { xAxis: "mes", yAxis: "valor" },
    });

    expect(markdown).toContain("# Vendas por mês");
    expect(markdown).toContain("| mes | valor |");
    expect(markdown).toContain("2026-02");
  });

  it("monta payload para lousa", () => {
    const payload = presentationToCanvasPayload({
      type: "chart",
      title: "Ranking",
      chartType: "bar",
      data: [{ produto: "A", qtd: 3 }],
      config: { xAxis: "produto", yAxis: "qtd" },
    });

    expect(payload.title).toBe("Ranking");
    expect(payload.markdown).toContain("Ranking");
  });
});
