import { describe, expect, it } from "vitest";

import { applyMarkdownToolbarAction } from "./processDocumentEditor";

describe("applyMarkdownToolbarAction", () => {
  it("envolve seleção em negrito e mantém a seleção interna", () => {
    const result = applyMarkdownToolbarAction("hello world", 6, 11, "bold");
    expect(result.next).toBe("hello **world**");
    expect(result.next.slice(result.selectionStart, result.selectionEnd)).toBe(
      "world",
    );
  });

  it("usa placeholder quando não há seleção", () => {
    const result = applyMarkdownToolbarAction("", 0, 0, "italic");
    expect(result.next).toBe("*texto em itálico*");
  });

  it("prefixa linhas para heading/lista/checklist/citação", () => {
    expect(
      applyMarkdownToolbarAction("título", 0, 0, "heading").next,
    ).toBe("## título");
    expect(
      applyMarkdownToolbarAction("a\nb", 0, 3, "list").next,
    ).toBe("- a\n- b");
    expect(
      applyMarkdownToolbarAction("item", 0, 0, "checklist").next,
    ).toBe("- [ ] item");
    expect(applyMarkdownToolbarAction("nota", 0, 0, "quote").next).toBe("> nota");
  });

  it("insere template de tabela cercado por linhas em branco", () => {
    const result = applyMarkdownToolbarAction("antes", 5, 5, "table");
    expect(result.next).toContain("\n\n| Coluna | Coluna |");
  });

  it("insere fence mermaid sem duplicar blocos", () => {
    const result = applyMarkdownToolbarAction("", 0, 0, "mermaid");
    expect(result.next).toContain("```mermaid");
    expect(result.next).toContain("flowchart TD");
  });

  it("link usa markup [texto](url)", () => {
    const result = applyMarkdownToolbarAction("", 0, 0, "link");
    expect(result.next).toBe("[texto do link](https://)");
  });
});
