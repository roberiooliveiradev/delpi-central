import { describe, expect, it } from "vitest";

import {
  buildMarkdownDocumentModel,
  isLeadingTitleDuplicate,
  markdownHeadingSlug,
} from "./markdownDocumentModel";

const SHOWCASE = `# Showcase

Texto **forte**, *itálico* e ~~riscado~~.

> Nota importante.

- [x] Etapa concluída
- [ ] Etapa pendente

## Estado atual

| Etapa | Responsável |
|---|---|
| Fechamento | Controladoria |

\`\`\`sql
SELECT 1;
\`\`\`

\`\`\`mermaid
flowchart LR
  A[Entrada] --> B{Validar}
\`\`\`

## Estado atual

Texto final.
`;

describe("buildMarkdownDocumentModel — GFM", () => {
  it("renderiza headings, ênfase, task list, blockquote, tabela e hr", () => {
    const model = buildMarkdownDocumentModel(SHOWCASE);
    const html = model.segments
      .filter((s) => s.type === "markdown")
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");

    expect(html).toContain("<h1");
    expect(html).toContain("<strong>forte</strong>");
    expect(html).toContain("<em>itálico</em>");
    expect(html).toContain("<del>riscado</del>");
    expect(html).toContain("<blockquote>");
    expect(html).toContain("type=\"checkbox\"");
    expect(html).toContain("checked");
    expect(html).toContain("<table>");
    expect(html).toContain("<td>Controladoria</td>");
  });

  it("emite blocos de código e mermaid como segmentos próprios", () => {
    const model = buildMarkdownDocumentModel(SHOWCASE);
    const code = model.segments.find((s) => s.type === "code");
    const mermaid = model.segments.find((s) => s.type === "mermaid");

    expect(code).toMatchObject({ type: "code", lang: "sql" });
    expect(code && code.type === "code" ? code.code : "").toContain("SELECT 1;");
    expect(mermaid).toMatchObject({ type: "mermaid" });
    expect(mermaid && mermaid.type === "mermaid" ? mermaid.code : "").toContain(
      "flowchart LR",
    );
    // mermaid source nunca vaza como HTML de markdown
    const html = model.segments
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");
    expect(html).not.toContain("flowchart LR");
  });
});

describe("buildMarkdownDocumentModel — anchors e outline", () => {
  it("atribui ids estáveis e resolve duplicatas deterministicamente", () => {
    const model = buildMarkdownDocumentModel(SHOWCASE);
    expect(markdownHeadingSlug("Estado atual")).toBe("estado-atual");

    const html = model.segments
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");
    expect(html).toContain('id="estado-atual"');
    expect(html).toContain('id="estado-atual-2"');

    const outline = model.outline;
    expect(outline).toEqual([
      { id: "estado-atual", depth: 2, text: "Estado atual" },
      { id: "estado-atual-2", depth: 2, text: "Estado atual" },
    ]);
  });

  it("outline inclui apenas depth >= 2 e nunca lista o H1 duplicado", () => {
    const model = buildMarkdownDocumentModel(SHOWCASE, {
      documentTitle: "Showcase",
    });
    expect(model.outline.map((i) => i.id)).toEqual([
      "estado-atual",
      "estado-atual-2",
    ]);
    const html = model.segments
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");
    expect(html).not.toContain("<h1");
  });
});

describe("title dedupe", () => {
  it("remove o H1 inicial quando igual ao título (case/whitespace-safe)", () => {
    expect(
      isLeadingTitleDuplicate("#  Manual  de fechamento\n\nBody", "manual de fechamento"),
    ).toBe(true);
    const model = buildMarkdownDocumentModel(
      "# Manual de fechamento\n\nCorpo.",
      { documentTitle: "Manual de fechamento" },
    );
    const html = model.segments
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");
    expect(html).not.toContain("<h1");
    expect(html).toContain("Corpo.");
  });

  it("preserva H1 diferente do título do documento", () => {
    expect(
      isLeadingTitleDuplicate("# Escopo técnico\n\nBody", "Manual de fechamento"),
    ).toBe(false);
    const model = buildMarkdownDocumentModel("# Escopo técnico", {
      documentTitle: "Manual de fechamento",
    });
    const html = model.segments
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");
    expect(html).toContain('id="escopo-tecnico"');
  });

  it("não deduplica quando o primeiro bloco não é H1", () => {
    expect(
      isLeadingTitleDuplicate("Intro texto\n\n# Manual\n", "Manual"),
    ).toBe(false);
    const model = buildMarkdownDocumentModel("Intro\n\n# Doc", {
      documentTitle: "Doc",
    });
    const html = model.segments
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");
    expect(html).toContain("<h1");
  });
});

describe("security — XSS nunca executa", () => {
  it("remove script, handlers inline e URLs javascript:", () => {
    const model = buildMarkdownDocumentModel(
      [
        "<script>alert(1)</script>",
        "",
        "![img](javascript:alert(1))",
        "",
        "[click](javascript:alert(1))",
        "",
        '<img src="x" onerror="alert(1)">',
        "",
        "safe text",
      ].join("\n"),
    );
    const html = model.segments
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");
    expect(html).not.toContain("<script");
    expect(html).not.toContain("onerror");
    expect(html.toLowerCase()).not.toContain("javascript:");
    expect(html).toContain("safe text");
  });

  it("links http externos ganham rel/target seguros", () => {
    const model = buildMarkdownDocumentModel("[site](https://example.com)");
    const html = model.segments
      .map((s) => (s.type === "markdown" ? s.html : ""))
      .join("\n");
    expect(html).toContain('rel="noopener noreferrer"');
    expect(html).toContain('target="_blank"');
  });
});

describe("edge cases", () => {
  it("documento vazio não produz segmentos nem outline", () => {
    const model = buildMarkdownDocumentModel("");
    expect(model.segments).toEqual([]);
    expect(model.outline).toEqual([]);
  });

  it("documento só com mermaid não quebra", () => {
    const model = buildMarkdownDocumentModel("```mermaid\nflowchart TD\n  A-->B\n```");
    expect(model.segments).toEqual([
      { type: "mermaid", code: "flowchart TD\n  A-->B" },
    ]);
  });
});
