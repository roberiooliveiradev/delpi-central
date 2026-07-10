import { describe, expect, it } from "vitest";

import { buildDelpiDocumentHtml } from "./delpiDocumentHtml";
import {
  buildDelpiDocumentColgroup,
  resolveDelpiDocumentTableClassName,
} from "./delpiDocumentTableLayout";
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

  it("aplica perfil compacto de colunas para tabelas de desenho", () => {
    const html = buildDelpiDocumentHtml(
      {
        documentTitle: "Relatório de Análise de Desenho DELPI",
        tables: [
          {
            title: "Estrutura (SG1010)",
            layoutKey: "structure",
            columns: [
              { key: "code", label: "Código" },
              { key: "description", label: "Descrição" },
              { key: "quantity", label: "Qtd" },
              { key: "unit", label: "Unid." },
              { key: "type", label: "Tipo" },
              { key: "level", label: "Nível" },
            ],
            rows: [
              {
                code: "`50222710`",
                description: "TERM. MAG MATE 18-22AWG",
                quantity: "1.0",
                unit: "MI",
                type: "PI",
                level: "0",
              },
            ],
          },
        ],
      },
      "https://example.com/logoDelpi.svg",
    );

    expect(html).toContain('class="cert-table cert-table--dense cert-table--structure"');
    expect(html).toContain("<colgroup>");
    expect(html).toContain('width:40%');
    expect(html).toContain("cert-cell--nowrap");
    expect(html).toContain("50222710");
    expect(html).not.toContain("`50222710`");
  });

  it("renderiza estrutura em outline ASCII quando presentation é outline", () => {
    const html = buildDelpiDocumentHtml(
      {
        documentTitle: "Relatório de Análise de Desenho DELPI",
        tables: [
          {
            title: "Estrutura (SG1010)",
            layoutKey: "structure",
            presentation: "outline",
            outline: "90262008 PA 1 MI — CHICOTE\n└── 50225424 PI 1 — CABO",
            columns: [],
            rows: [],
          },
        ],
      },
      "https://example.com/logoDelpi.svg",
    );

    expect(html).toContain("cert-structure-outline");
    expect(html).toContain("90262008 PA 1 MI — CHICOTE");
    expect(html).toContain("└── 50225424 PI 1 — CABO");
    expect(html).not.toContain("cert-table--structure");
  });
});

describe("delpiDocumentTableLayout", () => {
  it("gera colgroup para roteiro e checklist", () => {
    const guide = buildDelpiDocumentColgroup(
      [
        { key: "product", label: "Produto" },
        { key: "level", label: "Nível" },
        { key: "operation", label: "Operação" },
        { key: "center", label: "Centro" },
        { key: "description", label: "Descrição" },
      ],
      "guide",
    );

    expect(guide).toContain('width:65%');
    expect(resolveDelpiDocumentTableClassName("checklist")).toContain("cert-table--checklist");
  });
});
