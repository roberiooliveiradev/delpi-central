import { ClipboardCheck } from "lucide-react";

import { PAC_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  branchLabel,
  detailPath,
  effectivenessPendingPath,
  EFFECTIVENESS_STATUSES,
} from "../../constants/actionPlans";
import type { DashboardEffectivenessPendingAlert } from "../../types/actionPlan";
import { formatEffectivenessSubmittedBy } from "../../utils/actorDisplay";
import { KpiCard } from "../ui/KpiCard";
import { SectionCard } from "../ui/SectionCard";

type Props = {
  alert?: DashboardEffectivenessPendingAlert | null;
  loading?: boolean;
  onNavigate: (path: string) => void;
};

function proposedLabel(value?: string | null): string {
  if (!value) return "—";
  return EFFECTIVENESS_STATUSES.find((item) => item.value === value)?.label ?? value;
}

export function DashboardEffectivenessPendingCard({
  alert,
  loading = false,
  onNavigate,
}: Props) {
  if (!alert && !loading) {
    return null;
  }

  const plans = alert?.top_plans ?? [];
  const pendingCount = alert?.pending_plans ?? 0;

  return (
    <section className="pac-stalled-alert pac-effectiveness-pending-alert">
      <div className="pac-dashboard-grid pac-dashboard-grid--stalled">
        <KpiCard
          label="Aprovações de eficácia pendentes"
          value={loading ? "…" : pendingCount}
          tone={pendingCount > 0 ? "warning" : "default"}
          icon={<ClipboardCheck size={22} strokeWidth={1.75} />}
          hint={
            loading
              ? undefined
              : PAC_HELP_TOOLTIPS.alerts.effectivenessPending
          }
          loading={loading}
        />
      </div>

      <SectionCard
        title="Fila de aprovação de eficácia"
        hint={PAC_HELP_TOOLTIPS.alerts.effectivenessPending}
        subtitle="Submissões aguardando decisão — coordenação deve aprovar ou rejeitar."
        actions={
          pendingCount > 0 ? (
            <button
              type="button"
              className="pac-ghost-btn"
              onClick={() => onNavigate(effectivenessPendingPath())}
            >
              Abrir fila
            </button>
          ) : undefined
        }
      >
        {loading ? (
          <p className="pac-muted">Carregando fila de aprovações…</p>
        ) : plans.length ? (
          <ul className="pac-stalled-alert__list">
            {plans.map((plan) => (
              <li key={plan.id} className="pac-stalled-alert__item">
                <div>
                  <strong>
                    {plan.code ?? plan.id}
                    {plan.title ? ` · ${plan.title}` : ""}
                  </strong>
                  <p className="pac-muted">
                    {branchLabel(plan.branch_code)} · proposta: {proposedLabel(plan.effectiveness_proposed_status)}
                    {plan.effectiveness_submitted_by || plan.effectiveness_submitted_by_name
                      ? ` · por ${formatEffectivenessSubmittedBy(plan)}`
                      : ""}
                  </p>
                </div>
                <button
                  type="button"
                  className="pac-ghost-btn"
                  onClick={() => onNavigate(detailPath(plan.id))}
                >
                  Abrir plano
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="pac-muted">Nenhuma aprovação de eficácia pendente no momento.</p>
        )}
      </SectionCard>
    </section>
  );
}
