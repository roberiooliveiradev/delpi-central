import { describe, expect, it } from "vitest";

import {
  STAGE_GRID_SIZE_DEFAULT_PERCENT,
  STAGE_GRID_SIZE_PERCENT_PRESETS,
  clampStageGridSizePercent,
  migrateStageGridSizePxToPercent,
  stageGridSizePercentToDesignPx,
  stageGridSnapPercents,
} from "./stageGridSize";

describe("stageGridSize", () => {
  const hd = { width: 1920, height: 1080 };

  it("só admite divisores de 100% como presets", () => {
    for (const pct of STAGE_GRID_SIZE_PERCENT_PRESETS) {
      expect(100 % pct).toBe(0);
    }
  });

  it("encaixa no preset mais próximo (sem faixa contínua 1–50)", () => {
    expect(clampStageGridSizePercent(3)).toBe(2);
    expect(clampStageGridSizePercent(6)).toBe(5);
    expect(clampStageGridSizePercent(12)).toBe(10);
    expect(clampStageGridSizePercent(30)).toBe(25);
    expect(clampStageGridSizePercent(Number.NaN)).toBe(STAGE_GRID_SIZE_DEFAULT_PERCENT);
  });

  it("converte % → px por eixo para fechar nas bordas do slide", () => {
    expect(stageGridSizePercentToDesignPx(5, hd)).toEqual({ xPx: 96, yPx: 54 });
    expect(stageGridSizePercentToDesignPx(10, hd)).toEqual({ xPx: 192, yPx: 108 });
    expect(stageGridSizePercentToDesignPx(25, hd)).toEqual({ xPx: 480, yPx: 270 });
  });

  it("snap usa o mesmo percentual nos dois eixos", () => {
    expect(stageGridSnapPercents(5)).toEqual({ xPercent: 5, yPercent: 5 });
  });

  it("migra px legado para o preset % mais próximo (base = largura)", () => {
    expect(migrateStageGridSizePxToPercent(96, hd)).toBe(5);
    expect(migrateStageGridSizePxToPercent(192, hd)).toBe(10);
    expect(migrateStageGridSizePxToPercent(10, hd)).toBe(1);
  });
});
