import {
  Clock3,
  CircleDollarSign,
  ClipboardList,
  Factory,
} from "lucide-react";

import type { RetrabalhoResumo } from "../types/retrabalho";
import { formatCurrencyBrl, formatHours, formatInteger } from "../utils/formatters";
import { KpiCard } from "./KpiCard";

type SummaryCardsProps = {
  resumo: RetrabalhoResumo | null;
  loading?: boolean;
};

export function SummaryCards({ resumo, loading = false }: SummaryCardsProps) {
  const principalRecurso = resumo?.principalRecursoPorHoras?.recurso
    ? `${resumo.principalRecursoPorHoras.recurso} (${formatHours(resumo.principalRecursoPorHoras.totalHoras)})`
    : "—";

  return (
    <div className="cr-kpi-grid">
      <KpiCard title="Total de horas" value={formatHours(resumo?.totalHoras)} icon={<Clock3 size={20} />} loading={loading} />
      <KpiCard title="Custo total" value={formatCurrencyBrl(resumo?.totalCusto)} icon={<CircleDollarSign size={20} />} loading={loading} />
      <KpiCard title="Apontamentos" value={formatInteger(resumo?.totalApontamentos)} icon={<ClipboardList size={20} />} loading={loading} />
      <KpiCard title="Principal recurso" value={principalRecurso} icon={<Factory size={20} />} loading={loading} />
    </div>
  );
}
