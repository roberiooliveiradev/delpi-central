/**
 * Stacking no editor:
 * - Wrap/conteúdo: sempre o `zIndex` do modelo (ordem de camadas do slide).
 * - Chrome de seleção (handles/resize/rotate): overlay no palco, acima do conteúdo.
 * - Float (+ / pincel / funil): overlay irmão do chrome, acima do chrome e do
 *   group-chrome (CSS 13000) — nunca dentro do wrap (z-index: 6 ficava atrás).
 *
 * Anti-padrão: elevar o wrap selecionado — o corpo do bloco cobria vizinhos
 * com z maior no modelo (ex.: badge sobre tabela).
 */

/** Acima de zIndex típico do slide; abaixo de overlays de UI do deck. */
export const SELECTION_CHROME_STACK_FLOOR = 10_000;

/**
 * Float de opções (chart/kpi/table/input) — acima do chrome de bloco
 * (≤ ~12xxx) e do `.td-composer__group-chrome` (13000).
 */
export const SELECTION_FLOAT_TOOLBAR_STACK_FLOOR = 14_000;

/** z-index de paint do wrap — só o modelo, nunca o floor de chrome. */
export function resolveBlockWrapStackZIndex(params: {
  modelZIndex?: number | null;
}): number {
  const raw = Number(params.modelZIndex);
  return Number.isFinite(raw) && raw > 0 ? Math.round(raw) : 1;
}

function modelStackBase(modelZIndex?: number | null): number {
  const raw = Number(modelZIndex);
  return Number.isFinite(raw) && raw > 0 ? Math.round(raw) : 1;
}

/** Overlay de handles — acima do conteúdo; primário acima do multi. */
export function resolveSelectionChromeOverlayZIndex(params: {
  isPrimarySelection?: boolean;
  modelZIndex?: number | null;
}): number {
  const base = modelStackBase(params.modelZIndex);
  const tier = params.isPrimarySelection ? 2 : 1;
  return SELECTION_CHROME_STACK_FLOOR + tier * 1_000 + base;
}

/**
 * Overlay da coluna flutuante (+ / pincel / funil) — sempre na frente do
 * chrome de redimensionamento e de vizinhos no palco.
 */
export function resolveSelectionFloatToolbarOverlayZIndex(params: {
  modelZIndex?: number | null;
}): number {
  return SELECTION_FLOAT_TOOLBAR_STACK_FLOOR + modelStackBase(params.modelZIndex);
}
