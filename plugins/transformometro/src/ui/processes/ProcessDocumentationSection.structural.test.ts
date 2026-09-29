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

  it("reader desktop usa scroller interno do documento", () => {
    expect(section).toMatch(/documentScrollRef/);
    expect(section).toMatch(/tm-process-documentation__document-scroll/);
    // O observer aponta para o scroller interno, não para o `.content` do portal.
    expect(section).toMatch(/documentScrollRef\.current\s*\?\?/);
    // scrollToHeading calcula offset relativo ao scroller interno.
    expect(section).toMatch(/scroller\.scrollTo\(\{\s*top,/);
    // O header do artigo fica fora do scroller (título/meta/ações persistentes).
    const articleStart = section.indexOf("__article-header");
    const scrollStart = section.indexOf("__document-scroll");
    expect(scrollStart).toBeGreaterThan(articleStart);
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

  it("scroll interno só em desktop e sem nested-scroll em mobile", () => {
    const internalScroll = css.match(
      /@media \(min-width: 900px\)\{[^}]*tm-process-documentation__document-scroll\{[^}]*overflow-y:\s*auto/,
    );
    expect(internalScroll).not.toBeNull();
    // Sem overflow obrigatório no bloco base (mobile rola com a página).
    const base = css.match(/tm-process-documentation__document-scroll\{[^}]*\}/);
    expect(base?.[0]).not.toMatch(/overflow-y:\s*auto/);
  });

  it("busca da biblioteca é expandida; busca do rail permanece compacta", () => {
    const librarySearch = css.match(
      /__library-head\s*\.tm-process-documentation__rail-search\{[^}]*\}/,
    );
    expect(librarySearch?.[0]).toMatch(/flex:\s*1 1 30rem/);
    expect(librarySearch?.[0]).toMatch(/max-width:\s*38rem/);
  });

  it("headings dentro do scroller interno não usam o offset da top bar", () => {
    const inner = css.match(
      /__document-scroll\s*\.delpi-ui-md-doc\s*:is\(h1, h2, h3, h4, h5, h6\)\[id\]\{[^}]*scroll-margin-top:\s*0\.75rem/,
    );
    expect(inner).not.toBeNull();
  });
});
