// @vitest-environment jsdom
import { describe, expect, it } from "vitest";

import { prettyPrintRichTextHtml, stripDangerousRichTextTags } from "./richTextHtmlFormat";

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
});
