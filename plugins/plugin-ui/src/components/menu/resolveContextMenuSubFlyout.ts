import {
  resolveAnchoredPanelCoords,
  type AnchoredPanelCoords,
} from "../shape/anchoredPanelCoords";

export type ContextMenuSubFlyoutSide = "right" | "left";

export type ContextMenuSubFlyoutInput = {
  trigger: { left: number; top: number; right: number; bottom: number; width: number; height: number };
  panelWidth: number;
  panelHeight: number;
  viewportWidth: number;
  viewportHeight: number;
  gap?: number;
  margin?: number;
};

export type ContextMenuSubFlyoutCoords = {
  top: number;
  left: number;
  side: ContextMenuSubFlyoutSide;
  /** Altura máxima no viewport a partir de `top` (scroll só se o conteúdo passar disso). */
  maxHeight: number;
};

/**
 * Posiciona o flyout do `ContextMenuSub` (Organizar ▸ / Alinhar ▸ / Girar ▸)
 * com a mesma inteligência dos AnchoredPanel: lado preferido à direita,
 * flip à esquerda e clamp vertical (sobe quando há espaço acima).
 */
export function resolveContextMenuSubFlyout(
  input: ContextMenuSubFlyoutInput,
): ContextMenuSubFlyoutCoords {
  const margin = input.margin ?? 8;
  const vh = input.viewportHeight;
  const naturalHeight = Math.max(0, input.panelHeight);
  /* Altura usada no clamp: cabe no viewport inteiro — sobe o painel em vez de só scroll. */
  const heightForClamp = Math.min(naturalHeight, Math.max(0, vh - 2 * margin));

  const coords: AnchoredPanelCoords = resolveAnchoredPanelCoords({
    anchor: input.trigger,
    panelWidth: input.panelWidth,
    panelHeight: heightForClamp,
    gap: input.gap ?? 2,
    margin,
    viewportWidth: input.viewportWidth,
    viewportHeight: vh,
    preferredPlacement: "right",
    allowFlip: true,
  });

  const side: ContextMenuSubFlyoutSide =
    coords.placement === "left" ? "left" : "right";

  const maxHeight = Math.max(48, vh - coords.top - margin);

  return {
    top: coords.top,
    left: coords.left,
    side,
    maxHeight,
  };
}
