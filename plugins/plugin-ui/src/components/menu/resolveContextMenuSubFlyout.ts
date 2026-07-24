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
};

/**
 * Posiciona o flyout do `ContextMenuSub` (Organizar ▸ / Alinhar ▸ / Girar ▸)
 * com a mesma inteligência dos AnchoredPanel: lado preferido à direita,
 * flip à esquerda e clamp vertical no viewport.
 */
export function resolveContextMenuSubFlyout(
  input: ContextMenuSubFlyoutInput,
): ContextMenuSubFlyoutCoords {
  const coords: AnchoredPanelCoords = resolveAnchoredPanelCoords({
    anchor: input.trigger,
    panelWidth: input.panelWidth,
    panelHeight: input.panelHeight,
    gap: input.gap ?? 2,
    margin: input.margin ?? 8,
    viewportWidth: input.viewportWidth,
    viewportHeight: input.viewportHeight,
    preferredPlacement: "right",
    allowFlip: true,
  });

  const side: ContextMenuSubFlyoutSide =
    coords.placement === "left" ? "left" : "right";

  return {
    top: coords.top,
    left: coords.left,
    side,
  };
}
