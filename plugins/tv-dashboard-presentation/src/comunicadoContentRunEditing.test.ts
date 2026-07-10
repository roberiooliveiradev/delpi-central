import { describe, expect, it } from "vitest";

import {
  compactContentRuns,
  contentRunsFromEditableRoot,
  getEditableTextSelectionOffsets,
  renderContentRunsHtml,
  selectionRunStyleState,
  syncTextBlockFromRuns,
  toggleContentRunStyleInRange,
} from "./comunicadoContentRunEditing";
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
});
