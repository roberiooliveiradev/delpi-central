import { describe, expect, it } from "vitest";

import { clearVisualBoxTextFormatting } from "./clearVisualBoxTextFormatting";
import { defaultStyle } from "./comunicadoHelpers";
import type { ComunicadoShapeBlock, ComunicadoTextBlock } from "./comunicadoTypes";

describe("clearVisualBoxTextFormatting", () => {
  it("zera contentRuns e tipografia da forma estática", () => {
    const block: ComunicadoShapeBlock = {
      id: "s1",
      type: "shape",
      shape: "rectangle",
      frame: { x: 0, y: 0, w: 20, h: 10 },
      content: "Meta 1.400 PPM",
      contentRuns: [
        { text: "Meta", style: { fontWeight: "bold" } },
        { text: " 1.400 PPM" },
      ],
      style: { fontWeight: "bold", color: "#f00", fill: "#fff" },
    };
    const patch = clearVisualBoxTextFormatting(block, defaultStyle("shape", "rectangle"));
    expect(patch.contentRuns).toBeUndefined();
    expect(patch.content).toBe("Meta 1.400 PPM");
    expect(patch.style.fontWeight).not.toBe("bold");
    expect(patch.style.fill).toBe("#fff");
  });

  it("preserva dataRef + displayFormat ao limpar tipografia (RQ-08)", () => {
    const block: ComunicadoTextBlock = {
      id: "t1",
      type: "text",
      frame: { x: 0, y: 0, w: 40, h: 10 },
      content: "x",
      contentRuns: [
        {
          text: "",
          style: { fontWeight: "bold", textCase: "upper", color: "#f00" },
          dataRef: {
            field: "filter.end_date",
            displayFormat: { category: "date", formatId: "date-short" },
          },
        },
      ],
      style: { fontWeight: "bold", textCase: "upper", color: "#f00" },
    };
    const patch = clearVisualBoxTextFormatting(block, defaultStyle("text"));
    expect(patch.contentRuns).toHaveLength(1);
    expect(patch.contentRuns?.[0]?.dataRef?.field).toBe("filter.end_date");
    expect(patch.contentRuns?.[0]?.dataRef?.displayFormat).toEqual({
      category: "date",
      formatId: "date-short",
    });
    expect(patch.contentRuns?.[0]?.style).toBeUndefined();
    expect(patch.style.textCase).toBeUndefined();
    expect(patch.style.fontWeight).not.toBe("bold");
  });
});
