import { describe, expect, it } from "vitest";
import { buildDrawingAnalysisReportHtml } from "./drawingAnalysisPrint";
import type { DrawingAnalysisExportPayload } from "./drawingAnalysisExport";

const samplePayload: DrawingAnalysisExportPayload = {
  filename: "relatorio-desenho-90264227.md",
  mimeType: "text/markdown",
  markdown: "# Relatório",
  exportLabels: {
    pdfTitle: "Relatório de Análise de Desenho DELPI",
  },
  tables: [
    {
      key: "pdfData",
      title: "Dados identificados no PDF",
      columns: [
        { key: "field", label: "Campo" },
        { key: "value", label: "Valor" },
      ],
      rows: [{ field: "Código", value: "90264227" }],
    },
    {
      key: "checklist",
      title: "Checklist completo",
      columns: [
        { key: "section", label: "Seção" },
        { key: "item", label: "Item" },
        { key: "status", label: "Status" },
        { key: "observation", label: "Observação" },
      ],
      rows: [
        {
          section: "API",
          item: "Cadastro",
          status: "OK",
          observation: "—",
        },
      ],
    },
  ],
};

describe("drawingAnalysisPrint", () => {
  it("inclui logo, cabeçalho repetível e todas as tabelas no HTML", () => {
    const html = buildDrawingAnalysisReportHtml(
      samplePayload,
      {
        productCode: "90264227",
        overallLabel: "Reprovado",
        status: "rejected",
        criticalErrors: 2,
      },
      "https://example.com/logoDelpi.svg",
    );

    expect(html).toContain("logoDelpi.svg");
    expect(html).toContain("cert-print-running-header");
    expect(html).toContain("Relatório de Análise de Desenho DELPI");
    expect(html).toContain("Dados identificados no PDF");
    expect(html).toContain("Checklist completo");
    expect(html).toContain("cert-seal--rejected");
    expect(html).toContain("cert-section__title");
    expect(html).toContain("90264227");
  });
});
