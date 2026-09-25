import type { TicketDetail } from "../api/helpdeskApi";

import {
  SELECTOR_ACTION_IDS,
  ticketActionPresentation,
} from "./ticketActionPresentation";

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

function actionFromId(id: TicketWorkspaceActionId): TicketWorkspaceAction {
  const presentation = ticketActionPresentation(id);
  return {
    id,
    label: presentation.label,
    submitLabel: presentation.submitLabel,
  };
}

/** Surfaces available in left/context nav — only proven content (OPS-006A). */
export type TicketWorkspaceSurfaceId = "conversation" | "details" | "approvals";

export const TICKET_WORKSPACE_SURFACES: { id: TicketWorkspaceSurfaceId; label: string }[] = [
  { id: "conversation", label: "Conversa" },
  { id: "details", label: "Detalhes" },
  { id: "approvals", label: "Aprovações" },
];

/**
 * Build action menu from ticket capabilities only.
 * Frontend disclosure ≠ AuthZ — backend remains authoritative.
 * Accept/reject solution stay capability-driven but open as contextual cards
 * (also reachable from lifecycle cue); still listed when capability is true so
 * keyboard users can select them if no cue is visible.
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
    actions.push(actionFromId("reply"));
  }
  if (ticket.can_create_solution) actions.push(actionFromId("create_solution"));
  if (ticket.can_create_task) actions.push(actionFromId("create_task"));
  if (ticket.can_followup !== false) {
    // Attachment endpoint (H12 Document + Document_Item) — not a separate Document entity action.
    actions.push(actionFromId("attach_file"));
  }
  if (ticket.can_request_approval) actions.push(actionFromId("request_approval"));
  if (ticket.can_accept_solution) actions.push(actionFromId("accept_solution"));
  if (ticket.can_reject_solution) actions.push(actionFromId("reject_solution"));
  return actions;
}

/** Selector-primary actions (idle menu). Lifecycle accept/reject remain available via full list. */
export function ticketWorkspaceSelectorActions(
  actions: readonly TicketWorkspaceAction[],
): TicketWorkspaceAction[] {
  const allowed = new Set<string>(SELECTOR_ACTION_IDS);
  return actions.filter((item) => allowed.has(item.id));
}

/** Idle default: no composer open. */
export function defaultTicketWorkspaceAction(
  _actions: readonly TicketWorkspaceAction[],
): TicketWorkspaceActionId | null {
  return null;
}

export function ticketWorkspaceActionById(
  actions: readonly TicketWorkspaceAction[],
  id: TicketWorkspaceActionId | null,
): TicketWorkspaceAction | null {
  if (!id) return null;
  return actions.find((item) => item.id === id) ?? null;
}
