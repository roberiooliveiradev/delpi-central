/**
 * Public GLPI host used by the portal menu `helpdesk.console`.
 * Solicitante deep-links reuse the same origin + SAML entry (no technician permission required).
 */
export const GLPI_PUBLIC_ORIGIN = "https://helpdesk.centraldelpi.com.br";
export const GLPI_SAML_IDP_ID = "1";

/** SSO entry that lands on the ticket form after SAML (same host as Console do helpdesk). */
export function glpiTicketFormUrl(ticketId: number): string {
  const id = Math.trunc(Number(ticketId));
  const base = `${GLPI_PUBLIC_ORIGIN}/?samlIdpId=${GLPI_SAML_IDP_ID}`;
  if (!Number.isFinite(id) || id <= 0) return base;
  const formPath = `/front/ticket.form.php?id=${id}`;
  return `${base}&redirect=${encodeURIComponent(formPath)}`;
}
