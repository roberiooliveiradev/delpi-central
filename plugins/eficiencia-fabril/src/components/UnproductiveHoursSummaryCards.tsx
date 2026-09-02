import { CircleDollarSign, ClipboardList, Clock3, Factory, UserRound } from "lucide-react";

import { EF_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { UnproductiveHoursSummaryMetrics } from "../types/unproductiveHours";
import { resolveSummaryNumber } from "../types/unproductiveHours";
import { formatCurrency, formatHours, formatInteger, formatPercent } from "../utils/format";
import { KpiCard } from "./KpiCard";

type UnproductiveHoursSummaryCardsProps = {
  summary: UnproductiveHoursSummaryMetrics | null | undefined;
};

function topResourceLabel(summary: UnproductiveHoursSummaryMetrics | null | undefined): string {
  const top = summary?.top_resource_by_hours ?? summary?.principalRecursoPorHoras;
  if (!top) return "—";
  const name = top.resource ?? top.recurso ?? "";
  const hours = top.total_hours ?? top.totalHoras;
  if (!name) return "—";
  return typeof hours === "number" ? `${name} (${formatHours(hours)})` : name;
}

function topOperatorLabel(summary: UnproductiveHoursSummaryMetrics | null | undefined): string {
  const top = summary?.top_operator_by_hours ?? summary?.principalColaboradorPorHoras;
  if (!top) return "—";
  const name = top.operator_name ?? top.nomeOperador ?? top.operator_code ?? top.codigoOperador ?? "";
  const hours = top.total_hours ?? top.totalHoras;
  if (!name) return "—";
  return typeof hours === "number" ? `${name} (${formatHours(hours)})` : name;
}

export function UnproductiveHoursSummaryCards({ summary }: UnproductiveHoursSummaryCardsProps) {
  const totalHours = resolveSummaryNumber(summary, "total_hours", "totalHoras");
  const totalCost = resolveSummaryNumber(summary, "total_cost", "totalCusto");
  const totalAppointments = resolveSummaryNumber(summary, "total_appointments", "totalApontamentos");
  const pctWithoutCost = resolveSummaryNumber(
    summary,
    "pct_hours_without_cost",
    "percentualHorasSemCusto",
  );

  return (
    <section className="ef-kpi-grid" aria-label="Indicadores de horas improdutivas">
      <KpiCard
        label="Total de horas"
        titleHint={EF_HELP_TOOLTIPS.unproductiveHours.kpis.totalHours}
        value={formatHours(totalHours)}
        icon={<Clock3 size={22} />}
      />
      <KpiCard
        label="Custo total"
        titleHint={EF_HELP_TOOLTIPS.unproductiveHours.kpis.totalCost}
        value={formatCurrency(totalCost)}
        hint={`${formatPercent(pctWithoutCost, 1)} das horas sem custo`}
        icon={<CircleDollarSign size={22} />}
      />
      <KpiCard
        label="Apontamentos"
        titleHint={EF_HELP_TOOLTIPS.unproductiveHours.kpis.appointments}
        value={formatInteger(totalAppointments)}
        icon={<ClipboardList size={22} />}
      />
      <KpiCard
        label="Principal recurso"
        titleHint={EF_HELP_TOOLTIPS.unproductiveHours.kpis.topResource}
        value={topResourceLabel(summary)}
        hint={`Operador: ${topOperatorLabel(summary)}`}
        icon={<Factory size={22} />}
      />
      <KpiCard
        label="Principal operador"
        titleHint={EF_HELP_TOOLTIPS.unproductiveHours.kpis.topOperator}
        value={topOperatorLabel(summary)}
        icon={<UserRound size={22} />}
      />
    </section>
  );
}
