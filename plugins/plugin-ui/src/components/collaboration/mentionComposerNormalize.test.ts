import { describe, expect, it } from "vitest";

import {
  isComposerShellContentEmpty,
  normalizeComposerFormatShells,
} from "./mentionComposerNormalize";

describe("isComposerShellContentEmpty", () => {
  it("trata ZWSP e whitespace como vazio", () => {
    const span = document.createElement("code");
    span.textContent = "\u200b";
    expect(isComposerShellContentEmpty(span)).toBe(true);
    span.textContent = "  \u00a0  ";
    expect(isComposerShellContentEmpty(span)).toBe(true);
    span.textContent = "ok";
    expect(isComposerShellContentEmpty(span)).toBe(false);
  });
});

describe("normalizeComposerFormatShells", () => {
  it("remove code/strong/pre vazios e preserva conteúdo", () => {
    const editor = document.createElement("div");
    editor.innerHTML =
      'a<code>\u200b</code><strong></strong><pre><code>\u200b</code></pre><code>keep</code>b<blockquote>\u200b</blockquote>';
    document.body.appendChild(editor);
    normalizeComposerFormatShells(editor);
    expect(editor.innerHTML.toLowerCase()).not.toMatch(/<pre\b/);
    expect(editor.innerHTML.toLowerCase()).not.toMatch(/<blockquote\b/);
    expect(editor.innerHTML.toLowerCase()).not.toMatch(/<strong\b/);
    expect(editor.querySelectorAll("code")).toHaveLength(1);
    expect(editor.querySelector("code")?.textContent).toBe("keep");
    expect(editor.textContent).toContain("a");
    expect(editor.textContent).toContain("b");
    editor.remove();
  });

  it("preserva casca de digitação sob o caret", () => {
    const editor = document.createElement("div");
    const code = document.createElement("code");
    code.textContent = "\u200b";
    editor.appendChild(code);
    document.body.appendChild(editor);
    const selection = window.getSelection()!;
    const range = document.createRange();
    range.setStart(code.firstChild!, 1);
    range.collapse(true);
    selection.removeAllRanges();
    selection.addRange(range);
    normalizeComposerFormatShells(editor, { preserveActiveTypingShell: true });
    expect(editor.querySelector("code")).not.toBeNull();
    editor.remove();
  });

  it("no undo remove casca vazia mesmo sob caret", () => {
    const editor = document.createElement("div");
    const code = document.createElement("code");
    code.textContent = "\u200b";
    editor.appendChild(document.createTextNode("x"));
    editor.appendChild(code);
    document.body.appendChild(editor);
    normalizeComposerFormatShells(editor);
    expect(editor.querySelector("code")).toBeNull();
    expect(editor.textContent).toContain("x");
    editor.remove();
  });
});
