import { describe, expect, it } from "vitest";

import {
  estimateTextContentSizePx,
  hugFrameToContentSizePx,
  resizeHandleToHugAxes,
  resizeModeToHandlePosition,
  textBoxFrameFromContent,
  TEXT_BOX_HUG_MIN_HEIGHT_PX,
  TEXT_BOX_HUG_MIN_WIDTH_PX,
} from "./visualBoxTextHug";
import { framePercentToDesignPx } from "./frameDesignPixels";
import { createBlock, createShapeBlock, defaultFrame } from "./comunicadoHelpers";

const FULL_HD = { width: 1920, height: 1080 };

describe("visualBoxTextHug", () => {
  it("estima caixa maior para texto mais longo / fonte maior", () => {
    const short = estimateTextContentSizePx({ content: "Oi", fontSize: 28 });
    const long = estimateTextContentSizePx({ content: "Olá mundo DELPI", fontSize: 28 });
    const large = estimateTextContentSizePx({ content: "Oi", fontSize: 56 });
    expect(long.w).toBeGreaterThan(short.w);
    expect(large.h).toBeGreaterThanOrEqual(short.h);
    expect(short.w).toBeGreaterThanOrEqual(TEXT_BOX_HUG_MIN_WIDTH_PX);
    expect(short.h).toBeGreaterThanOrEqual(TEXT_BOX_HUG_MIN_HEIGHT_PX);
  });

  it("text/heading na inserção abraçam o placeholder — não o quadrado das formas", () => {
    const text = createBlock("text", "Texto");
    const shape = createShapeBlock("rectangle");
    const textPx = framePercentToDesignPx(text.frame, FULL_HD);
    const shapePx = framePercentToDesignPx(shape.frame, FULL_HD);
    expect(textPx.w).toBeLessThan(shapePx.w * 0.5);
    expect(textPx.h).toBeLessThan(shapePx.h * 0.5);

    const heading = createBlock("heading", "Novo título");
    const headingPx = framePercentToDesignPx(heading.frame, FULL_HD);
    expect(headingPx.w).toBeGreaterThan(textPx.w);
    expect(headingPx.h).toBeGreaterThan(textPx.h);

    expect(defaultFrame("text").w).toBeCloseTo(
      textBoxFrameFromContent({ content: "Texto", fontSize: 28 }).w,
      5,
    );
  });

  it("resizeHandleToHugAxes espelha Figma (borda vs canto)", () => {
    expect(resizeHandleToHugAxes("e")).toEqual({ width: true, height: false });
    expect(resizeHandleToHugAxes("n")).toEqual({ width: false, height: true });
    expect(resizeHandleToHugAxes("se")).toEqual({ width: true, height: true });
    expect(resizeModeToHandlePosition("resize-w")).toBe("w");
    expect(resizeModeToHandlePosition("rotate")).toBeNull();
  });

  it("hugFrameToContentSizePx mantém a borda oposta ao handle", () => {
    const frame = { x: 10, y: 20, w: 40, h: 30 };
    const huggedE = hugFrameToContentSizePx(
      frame,
      { w: 200, h: 100 },
      FULL_HD,
      { width: true, height: false },
      "e",
    );
    const px0 = framePercentToDesignPx(frame, FULL_HD);
    const pxE = framePercentToDesignPx(huggedE, FULL_HD);
    expect(pxE.x).toBeCloseTo(px0.x, 5);
    expect(pxE.w).toBeCloseTo(200, 5);
    expect(pxE.h).toBeCloseTo(px0.h, 5);

    const huggedW = hugFrameToContentSizePx(
      frame,
      { w: 200, h: 100 },
      FULL_HD,
      { width: true, height: false },
      "w",
    );
    const pxW = framePercentToDesignPx(huggedW, FULL_HD);
    expect(pxW.x + pxW.w).toBeCloseTo(px0.x + px0.w, 5);
    expect(pxW.w).toBeCloseTo(200, 5);
  });
});
