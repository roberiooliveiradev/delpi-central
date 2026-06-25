import { Repeat } from "lucide-react";

import { branchLabel, recurrencePath } from "../../constants/actionPlans";
import type { DashboardRecurrenceAlert } from "../../types/actionPlan";
import { KpiCard } from "../ui/KpiCard";
import { SectionCard } from "../ui/SectionCard";

type Props = {
  alert?: DashboardRecurrenceAlert | null;
  loading?: boolean;
  onNavigate: (path: string) => void;
};

export function DashboardRecurrenceAlertCard({ alert, loading = false, onNavigate }: Props) {
  if (!alert && !loading) {
    return null;
  }

  const windowMonths = alert?.window_months ?? 12;
  const groups = alert?.top_groups ?? [];

  return (
    <section className="pac-recurrence-alert">
      <div className="pac-dashboard-grid pac-dashboard-grid--recurrence">
        <KpiCard
          label="Reincidências detectadas"
          value={loading ? "…" : (alert?.groups_detected ?? 0)}
          tone={alert && alert.groups_detected > 0 ? "warning" : "default"}
          icon={<Repeat size={22} strokeWidth={1.75} />}
          hint={
            loading
              ? undefined
              : `${windowMonths} meses · ${alert?.plans_in_window ?? 0} planos · ${alert?.open_plans_in_recurrence ?? 0} abertos`
          }
          loading={loading}
        />
      </div>

      <SectionCard
        title="Padrões recorrentes recentes"
        subtitle={`Mesmo produto + modo de falha com ≥ 2 aberturas nos últimos ${windowMonths} meses.`}
        actions={
          <button type="button" className="pac-ghost-btn" onClick={() => onNavigate(recurrencePath())}>
            Ver painel de recorrência
          </button>
        }
      >
        {loading ? (
          <p className="pac-muted">Carregando reincidências…</p>
        ) : groups.length ? (
          <ul className="pac-recurrence-alert__list">
            {groups.map((group) => (
              <li key={group.recurrence_key} className="pac-recurrence-alert__item">
                <div>
                  <strong>
                    {group.product_code ?? "—"}
                    {group.failure_mode ? ` · ${group.failure_mode}` : ""}
                  </strong>
                  <p className="pac-muted">
                    {branchLabel(group.branch_code)} · {group.plans_in_window} no período ·{" "}
                    {group.open_plans} abertos
                  </p>
                </div>
                <span className="pac-recurrence-alert__badge">{group.total_plans} total</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="pac-muted">Nenhuma reincidência detectada no período.</p>
        )}
      </SectionCard>
    </section>
  );
}
