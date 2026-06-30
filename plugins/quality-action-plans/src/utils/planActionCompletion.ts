import type { PlanAction } from "../types/actionPlan";
import { ACTION_STATUSES } from "../constants/actionPlans";

const TERMINAL_ACTION_STATUSES = new Set(["completed", "cancelled"]);

const MAX_LISTED_ACTIONS = 3;
const DESCRIPTION_SNIPPET_LEN = 72;

export function listIncompletePlanActions(actions: PlanAction[]): PlanAction[] {
  return actions.filter((action) => !TERMINAL_ACTION_STATUSES.has(action.status));
}

export function openPlanActionsCountLabel(count: number): string {
  if (count === 1) {
    return "1 ação aberta";
  }
  return `${count} ações abertas`;
}

function actionSnippet(action: PlanAction): string {
  const description = action.description.trim();
  if (!description) {
    return action.id;
  }
  if (description.length <= DESCRIPTION_SNIPPET_LEN) {
    return description;
  }
  return `${description.slice(0, DESCRIPTION_SNIPPET_LEN)}…`;
}

export function buildIncompletePlanActionsMessage(actions: PlanAction[]): string {
  const count = actions.length;
  if (count === 0) {
    return "";
  }

  const header =
    `Ainda há ${count} ação(ões) não concluída(s). ` +
    "Revise a seção de ações e conclua ou cancele as pendências quando possível.";
  const lines = [header];
  for (const action of actions.slice(0, MAX_LISTED_ACTIONS)) {
    const statusLabel = ACTION_STATUSES[action.status] ?? action.status;
    lines.push(`• ${actionSnippet(action)} (${statusLabel})`);
  }
  if (count > MAX_LISTED_ACTIONS) {
    lines.push(`… e mais ${count - MAX_LISTED_ACTIONS}.`);
  }
  return lines.join("\n");
}
