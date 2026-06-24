import type { DashboardSummary } from "../types/actionPlan";

type Props = {
  summary: DashboardSummary;
};

const CARDS: Array<{
  key: keyof DashboardSummary;
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
  );
}
