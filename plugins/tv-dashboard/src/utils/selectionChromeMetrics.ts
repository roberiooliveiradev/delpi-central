/**
 * Chrome de seleção no palco — visual tipo Figma/Canva:
 * outline sólido, cantos circulares ocos, mid-edge em pill, giro com ícone.
 * Counter-scale com o zoom do palco.
 */

export type SelectionChromeMetrics = {
  /** Diâmetro do handle de canto (círculo). */
  handleSize: number;
  /** Comprimento do pill nas bordas N/S/E/W. */
  edgeLength: number;
  /** Espessura do pill nas bordas. */
  edgeThickness: number;
  /** Losango de ajuste (laranja). */
  adjustSize: number;
  /** Disco de giro. */
  rotateSize: number;
  /** Espessura do outline sólido. */
  outlineWidth: number;
  /** Pad entre conteúdo e outline/handles. */
  selectionPad: number;
  /** Metade do handle de canto — offset. */
  handleHalf: number;
  /**
   * Distância do centro do disco de giro até a borda superior do frame (y=0).
   * Usada no offset do botão; não é a altura visual da haste.
   */
  rotateStem: number;
  /**
   * Comprimento desenhado da haste — do fundo do disco ao topo do pill N
   * (não atravessa o handle de redimensionamento).
   */
  rotateStemDraw: number;
};

/** Alvo visual na tela @ zoom 100% — alinhado aos prints de referência. */
const SCREEN_AT_100 = {
  handle: 10,
  edgeLength: 14,
  edgeThickness: 6,
  adjust: 10,
  rotate: 18,
  outline: 1.5,
  pad: 4,
} as const;

export const SELECTION_CHROME_ZOOM_FLOOR = 0.5;
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
 */
export function resolveSelectionChromeMetrics(stageZoom: number): SelectionChromeMetrics {
  const effective = clampZoomForChrome(stageZoom);
  const handleSize = scaleToDesign(SCREEN_AT_100.handle, effective);
  const edgeLength = scaleToDesign(SCREEN_AT_100.edgeLength, effective);
  const edgeThickness = scaleToDesign(SCREEN_AT_100.edgeThickness, effective);
  const adjustSize = scaleToDesign(SCREEN_AT_100.adjust, effective);
  const rotateSize = scaleToDesign(SCREEN_AT_100.rotate, effective);
  const outlineWidth = scaleToDesign(SCREEN_AT_100.outline, effective);
  const selectionPad = scaleToDesign(SCREEN_AT_100.pad, effective);
  /*
   * Haste longa o bastante para o disco de giro ficar acima do pill N
   * e do losango de ajuste na borda superior (antes ficavam quase colados).
   */
  const topChromeClearance = edgeThickness + adjustSize / 2 + 12;
  const rotateStem =
    Math.round((rotateSize * 0.5 + selectionPad + topChromeClearance) * 10) / 10;
  /*
   * Centro do disco em -rotateStem; fundo em -rotateStem + rotateSize/2.
   * Pill N centrado em y=0 → topo em -edgeThickness/2.
   */
  const rotateStemDraw =
    Math.round(
      Math.max(0, rotateStem - rotateSize / 2 - edgeThickness / 2) * 10,
    ) / 10;
  return {
    handleSize,
    edgeLength,
    edgeThickness,
    adjustSize,
    rotateSize,
    outlineWidth,
    selectionPad,
    handleHalf: Math.round((handleSize / 2) * 10) / 10,
    rotateStem,
    rotateStemDraw,
  };
}

/** CSS custom properties para o canvas do composer. */
export function selectionChromeCssVars(
  metrics: SelectionChromeMetrics,
): Record<string, string> {
  return {
    "--td-selection-handle-size": `${metrics.handleSize}px`,
    "--td-selection-handle-half": `${metrics.handleHalf}px`,
    "--td-selection-edge-length": `${metrics.edgeLength}px`,
    "--td-selection-edge-thickness": `${metrics.edgeThickness}px`,
    "--td-selection-adjust-size": `${metrics.adjustSize}px`,
    "--td-selection-rotate-size": `${metrics.rotateSize}px`,
    "--td-selection-outline-width": `${metrics.outlineWidth}px`,
    "--td-global-selection-pad": `${metrics.selectionPad}px`,
    "--td-selection-rotate-stem": `${metrics.rotateStemDraw}px`,
    "--td-selection-rotate-offset": `${metrics.rotateStem + metrics.rotateSize / 2}px`,
  };
}
