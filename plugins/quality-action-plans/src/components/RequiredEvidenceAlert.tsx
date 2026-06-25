import type { PlanAction } from "../types/actionPlan";
import type { PlanEvidence } from "../types/rnc8d";
import { listActionsMissingRequiredEvidence } from "../utils/rnc8dDisciplineProgress";

type Props = {
  actions: PlanAction[];
  evidences: PlanEvidence[];
};

export function RequiredEvidenceAlert({ actions, evidences }: Props) {
  const missing = listActionsMissingRequiredEvidence(actions, evidences);

  if (!missing.length) {
    return null;
  }

  return (
    <div className="pac-state pac-state--warning" role="status">
      <strong>Evidência obrigatória pendente</strong>
      <ul className="pac-required-evidence-list">
        {missing.map((action) => (
          <li key={action.id}>
            {action.description.trim() || action.id.slice(0, 8)} — anexe arquivo vinculado à ação.
          </li>
        ))}
      </ul>
    </div>
  );
}
