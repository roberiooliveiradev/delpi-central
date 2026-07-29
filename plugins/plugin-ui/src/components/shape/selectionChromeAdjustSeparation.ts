/**
 * Separação entre losango de ajuste (laranja) e handles de resize/giro.
 * Padrão de mercado (PowerPoint/Figma): controles não se sobrepõem —
 * o ajuste fica na borda, fora dos cantos e do meio (pill N + giro).
 */

/** Faixa segura do handle de cantos (raio) — evita NW e o centro superior. */
export const SHAPE_CORNER_ADJUST_HANDLE = {
  trackStartPct: 18,
  trackEndPct: 36,
  /** Entrou no quadro (não cola no pill N / contorno). */
  yPct: 10,
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
 */
export function separateAdjustmentHandleFromChromeControls(input: {
  xPct: number;
  yPct: number;
  boxWidthPx: number;
  boxHeightPx: number;
  minSeparationPx?: number;
  /** Extra: disco de giro acima do topo-centro (y negativo em % da altura). */
  rotateOffsetYPct?: number;
}): { x: number; y: number } {
  const w = Math.max(1, input.boxWidthPx);
  const h = Math.max(1, input.boxHeightPx);
  const minSep = Math.max(8, input.minSeparationPx ?? 16);
  const controls: ChromeControlPointPct[] = [...SHAPE_CHROME_RESIZE_CONTROL_POINTS_PCT];
  if (
    typeof input.rotateOffsetYPct === "number" &&
    Number.isFinite(input.rotateOffsetYPct) &&
    input.rotateOffsetYPct > 0
  ) {
    controls.push({ x: 50, y: -input.rotateOffsetYPct });
  }

  let x = clampPct(input.xPct);
  let y = clampPct(input.yPct);

  for (let iter = 0; iter < 5; iter += 1) {
    let moved = false;
    for (const control of controls) {
      const dx = ((x - control.x) / 100) * w;
      const dy = ((y - control.y) / 100) * h;
      const dist = Math.hypot(dx, dy);
      if (dist >= minSep) continue;
      moved = true;

      if (dist < 1e-6) {
        /* Coincidente: entra no quadro / afasta do centro do topo. */
        if (control.y <= 0 && control.x === 0) {
          x = clampPct((minSep / w) * 100);
          y = clampPct((minSep / h) * 100);
        } else if (control.y <= 0 && control.x === 100) {
          x = clampPct(100 - (minSep / w) * 100);
          y = clampPct((minSep / h) * 100);
        } else if (control.y <= 0 && Math.abs(control.x - 50) < 1) {
          y = clampPct((minSep / h) * 100);
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
      y = clampPct(control.y + ((dy * scale) / h) * 100);
    }
    if (!moved) break;
  }

  return { x, y };
}

/** Distância mínima centro-a-centro a partir dos diâmetros dos controles. */
export function resolveAdjustmentChromeMinSeparationPx(
  handleSizePx: number,
  adjustSizePx: number,
  gapPx = 6,
): number {
  return (Math.max(0, handleSizePx) + Math.max(0, adjustSizePx)) / 2 + Math.max(0, gapPx);
}
