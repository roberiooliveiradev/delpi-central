import { describe, expect, it } from "vitest";

import { clearVisualBoxTextFormatting } from "./clearVisualBoxTextFormatting";
import { defaultStyle } from "./comunicadoHelpers";
import type { ComunicadoShapeBlock } from "./comunicadoTypes";

describe("clearVisualBoxTextFormatting", () => {
  it("zera contentRuns e tipografia da forma", () => {
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
});
