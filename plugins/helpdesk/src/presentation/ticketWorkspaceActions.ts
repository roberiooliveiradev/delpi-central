import type { TicketDetail } from "../api/helpdeskApi";

/** Proven ticket write/action modes — capability-driven, no invented roles. */
export type TicketWorkspaceActionId =
  | "reply"
  | "accept_solution"
  | "reject_solution"
  | "add_document";

export type TicketWorkspaceAction = {
  id: TicketWorkspaceActionId;
  label: string;
  submitLabel: string;
};

const REPLY: TicketWorkspaceAction = {
  id: "reply",
  label: "Responder",
  submitLabel: "Enviar",
};

const ACCEPT_SOLUTION: TicketWorkspaceAction = {
  id: "accept_solution",
  label: "Aceitar solução",
  submitLabel: "Aceitar solução",
};

const REJECT_SOLUTION: TicketWorkspaceAction = {
  id: "reject_solution",
  label: "Recusar / reabrir",
  submitLabel: "Recusar / reabrir",
};

const ADD_DOCUMENT: TicketWorkspaceAction = {
  id: "add_document",
  label: "Adicionar documento",
  submitLabel: "Adicionar documento",
};

/** Surfaces available in left/context nav — only proven content. */
export type TicketWorkspaceSurfaceId = "conversation" | "details";

export const TICKET_WORKSPACE_SURFACES: { id: TicketWorkspaceSurfaceId; label: string }[] = [
  { id: "conversation", label: "Conversa" },
  { id: "details", label: "Detalhes" },
];

/**
 * Build action menu from ticket capabilities only.
 * Frontend disclosure ≠ AuthZ — backend remains authoritative.
 */
export function ticketWorkspaceActions(ticket: Pick<
  TicketDetail,
  "can_followup" | "can_accept_solution" | "can_reject_solution"
>): TicketWorkspaceAction[] {
  const actions: TicketWorkspaceAction[] = [];
  if (ticket.can_followup !== false) {
    actions.push(REPLY);
    // Standalone upload uses the same proven attachment endpoint as reply attach.
    actions.push(ADD_DOCUMENT);
  }
  if (ticket.can_accept_solution) actions.push(ACCEPT_SOLUTION);
  if (ticket.can_reject_solution) actions.push(REJECT_SOLUTION);
  return actions;
}

export function defaultTicketWorkspaceAction(
  actions: readonly TicketWorkspaceAction[],
): TicketWorkspaceActionId | null {
  if (actions.length === 0) return null;
  if (actions.some((item) => item.id === "reply")) return "reply";
  return actions[0]?.id ?? null;
}

export function ticketWorkspaceActionById(
  actions: readonly TicketWorkspaceAction[],
  id: TicketWorkspaceActionId | null,
): TicketWorkspaceAction | null {
  if (!id) return null;
  return actions.find((item) => item.id === id) ?? null;
}
