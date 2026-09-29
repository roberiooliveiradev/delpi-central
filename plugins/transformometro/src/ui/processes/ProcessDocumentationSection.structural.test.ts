import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

const section = readFileSync(
  join(root, "ui/processes/ProcessDocumentationSection.tsx"),
  "utf8",
);

describe("Process Documentation wiring", () => {
  it("expõe seção Documentação no ProcessDetailPage", () => {
    const page = readFileSync(join(root, "ui/pages/ProcessDetailPage.tsx"), "utf8");
    expect(page).toMatch(/ProcessDocumentationSection/);
    expect(page).toMatch(/sectionId="documentacao"/);
  });

  it("não importa Meeting Minutes na seção de documentação", () => {
    expect(section).not.toMatch(/meeting.?minute|MeetingMinute|tm_meeting/i);
    expect(section).not.toMatch(/importar ata|atas\b/i);
  });

  it("usa o renderer documental compartilhado (não o de mensagens/chat)", () => {
    expect(section).toMatch(/MarkdownDocumentView/);
    expect(section).toMatch(/buildMarkdownDocumentModel/);
    expect(section).not.toMatch(/MessageBodyReadonly/);
    // Nunca importa renderer de outro MFE (coupling proibido).
    expect(section).not.toMatch(/minha-delpi-chat|ChatMarkdown|ChatMermaidBlock/);
    // Sem renderizador Mermaid próprio — primitive canônica do plugin-ui.
    expect(section).not.toMatch(/from ["']mermaid["']/);
  });

  it("assina a sala realtime do processo para invalidação de documentos", () => {
    expect(section).toMatch(/useTransformometroEntityWatch/);
    expect(section).toMatch(/entityType:\s*"processo"/);
    expect(section).toMatch(/resolveProcessDocumentEventIntent/);
  });

  it("registra guarda de alterações não salvas", () => {
    expect(section).toMatch(/useUnsavedChangesGuard/);
  });

  it("library mode full-width quando nenhum documento está selecionado", () => {
    expect(section).toMatch(/libraryMode\s*=\s*!editing\s*&&\s*selectedId\s*==\s*null/);
    expect(section).toMatch(/tm-process-documentation__library\b/);
    expect(section).toMatch(/tm-process-documentation__library-row\b/);
    // Não monta reader fantasma nem outline no modo biblioteca.
    expect(section).toMatch(/libraryMode\s*\?\s*\(/);
    // O antigo hint de "selecione um documento" não existe mais.
    expect(section).not.toMatch(/Selecione um documento na lista/);
  });

  it("links internos do Markdown delegam ao scroll local e não quebram a rota", () => {
    expect(section).toMatch(/onInternalAnchorNavigate=\{scrollToHeading\}/);
    // Nenhum link interno deve reescrever o hash #documentacao/{id}.
    expect(section).not.toMatch(/location\.hash\s*=\s*["'`]?#/);
  });

  it("outline marca a seção ativa via IntersectionObserver", () => {
    expect(section).toMatch(/IntersectionObserver/);
    expect(section).toMatch(/activeHeadingId/);
    expect(section).toMatch(/aria-current=\{/);
  });
});

describe("Process Documentation layout/sticky CSS contract", () => {
  const css = readFileSync(join(root, "index.css"), "utf8");

  it("usa um único offset canônico para rail, outline e scroll-margin", () => {
    expect(css).toMatch(/--tm-documentation-sticky-offset/);
    expect(css).toMatch(/scroll-margin-top:\s*calc\(var\(--tm-documentation-sticky-offset\)/);
    const stickyTops = css.match(/top:\s*calc\(var\(--tm-documentation-sticky-offset\)/g) ?? [];
    // rail + outline compartilham o mesmo offset medido.
    expect(stickyTops.length).toBeGreaterThanOrEqual(2);
    // Nenhum sticky solto com número mágico legado.
    expect(css).not.toMatch(/tm-process-documentation__outline\{[^}]*top:\s*1rem/);
  });

  it("reader de 3 colunas só existe acima de 1440px", () => {
    const threeCol = css.match(
      /@media \(min-width: 1440px\)\{[^}]*tm-process-documentation__layout\.has-outline/,
    );
    expect(threeCol).not.toBeNull();
    expect(css).toMatch(/@media \(max-width: 899\.98px\)/);
  });
});
