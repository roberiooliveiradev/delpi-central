import type { AppointmentTotals } from "../types/appointments";
import { formatInteger, formatQuantity } from "../utils/formatters";

type SummaryCardsProps = {
  totals: AppointmentTotals | null;
};

export function SummaryCards({ totals }: SummaryCardsProps) {
  const cards = [
    { label: "Apontamentos", value: formatInteger(totals?.appointment_count) },
    { label: "Qtd. produzida", value: formatQuantity(totals?.qty_produced) },
    { label: "Qtd. perdida", value: formatQuantity(totals?.qty_lost) },
    { label: "OPs", value: formatInteger(totals?.op_count) },
    { label: "CTs", value: formatInteger(totals?.work_center_count) },
  ];

  return (
    <section className="pa-kpi-grid" aria-label="Resumo do período">
      {cards.map((card) => (
        <article key={card.label} className="pa-card pa-kpi-card">
          <p className="pa-kpi-card__title">{card.label}</p>
          <p className="pa-kpi-card__value">{card.value}</p>
        </article>
      ))}
    </section>
  );
}
