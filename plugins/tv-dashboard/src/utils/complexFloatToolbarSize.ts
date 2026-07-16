import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

export type ComplexFloatToolbarMetrics = {
  /** Lado do botão em px de design (CSS no wrap do bloco). */
  btnSize: number;
  /** Ícone Lucide proporcional ao botão. */
  iconSize: number;
  gap: number;
  /** Distância do canto direito do bbox até a coluna. */
  offset: number;
  radius: number;
};

/** @deprecated Preferir `ComplexFloatToolbarMetrics`. */
export type ChartFloatToolbarMetrics = ComplexFloatToolbarMetrics;

/** Referência: lado curto ~320px → botão 40px. */
const REF_SHORT_SIDE_PX = 320;
const REF_BTN_SIZE = 40;
const MIN_BTN = 36;
const MAX_BTN = 56;

function clamp(n: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, n));
}

/**
 * Tamanho da coluna flutuante (+ / pincel / funil) proporcional ao lado curto do bloco.
 */
export function resolveComplexFloatToolbarMetrics(shortSidePx: number): ComplexFloatToolbarMetrics {
  const safe = Number.isFinite(shortSidePx) && shortSidePx > 0 ? shortSidePx : REF_SHORT_SIDE_PX;
  const btnSize = clamp(Math.round((safe / REF_SHORT_SIDE_PX) * REF_BTN_SIZE), MIN_BTN, MAX_BTN);
  const iconSize = clamp(Math.round(btnSize * 0.5), 16, 28);
  const gap = clamp(Math.round(btnSize * 0.14), 4, 8);
  const offset = clamp(Math.round(btnSize * 0.22), 6, 12);
  const radius = clamp(Math.round(btnSize * 0.14), 4, 8);
  return { btnSize, iconSize, gap, offset, radius };
}

/** @deprecated Preferir `resolveComplexFloatToolbarMetrics`. */
export const resolveChartFloatToolbarMetrics = resolveComplexFloatToolbarMetrics;

/** Lado curto do frame em px de design (frame.w/h são %). */
export function complexFrameShortSidePx(
  frame: Pick<ComunicadoFrame, "w" | "h">,
  designSize: { width: number; height: number },
): number {
  const w = (frame.w / 100) * designSize.width;
  const h = (frame.h / 100) * designSize.height;
  return Math.min(w, h);
}

/** @deprecated Preferir `complexFrameShortSidePx`. */
export const chartFrameShortSidePx = complexFrameShortSidePx;
