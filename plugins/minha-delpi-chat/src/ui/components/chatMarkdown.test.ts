import { describe, expect, it } from "vitest";

import { hasMarkdownSyntax, prepareMarkdownContent } from "./chatMarkdown";

describe("chatMarkdown", () => {
  it("detecta negrito e cabeçalhos", () => {
    expect(hasMarkdownSyntax("Olá! Sou o **Agente Minha DELPI**.")).toBe(true);
    expect(hasMarkdownSyntax("### Título")).toBe(true);
    expect(hasMarkdownSyntax("Texto simples sem formatação.")).toBe(false);
  });

  it("remove escapes de asterisco", () => {
    expect(prepareMarkdownContent("Olá \\*\\*Agente\\*\\*")).toBe("Olá **Agente**");
  });
});
