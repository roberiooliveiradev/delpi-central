/**
 * Stacking no editor:
 * - Wrap/conteúdo: sempre o `zIndex` do modelo (ordem de camadas do slide).
 * - Chrome de seleção (handles/resize/rotate): overlay no palco, acima do conteúdo.
 *
 * Anti-padrão: elevar o wrap selecionado — o corpo do bloco cobria vizinhos
 * com z maior no modelo (ex.: badge sobre tabela).
 */

/** Acima de zIndex típico do slide; abaixo de overlays de UI do deck. */
export const SELECTION_CHROME_STACK_FLOOR = 10_000;

/** z-index de paint do wrap — só o modelo, nunca o floor de chrome. */
export function resolveBlockWrapStackZIndex(params: {
  modelZIndex?: number | null;
}): number {
  const raw = Number(params.modelZIndex);
  return Number.isFinite(raw) && raw > 0 ? Math.round(raw) : 1;
}

/** Overlay de handles — acima do conteúdo; primário acima do multi. */
export function resolveSelectionChromeOverlayZIndex(params: {
  isPrimarySelection?: boolean;
  modelZIndex?: number | null;
}): number {
  const raw = Number(params.modelZIndex);
  const base = Number.isFinite(raw) && raw > 0 ? Math.round(raw) : 1;
  const tier = params.isPrimarySelection ? 2 : 1;
  return SELECTION_CHROME_STACK_FLOOR + tier * 1_000 + base;
}
