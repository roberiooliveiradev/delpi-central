import { describe, expect, it } from "vitest";

import {
  compactContentRuns,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  insertLineBreakAtOffset,
  renderContentRunsHtml,
  restoreEditableTextSelection,
  selectionRunStyleState,
  syncTextBlockFromRuns,
  toggleContentRunStyleInRange,
} from "./comunicadoContentRunEditing";
import { renderTextBlockEditorHtml } from "./comunicadoTextBlockLink";
import type { ComunicadoContentRun } from "./comunicadoTypes";

describe("comunicadoContentRunEditing", () => {
  it("compacta runs adjacentes com o mesmo estilo", () => {
    const runs: ComunicadoContentRun[] = [
      { text: "A", style: { fontWeight: "bold" } },
      { text: "B", style: { fontWeight: "bold" } },
      { text: "C" },
    ];
    expect(compactContentRuns(runs)).toEqual([
      { text: "AB", style: { fontWeight: "bold" } },
      { text: "C" },
    ]);
  });

  it("aplica negrito só no trecho selecionado", () => {
    const runs: ComunicadoContentRun[] = [{ text: "ABCDEF" }];
    const toggled = toggleContentRunStyleInRange(runs, 1, 4, "fontWeight");
    expect(toggled).toEqual([
      { text: "A" },
      { text: "BCD", style: { fontWeight: "bold" } },
      { text: "EF" },
    ]);
    expect(syncTextBlockFromRuns(toggled)).toEqual({
      content: "ABCDEF",
      contentRuns: [
        { text: "A" },
        { text: "BCD", style: { fontWeight: "bold" } },
        { text: "EF" },
      ],
    });
  });

  it("remove negrito parcial quando toda a seleção já está em negrito", () => {
    const runs: ComunicadoContentRun[] = [
      { text: "A" },
      { text: "BC", style: { fontWeight: "bold" } },
      { text: "D" },
    ];
    const toggled = toggleContentRunStyleInRange(runs, 1, 3, "fontWeight");
    expect(toggled).toEqual([{ text: "ABCD" }]);
    expect(syncTextBlockFromRuns(toggled).contentRuns).toBeUndefined();
  });

  it("detecta estado misto da seleção", () => {
    const runs: ComunicadoContentRun[] = [
      { text: "A", style: { fontWeight: "bold" } },
      { text: "B" },
    ];
    expect(selectionRunStyleState(runs, 0, 2)).toEqual({
      fontWeight: "mixed",
      fontStyle: "normal",
      underline: false,
      strikethrough: false,
    });
    expect(selectionRunStyleState(runs, 1, 2).fontWeight).toBe("normal");
    expect(selectionRunStyleState(runs, 0, 1).fontWeight).toBe("bold");
  });

  it("serializa e reidrata HTML editável", () => {
    const html = renderContentRunsHtml([
      { text: "Oi " },
      { text: "mundo", style: { fontWeight: "bold", fontStyle: "italic" } },
    ]);
    const root = document.createElement("div");
    root.innerHTML = html;
    expect(contentRunsFromEditableRoot(root)).toEqual([
      { text: "Oi " },
      { text: "mundo", style: { fontWeight: "bold", fontStyle: "italic" } },
    ]);
  });

  it("serializa listas com linhas marcadas no HTML editável", () => {
    const html = renderContentRunsHtml([
      { text: "Primeiro", style: { listType: "bullet" } },
      { text: "\n" },
      { text: "Segundo", style: { listType: "bullet" } },
      { text: "\n" },
      { text: "Terceiro", style: { listType: "bullet" } },
    ]);
    expect(html).toContain('data-list-type="bullet"');
    const root = document.createElement("div");
    root.innerHTML = html;
    expect(contentRunsFromEditableRoot(root)).toEqual([
      { text: "Primeiro", style: { listType: "bullet" } },
      { text: "\n" },
      { text: "Segundo", style: { listType: "bullet" } },
      { text: "\n" },
      { text: "Terceiro", style: { listType: "bullet" } },
    ]);
  });

  it("lê offsets de seleção em contentEditable", () => {
    const root = document.createElement("div");
    root.contentEditable = "true";
    root.innerHTML = renderContentRunsHtml([{ text: "ABCDEF" }]);
    document.body.appendChild(root);

    const textNode = root.firstChild as Text;
    const range = document.createRange();
    range.setStart(textNode, 1);
    range.setEnd(textNode, 4);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);

    expect(getEditableTextSelectionOffsets(root)).toEqual({ start: 1, end: 4 });
    document.body.removeChild(root);
  });

  it("restaura cursor no início de linha vazia após Enter", () => {
    const runs = insertLineBreakAtOffset([{ text: "Linha 1" }], "Linha 1".length);
    const root = document.createElement("div");
    root.contentEditable = "true";
    root.innerHTML = renderTextBlockEditorHtml(runs);
    document.body.appendChild(root);

    const nextOffset = "Linha 1".length + 1;
    restoreEditableTextSelection(root, nextOffset, nextOffset);

    expect(getEditableTextSelectionOffsets(root)).toEqual({
      start: nextOffset,
      end: nextOffset,
    });

    document.body.removeChild(root);
  });

  it("preserva seleção após re-render do HTML multilinha", () => {
    const runs = insertLineBreakAtOffset(
      insertLineBreakAtOffset([{ text: "Primeira" }], "Primeira".length),
      "Primeira".length + 1,
    );
    const root = document.createElement("div");
    root.contentEditable = "true";
    document.body.appendChild(root);

    root.innerHTML = renderTextBlockEditorHtml(runs);
    const caretOffset = "Primeira".length + 2;
    restoreEditableTextSelection(root, caretOffset, caretOffset);

    root.innerHTML = renderTextBlockEditorHtml(runs);
    restoreEditableTextSelection(root, caretOffset, caretOffset);

    expect(getEditableTextSelectionOffsets(root)).toEqual({
      start: caretOffset,
      end: caretOffset,
    });

    document.body.removeChild(root);
  });
});
