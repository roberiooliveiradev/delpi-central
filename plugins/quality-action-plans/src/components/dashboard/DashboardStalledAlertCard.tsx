import { AlertTriangle } from "lucide-react";

import { branchLabel, detailPath } from "../../constants/actionPlans";
import type { DashboardStalledAlert } from "../../types/actionPlan";
import { KpiCard } from "../ui/KpiCard";
import { SectionCard } from "../ui/SectionCard";

type Props = {
  alert?: DashboardStalledAlert | null;
  loading?: boolean;
  onNavigate: (path: string) => void;
};

export function DashboardStalledAlertCard({ alert, loading = false, onNavigate }: Props) {
  if (!alert && !loading) {
    return null;
  }

  const plans = alert?.top_plans ?? [];
  const stallDays = alert?.stall_days ?? 7;

  return (
    <section className="pac-stalled-alert">
      <div className="pac-dashboard-grid pac-dashboard-grid--stalled">
        <KpiCard
          label="Críticos sem movimento"
          value={loading ? "…" : (alert?.stalled_plans ?? 0)}
          tone={alert && alert.stalled_plans > 0 ? "danger" : "default"}
          icon={<AlertTriangle size={22} strokeWidth={1.75} />}
          hint={
            loading
              ? undefined
              : `Sem atualização há ≥ ${stallDays} dias (~5 dias úteis)`
          }
          loading={loading}
        />
      </div>

      <SectionCard
        title="Planos críticos parados"
        subtitle="Severidade crítica sem atualização recente — exige acompanhamento da coordenação."
      >
        {loading ? (
          <p className="pac-muted">Carregando alertas de SLA…</p>
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
                    {branchLabel(plan.branch_code)} · {plan.days_without_update} dia(s) parado
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
          <p className="pac-muted">Nenhum plano crítico parado no momento.</p>
        )}
      </SectionCard>
    </section>
  );
}
