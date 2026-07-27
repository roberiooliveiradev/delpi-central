/**
 * Stacking visual do wrap no editor — sem alterar `style.zIndex` persistido.
 *
 * Handles/outline vivem dentro do wrap; se o vizinho tem z maior (ou DOM
 * posterior na mesma faixa), cobre resize/adjust. Elevamos só o paint da
 * seleção acima do piso do modelo.
 */

/** Acima de zIndex típico do slide; abaixo de overlays de UI do deck. */
export const SELECTION_CHROME_STACK_FLOOR = 10_000;

export function resolveBlockWrapStackZIndex(params: {
  modelZIndex?: number | null;
  /** Outline/handles visíveis neste wrap. */
  selectionChromeVisible: boolean;
  /** Primário da seleção (acima dos demais multi). */
  isPrimarySelection?: boolean;
}): number {
  const raw = Number(params.modelZIndex);
  const base = Number.isFinite(raw) && raw > 0 ? Math.round(raw) : 1;
  if (!params.selectionChromeVisible) return base;
  const tier = params.isPrimarySelection ? 2 : 1;
  return SELECTION_CHROME_STACK_FLOOR + tier * 1_000 + base;
}
