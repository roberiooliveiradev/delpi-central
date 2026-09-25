import type { TicketValidation } from "../api/helpdeskApi";

/** Matches BFF mapping.VALIDATION_WAITING — row status only, not ticket-global. */
export const VALIDATION_STATUS_WAITING = 2;
export const VALIDATION_STATUS_ACCEPTED = 3;
export const VALIDATION_STATUS_REFUSED = 4;

export function validationStatusLabel(status: number): string {
  switch (status) {
    case VALIDATION_STATUS_WAITING:
      return "Aguardando decisão";
    case VALIDATION_STATUS_ACCEPTED:
      return "Aceita";
    case VALIDATION_STATUS_REFUSED:
      return "Recusada";
    default:
      return `Status ${status}`;
  }
}

export function approvalSummaryCounts(validations: readonly TicketValidation[] | undefined): {
  total: number;
  pending: number;
} {
  const items = validations ?? [];
  return {
    total: items.length,
    pending: items.filter((item) => item.status === VALIDATION_STATUS_WAITING).length,
  };
}
