export const STAGE_ZOOM_MIN = 0.1;
export const STAGE_ZOOM_MAX = 2;
/** Abaixo disso a grade some (linhas ficam densas demais no zoom out). */
export const STAGE_GRID_MIN_ZOOM = 0.5;
/** Passo base do Ctrl+scroll (ajustado pela magnitude do wheel). */
export const STAGE_ZOOM_WHEEL_STEP = 0.05;
/** @deprecated Régua passa a usar px de design do viewport; mantido para testes legados. */
export const STAGE_RULER_UNITS = 100;
export const STAGE_RULER_SIZE_PX = 22;

export function clampStageZoom(zoom: number): number {
  return Math.min(STAGE_ZOOM_MAX, Math.max(STAGE_ZOOM_MIN, Math.round(zoom * 100) / 100));
}

/** Grade ligada pelo usuário e zoom alto o bastante para ser útil. */
export function shouldRenderStageGrid(showStageGrid: boolean, stageZoom: number): boolean {
  return showStageGrid && stageZoom >= STAGE_GRID_MIN_ZOOM;
}

/**
 * Novo zoom a partir do delta do wheel (Ctrl+scroll).
 * Scroll para cima (deltaY < 0) → aproxima.
 */
export function stageZoomFromWheelDelta(currentZoom: number, deltaY: number): number {
  if (!Number.isFinite(deltaY) || deltaY === 0) return clampStageZoom(currentZoom);
  const steps = Math.max(1, Math.min(4, Math.round(Math.abs(deltaY) / 100)));
  const direction = deltaY < 0 ? 1 : -1;
  return clampStageZoom(currentZoom + direction * STAGE_ZOOM_WHEEL_STEP * steps);
}

export function computeFitStageZoom(wrap: HTMLElement, canvas: HTMLElement): number {
  const style = getComputedStyle(wrap);
  const padX = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
  const padY = parseFloat(style.paddingTop) + parseFloat(style.paddingBottom);
  const availW = Math.max(0, wrap.clientWidth - padX);
  const availH = Math.max(0, wrap.clientHeight - padY);
  const baseW = canvas.offsetWidth;
  const baseH = canvas.offsetHeight;
  if (baseW <= 0 || baseH <= 0) return 1;
  return clampStageZoom(Math.min(availW / baseW, availH / baseH));
}

export type RulerTick = {
  pos: number;
  label?: string;
  major: boolean;
};

/** Passo de marcas da régua conforme o comprimento do eixo em px de design. */
export function resolveRulerTickStep(unitsTotal: number): { step: number; labelEvery: number } {
  if (unitsTotal <= 100) return { step: 5, labelEvery: 20 };
  if (unitsTotal <= 1280) return { step: 50, labelEvery: 200 };
  if (unitsTotal <= 2000) return { step: 100, labelEvery: 200 };
  return { step: 200, labelEvery: 400 };
}

export function buildAxisRulerTicks(
  spanPx: number,
  pxPerUnit: number,
  originPx: number,
  scrollPx: number,
  unitsTotal: number = STAGE_RULER_UNITS,
): RulerTick[] {
  if (pxPerUnit <= 0 || spanPx <= 0 || unitsTotal <= 0) return [];

  const { step, labelEvery } = resolveRulerTickStep(unitsTotal);
  const startUnit = (scrollPx - originPx) / pxPerUnit;
  const endUnit = startUnit + spanPx / pxPerUnit;
  const ticks: RulerTick[] = [];
  const first = Math.floor(startUnit / step) * step;

  for (let unit = first; unit <= endUnit + step; unit += step) {
    if (unit < 0 || unit > unitsTotal) continue;
    const pos = originPx + unit * pxPerUnit - scrollPx;
    if (pos < -4 || pos > spanPx + 4) continue;
    ticks.push({
      pos,
      major: unit % (step * 2) === 0,
      label: unit % labelEvery === 0 ? String(Math.round(unit)) : undefined,
    });
  }

  return ticks;
}
