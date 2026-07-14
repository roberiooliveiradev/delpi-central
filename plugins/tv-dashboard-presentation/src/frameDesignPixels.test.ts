import { describe, expect, it } from "vitest";

import { clampFrame, createBlock } from "./comunicadoHelpers";
import {
  clampFramePositionPercent,
  designPxToPercent,
  formatDesignPx,
  FRAME_POSITION_SOFT_MAX,
  frameDesignPxToPercent,
  framePercentToDesignPx,
  hostDesignSizeFromFramePercent,
  patchComunicadoFrame,
  patchComunicadoFrameDesignPx,
  percentToDesignPx,
} from "./frameDesignPixels";
import { clampFrameForBlock } from "./comunicadoShapeGeometry";

const FULL_HD = { width: 1920, height: 1080 };

describe("frameDesignPixels", () => {
  it("converte % ↔ px de design (ida e volta)", () => {
    expect(percentToDesignPx(50, 1920)).toBe(960);
    expect(designPxToPercent(960, 1920)).toBe(50);
    expect(percentToDesignPx(100, 1080)).toBe(1080);

    const pct = { x: 10, y: 20, w: 30, h: 40 };
    const px = framePercentToDesignPx(pct, FULL_HD);
    expect(px).toEqual({
      x: 192,
      y: 216,
      w: 576,
      h: 432,
    });
    const back = frameDesignPxToPercent(px, FULL_HD);
    expect(back.x).toBeCloseTo(10);
    expect(back.y).toBeCloseTo(20);
    expect(back.w).toBeCloseTo(30);
    expect(back.h).toBeCloseTo(40);
  });

  it("deriva host em px a partir do frame do bloco", () => {
    expect(hostDesignSizeFromFramePercent({ w: 20, h: 15 }, FULL_HD)).toEqual({
      width: 384,
      height: 162,
    });
  });

  it("patchComunicadoFrame limita tamanho e permite posição fora do slide", () => {
    const base = { x: 10, y: 20, w: 30, h: 40 };
    expect(patchComunicadoFrame(base, "w", 95)).toEqual({
      x: 10,
      y: 20,
      w: 95,
      h: 40,
    });
    expect(patchComunicadoFrame(base, "x", 90)).toEqual({
      x: 90,
      y: 20,
      w: 30,
      h: 40,
    });
    expect(patchComunicadoFrame(base, "x", -15)).toEqual({
      x: -15,
      y: 20,
      w: 30,
      h: 40,
    });
    expect(patchComunicadoFrame(base, "h", 0).h).toBe(0.5);
  });

  it("patchComunicadoFrameDesignPx edita em px e persiste %", () => {
    const base = { x: 10, y: 20, w: 30, h: 40 };
    // Largura 960px = 50% de 1920
    const next = patchComunicadoFrameDesignPx(base, "w", 960, FULL_HD);
    expect(next.w).toBeCloseTo(50);
    expect(next.x).toBeCloseTo(10);

    // X 0px
    const atLeft = patchComunicadoFrameDesignPx(base, "x", 0, FULL_HD);
    expect(atLeft.x).toBeCloseTo(0);
  });

  it("formatDesignPx arredonda para UI", () => {
    expect(formatDesignPx(192)).toBe(192);
    expect(formatDesignPx(192.04)).toBe(192);
    expect(formatDesignPx(192.16)).toBe(192.2);
  });

  it("clampFrame / clampFrameForBlock preservam posição fora do slide", () => {
    expect(clampFrame({ x: -10, y: 105, w: 20, h: 10 })).toEqual({
      x: -10,
      y: 105,
      w: 20,
      h: 10,
    });
    const block = createBlock("text", "oi");
    expect(clampFrameForBlock(block, { x: 90, y: -5, w: 30, h: 20 })).toEqual({
      x: 90,
      y: -5,
      w: 30,
      h: 20,
    });
    expect(clampFramePositionPercent(FRAME_POSITION_SOFT_MAX + 1)).toBe(FRAME_POSITION_SOFT_MAX);
  });
});
