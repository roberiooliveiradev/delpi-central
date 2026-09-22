// @vitest-environment jsdom
import { describe, expect, it } from "vitest";

import {
  prettyPrintRichTextHtml,
  stripDangerousRichTextTags,
  wrapOrphanRichTextNodes,
} from "./richTextHtmlFormat";

describe("prettyPrintRichTextHtml", () => {
  it("indenta blocos e preserva conteúdo", () => {
    const out = prettyPrintRichTextHtml("<p>Olá</p><p><strong>mundo</strong></p>");
    expect(out).toContain("<p>Olá</p>");
    expect(out).toContain("<strong>mundo</strong>");
    expect(out.split("\n").length).toBeGreaterThan(1);
  });

  it("indenta tabelas", () => {
    const out = prettyPrintRichTextHtml(
      '<table class="delpi-ui-rich-text-table"><tbody><tr><th>A</th><td>B</td></tr></tbody></table>',
    );
    expect(out).toContain("<table");
    expect(out).toContain("<tbody>");
    expect(out).toContain("<th>A</th>");
    expect(out.split("\n").length).toBeGreaterThan(3);
  });

  it("fallback para HTML vazio", () => {
    expect(prettyPrintRichTextHtml("")).toBe("<p></p>");
  });
});

describe("stripDangerousRichTextTags", () => {
  it("remove script e style", () => {
    const cleaned = stripDangerousRichTextTags(
      '<p>ok</p><script>alert(1)</script><style>body{}</style><table><tr><td>A</td></tr></table>',
    );
    expect(cleaned).toContain("<p>ok</p>");
    expect(cleaned).toContain("<table");
    expect(cleaned.toLowerCase()).not.toContain("<script");
    expect(cleaned.toLowerCase()).not.toContain("<style");
  });

  it("remove iframe e form", () => {
    const cleaned = stripDangerousRichTextTags(
      '<p>x</p><iframe src="https://evil"></iframe><form action="/"></form>',
    );
    expect(cleaned).toContain("<p>x</p>");
    expect(cleaned.toLowerCase()).not.toContain("<iframe");
    expect(cleaned.toLowerCase()).not.toContain("<form");
  });

  it("envolve texto solto em parágrafo ao sanitizar", () => {
    const cleaned = stripDangerousRichTextTags("<p></p>\nsdsdsdsdsd\n<hr>");
    expect(cleaned).toMatch(/<p[^>]*>\s*sdsdsdsdsd\s*<\/p>/i);
    expect(cleaned.toLowerCase()).toContain("<hr");
  });

  it("preserva <hr> entre blocos", () => {
    const cleaned = stripDangerousRichTextTags("<p>a</p><hr><p>b</p>");
    expect(cleaned.toLowerCase()).toContain("<hr");
    expect(cleaned).toContain("<p>a</p>");
    expect(cleaned).toContain("<p>b</p>");
  });

  it("preserva blob: em src de imagem (preview autenticado)", () => {
    const cleaned = stripDangerousRichTextTags(
      '<p><img src="blob:http://localhost/uuid" alt="foto" data-attachment-id="12" /></p>',
    );
    expect(cleaned).toContain('src="blob:http://localhost/uuid"');
    expect(cleaned).toContain('data-attachment-id="12"');
  });

  it("remove javascript: em src", () => {
    const cleaned = stripDangerousRichTextTags('<p><img src="javascript:alert(1)" alt="x" /></p>');
    expect(cleaned.toLowerCase()).not.toContain("javascript:");
  });
});

describe("wrapOrphanRichTextNodes", () => {
  it("não altera HTML já em blocos", () => {
    expect(wrapOrphanRichTextNodes("<p>ok</p>")).toBe("<p>ok</p>");
  });

  it("envolve texto solto de nível raiz", () => {
    expect(wrapOrphanRichTextNodes("<p></p>texto solto")).toContain("<p>texto solto</p>");
  });
});
