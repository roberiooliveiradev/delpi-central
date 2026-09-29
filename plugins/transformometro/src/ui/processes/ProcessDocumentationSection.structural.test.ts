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
});
