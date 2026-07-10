import { describe, expect, it } from "vitest";

import { renderContentRunsHtml, contentRunsFromEditableRoot } from "./comunicadoContentRunEditing";
import { splitContentRunsIntoLines } from "./comunicadoContentList";
import {
  applyNamedStyleInRange,
  applyNamedStyleOnAllLines,
  namedTextStylePreset,
  resolveEffectiveRunStyle,
  resolveNamedStyleSelectionForBlock,
  selectionNamedStyleState,
} from "./comunicadoNamedTextStyles";
import { syncTextBlockFromRuns } from "./comunicadoContentRunEditing";
import type { ComunicadoContentRun } from "./comunicadoTypes";

describe("comunicadoNamedTextStyles", () => {
  it("expõe presets Título 1, Subtítulo e Corpo", () => {
    expect(namedTextStylePreset("title1")).toMatchObject({
      fontSize: 56,
      fontWeight: "bold",
    });
    expect(namedTextStylePreset("subtitle")).toMatchObject({
      fontSize: 36,
      fontWeight: "normal",
    });
    expect(namedTextStylePreset("body")).toMatchObject({
      fontSize: 28,
      fontWeight: "normal",
    });
  });

  it("aplica estilo nomeado só nas linhas selecionadas", () => {
    const runs: ComunicadoContentRun[] = [{ text: "A\nB\nC" }];
    const styled = applyNamedStyleInRange(runs, 2, 4, "subtitle");
    expect(splitContentRunsIntoLines(styled)).toEqual([
      { runs: [{ text: "A" }] },
      { runs: [{ text: "B", style: { namedStyle: "subtitle" } }], namedStyle: "subtitle" },
      { runs: [{ text: "C" }] },
    ]);
  });

  it("aplica estilo a todas as linhas do bloco", () => {
    const styled = applyNamedStyleOnAllLines([{ text: "Linha 1\nLinha 2" }], "title1");
    expect(selectionNamedStyleState(styled, 0, 20)).toBe("title1");
    expect(syncTextBlockFromRuns(styled).contentRuns?.some((run) => run.style?.namedStyle === "title1")).toBe(
      true,
    );
  });

  it("resolve CSS efetivo com preset + override inline", () => {
    const css = resolveEffectiveRunStyle(
      { namedStyle: "body", fontWeight: "bold", color: "#ff0000" },
      { fontScale: 1 },
    );
    expect(css.fontSize).toBe("28px");
    expect(css.fontWeight).toBe("bold");
    expect(css.color).toBe("#ff0000");
  });

  it("serializa e reidrata estilo nomeado no HTML editável", () => {
    const html = renderContentRunsHtml([
      { text: "Título", style: { namedStyle: "title1" } },
      { text: "\n" },
      { text: "Corpo", style: { namedStyle: "body" } },
    ]);
    expect(html).toContain('data-named-style="title1"');
    expect(html).toContain('data-named-style="body"');
    const root = document.createElement("div");
    root.innerHTML = html;
    expect(contentRunsFromEditableRoot(root)).toEqual([
      { text: "Título", style: { namedStyle: "title1" } },
      { text: "\n" },
      { text: "Corpo", style: { namedStyle: "body" } },
    ]);
  });

  it("infere estilo padrão do tipo de bloco quando não há contentRuns", () => {
    expect(
      resolveNamedStyleSelectionForBlock(
        { type: "heading", content: "Olá" },
        0,
        3,
      ),
    ).toBe("title1");
    expect(
      resolveNamedStyleSelectionForBlock(
        { type: "text", content: "Olá" },
        0,
        3,
      ),
    ).toBe("body");
  });
});
