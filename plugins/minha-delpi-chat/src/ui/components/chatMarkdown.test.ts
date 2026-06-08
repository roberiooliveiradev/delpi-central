import { describe, expect, it } from "vitest";

import {
  applySoftLineBreaks,
  hasMarkdownSyntax,
  prepareMarkdownContent,
} from "./chatMarkdown";

describe("chatMarkdown", () => {
  it("detecta negrito e cabeçalhos", () => {
    expect(hasMarkdownSyntax("Olá! Sou o **Agente Minha DELPI**.")).toBe(true);
    expect(hasMarkdownSyntax("Olá! Sou o **Agente")).toBe(true);
    expect(hasMarkdownSyntax("### Título")).toBe(true);
    expect(hasMarkdownSyntax("Texto simples sem formatação.")).toBe(false);
  });

  it("remove escapes de asterisco", () => {
    expect(prepareMarkdownContent("Olá \\*\\*Agente\\*\\*")).toBe("Olá **Agente**");
  });
});

describe("applySoftLineBreaks", () => {
  it("converte quebra simples em hard break", () => {
    expect(applySoftLineBreaks("linha 1\nlinha 2")).toBe("linha 1  \nlinha 2");
  });

  it("preserva parágrafos (quebra dupla)", () => {
    expect(applySoftLineBreaks("p1\n\np2")).toBe("p1\n\np2");
  });

  it("não altera quebras dentro de bloco de código cercado", () => {
    const input = "antes\n```sql\nSELECT 1\nFROM x\n```\ndepois";
    const output = applySoftLineBreaks(input);
    expect(output).toContain("```sql\nSELECT 1\nFROM x\n```");
    expect(output.startsWith("antes")).toBe(true);
  });
});
