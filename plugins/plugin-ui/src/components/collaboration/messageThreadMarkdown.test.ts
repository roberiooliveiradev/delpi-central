import { describe, expect, it } from "vitest";

import {
  enrichGlpiUserMentionSpans,
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
    expect(
      messageBodyHtmlIsPlainParagraph(
        '<p><span data-user-mention="true" data-user-id="12">@Ana</span></p>',
      ),
    ).toBe(false);
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
    expect(html).not.toContain('class="chip"');
  });
});

describe("enrichGlpiUserMentionSpans", () => {
  it("converte span GLPI em chip preservando data-user-id", () => {
    const html = enrichGlpiUserMentionSpans(
      '<p>Oi <span data-user-mention="true" data-user-id="123">@Ana</span></p>',
      "delpi-ui-mention-text__chip",
    );
    expect(html).toContain('data-user-id="123"');
    expect(html).toContain('data-user-mention="true"');
    expect(html).toContain('data-mention-kind="user"');
    expect(html).toContain("delpi-ui-mention-text__chip");
    expect(html).toContain("delpi-ui-mention-text__chip-label");
    expect(html).toContain("Ana");
    expect(html).not.toContain(">@Ana<");
  });

  it("irmão: span sem menção GLPI permanece intacto", () => {
    const source = '<p><span class="note">aviso</span></p>';
    expect(enrichGlpiUserMentionSpans(source, "chip")).toBe(source);
  });

  it("negativo: não inventa id a partir de @nome em texto", () => {
    const html = enrichGlpiUserMentionSpans("<p>Oi @Ana</p>", "chip");
    expect(html).toBe("<p>Oi @Ana</p>");
    expect(html).not.toContain("data-user-id");
    expect(html).not.toContain('class="chip"');
  });

  it("ignora data-user-id não numérico", () => {
    const source =
      '<p><span data-user-mention="true" data-user-id="abc">@X</span></p>';
    const html = enrichGlpiUserMentionSpans(source, "chip");
    expect(html).toContain('data-user-id="abc"');
    expect(html).not.toContain('class="chip"');
  });
});
