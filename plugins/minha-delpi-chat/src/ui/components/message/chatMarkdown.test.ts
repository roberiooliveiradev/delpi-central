import { describe, expect, it } from "vitest";

import {
  applySoftLineBreaks,
  hasMarkdownSyntax,
  prepareMarkdownContent,
  resolveCitationBadgeDisplay,
  stripPresentationSectionMarkers,
  tableRowsToClipboardText,
  tableRowsToGfmMarkdown,
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

  it("serializa linhas em markdown GFM para copiar como texto", () => {
    expect(
      tableRowsToGfmMarkdown([
        ["Campo", "Valor"],
        ["OPs de PA", "305"],
      ]),
    ).toBe("| Campo | Valor |\n| --- | --- |\n| OPs de PA | 305 |");
  });

  it("serializa linhas tabuladas para copiar em planilha", () => {
    expect(
      tableRowsToClipboardText([
        ["Cód.", "Qtd."],
        ["10080063", "350000"],
        ["10130006", "3104"],
      ]),
    ).toBe("Cód.\tQtd.\n10080063\t350000\n10130006\t3104");
  });

  it("remove marcadores internos de seção do stack humanizado", () => {
    const raw =
      "### Escopo\n\n<!-- section:scope -->\n\nProduto 10070012.\n\n<!-- section:highlights -->\n\n**Destaques**";

    expect(stripPresentationSectionMarkers(raw)).toBe(
      "### Escopo\n\nProduto 10070012.\n\n**Destaques**",
    );
    expect(prepareMarkdownContent(raw)).not.toContain("<!-- section:");
  });
});

describe("resolveCitationBadgeDisplay", () => {
  it("usa badge para todo link http(s) externo", () => {
    expect(
      resolveCitationBadgeDisplay(
        "https://delpi.com.br/delpi-conexoes-eletricas/",
        "https://delpi.com.br/delpi-conexoes-eletricas/",
      ),
    ).toEqual({ useBadge: true, displayLabel: "delpi.com.br" });

    expect(
      resolveCitationBadgeDisplay("https://delpi.com.br/", "https://delpi.com.br/"),
    ).toEqual({ useBadge: true, displayLabel: "delpi.com.br" });
  });

  it("preserva marcadores numéricos de citação", () => {
    expect(resolveCitationBadgeDisplay("https://example.com/a", "[1]")).toEqual({
      useBadge: true,
      displayLabel: "[1]",
    });
  });

  it("preserva rótulo curto descritivo", () => {
    expect(resolveCitationBadgeDisplay("https://delpi.com.br/", "site oficial")).toEqual({
      useBadge: true,
      displayLabel: "site oficial",
    });
  });

  it("não usa badge em links internos", () => {
    expect(resolveCitationBadgeDisplay("/docs/guia", "guia")).toEqual({
      useBadge: false,
      displayLabel: "guia",
    });
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
