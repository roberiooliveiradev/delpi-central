import { describe, expect, it } from "vitest";

import {
  enrichMessageHtmlMentions,
  markdownToPlainPreview,
  messageBodyHtmlFromMarkdown,
  messageBodyHtmlIsPlainParagraph,
} from "./messageThreadMarkdown";

describe("markdownToPlainPreview", () => {
  it("remove negrito, código e links", () => {
    expect(markdownToPlainPreview("**oi** e `x` e [a](https://ex.com)")).toBe("oi e x e a");
  });

  it("trunca com reticências", () => {
    const long = "a".repeat(200);
    const preview = markdownToPlainPreview(long, 20);
    expect(preview.endsWith("…")).toBe(true);
    expect(preview.length).toBeLessThanOrEqual(21);
  });

  it("esvazia markdown vazio", () => {
    expect(markdownToPlainPreview("   ")).toBe("");
  });
});

describe("messageBodyHtmlFromMarkdown", () => {
  it("gera strong e code sanitizados", () => {
    const html = messageBodyHtmlFromMarkdown("**forte** e `code`");
    expect(html.toLowerCase()).toMatch(/<(strong|b)\b/);
    expect(html.toLowerCase()).toMatch(/<code\b/);
    expect(html.toLowerCase()).not.toContain("<script");
  });

  it("fence markdown vira pre>code na bolha", () => {
    const html = messageBodyHtmlFromMarkdown("```\nMais qualidade.\n```");
    expect(html.toLowerCase()).toMatch(/<pre\b/);
    expect(html.toLowerCase()).toMatch(/<code\b/);
    expect(html).toContain("Mais qualidade.");
  });

  it("enriquece menções com chip", () => {
    const html = messageBodyHtmlFromMarkdown("Oi @Ana", [
      { kind: "user", label: "Ana" },
    ]);
    expect(html).toMatch(/delpi-ui-mention-text__chip/);
    expect(html).toContain("Ana");
  });

  it("detecta parágrafo plano vs rico", () => {
    expect(messageBodyHtmlIsPlainParagraph("<p>oi</p>")).toBe(true);
    expect(messageBodyHtmlIsPlainParagraph("<p><strong>x</strong></p>")).toBe(false);
    expect(messageBodyHtmlIsPlainParagraph("<ul><li>a</li></ul>")).toBe(false);
  });
});

describe("enrichMessageHtmlMentions", () => {
  it("não altera código", () => {
    const html = enrichMessageHtmlMentions(
      "<p><code>@Ana</code></p>",
      [{ kind: "user", label: "Ana" }],
      "chip",
    );
    expect(html).toContain("<code>@Ana</code>");
    expect(html).not.toContain("class=\"chip\"");
  });
});
