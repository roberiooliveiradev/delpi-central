import type { TicketDetail } from "../api/helpdeskApi";

/** Proven ticket write/action modes — capability-driven, no invented roles. */
export type TicketWorkspaceActionId =
  | "reply"
  | "create_solution"
  | "create_task"
  | "attach_file"
  | "request_approval"
  | "accept_solution"
  | "reject_solution";

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

const CREATE_SOLUTION: TicketWorkspaceAction = {
  id: "create_solution",
  label: "Adicionar solução",
  submitLabel: "Adicionar solução",
};

const CREATE_TASK: TicketWorkspaceAction = {
  id: "create_task",
  label: "Criar tarefa",
  submitLabel: "Criar tarefa",
};

const ATTACH_FILE: TicketWorkspaceAction = {
  id: "attach_file",
  label: "Anexar arquivo",
  submitLabel: "Anexar arquivo",
};

const REQUEST_APPROVAL: TicketWorkspaceAction = {
  id: "request_approval",
  label: "Pedir aprovação",
  submitLabel: "Pedir aprovação",
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
  | "can_followup"
  | "can_create_solution"
  | "can_create_task"
  | "can_request_approval"
  | "can_accept_solution"
  | "can_reject_solution"
>): TicketWorkspaceAction[] {
  const actions: TicketWorkspaceAction[] = [];
  if (ticket.can_followup !== false) {
    actions.push(REPLY);
  }
  if (ticket.can_create_solution) actions.push(CREATE_SOLUTION);
  if (ticket.can_create_task) actions.push(CREATE_TASK);
  if (ticket.can_followup !== false) {
    // Attachment endpoint (H12 Document + Document_Item) — not a separate Document entity action.
    actions.push(ATTACH_FILE);
  }
  if (ticket.can_request_approval) actions.push(REQUEST_APPROVAL);
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
