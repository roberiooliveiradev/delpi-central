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

  it("vence font-size aninhado de HTML colado (Word)", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML =
      '<p><span style="font-size:11pt">texto colado</span></p>';
    document.body.appendChild(editor);

    const text = editor.querySelector("span")!.firstChild as Text;
    const range = document.createRange();
    range.setStart(text, 0);
    range.setEnd(text, text.textContent!.length);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);

    applyRichTextFontSize(editor, 24);

    const inner = editor.querySelector("span");
    expect(inner?.style.fontSize).toBe("24px");
    expect(editor.innerHTML).toContain("24px");
    expect(editor.innerHTML).not.toContain("11pt");

    document.body.removeChild(editor);
  });

  it("com caret colapsado aplica no bloco (p/h2), não só no próximo digitar", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>parágrafo</p>";
    document.body.appendChild(editor);

    const text = editor.querySelector("p")!.firstChild as Text;
    const range = document.createRange();
    range.setStart(text, 3);
    range.collapse(true);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);

    applyRichTextFontSize(editor, 20);

    const paragraph = editor.querySelector("p");
    expect(paragraph?.style.fontSize).toBe("20px");

    document.body.removeChild(editor);
  });

  it("aplica font-size inline em heading (vence CSS do editor)", () => {
    const editor = document.createElement("div");
    editor.className = "delpi-ui-rich-text__editor";
    editor.contentEditable = "true";
    editor.innerHTML = "<h2>Título da ata</h2>";
    document.body.appendChild(editor);

    const heading = editor.querySelector("h2")!;
    const text = heading.firstChild as Text;
    const range = document.createRange();
    range.selectNodeContents(heading);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);

    applyRichTextFontSize(editor, 28);

    expect(heading.style.fontSize).toBe("28px");
    // seleção de bloco inteiro não deve criar span wrapper inválido
    expect(editor.querySelector("span > h2")).toBeNull();

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
