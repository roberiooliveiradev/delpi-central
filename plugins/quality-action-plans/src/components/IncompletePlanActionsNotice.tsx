import type { PlanAction } from "../types/actionPlan";
import { ACTION_STATUSES } from "../constants/actionPlans";
import { listIncompletePlanActions } from "../utils/planActionCompletion";

type Props = {
  actions: PlanAction[];
};

export function IncompletePlanActionsNotice({ actions }: Props) {
  const incomplete = listIncompletePlanActions(actions);

  if (!incomplete.length) {
    return null;
  }

  return (
    <div className="pac-state pac-state--warning" role="status" style={{ marginBottom: "0.75rem" }}>
      <strong>Ações ainda não concluídas</strong>
      <p className="pac-muted" style={{ margin: "0.35rem 0 0.5rem" }}>
        Ainda há {incomplete.length} ação(ões) aberta(s). Você pode prosseguir com a eficácia,
        mas revise e conclua ou cancele as pendências quando possível.
      </p>
      <ul className="pac-required-evidence-list">
        {incomplete.map((action) => (
          <li key={action.id}>
            {action.description.trim() || action.id.slice(0, 8)} —{" "}
            {ACTION_STATUSES[action.status] ?? action.status}
          </li>
        ))}
      </ul>
    </div>
  );
}
