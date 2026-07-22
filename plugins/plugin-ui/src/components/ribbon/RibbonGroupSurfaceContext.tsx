import { createContext, useContext } from "react";

/**
 * Onde os filhos de um `RibbonGroup` estão sendo renderizados.
 * - `band` — faixa expandida (tiles + popovers internos OK)
 * - `section-popover` — dentro do popover do grupo colapsado (achatar nested portals)
 */
export type RibbonGroupSurface = "band" | "section-popover";

const RibbonGroupSurfaceContext = createContext<RibbonGroupSurface>("band");

export const RibbonGroupSurfaceProvider = RibbonGroupSurfaceContext.Provider;

export function useRibbonGroupSurface(): RibbonGroupSurface {
  return useContext(RibbonGroupSurfaceContext);
}

/** True quando controles devem renderizar painel inline (sem segundo AnchoredPanelPortal). */
export function useRibbonSectionPopoverSurface(): boolean {
  return useRibbonGroupSurface() === "section-popover";
}
