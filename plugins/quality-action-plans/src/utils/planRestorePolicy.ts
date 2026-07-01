import type { ActionPlanSummary } from "../types/actionPlan";

type PlanRestoreGuardInput = Pick<
  ActionPlanSummary,
  "status" | "effectiveness_approval_status" | "was_ever_completed"
>;

export function canRestorePlanRevision(plan: PlanRestoreGuardInput | null | undefined): boolean {
  if (!plan) return false;
  if (plan.status === "completed" || plan.was_ever_completed) return false;
  if (plan.effectiveness_approval_status === "approved") return false;
  if (plan.effectiveness_approval_status === "pending_review") return false;
  return true;
}

export function planRestoreBlockedReason(
  plan: PlanRestoreGuardInput | null | undefined,
): string | null {
  if (!plan) return null;
  if (plan.status === "completed" || plan.was_ever_completed) {
    return "Planos que já foram concluídos não podem ser restaurados, mesmo após reabertura.";
  }
  if (plan.effectiveness_approval_status === "approved") {
    return "Planos com eficácia aprovada não podem ser restaurados.";
  }
  if (plan.effectiveness_approval_status === "pending_review") {
    return "Planos com eficácia pendente de aprovação não podem ser restaurados.";
  }
  return null;
}
