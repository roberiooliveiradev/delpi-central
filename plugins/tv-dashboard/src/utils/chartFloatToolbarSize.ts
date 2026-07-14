import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

export type ChartFloatToolbarMetrics = {
  /** Lado do botão em px de design (CSS no wrap do bloco). */
  btnSize: number;
  /** Ícone Lucide proporcional ao botão. */
  iconSize: number;
  gap: number;
  /** Distância do canto direito do bbox até a coluna. */
  offset: number;
  radius: number;
};

/** Referência: lado curto ~320px → botão 40px (base maior que o fixo antigo de 32). */
const REF_SHORT_SIDE_PX = 320;
const REF_BTN_SIZE = 40;
const MIN_BTN = 36;
const MAX_BTN = 56;

function clamp(n: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, n));
}

/**
 * Tamanho da coluna flutuante (+ / pincel / funil) proporcional ao lado curto do gráfico.
 * Cresce com o bloco (min/max) para permanecer clicável sem dominar slides pequenos.
 */
export function resolveChartFloatToolbarMetrics(shortSidePx: number): ChartFloatToolbarMetrics {
  const safe = Number.isFinite(shortSidePx) && shortSidePx > 0 ? shortSidePx : REF_SHORT_SIDE_PX;
  const btnSize = clamp(Math.round((safe / REF_SHORT_SIDE_PX) * REF_BTN_SIZE), MIN_BTN, MAX_BTN);
  const iconSize = clamp(Math.round(btnSize * 0.5), 16, 28);
  const gap = clamp(Math.round(btnSize * 0.14), 4, 8);
  const offset = clamp(Math.round(btnSize * 0.22), 6, 12);
  const radius = clamp(Math.round(btnSize * 0.14), 4, 8);
  return { btnSize, iconSize, gap, offset, radius };
}

/** Lado curto do frame em px de design (frame.w/h são %). */
export function chartFrameShortSidePx(
  frame: Pick<ComunicadoFrame, "w" | "h">,
  designSize: { width: number; height: number },
): number {
  const w = (frame.w / 100) * designSize.width;
  const h = (frame.h / 100) * designSize.height;
  return Math.min(w, h);
}
