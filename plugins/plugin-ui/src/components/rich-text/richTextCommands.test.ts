// @vitest-environment jsdom
import { describe, expect, it } from "vitest";

import {
  applyRichTextFontSize,
  normalizeRichTextLinkUrl,
  unwrapRichTextLink,
} from "./richTextCommands";
import { clampRichTextFontSize } from "./richTextConfig";
import {
  buildRichTextTableHtml,
  normalizeRichTextPastedHtml,
} from "./richTextTable";

describe("richTextConfig", () => {
  it("limita tamanho de fonte", () => {
    expect(clampRichTextFontSize(8)).toBe(10);
    expect(clampRichTextFontSize(80)).toBe(72);
    expect(clampRichTextFontSize(16.4)).toBe(16);
  });
});

describe("applyRichTextFontSize", () => {
  it("aplica tamanho em px na seleção (não usa escala legada 1–7)", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>abcdef</p>";
    document.body.appendChild(editor);

    const text = editor.querySelector("p")!.firstChild as Text;
    const range = document.createRange();
    range.setStart(text, 0);
    range.setEnd(text, 6);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);

    applyRichTextFontSize(editor, 24);

    const span = editor.querySelector("span");
    expect(span?.style.fontSize).toBe("24px");
    expect(editor.innerHTML).not.toMatch(/font\s+size=/i);

    document.body.removeChild(editor);
  });

  it("com caret colapsado cria span marcador para o próximo digitar", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>x</p>";
    document.body.appendChild(editor);

    const text = editor.querySelector("p")!.firstChild as Text;
    const range = document.createRange();
    range.setStart(text, 1);
    range.collapse(true);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);

    applyRichTextFontSize(editor, 18);

    const span = editor.querySelector("span");
    expect(span?.style.fontSize).toBe("18px");
    expect(span?.textContent).toBe("\u200B");

    document.body.removeChild(editor);
  });
});

describe("richTextTable", () => {
  it("monta tabela com cabeçalho e preset", () => {
    const html = buildRichTextTableHtml({ rows: 3, cols: 2, preset: "banded" });
    expect(html).toContain('class="delpi-ui-rich-text-table delpi-ui-rich-text-table--banded"');
    expect(html).toContain("<th>Coluna 1</th>");
    expect(html).toContain("<th>Coluna 2</th>");
    expect((html.match(/<tr>/g) || []).length).toBe(3);
  });

  it("normaliza tabela colada com classe do editor", () => {
    const normalized = normalizeRichTextPastedHtml(
      '<table><tr><td onclick="evil()">A</td><td>B</td></tr></table><script>x()</script>',
    );
    expect(normalized).toBeTruthy();
    expect(normalized).toContain("delpi-ui-rich-text-table");
    expect(normalized).not.toContain("onclick");
    expect(normalized).not.toContain("<script");
  });
});

describe("normalizeRichTextLinkUrl", () => {
  it("mantém URLs com esquema, âncoras e paths", () => {
    expect(normalizeRichTextLinkUrl("https://delpi.com.br")).toBe("https://delpi.com.br");
    expect(normalizeRichTextLinkUrl("mailto:x@delpi.com.br")).toBe("mailto:x@delpi.com.br");
    expect(normalizeRichTextLinkUrl("/apps/cipa")).toBe("/apps/cipa");
    expect(normalizeRichTextLinkUrl("#secao")).toBe("#secao");
  });

  it("completa https:// para domínio sem esquema", () => {
    expect(normalizeRichTextLinkUrl("delpi.com.br/ata")).toBe("https://delpi.com.br/ata");
  });

  it("retorna vazio para entrada em branco", () => {
    expect(normalizeRichTextLinkUrl("  ")).toBe("");
  });
});

describe("unwrapRichTextLink", () => {
  it("remove a âncora preservando o conteúdo", () => {
    const wrapper = document.createElement("p");
    wrapper.innerHTML = 'antes <a href="https://x.dev">meio <b>forte</b></a> depois';
    const anchor = wrapper.querySelector("a")!;

    unwrapRichTextLink(anchor);

    expect(wrapper.querySelector("a")).toBeNull();
    expect(wrapper.innerHTML).toBe("antes meio <b>forte</b> depois");
  });
});
