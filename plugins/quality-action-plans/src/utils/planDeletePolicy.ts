import type { ActionPlanSummary } from "../types/actionPlan";

type PlanDeleteGuardInput = Pick<
  ActionPlanSummary,
  "status" | "effectiveness_approval_status"
>;

export function canDeleteActionPlan(plan: PlanDeleteGuardInput | null | undefined): boolean {
  if (!plan) return false;
  if (plan.status === "completed") return false;
  if (plan.effectiveness_approval_status === "approved") return false;
  if (plan.effectiveness_approval_status === "pending_review") return false;
  return true;
}

export function planDeleteBlockedReason(
  plan: PlanDeleteGuardInput | null | undefined,
): string | null {
  if (!plan) return null;
  if (plan.status === "completed") {
    return "Planos concluídos não podem ser excluídos.";
  }
  if (plan.effectiveness_approval_status === "approved") {
    return "Planos com eficácia aprovada não podem ser excluídos.";
  }
  if (plan.effectiveness_approval_status === "pending_review") {
    return "Planos com eficácia pendente de aprovação não podem ser excluídos.";
  }
  return null;
}
