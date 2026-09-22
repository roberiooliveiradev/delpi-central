// @vitest-environment jsdom
import { describe, expect, it } from "vitest";

import { applyFormat, formatIntent, resolveFormatTarget } from "./formatApply";
import { insertRichTextInlineImageAtCaret } from "./richTextInlineImage";

function selectText(editor: HTMLElement, start: number, end: number) {
  const text = editor.querySelector("p")!.firstChild as Text;
  const range = document.createRange();
  range.setStart(text, start);
  range.setEnd(text, end);
  const selection = window.getSelection()!;
  selection.removeAllRanges();
  selection.addRange(range);
  return range;
}

function placeCaret(editor: HTMLElement, offset: number) {
  const text = editor.querySelector("p")!.firstChild as Text;
  const range = document.createRange();
  range.setStart(text, offset);
  range.collapse(true);
  const selection = window.getSelection()!;
  selection.removeAllRanges();
  selection.addRange(range);
  return range;
}

describe("applyFormat", () => {
  it("positive: seleção parcial + fontSize só no trecho", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>abcdef</p>";
    document.body.appendChild(editor);
    selectText(editor, 1, 4);

    applyFormat(editor, formatIntent.fontSize(24));

    const span = editor.querySelector("span");
    expect(span?.style.fontSize).toBe("24px");
    expect(span?.textContent).toBe("bcd");
    // trecho formatado; texto fora do span permanece no <p> sem herdar via bloco
    expect(editor.textContent).toBe("abcdef");
    expect((editor.querySelector("p") as HTMLElement).style.fontSize).toBe("");

    document.body.removeChild(editor);
  });

  it("sibling: seleção parcial + fontName só no trecho", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>abcdef</p>";
    document.body.appendChild(editor);
    selectText(editor, 1, 4);

    applyFormat(editor, formatIntent.fontName("Georgia, serif"));

    const span = editor.querySelector("span");
    expect(span?.style.fontFamily).toContain("Georgia");
    expect(span?.textContent).toBe("bcd");
    expect((editor.querySelector("p") as HTMLElement).style.fontFamily).toBe("");

    document.body.removeChild(editor);
  });

  it("sibling: seleção parcial + foreColor só no trecho", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>abcdef</p>";
    document.body.appendChild(editor);
    selectText(editor, 1, 4);

    applyFormat(editor, formatIntent.foreColor("#00aa00"));

    const span = editor.querySelector("span");
    expect(span?.style.color).toBe("rgb(0, 170, 0)");
    expect(span?.textContent).toBe("bcd");
    expect((editor.querySelector("p") as HTMLElement).style.color).toBe("");

    document.body.removeChild(editor);
  });

  it("sibling: seleção parcial + align afeta o bloco", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>abcdef</p>";
    document.body.appendChild(editor);
    selectText(editor, 1, 4);

    const target = resolveFormatTarget(editor, formatIntent.align("center"));
    expect(target.type).toBe("block");
    applyFormat(editor, formatIntent.align("center"));
    expect((editor.querySelector("p") as HTMLElement).style.textAlign).toBe("center");

    document.body.removeChild(editor);
  });

  it("negative: caret + fontSize não stamp no parágrafo", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>abcdef</p>";
    document.body.appendChild(editor);
    placeCaret(editor, 3);

    applyFormat(editor, formatIntent.fontSize(20));

    expect((editor.querySelector("p") as HTMLElement).style.fontSize).toBe("");
    expect(editor.querySelector("span")?.style.fontSize).toBe("20px");

    document.body.removeChild(editor);
  });
});

describe("insertRichTextInlineImageAtCaret", () => {
  it("insere imagem no caret dentro do mesmo parágrafo quando há texto depois", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>antesdepois</p>";
    document.body.appendChild(editor);
    placeCaret(editor, 5);

    const span = insertRichTextInlineImageAtCaret(editor, {
      src: "blob:preview",
      pendingId: "p1",
      alt: "shot",
    });

    expect(span).not.toBeNull();
    const p = editor.querySelector("p")!;
    expect(p.querySelector("img")?.getAttribute("data-attachment-pending")).toBe("p1");
    expect(p.textContent).toContain("antes");
    expect(p.textContent).toContain("depois");
    expect(editor.querySelectorAll("p")).toHaveLength(1);

    document.body.removeChild(editor);
  });

  it("irmão: imagem sozinha abre parágrafo abaixo para escrita", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p><br></p>";
    document.body.appendChild(editor);
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(editor.querySelector("p")!);
    range.collapse(true);
    selection?.removeAllRanges();
    selection?.addRange(range);

    insertRichTextInlineImageAtCaret(editor, {
      src: "blob:preview",
      pendingId: "solo",
      alt: "shot",
    });

    const paragraphs = editor.querySelectorAll("p");
    expect(paragraphs.length).toBeGreaterThanOrEqual(2);
    expect(paragraphs[0]?.querySelector("img")).not.toBeNull();

    document.body.removeChild(editor);
  });
});
