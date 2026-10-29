import type { HelpdeskApiError, TicketDeleteResult, TicketDetail } from "../api/helpdeskApi";

/**
 * Move-to-trash flow for the ticket detail page.
 *
 * `can_delete` is UX disclosure only — the BFF computed it from the actor's
 * own GLPI session profile (`Ticket::canDeleteItem` mirror), and the GLPI
 * DELETE endpoint stays the authority of record. The UI therefore only
 * uses the flag to show/hide the affordance; errors still render typed.
 */
export function canShowTicketDelete(
  ticket: Pick<TicketDetail, "can_delete"> | null | undefined,
): boolean {
  return ticket?.can_delete === true;
}

/**
 * Authoritative postcondition of a move-to-trash write.
 *
 * The BFF returns `deleted: true` only after its own read-back proved the
 * ticket left the same-user active view. Any other 2xx shape is an
 * unconfirmed outcome — never presented as success.
 */
export function ticketDeleteConfirmed(result: TicketDeleteResult | null | undefined): boolean {
  return result?.deleted === true && result.delete_semantics === "trash";
}

export function ticketDeleteSuccessText(ticketId: number | string): string {
  return `Chamado #${ticketId} movido para a lixeira.`;
}

export const TICKET_DELETE_UNCONFIRMED_TEXT =
  "A exclusão foi enviada, mas o helpdesk não confirmou a remoção do chamado. " +
  "Verifique a lista antes de tentar de novo.";

/** Typed error copy for the delete intent (pt-BR, error-code driven). */
export function ticketDeleteErrorText(error: unknown): string {
  const code = error instanceof Object && "code" in error ? String((error as HelpdeskApiError).code) : "";
  const status =
    error instanceof Object && "status" in error ? Number((error as HelpdeskApiError).status) : 0;
  if (code === "idempotency_in_flight") {
    return "Uma tentativa anterior pode ter sido concluída. Recarregue a página e verifique o chamado antes de tentar de novo.";
  }
  if (code === "glpi_forbidden" || status === 403) {
    return "Seu perfil no helpdesk não permite excluir este chamado.";
  }
  if (code === "not_found" || status === 404) {
    return "Este chamado não está mais disponível para você. Atualize a página.";
  }
  if (code === "glpi_link_required" || status === 401) {
    return "Sua sessão com o helpdesk expirou. Entre novamente para continuar.";
  }
  if (status === 409) {
    return "O chamado mudou enquanto a exclusão era confirmada. Atualize a página e tente de novo.";
  }
  if (status >= 500 || code === "glpi_unavailable") {
    return "O helpdesk está indisponível. Tente novamente em instantes.";
  }
  return "Não foi possível excluir o chamado. Tente novamente.";
}

// ---------------------------------------------------------------------------
// Flash notice — staged before navigating away (detail → list).
// ---------------------------------------------------------------------------

const STAGED_DELETE_NOTICE_KEY = "helpdesk:ticket-delete-notice";

export function stageTicketDeleteNotice(text: string): void {
  try {
    sessionStorage.setItem(STAGED_DELETE_NOTICE_KEY, text);
  } catch {
    /* storage unavailable — notice simply isn't staged */
  }
}

export function consumeTicketDeleteNotice(): string | null {
  try {
    const text = sessionStorage.getItem(STAGED_DELETE_NOTICE_KEY);
    if (!text) return null;
    sessionStorage.removeItem(STAGED_DELETE_NOTICE_KEY);
    return text;
  } catch {
    return null;
  }
}
