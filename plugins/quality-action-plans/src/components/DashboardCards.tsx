import { PAC_BRANCH_OPTIONS } from "../constants/actionPlans";
import type { DashboardSummary } from "../types/actionPlan";

type Props = {
  summary: DashboardSummary;
};

const CARDS: Array<{
  key: "open_plans" | "critical_open" | "waiting_validation" | "completed_this_month" | "overdue_actions" | "overdue_plans";
  label: string;
  hint?: string;
  tone?: "default" | "danger" | "warning" | "success";
}> = [
  { key: "open_plans", label: "Planos abertos" },
  { key: "critical_open", label: "Críticos abertos", tone: "danger" },
  { key: "overdue_plans", label: "Planos com atraso", tone: "warning" },
  { key: "overdue_actions", label: "Ações atrasadas", tone: "warning" },
  { key: "waiting_validation", label: "Aguardando validação" },
  { key: "completed_this_month", label: "Concluídos no mês", tone: "success" },
];

export function DashboardCards({ summary }: Props) {
  return (
    <>
      <div className="pac-dashboard-grid">
        {CARDS.map((card) => (
          <article
            key={card.key}
            className={
              card.tone
                ? `pac-metric-card pac-metric-card--${card.tone}`
                : "pac-metric-card"
            }
          >
            <p className="pac-metric-card__label">{card.label}</p>
            <p className="pac-metric-card__value">{summary[card.key]}</p>
            {card.hint ? <p className="pac-metric-card__hint">{card.hint}</p> : null}
          </article>
        ))}
      </div>
      {summary.by_branch?.length ? (
        <section className="pac-card pac-branch-summary">
          <h2 className="pac-section-title">Por filial</h2>
          <div className="pac-dashboard-grid">
            {summary.by_branch.map((branch) => (
              <article key={branch.branch_code} className="pac-metric-card">
                <p className="pac-metric-card__label">
                  {PAC_BRANCH_OPTIONS.find((item) => item.value === branch.branch_code)?.label ??
                    `Filial ${branch.branch_code}`}
                </p>
                <p className="pac-metric-card__value">{branch.open_plans}</p>
                <p className="pac-metric-card__hint">
                  {branch.critical_open} crítico(s) aberto(s)
                </p>
              </article>
            ))}
          </div>
        </section>
      ) : null}
    </>
  );
}
