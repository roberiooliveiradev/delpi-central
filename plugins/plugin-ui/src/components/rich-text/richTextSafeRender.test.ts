import { describe, expect, it } from "vitest";

import { stripDangerousRichTextTags } from "./richTextHtmlFormat";

describe("stripDangerousRichTextTags markdown security", () => {
  it("remove script e raw HTML perigoso", () => {
    const cleaned = stripDangerousRichTextTags(
      '<p>Olá</p><script>alert(1)</script><p><strong>ok</strong></p><img src="x" onerror="alert(1)">',
    );
    expect(cleaned.toLowerCase()).not.toContain("<script");
    expect(cleaned.toLowerCase()).not.toContain("onerror");
    expect(cleaned).toContain("<strong>");
  });

  it("bloqueia javascript: em links", () => {
    const cleaned = stripDangerousRichTextTags(
      '<p><a href="javascript:alert(1)">clique</a></p>',
    );
    expect(cleaned.toLowerCase()).not.toContain("javascript:");
  });

  it("mantém Markdown seguro renderizado e reforça rel em links externos", () => {
    const cleaned = stripDangerousRichTextTags(
      '<h2>Título</h2><ul><li>item</li></ul><p><a href="https://example.com">site</a></p>',
    );
    expect(cleaned).toContain("<h2>");
    expect(cleaned).toContain("<ul>");
    expect(cleaned).toContain('href="https://example.com"');
    expect(cleaned).toMatch(/rel="[^"]*noopener/);
  });

  it("remove handlers e urls perigosas", () => {
    const cleaned = stripDangerousRichTextTags(
      '<p><a href="javascript:alert(1)">x</a><img src="x" onerror="alert(1)"></p>',
    );
    expect(cleaned.toLowerCase()).not.toContain("javascript:");
    expect(cleaned.toLowerCase()).not.toContain("onerror");
  });
});
