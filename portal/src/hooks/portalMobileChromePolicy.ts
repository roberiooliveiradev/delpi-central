/** Largura máxima (inclusive) em que o chrome mobile substitui controles desktop. */
export const PORTAL_NARROW_VIEWPORT_QUERY = "(max-width: 1024px)";

/**
 * Barra mobile (menu / apps / tema) e sidebar drawer são mutuamente exclusivos:
 * sidebar fechada → barra visível; sidebar aberta → barra oculta.
 */
export function resolvePortalMobileNavVisible(
  isNarrowViewport: boolean,
  sidebarCollapsed: boolean,
): boolean {
  return isNarrowViewport && sidebarCollapsed;
}
