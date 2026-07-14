import { describe, expect, it } from "vitest";

import {
  COMPLEX_VIEW_BLOCK_TYPES,
  isComplexViewBlock,
  isComplexViewBlockType,
} from "./complexViewBlocks";
import { createInputBlock } from "./comunicadoHelpers";
import { scaleComplexBlockOnResize } from "./scaleComplexBlockTypography";
import { getInputPartState } from "./comunicadoInputParts";

describe("complexViewBlocks", () => {
  it("inclui input no registry", () => {
    expect(COMPLEX_VIEW_BLOCK_TYPES).toContain("input");
    expect(isComplexViewBlockType("input")).toBe(true);
    expect(isComplexViewBlock(createInputBlock({ paramKey: "branch" }))).toBe(true);
  });

  it("scaleComplexBlockOnResize escala tipografia do filtro", () => {
    const block = {
      ...createInputBlock({ paramKey: "branch", label: "Filial" }),
      inputParts: {
        label: { style: { fontSize: 14 } },
      },
    };
    const scaled = scaleComplexBlockOnResize(block, { w: 20, h: 10 }, { w: 40, h: 20 });
    expect(scaled.type).toBe("input");
    if (scaled.type !== "input") return;
    expect(getInputPartState(scaled.inputParts, { kind: "label" })?.style?.fontSize).toBe(28);
  });
});
