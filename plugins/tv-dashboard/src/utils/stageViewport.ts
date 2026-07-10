export const STAGE_ZOOM_MIN = 0.5;
export const STAGE_ZOOM_MAX = 2;
export const STAGE_RULER_UNITS = 100;
export const STAGE_RULER_SIZE_PX = 22;

export function clampStageZoom(zoom: number): number {
  return Math.min(STAGE_ZOOM_MAX, Math.max(STAGE_ZOOM_MIN, Math.round(zoom * 100) / 100));
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

export function buildAxisRulerTicks(
  spanPx: number,
  pxPerUnit: number,
  originPx: number,
  scrollPx: number,
  unitsTotal: number = STAGE_RULER_UNITS,
): RulerTick[] {
  if (pxPerUnit <= 0 || spanPx <= 0) return [];

  const startUnit = (scrollPx - originPx) / pxPerUnit;
  const endUnit = startUnit + spanPx / pxPerUnit;
  const ticks: RulerTick[] = [];
  const step = 5;
  const labelEvery = 20;
  const first = Math.floor(startUnit / step) * step;

  for (let unit = first; unit <= endUnit + step; unit += step) {
    if (unit < 0 || unit > unitsTotal) continue;
    const pos = originPx + unit * pxPerUnit - scrollPx;
    if (pos < -4 || pos > spanPx + 4) continue;
    ticks.push({
      pos,
      major: unit % 10 === 0,
      label: unit % labelEvery === 0 ? String(unit) : undefined,
    });
  }

  return ticks;
}
