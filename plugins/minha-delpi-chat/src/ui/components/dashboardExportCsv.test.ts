import { describe, expect, it } from "vitest";

import { buildDashboardCsv } from "./dashboardExportCsv";

describe("dashboardExportCsv", () => {
  it("exporta KPI, tabela e gráfico em seções", () => {
    const csv = buildDashboardCsv({
      type: "dashboard",
      title: "Resumo LMP",
      panels: [
        {
          id: "kpi1",
          title: "Indicadores",
          presentation: {
            type: "kpi",
            title: "",
            cards: [{ label: "Itens", value: "42", unit: "un" }],
          },
        },
        {
          id: "tbl1",
          title: "Top itens",
          presentation: {
            type: "table",
            title: "",
            columns: [
              { key: "produto", label: "Produto" },
              { key: "qtd", label: "Qtd" },
            ],
            rows: [{ produto: "A", qtd: 3 }],
          },
        },
        {
          id: "ch1",
          title: "Série",
          presentation: {
            type: "chart",
            title: "",
            chartType: "line",
            data: [{ mes: "Jan", valor: 10 }],
            config: { xAxis: "mes", yAxis: "valor" },
          },
        },
      ],
    });

    expect(csv.charCodeAt(0)).toBe(0xfeff);
    expect(csv).toContain("Painel: Indicadores");
    expect(csv).toContain("Itens;42;un");
    expect(csv).toContain("Produto;Qtd");
    expect(csv).toContain("mes;valor");
    expect(csv).toContain("Jan;10");
  });
});
