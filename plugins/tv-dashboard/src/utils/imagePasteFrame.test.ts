import { describe, expect, it } from "vitest";

import { frameForImageNaturalSize } from "./imagePasteFrame";

describe("frameForImageNaturalSize", () => {
  it("preserva proporção de logo largo dentro do teto", () => {
    const designWidth = 1920;
    const designHeight = 1080;
    const frame = frameForImageNaturalSize(1200, 400, {
      designWidth,
      designHeight,
      maxWidthPercent: 36,
      maxHeightPercent: 32,
    });
    // Limitado pela largura: 36% de 1920 = 691.2 → altura = 230.4 px
    expect(frame.w).toBeCloseTo(36, 5);
    expect(frame.h).toBeCloseTo((230.4 / designHeight) * 100, 5);
    const aspectPx =
      ((frame.w / 100) * designWidth) / ((frame.h / 100) * designHeight);
    expect(aspectPx).toBeCloseTo(1200 / 400, 5);
  });

  it("preserva proporção de imagem alta", () => {
    const designWidth = 1920;
    const designHeight = 1080;
    const frame = frameForImageNaturalSize(400, 1200, {
      designWidth,
      designHeight,
      maxWidthPercent: 36,
      maxHeightPercent: 32,
    });
    expect(frame.h).toBeCloseTo(32, 5);
    const aspectPx =
      ((frame.w / 100) * designWidth) / ((frame.h / 100) * designHeight);
    expect(aspectPx).toBeCloseTo(400 / 1200, 5);
  });

  it("fallback quando dimensões inválidas", () => {
    expect(frameForImageNaturalSize(0, 0)).toEqual({ x: 10, y: 15, w: 36, h: 32 });
  });
});
