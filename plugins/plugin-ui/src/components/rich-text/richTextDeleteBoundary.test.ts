// @vitest-environment jsdom
import { describe, expect, it } from "vitest";

import {
  richTextEmphasisSignature,
  tryDeleteRichTextAtEmphasisBoundary,
} from "./richTextDeleteBoundary";

function placeCaret(node: Text, offset: number) {
  const selection = window.getSelection()!;
  const range = document.createRange();
  range.setStart(node, offset);
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
}

describe("richTextEmphasisSignature", () => {
  it("detecta negrito por <strong> e font-weight:normal aninhado (Word)", () => {
    const editor = document.createElement("div");
    editor.innerHTML =
      "<p><strong>Assunto: <span style=\"font-weight:normal\">indicadores</span></strong></p>";
    document.body.appendChild(editor);

    const boldText = editor.querySelector("strong")!.firstChild as Text;
    const normalText = editor.querySelector("span")!.firstChild as Text;

    expect(richTextEmphasisSignature(boldText, editor)).toContain("b");
    expect(richTextEmphasisSignature(normalText, editor)).not.toContain("b");

    document.body.removeChild(editor);
  });
});

describe("tryDeleteRichTextAtEmphasisBoundary", () => {
  it("ao apagar espaço antes de negrito, não engole o texto normal no <strong>", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>ddsd <strong>Assunto:</strong> indicadores</p>";
    document.body.appendChild(editor);

    const strongText = editor.querySelector("strong")!.firstChild as Text;
    // Caret no início de "Assunto:" (logo após o espaço)
    placeCaret(strongText, 0);

    const handled = tryDeleteRichTextAtEmphasisBoundary(editor, "backward");
    expect(handled).toBe(true);

    // Espaço removido, "ddsd" permanece fora do strong
    expect(editor.innerHTML).toContain("<strong>Assunto:</strong>");
    expect(editor.textContent).toContain("ddsdAssunto:");
    const strong = editor.querySelector("strong");
    expect(strong?.textContent).toBe("Assunto:");
    expect(strong?.textContent).not.toContain("ddsd");
    expect(editor.textContent).toContain("indicadores");

    document.body.removeChild(editor);
  });

  it("não intercepta delete no meio do mesmo estilo", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>abcdef</p>";
    document.body.appendChild(editor);

    const text = editor.querySelector("p")!.firstChild as Text;
    placeCaret(text, 3);

    const handled = tryDeleteRichTextAtEmphasisBoundary(editor, "backward");
    expect(handled).toBe(false);
    expect(editor.textContent).toBe("abcdef");

    document.body.removeChild(editor);
  });

  it("ao apagar fronteira com span font-weight:normal dentro de <b>, não boldifica a linha", () => {
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML =
      '<p><b>Assunto: <span style="font-weight:normal">indicadores</span></b></p>';
    document.body.appendChild(editor);

    const normalText = editor.querySelector("span")!.firstChild as Text;
    placeCaret(normalText, 0);

    const handled = tryDeleteRichTextAtEmphasisBoundary(editor, "backward");
    expect(handled).toBe(true);

    const span = editor.querySelector("span");
    expect(span?.style.fontWeight).toBe("normal");
    expect(span?.textContent).toBe("indicadores");
    // O trecho normal não deve ter sido absorvido como negrito puro
    expect(richTextEmphasisSignature(span!.firstChild as Text, editor)).not.toContain("b");

    document.body.removeChild(editor);
  });
});
