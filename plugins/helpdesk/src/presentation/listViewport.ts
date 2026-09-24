/** Kit-aligned breakpoint: force card/list presentation below this width. */
export const HELPDESK_FORCE_CARDS_MAX_WIDTH = 768;

export function shouldForceTicketCards(viewportWidth: number): boolean {
  if (!Number.isFinite(viewportWidth) || viewportWidth <= 0) return false;
  return viewportWidth <= HELPDESK_FORCE_CARDS_MAX_WIDTH;
}
