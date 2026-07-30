/**
 * Separação entre losango de ajuste (laranja) e handles de resize/giro.
 * Padrão de mercado (PowerPoint/Figma): controles não se sobrepõem —
 * o ajuste fica na borda, fora dos cantos e do meio (pill N + giro).
 */

/** Faixa do handle de cantos (raio) na borda superior — paridade PowerPoint/Figma. */
export const SHAPE_CORNER_ADJUST_HANDLE = {
  /** Longe do NW (resize) e do pill N + giro (centro do topo). */
  trackStartPct: 12,
  /** Adj máx. 0.5 ≈ metade do lado curto; no quadro usa até ~metade da largura. */
  trackEndPct: 48,
  /** Centro do losango na borda superior do chrome (não dentro do fill). */
  yPct: 0,
} as const;

export type ChromeControlPointPct = { x: number; y: number };

/** Âncoras dos 8 handles de redimensionamento (0–100 % do chrome). */
export const SHAPE_CHROME_RESIZE_CONTROL_POINTS_PCT: readonly ChromeControlPointPct[] = [
  { x: 0, y: 0 },
  { x: 50, y: 0 },
  { x: 100, y: 0 },
  { x: 0, y: 50 },
  { x: 100, y: 50 },
  { x: 0, y: 100 },
  { x: 50, y: 100 },
  { x: 100, y: 100 },
] as const;

function clampPct(value: number): number {
  return Math.min(100, Math.max(0, value));
}

/**
 * Empurra o centro do losango para fora das zonas reservadas aos resize handles.
 * Coordenadas em % do box de chrome; `minSeparationPx` = centro-a-centro.
 *
 * Na borda superior (`y≈0`), prefere deslizar em X — não empurra o handle
 * para dentro do fill (sintoma do losango “flutuando” no meio da forma).
 */
export function separateAdjustmentHandleFromChromeControls(input: {
  xPct: number;
  yPct: number;
  boxWidthPx: number;
  boxHeightPx: number;
  minSeparationPx?: number;
  /** Extra: disco de giro acima do topo-centro (y negativo em % da altura). */
  rotateOffsetYPct?: number;
  /**
   * Trava o eixo Y quando o handle deve permanecer na borda superior
   * (cantos arredondados). Default: trava se `yPct` ≤ 2.
   */
  lockTopEdge?: boolean;
}): { x: number; y: number } {
  const w = Math.max(1, input.boxWidthPx);
  const h = Math.max(1, input.boxHeightPx);
  const minSep = Math.max(8, input.minSeparationPx ?? 16);
  const lockTop =
    input.lockTopEdge === true ||
    (input.lockTopEdge !== false && input.yPct <= 2);
  const controls: ChromeControlPointPct[] = [...SHAPE_CHROME_RESIZE_CONTROL_POINTS_PCT];
  if (
    typeof input.rotateOffsetYPct === "number" &&
    Number.isFinite(input.rotateOffsetYPct) &&
    input.rotateOffsetYPct > 0
  ) {
    controls.push({ x: 50, y: -input.rotateOffsetYPct });
  }

  let x = clampPct(input.xPct);
  let y = lockTop ? 0 : clampPct(input.yPct);

  for (let iter = 0; iter < 5; iter += 1) {
    let moved = false;
    for (const control of controls) {
      const dx = ((x - control.x) / 100) * w;
      const dy = ((y - control.y) / 100) * h;
      const dist = Math.hypot(dx, dy);
      if (dist >= minSep) continue;
      moved = true;

      if (lockTop && control.y <= 0) {
        /* Borda superior: só desliza em X (afasta de NW / N / giro). */
        if (dist < 1e-6 || Math.abs(dx) < 1e-6) {
          const preferLeft = control.x >= 50;
          x = clampPct(
            preferLeft
              ? control.x - (minSep / w) * 100
              : control.x + (minSep / w) * 100,
          );
        } else {
          const sign = dx >= 0 ? 1 : -1;
          x = clampPct(control.x + sign * (minSep / w) * 100);
        }
        y = 0;
        continue;
      }

      if (dist < 1e-6) {
        /* Coincidente: entra no quadro / afasta do centro do topo. */
        if (control.y <= 0 && control.x === 0) {
          x = clampPct((minSep / w) * 100);
          y = lockTop ? 0 : clampPct((minSep / h) * 100);
        } else if (control.y <= 0 && control.x === 100) {
          x = clampPct(100 - (minSep / w) * 100);
          y = lockTop ? 0 : clampPct((minSep / h) * 100);
        } else if (control.y <= 0 && Math.abs(control.x - 50) < 1) {
          y = lockTop ? 0 : clampPct((minSep / h) * 100);
          x = clampPct(Math.min(x, 50 - (minSep / w) * 100));
        } else if (control.y >= 100 && control.x === 0) {
          x = clampPct((minSep / w) * 100);
          y = clampPct(100 - (minSep / h) * 100);
        } else if (control.y >= 100 && control.x === 100) {
          x = clampPct(100 - (minSep / w) * 100);
          y = clampPct(100 - (minSep / h) * 100);
        } else if (control.y >= 100 && Math.abs(control.x - 50) < 1) {
          y = clampPct(100 - (minSep / h) * 100);
        } else if (control.x <= 0) {
          x = clampPct((minSep / w) * 100);
        } else if (control.x >= 100) {
          x = clampPct(100 - (minSep / w) * 100);
        } else {
          y = clampPct(y + (minSep / h) * 100);
        }
        continue;
      }

      const scale = minSep / dist;
      x = clampPct(control.x + ((dx * scale) / w) * 100);
      if (lockTop) {
        y = 0;
      } else {
        y = clampPct(control.y + ((dy * scale) / h) * 100);
      }
    }
    if (!moved) break;
  }

  return { x, y: lockTop ? 0 : y };
}

/** Distância mínima centro-a-centro a partir dos diâmetros dos controles. */
export function resolveAdjustmentChromeMinSeparationPx(
  handleSizePx: number,
  adjustSizePx: number,
  gapPx = 6,
): number {
  return (Math.max(0, handleSizePx) + Math.max(0, adjustSizePx)) / 2 + Math.max(0, gapPx);
}
