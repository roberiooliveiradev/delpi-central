import { describe, expect, it } from "vitest";

import type { ComunicadoTextBlock } from "./comunicadoTypes";
import {
  applyVisualBoxContainerTypographyPatch,
  materializeNamedStylesForContainerOverride,
  resolveVisualBoxEffectiveTextFormatSnapshot,
} from "./visualBoxTextFormat";
import { hasNamedStyleContentRuns } from "./comunicadoNamedTextStyles";
import { splitContentRunsIntoLines } from "./comunicadoContentList";

function subtitleBlock(): ComunicadoTextBlock {
  return {
    id: "t1",
    type: "text",
    content: "Departamento Comercial",
    x: 10,
    y: 10,
    width: 80,
    height: 20,
    style: { fontSize: 28, color: "#ffffff" },
    contentRuns: [
      {
        text: "Departamento Comercial",
        style: { namedStyle: "subtitle" },
      },
    ],
  };
}

describe("visualBoxTextFormat", () => {
  it("resolveVisualBoxEffectiveTextFormatSnapshot: namedStyle subtitle → fontSize 36", () => {
    const snap = resolveVisualBoxEffectiveTextFormatSnapshot(subtitleBlock());
    expect(snap.fontSize).toBe(36);
    expect(snap.fontWeight).toBe("normal");
  });

  it("applyVisualBoxContainerTypographyPatch: fontSize 48 remove namedStyle", () => {
    const next = applyVisualBoxContainerTypographyPatch(subtitleBlock(), { fontSize: 48 });
    expect(next.style?.fontSize).toBe(48);
    expect(hasNamedStyleContentRuns(next.contentRuns ?? [])).toBe(false);
    const lines = splitContentRunsIntoLines(next.contentRuns ?? []);
    expect(lines.every((line) => line.namedStyle == null)).toBe(true);
    const snap = resolveVisualBoxEffectiveTextFormatSnapshot(next);
    expect(snap.fontSize).toBe(48);
  });

  it("legado sem runs usa block.style", () => {
    const block: ComunicadoTextBlock = {
      id: "t2",
      type: "heading",
      content: "Título",
      x: 0,
      y: 0,
      width: 50,
      height: 10,
      style: { fontSize: 56, fontWeight: "bold" },
    };
    const snap = resolveVisualBoxEffectiveTextFormatSnapshot(block);
    expect(snap.fontSize).toBe(56);
    expect(snap.fontWeight).toBe("bold");
  });

  it("materializeNamedStylesForContainerOverride preserva runs sem namedStyle", () => {
    const runs = [{ text: "plain" }];
    expect(materializeNamedStylesForContainerOverride(runs, ["fontSize"])).toEqual(runs);
  });
});
