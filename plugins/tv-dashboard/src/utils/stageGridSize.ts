/**
 * Tamanho da grade do palco em **% do slide**.
 * Só divisores de 100 — a malha encaixa de canto a canto nos dois eixos.
 */

export type StageDesignSize = { width: number; height: number };

/**
 * Presets canônicos (divisores de 100).
 * Não há faixa contínua 1–50: só estes passos garantem divisão exata.
 */
export const STAGE_GRID_SIZE_PERCENT_PRESETS = [1, 2, 4, 5, 10, 20, 25, 50] as const;

export const STAGE_GRID_SIZE_DEFAULT_PERCENT = 5;
export const STAGE_GRID_SIZE_MIN_PERCENT = STAGE_GRID_SIZE_PERCENT_PRESETS[0];
export const STAGE_GRID_SIZE_MAX_PERCENT =
  STAGE_GRID_SIZE_PERCENT_PRESETS[STAGE_GRID_SIZE_PERCENT_PRESETS.length - 1]!;

/** @deprecated Preferir STAGE_GRID_SIZE_DEFAULT_PERCENT — mantido para migração de prefs em px. */
export const STAGE_GRID_SIZE_DEFAULT_PX = 96;
/** @deprecated */
export const STAGE_GRID_SIZE_MIN_PX = 10;

export function stageGridSizePercentPresets(): number[] {
  return [...STAGE_GRID_SIZE_PERCENT_PRESETS];
}

/** Encaixa no preset mais próximo (nunca valor intermediário arbitrário). */
export function clampStageGridSizePercent(value: number): number {
  if (!Number.isFinite(value)) return STAGE_GRID_SIZE_DEFAULT_PERCENT;
  let best: number = STAGE_GRID_SIZE_DEFAULT_PERCENT;
  let bestDist = Number.POSITIVE_INFINITY;
  for (const preset of STAGE_GRID_SIZE_PERCENT_PRESETS) {
    const dist = Math.abs(preset - value);
    if (dist < bestDist) {
      best = preset;
      bestDist = dist;
    }
  }
  return best;
}

/**
 * Célula em px de design (antes do zoom): % da largura × % da altura,
 * para a malha fechar exatamente nas bordas do slide.
 */
export function stageGridSizePercentToDesignPx(
  percent: number,
  design: StageDesignSize,
): { xPx: number; yPx: number } {
  const pct = clampStageGridSizePercent(percent);
  const width = Math.max(0, design.width);
  const height = Math.max(0, design.height);
  return {
    xPx: (width * pct) / 100,
    yPx: (height * pct) / 100,
  };
}

/** Legado: px → % da largura do design (célula era quadrada em px), depois encaixa no preset. */
export function migrateStageGridSizePxToPercent(
  sizePx: number,
  design: StageDesignSize = { width: 1920, height: 1080 },
): number {
  if (!Number.isFinite(sizePx) || sizePx <= 0) return STAGE_GRID_SIZE_DEFAULT_PERCENT;
  const width = Math.max(0, design.width);
  if (!(width > 0)) return STAGE_GRID_SIZE_DEFAULT_PERCENT;
  return clampStageGridSizePercent((sizePx / width) * 100);
}

/** @deprecated Use clampStageGridSizePercent. */
export function clampStageGridSizePx(sizePx: number, design: StageDesignSize): number {
  const pct = migrateStageGridSizePxToPercent(sizePx, design);
  return stageGridSizePercentToDesignPx(pct, design).xPx;
}

/** @deprecated */
export function stageGridSizeMaxPx(design: StageDesignSize): number {
  return Math.max(STAGE_GRID_SIZE_MIN_PX, Math.floor(Math.min(design.width, design.height) / 2));
}

/** @deprecated */
export function stageGridSizePresetsForDesign(design: StageDesignSize): number[] {
  return STAGE_GRID_SIZE_PERCENT_PRESETS.map(
    (pct) => stageGridSizePercentToDesignPx(pct, design).xPx,
  );
}

/** Snap usa o mesmo % nos dois eixos. */
export function stageGridSnapPercents(percent: number): { xPercent: number; yPercent: number } {
  const pct = clampStageGridSizePercent(percent);
  return { xPercent: pct, yPercent: pct };
}

/** @deprecated Preferir stageGridSnapPercents. */
export function stageGridSizePxToPercent(sizePx: number, axisLengthPx: number): number {
  if (!(axisLengthPx > 0) || !(sizePx > 0)) return STAGE_GRID_SIZE_DEFAULT_PERCENT;
  return clampStageGridSizePercent((sizePx / axisLengthPx) * 100);
}
