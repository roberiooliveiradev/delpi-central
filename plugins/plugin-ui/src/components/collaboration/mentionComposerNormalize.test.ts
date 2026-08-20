import { describe, expect, it } from "vitest";

import {
  ensureComposerParagraphFlow,
  insertComposerParagraph,
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

describe("ensureComposerParagraphFlow", () => {
  it("envolve imagem órfã (irmã do editor) num <p> e coloca ZWSP dos dois lados", () => {
    const editor = document.createElement("div");
    editor.innerHTML =
      "<p>antes</p>" +
      '<span class="delpi-ui-mention-composer__inline-image" contenteditable="false">' +
      '<img alt="x" />' +
      "</span>" +
      "depois";
    document.body.appendChild(editor);
    ensureComposerParagraphFlow(editor);
    const paragraphs = Array.from(editor.querySelectorAll(":scope > p"));
    expect(paragraphs).toHaveLength(2);
    expect(paragraphs[0]?.textContent).toBe("antes");
    const imageP = paragraphs[1]!;
    const image = imageP.querySelector(".delpi-ui-mention-composer__inline-image");
    expect(image).not.toBeNull();
    expect(image?.parentElement).toBe(imageP);
    expect(image?.previousSibling?.nodeType).toBe(Node.TEXT_NODE);
    expect(image?.previousSibling?.textContent).toBe("\u200b");
    expect(imageP.textContent).toContain("depois");
    editor.remove();
  });

  it("quebra <br> em parágrafos novos sem inverter a ordem", () => {
    const editor = document.createElement("div");
    editor.innerHTML = "<p>um<br>dois<br>tres</p>";
    document.body.appendChild(editor);
    ensureComposerParagraphFlow(editor);
    const texts = Array.from(editor.querySelectorAll(":scope > p")).map((p) =>
      (p.textContent ?? "").replace(/\u200b/g, ""),
    );
    expect(texts).toEqual(["um", "dois", "tres"]);
    editor.remove();
  });

  it("separa texto antes do <br> da imagem no mesmo <p>", () => {
    const editor = document.createElement("div");
    editor.innerHTML =
      "<p>titulo<br>" +
      '<span class="delpi-ui-mention-composer__inline-image"><img alt="x" /></span>' +
      "lado</p>";
    document.body.appendChild(editor);
    ensureComposerParagraphFlow(editor);
    const paragraphs = Array.from(editor.querySelectorAll(":scope > p"));
    expect(paragraphs).toHaveLength(2);
    expect(paragraphs[0]?.textContent).toBe("titulo");
    expect(paragraphs[1]?.querySelector(".delpi-ui-mention-composer__inline-image")).not.toBeNull();
    expect(paragraphs[1]?.textContent).toContain("lado");
    editor.remove();
  });

  it("promove <div> filho do editor a <p>", () => {
    const editor = document.createElement("div");
    editor.innerHTML = "<div>bloco</div>";
    document.body.appendChild(editor);
    ensureComposerParagraphFlow(editor);
    expect(editor.querySelector(":scope > div")).toBeNull();
    expect(editor.querySelector(":scope > p")?.textContent).toBe("bloco");
    editor.remove();
  });

  it("não envolve wrapper inline que já contém <p> (preserva seleção de formato)", () => {
    const editor = document.createElement("div");
    editor.innerHTML = "<strong><p>negrito</p></strong>";
    document.body.appendChild(editor);
    ensureComposerParagraphFlow(editor);
    expect(editor.querySelector(":scope > strong > p")?.textContent).toBe("negrito");
    expect(editor.querySelectorAll(":scope > p")).toHaveLength(0);
    editor.remove();
  });

  it("insertComposerParagraph cria um <p> novo após o bloco do caret", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>linha</p>";
    document.body.appendChild(editor);
    const text = editor.querySelector("p")!.firstChild as Text;
    const range = document.createRange();
    range.setStart(text, text.length);
    range.collapse(true);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);
    insertComposerParagraph(editor);
    expect(editor.querySelectorAll(":scope > p").length).toBeGreaterThanOrEqual(2);
    editor.remove();
  });
});
