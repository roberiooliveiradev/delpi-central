import { describe, expect, it } from "vitest";

import {
  buildBlockTransformCss,
  clampRotationDeg,
  flipHorizontalStyle,
  flipVerticalStyle,
  normalizeRotationDeg,
  rotateBlockStyle,
} from "./comunicadoTransform";

describe("comunicadoTransform", () => {
  it("normaliza rotação para −180…180", () => {
    expect(normalizeRotationDeg(270)).toBe(-90);
    expect(normalizeRotationDeg(-270)).toBe(90);
    expect(clampRotationDeg(200)).toBe(-160);
  });

  it("rotateBlockStyle soma delta", () => {
    expect(rotateBlockStyle({ rotation: 10 }, 90).rotation).toBe(100);
    expect(rotateBlockStyle({}, -90).rotation).toBe(-90);
  });

  it("flipHorizontal/Vertical inverte scale", () => {
    expect(flipHorizontalStyle({}).scaleX).toBe(-1);
    expect(flipHorizontalStyle({ scaleX: -1 }).scaleX).toBe(1);
    expect(flipVerticalStyle({ scaleY: 1 }).scaleY).toBe(-1);
  });

  it("buildBlockTransformCss compõe scale + rotate", () => {
    expect(buildBlockTransformCss({ rotation: 45 })).toBe("rotate(45deg)");
    expect(buildBlockTransformCss({ scaleX: -1, rotation: 90 })).toBe("scaleX(-1) rotate(90deg)");
    expect(buildBlockTransformCss({})).toBeUndefined();
  });
});
