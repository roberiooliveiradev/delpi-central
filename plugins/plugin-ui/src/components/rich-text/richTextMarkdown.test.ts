import { describe, expect, it } from "vitest";

import { messageBodyHtmlFromMarkdown } from "../collaboration/messageThreadMarkdown";
import {
  clipboardHasUsefulHtml,
  clipboardLooksLikeMarkdown,
  markdownToRichTextHtml,
  normalizeRichTextHtmlForMarkdown,
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
    expect(clipboardHasUsefulHtml("<p>Olá</p>")).toBe(true);
    expect(clipboardHasUsefulHtml("<html><body>texto</body></html>")).toBe(false);
    expect(clipboardHasUsefulHtml("")).toBe(false);
  });
});

describe("normalizeRichTextHtmlForMarkdown", () => {
  it("envolve pre solto em code e troca br por newline", () => {
    const out = normalizeRichTextHtmlForMarkdown("<pre>a<br>b</pre>");
    expect(out.toLowerCase()).toMatch(/<pre><code>/);
    expect(out).toContain("a\nb");
    expect(out.toLowerCase()).not.toContain("<br");
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

  it("preserva span de font-size no round-trip markdown", () => {
    const md = richTextHtmlToMarkdown(
      '<p><span style="font-size:18px">hi</span></p>',
    );
    expect(md).toMatch(/font-size:\s*18px/);
    expect(markdownToRichTextHtml(md)).toMatch(/font-size:\s*18px/);
  });

  it("preserva sublinhado <u> no round-trip markdown", () => {
    const md = richTextHtmlToMarkdown("<p><u>hi</u></p>");
    expect(md).toContain("<u>hi</u>");
    expect(markdownToRichTextHtml(md)).toContain("<u>");
  });

  it("vazio vira parágrafo mínimo / string vazia", () => {
    expect(markdownToRichTextHtml("")).toBe("<p></p>");
    expect(richTextHtmlToMarkdown("<p></p>")).toBe("");
  });

  it("round-trip pre>code com newlines reais preserva fence e linhas", () => {
    const html =
      "<pre><code>Opção 3: Mais qualidade.\nMais qualidade.\nMais qualidade.</code></pre>";
    const md = richTextHtmlToMarkdown(html);
    expect(md).toMatch(/```[\s\S]*Opção 3: Mais qualidade\./);
    expect(md).toContain("Mais qualidade.");
    const back = markdownToRichTextHtml(md);
    expect(back.toLowerCase()).toMatch(/<pre\b/);
    expect(back.toLowerCase()).toMatch(/<code\b/);
    expect(back).toContain("Mais qualidade.");
  });

  it("pre>code com <br> internos vira fence com newlines", () => {
    const html = "<pre><code>linha1<br>linha2<br/>linha3</code></pre>";
    const md = richTextHtmlToMarkdown(html);
    expect(md).toMatch(/```/);
    expect(md).toContain("linha1");
    expect(md).toContain("linha2");
    expect(md).toContain("linha3");
    const back = markdownToRichTextHtml(md);
    expect(back.toLowerCase()).toMatch(/<pre\b/);
    expect(back.toLowerCase()).toMatch(/<code\b/);
    expect(back).toContain("linha1");
    expect(back).toContain("linha3");
  });

  it("pre solto normaliza para fence e volta com pre+code", () => {
    const md = richTextHtmlToMarkdown("<pre>solto\nbloco</pre>");
    expect(md).toMatch(/```[\s\S]*solto/);
    const back = markdownToRichTextHtml(md);
    expect(back.toLowerCase()).toMatch(/<pre\b/);
    expect(back.toLowerCase()).toMatch(/<code\b/);
    expect(back).toContain("solto");
  });

  it("preserva code inline, quote, listas e ênfase no round-trip", () => {
    const html = [
      "<p>inline <code>x</code> e <strong>b</strong> <em>i</em> <s>s</s> <u>u</u></p>",
      "<blockquote><p>citação</p></blockquote>",
      "<ul><li>um</li><li>dois</li></ul>",
    ].join("");
    const md = richTextHtmlToMarkdown(html);
    expect(md).toContain("`x`");
    expect(md).toMatch(/\*\*b\*\*/);
    expect(md).toMatch(/(^|\n)>\s*citação/m);
    expect(md).toMatch(/[-*]\s+um/);
    const back = markdownToRichTextHtml(md);
    expect(back.toLowerCase()).toMatch(/<code\b/);
    expect(back.toLowerCase()).toMatch(/<blockquote\b/);
    expect(back.toLowerCase()).toMatch(/<ul\b/);
    expect(back.toLowerCase()).toMatch(/<(strong|b)\b/);
  });

  it("fixture Opção 3 com div/br no pre ainda fecha fence na bolha", () => {
    const composerHtml =
      "<pre><code>Opção 3: Mais qualidade.<br><div>Mais qualidade.</div>Mais qualidade.</code></pre>";
    const md = richTextHtmlToMarkdown(composerHtml);
    expect(md).toMatch(/```/);
    const bubble = messageBodyHtmlFromMarkdown(md);
    expect(bubble.toLowerCase()).toMatch(/<pre\b/);
    expect(bubble.toLowerCase()).toMatch(/<code\b/);
    expect(bubble).toContain("Mais qualidade.");
  });

  it("round-trip attachment:pending e attachment:uuid", () => {
    const md =
      "antes\n\n![a](attachment:pending:abc123)\n\nmeio\n\n![b](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)\n\ndepois";
    const html = markdownToRichTextHtml(md);
    expect(html).toContain("data-attachment-pending=\"abc123\"");
    expect(html).toContain("data-attachment-id=\"aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee\"");
    expect(html).toContain("delpi-ui-mention-composer__inline-image");
    expect(html).toContain("<span");
    expect(html).not.toContain("<figure");
    const back = richTextHtmlToMarkdown(html);
    expect(back).toContain("![a](attachment:pending:abc123)");
    expect(back).toContain("![b](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)");
  });

  it("imagem no mesmo parágrafo + text-align no p (modelo Word)", () => {
    const md = 'ola ![x](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee) fim';
    const html = markdownToRichTextHtml(md);
    expect(html).toMatch(/<p[^>]*>.*ola.*span.*fim/i);
    expect(html).not.toContain("<figure");
    const centered = richTextHtmlToMarkdown(
      '<p style="text-align:center">ola <span class="delpi-ui-mention-composer__inline-image" contenteditable="false"><img alt="x" data-attachment-href="attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" data-attachment-id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" /></span> fim</p>',
    );
    expect(centered).toContain('style="text-align:center"');
    expect(centered).toContain(
      "![x](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)",
    );
    expect(centered).not.toMatch(/align=center/);
  });

  it("title align legado vira text-align no p no enhance", () => {
    const html = markdownToRichTextHtml(
      '![shot](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee "align=center")',
    );
    expect(html).toMatch(/text-align:\s*center/i);
    expect(html).not.toMatch(/data-align=/);
    const back = richTextHtmlToMarkdown(html);
    expect(back).toContain("![shot](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)");
    expect(back).not.toMatch(/"align=/);
  });
});
