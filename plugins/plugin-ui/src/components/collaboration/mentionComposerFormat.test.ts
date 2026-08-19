import { describe, expect, it } from "vitest";

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
});
