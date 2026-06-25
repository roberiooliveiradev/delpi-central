import type { ActionPlanSummary } from "../types/actionPlan";

type Props = {
  plan: Pick<
    ActionPlanSummary,
    "status" | "sla_level" | "days_without_update" | "sla_breach_days"
  >;
};

export function PlanSlaBadge({ plan }: Props) {
  const level = plan.sla_level ?? "ok";
  if (level === "ok" || plan.status === "completed" || plan.status === "cancelled") {
    return <span className="pac-muted">—</span>;
  }

  const days = plan.days_without_update ?? 0;
  const breach = plan.sla_breach_days ?? days;
  const label =
    level === "breached"
      ? `Parado ${days}d (meta ${breach}d)`
      : `Atenção ${days}d`;

  return (
    <span className={`pac-badge pac-badge--sla pac-badge--sla-${level}`} title={label}>
      {level === "breached" ? "SLA estourado" : "SLA em risco"}
    </span>
  );
}
