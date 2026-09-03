import { describe, expect, it } from "vitest";

import {
  buildDelpiDocumentHtml,
  buildDelpiDocumentTextSectionsHtml,
  escapeDelpiDocumentHtml,
} from "./delpiDocumentHtml";

describe("buildDelpiDocumentTextSectionsHtml", () => {
  it("retorna vazio sem seções", () => {
    expect(buildDelpiDocumentTextSectionsHtml([])).toBe("");
  });

  it("renderiza títulos e corpos escapados", () => {
    const html = buildDelpiDocumentTextSectionsHtml([
      { title: "Processo", body: "Antes <script>" },
      { title: "Problema", body: "" },
    ]);

    expect(html).toContain('class="cert-text-sections"');
    expect(html).toContain("Processo");
    expect(html).toContain(escapeDelpiDocumentHtml("Antes <script>"));
    expect(html).toContain("Problema");
    expect(html).toContain("—");
    expect(html).not.toContain("<script>");
  });
});

describe("buildDelpiDocumentHtml textSections", () => {
  it("inclui blocos narrativos entre summary e rodapé", () => {
    const html = buildDelpiDocumentHtml({
      documentTitle: "Ficha Kaizen",
      subtitle: "Suporte tablet",
      summaryLines: [{ label: "Unidade", value: "Santa Catarina" }],
      textSections: [
        { title: "Processo", body: "Linha de montagem" },
        { title: "Problema", body: "Tempo perdido" },
        { title: "Melhoria", body: "Suporte fixo" },
        { title: "Resultado esperado", body: "Menos retrabalho" },
      ],
    });

    expect(html).toContain("Ficha Kaizen");
    expect(html).toContain("Santa Catarina");
    expect(html).toContain("Linha de montagem");
    expect(html).toContain("Tempo perdido");
    expect(html).toContain("Suporte fixo");
    expect(html).toContain("Menos retrabalho");
    expect(html).toContain("cert-text-sections__grid");
  });
});
