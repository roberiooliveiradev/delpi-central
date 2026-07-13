import { describe, expect, it } from "vitest";

import {
  STAGE_GRID_SIZE_DEFAULT_PX,
  STAGE_GRID_SIZE_MIN_PX,
  clampStageGridSizePx,
  stageGridSizeMaxPx,
  stageGridSizePresetsForDesign,
  stageGridSizePxToPercent,
} from "./stageGridSize";

describe("stageGridSize", () => {
  const hd = { width: 1920, height: 1080 };

  it("máximo é metade do menor lado", () => {
    expect(stageGridSizeMaxPx(hd)).toBe(540);
    expect(stageGridSizeMaxPx({ width: 800, height: 2000 })).toBe(400);
  });

  it("respeita mínimo 10px e máximo do viewport", () => {
    expect(clampStageGridSizePx(5, hd)).toBe(STAGE_GRID_SIZE_MIN_PX);
    expect(clampStageGridSizePx(9999, hd)).toBe(540);
    expect(clampStageGridSizePx(50.4, hd)).toBe(50);
    expect(clampStageGridSizePx(Number.NaN, hd)).toBe(STAGE_GRID_SIZE_DEFAULT_PX);
  });

  it("presets ficam dentro do máximo e incluem o teto quando útil", () => {
    const presets = stageGridSizePresetsForDesign(hd);
    expect(presets[0]).toBe(10);
    expect(presets.every((value) => value <= 540)).toBe(true);
    expect(presets).toContain(540);
  });

  it("converte px para percentual do eixo", () => {
    expect(stageGridSizePxToPercent(96, 1920)).toBe(5);
    expect(stageGridSizePxToPercent(54, 1080)).toBe(5);
  });
});
