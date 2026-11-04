import { describe, expect, it } from "vitest";

import {
  resolvePptxFillColor,
  resolvePptxHexColor,
  resolvePptxStrokeColor,
  resolvePptxTextColor,
} from "./exportSlidePptxPaint";

describe("exportSlidePptxPaint", () => {
  it("colorPaint solid vence style.color divergente (Meta PPM Case B)", () => {
    expect(
      resolvePptxTextColor({
        color: "#ffffff",
        colorPaint: { kind: "solid", color: "#000000" },
      }),
    ).toBe("000000");
  });

  it("fillPaint/strokePaint solid vencem hex legado", () => {
    expect(
      resolvePptxFillColor({
        fill: "#ffffff",
        fillPaint: { kind: "solid", color: "#089bdb" },
      }),
    ).toBe("089bdb");
    expect(
      resolvePptxStrokeColor({
        stroke: "#00ff00",
        strokePaint: { kind: "solid", color: "#ff0000" },
      }),
    ).toBe("ff0000");
  });

  it("gradient cai no primeiro stop; auto/ausente usam legado ou fallback", () => {
    expect(
      resolvePptxHexColor(
        {
          kind: "gradient",
          angle: 90,
          stops: [
            { color: "#111111", position: 0 },
            { color: "#eeeeee", position: 100 },
          ],
        },
        "#ffffff",
        "1F2937",
      ),
    ).toBe("111111");
    expect(resolvePptxTextColor({ color: "#089bdb", colorPaint: { kind: "solid", color: "auto" } })).toBe(
      "089bdb",
    );
    expect(resolvePptxTextColor({ color: "#089bdb" })).toBe("089bdb");
    expect(resolvePptxTextColor({})).toBe("1F2937");
  });
});
