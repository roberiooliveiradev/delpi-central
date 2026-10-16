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
  | "reject_solution"
  | "decide_validation"
  | "submit_satisfaction";

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
 */
export function ticketWorkspaceActions(ticket: Pick<
  TicketDetail,
  | "can_followup"
  | "can_create_solution"
  | "can_create_task"
  | "can_request_approval"
  | "can_accept_solution"
  | "can_reject_solution"
  | "can_decide_validation"
  | "can_submit_satisfaction"
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
  if (ticket.can_decide_validation) actions.push(actionFromId("decide_validation"));
  if (ticket.can_submit_satisfaction) actions.push(actionFromId("submit_satisfaction"));
  return actions;
}

/**
 * Selector actions ordered by SELECTOR_ACTION_IDS — pending lifecycle
 * decisions (accept/reject) surface first when capabilities allow them.
 */
export function ticketWorkspaceSelectorActions(
  actions: readonly TicketWorkspaceAction[],
): TicketWorkspaceAction[] {
  const order = new Map<string, number>(
    SELECTOR_ACTION_IDS.map((id, index) => [id, index]),
  );
  return actions
    .filter((item) => order.has(item.id))
    .sort((a, b) => (order.get(a.id) ?? 0) - (order.get(b.id) ?? 0));
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
