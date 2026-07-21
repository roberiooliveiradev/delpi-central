/**
 * Chrome de seleção no palco (outline pontilhado, quadrados de resize, losango amarelo).
 * Counter-scale com o zoom do palco para manter tamanho útil na tela, com teto/piso de zoom.
 */

export type SelectionChromeMetrics = {
  /** Quadrado de resize (px de design). */
  handleSize: number;
  /** Losango de ajuste (amarelo). */
  adjustSize: number;
  /** Disco de giro. */
  rotateSize: number;
  /** Espessura do outline pontilhado. */
  outlineWidth: number;
  /** Pad entre conteúdo e outline/handles. */
  selectionPad: number;
  /** Metade do handle — offset dos cantos. */
  handleHalf: number;
  /** Haste do rotate até o outline. */
  rotateStem: number;
};

/** Alvo visual na tela @ zoom 100% — pad enxuto (ícone/forma na mesma moldura). */
const SCREEN_AT_100 = {
  handle: 16,
  adjust: 16,
  rotate: 16,
  outline: 2.5,
  pad: 6,
} as const;

/**
 * Abaixo deste zoom o chrome deixa de crescer em px de design
 * (evita handles enormes em zoom muito baixo).
 */
export const SELECTION_CHROME_ZOOM_FLOOR = 0.5;
/**
 * Acima deste zoom o chrome deixa de encolher em px de design
 * (evita handles minúsculos em zoom alto).
 */
export const SELECTION_CHROME_ZOOM_CEIL = 1.25;

function clampZoomForChrome(zoom: number): number {
  const z = Number.isFinite(zoom) && zoom > 0 ? zoom : 1;
  return Math.min(SELECTION_CHROME_ZOOM_CEIL, Math.max(SELECTION_CHROME_ZOOM_FLOOR, z));
}

function scaleToDesign(screenPx: number, effectiveZoom: number): number {
  return Math.round((screenPx / effectiveZoom) * 10) / 10;
}

/**
 * Métricas em px de design (dentro do canvas com `transform: scale(zoom)`).
 * Na tela ≈ SCREEN_AT_100 entre 50% e 125% de zoom.
 */
export function resolveSelectionChromeMetrics(stageZoom: number): SelectionChromeMetrics {
  const effective = clampZoomForChrome(stageZoom);
  const handleSize = scaleToDesign(SCREEN_AT_100.handle, effective);
  const adjustSize = scaleToDesign(SCREEN_AT_100.adjust, effective);
  const rotateSize = scaleToDesign(SCREEN_AT_100.rotate, effective);
  const outlineWidth = scaleToDesign(SCREEN_AT_100.outline, effective);
  const selectionPad = scaleToDesign(SCREEN_AT_100.pad, effective);
  return {
    handleSize,
    adjustSize,
    rotateSize,
    outlineWidth,
    selectionPad,
    handleHalf: Math.round((handleSize / 2) * 10) / 10,
    rotateStem: Math.round((handleSize * 0.75 + selectionPad) * 10) / 10,
  };
}

/** CSS custom properties para o canvas do composer. */
export function selectionChromeCssVars(
  metrics: SelectionChromeMetrics,
): Record<string, string> {
  return {
    "--td-selection-handle-size": `${metrics.handleSize}px`,
    "--td-selection-handle-half": `${metrics.handleHalf}px`,
    "--td-selection-adjust-size": `${metrics.adjustSize}px`,
    "--td-selection-rotate-size": `${metrics.rotateSize}px`,
    "--td-selection-outline-width": `${metrics.outlineWidth}px`,
    "--td-global-selection-pad": `${metrics.selectionPad}px`,
    "--td-selection-rotate-stem": `${metrics.rotateStem}px`,
    "--td-selection-rotate-offset": `${metrics.rotateStem + metrics.rotateSize / 2}px`,
  };
}
