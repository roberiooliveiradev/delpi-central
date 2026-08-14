import { describe, expect, it } from "vitest";

import {
  clipboardHasUsefulHtml,
  clipboardLooksLikeMarkdown,
  markdownToRichTextHtml,
  richTextHtmlToMarkdown,
} from "./richTextMarkdown";

describe("clipboardLooksLikeMarkdown", () => {
  it("aceita títulos, listas e ênfase GFM", () => {
    expect(clipboardLooksLikeMarkdown("# Título\n\n- item")).toBe(true);
    expect(clipboardLooksLikeMarkdown("Texto com **negrito** e mais")).toBe(true);
    expect(clipboardLooksLikeMarkdown("```\ncode\n```")).toBe(true);
  });

  it("rejeita prosa simples e HTML", () => {
    expect(clipboardLooksLikeMarkdown("Apenas um parágrafo sem marcações.")).toBe(false);
    expect(clipboardLooksLikeMarkdown("<p>Olá</p>")).toBe(false);
  });
});

describe("clipboardHasUsefulHtml", () => {
  it("detecta HTML rico e ignora envelope vazio", () => {
    expect(clipboardHasUsefulHtml('<p>Olá</p>')).toBe(true);
    expect(clipboardHasUsefulHtml("<html><body>texto</body></html>")).toBe(false);
    expect(clipboardHasUsefulHtml("")).toBe(false);
  });
});

describe("markdownToRichTextHtml / richTextHtmlToMarkdown", () => {
  it("converte Markdown GFM para HTML allowlist-friendly", () => {
    const html = markdownToRichTextHtml("## Título\n\n**forte** e *itálico*\n\n- um\n- dois");
    expect(html).toContain("<h2>");
    expect(html).toContain("<strong>");
    expect(html).toContain("<em>");
    expect(html).toContain("<ul>");
    expect(html.toLowerCase()).not.toContain("<script");
  });

  it("converte tabela GFM", () => {
    const html = markdownToRichTextHtml("| A | B |\n| - | - |\n| 1 | 2 |");
    expect(html).toContain("<table>");
    expect(html).toContain("<th>");
  });

  it("round-trip básico HTML → MD → HTML preserva ênfase", () => {
    const md = richTextHtmlToMarkdown("<p><strong>hi</strong></p>");
    expect(md).toContain("**hi**");
    const back = markdownToRichTextHtml(md);
    expect(back).toContain("<strong>");
  });

  it("vazio vira parágrafo mínimo / string vazia", () => {
    expect(markdownToRichTextHtml("")).toBe("<p></p>");
    expect(richTextHtmlToMarkdown("<p></p>")).toBe("");
  });
});
