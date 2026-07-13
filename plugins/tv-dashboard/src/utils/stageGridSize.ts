/**
 * Tamanho da grade do palco em pixels de design (antes do zoom).
 * Mínimo 10px; máximo = metade do menor lado do viewport.
 */

export const STAGE_GRID_SIZE_MIN_PX = 10;

/** Default legado ≈ 5% de 1920 (Full HD). */
export const STAGE_GRID_SIZE_DEFAULT_PX = 96;

/**
 * Presets da lista (como tamanho de fonte): o usuário ainda pode digitar
 * valores intermediários dentro do intervalo.
 */
export const STAGE_GRID_SIZE_PRESETS = [
  10, 16, 20, 25, 32, 40, 50, 60, 80, 96, 100, 120, 160, 200, 240, 320, 400, 480, 540,
] as const;

export type StageDesignSize = { width: number; height: number };

/** Limite superior: metade do menor lado do slide. */
export function stageGridSizeMaxPx(design: StageDesignSize): number {
  const shorter = Math.min(
    Math.max(0, design.width),
    Math.max(0, design.height),
  );
  return Math.max(STAGE_GRID_SIZE_MIN_PX, Math.floor(shorter / 2));
}

export function clampStageGridSizePx(sizePx: number, design: StageDesignSize): number {
  if (!Number.isFinite(sizePx)) return STAGE_GRID_SIZE_DEFAULT_PX;
  const max = stageGridSizeMaxPx(design);
  return Math.min(max, Math.max(STAGE_GRID_SIZE_MIN_PX, Math.round(sizePx)));
}

/** Presets filtrados ao máximo do viewport atual. */
export function stageGridSizePresetsForDesign(design: StageDesignSize): number[] {
  const max = stageGridSizeMaxPx(design);
  const filtered = STAGE_GRID_SIZE_PRESETS.filter((value) => value <= max);
  if (filtered.length === 0) return [STAGE_GRID_SIZE_MIN_PX];
  if (filtered[filtered.length - 1] !== max && max > filtered[filtered.length - 1]!) {
    return [...filtered, max];
  }
  return [...filtered];
}

/** Converte passo em px → % do eixo (frames do comunicado são percentuais). */
export function stageGridSizePxToPercent(sizePx: number, axisLengthPx: number): number {
  if (!(axisLengthPx > 0) || !(sizePx > 0)) return 5;
  return (sizePx / axisLengthPx) * 100;
}
