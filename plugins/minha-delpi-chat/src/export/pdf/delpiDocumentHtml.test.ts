import { describe, expect, it } from "vitest";

import { buildDelpiDocumentHtml } from "./delpiDocumentHtml";
import type { DelpiDocumentSpec } from "./types";

const tableSpec: DelpiDocumentSpec = {
  documentTitle: "Produtos programados",
  subtitle: "Minha DELPI · Exportação de dados",
  runningMeta: "2 registros",
  summaryLines: [
    { label: "Registros", value: "2" },
    { label: "Emitido em", value: "22/06/2026 10:00:00" },
  ],
  tables: [
    {
      title: "Produtos programados",
      columns: [
        { key: "op", label: "OP" },
        { key: "product", label: "Produto" },
        { key: "qty", label: "Qtd. planejada" },
      ],
      rows: [
        { op: "24602201014", product: "70260022", qty: "3" },
        { op: "24602201015", product: "70260023", qty: "3" },
      ],
    },
  ],
  footerContext: "Produtos programados",
};

describe("delpiDocumentHtml", () => {
  it("inclui logo, cabeçalho repetível e tabela no layout certificado", () => {
    const html = buildDelpiDocumentHtml(tableSpec, "https://example.com/logoDelpi.svg");

    expect(html).toContain("logoDelpi.svg");
    expect(html).toContain("cert-print-running-header");
    expect(html).toContain("Produtos programados");
    expect(html).toContain("Minha DELPI · Exportação de dados");
    expect(html).toContain("cert-table");
    expect(html).toContain("70260022");
    expect(html).toContain("www.delpi.com.br");
  });

  it("omite selo quando badge não é informado", () => {
    const html = buildDelpiDocumentHtml(tableSpec, "https://example.com/logoDelpi.svg");

    expect(html).not.toContain("cert-seal cert-seal--compact");
    expect(html).not.toMatch(/class="cert-seal /);
  });
});
