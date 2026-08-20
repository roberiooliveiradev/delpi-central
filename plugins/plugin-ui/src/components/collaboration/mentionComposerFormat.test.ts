import { describe, expect, it, vi } from "vitest";

import {
  queryComposerFormatFlags,
  toggleComposerFormat,
} from "./mentionComposerFormat";

function selectAll(editor: HTMLElement) {
  const range = document.createRange();
  range.selectNodeContents(editor);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
}

function selectTextIn(editor: HTMLElement, needle: string) {
  const walker = document.createTreeWalker(editor, NodeFilter.SHOW_TEXT);
  let node = walker.nextNode() as Text | null;
  while (node) {
    const idx = node.data.indexOf(needle);
    if (idx >= 0) {
      const range = document.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + needle.length);
      const selection = window.getSelection();
      selection?.removeAllRanges();
      selection?.addRange(range);
      return;
    }
    node = walker.nextNode() as Text | null;
  }
  throw new Error(`needle not found: ${needle}`);
}

function collapseCaretAtEnd(editor: HTMLElement) {
  const range = document.createRange();
  range.selectNodeContents(editor);
  range.collapse(false);
  const selection = window.getSelection();
  selection?.removeAllRanges();
  selection?.addRange(range);
}

describe("toggleComposerFormat", () => {
  it("liga e desliga negrito no trecho e reporta o estado", () => {
    const editor = document.createElement("div");
    editor.textContent = "dsdsd";
    document.body.appendChild(editor);
    selectAll(editor);
    toggleComposerFormat(editor, "bold");
    expect(editor.innerHTML.toLowerCase()).toMatch(/<(strong|b)\b/);
    selectAll(editor);
    expect(queryComposerFormatFlags(editor).bold).toBe(true);
    toggleComposerFormat(editor, "bold");
    expect(editor.innerHTML.toLowerCase()).not.toMatch(/<(strong|b)\b/);
    expect(queryComposerFormatFlags(editor).bold).toBe(false);
    editor.remove();
  });

  it("remove negrito só no trecho parcial dentro de strong maior (Word)", () => {
    document.execCommand = vi.fn().mockReturnValue(true);
    const editor = document.createElement("div");
    editor.innerHTML = "<strong>lorem gravida enim. ipsum</strong>";
    document.body.appendChild(editor);
    selectTextIn(editor, "gravida enim.");
    expect(queryComposerFormatFlags(editor).bold).toBe(true);
    toggleComposerFormat(editor, "bold");
    const html = editor.innerHTML.toLowerCase();
    expect(html).toContain("gravida enim.");
    expect(html).toMatch(/<(strong|b)\b/);
    expect(html).toMatch(/lorem/);
    expect(html).toMatch(/ipsum/);
    // O trecho parcial não deve permanecer dentro de um único strong contínuo.
    expect(html).not.toMatch(/<strong>lorem gravida enim\. ipsum<\/strong>/);
    expect(html).not.toMatch(/<b>lorem gravida enim\. ipsum<\/b>/);
    editor.remove();
  });

  it("caret colapsado não seleciona nem formata a mensagem inteira", () => {
    document.execCommand = vi.fn().mockReturnValue(true);
    const editor = document.createElement("div");
    editor.textContent = "mensagem inteira";
    document.body.appendChild(editor);
    collapseCaretAtEnd(editor);
    toggleComposerFormat(editor, "bold");
    const selection = window.getSelection();
    expect(selection?.toString()).not.toBe("mensagem inteira");
    // Pode inserir marcador ZWSP para estilo de digitação; o texto original permanece.
    expect(editor.textContent?.replace(/\u200b/g, "")).toBe("mensagem inteira");
    expect(editor.innerHTML.toLowerCase()).not.toMatch(
      /<(strong|b)>mensagem inteira<\/(strong|b)>/,
    );
    editor.remove();
  });

  it("liga e desliga italic e strike", () => {
    document.execCommand = vi.fn().mockReturnValue(true);
    const editor = document.createElement("div");
    editor.textContent = "abc";
    document.body.appendChild(editor);
    selectAll(editor);
    toggleComposerFormat(editor, "italic");
    expect(editor.innerHTML.toLowerCase()).toMatch(/<(em|i)\b/);
    selectAll(editor);
    toggleComposerFormat(editor, "italic");
    expect(editor.innerHTML.toLowerCase()).not.toMatch(/<(em|i)\b/);

    selectAll(editor);
    toggleComposerFormat(editor, "strike");
    expect(editor.innerHTML.toLowerCase()).toMatch(/<(s|strike|del)\b/);
    selectAll(editor);
    toggleComposerFormat(editor, "strike");
    expect(editor.innerHTML.toLowerCase()).not.toMatch(/<(s|strike|del)\b/);
    editor.remove();
  });

  it("smoke: lista e code toggle sem expand-all", () => {
    document.execCommand = vi.fn().mockImplementation((cmd: string) => {
      if (cmd === "insertUnorderedList") return true;
      return true;
    });
    const editor = document.createElement("div");
    editor.textContent = "item";
    document.body.appendChild(editor);
    selectAll(editor);
    toggleComposerFormat(editor, "ul");
    expect(document.execCommand).toHaveBeenCalledWith(
      "insertUnorderedList",
      false,
      undefined,
    );

    editor.innerHTML = "codigo";
    selectAll(editor);
    toggleComposerFormat(editor, "code");
    expect(editor.innerHTML.toLowerCase()).toMatch(/<code\b/);
    selectAll(editor);
    toggleComposerFormat(editor, "code");
    expect(editor.innerHTML.toLowerCase()).not.toMatch(/<code\b/);
    editor.remove();
  });
});
