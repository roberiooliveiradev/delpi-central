import {
  CheckCircle2,
  Clock3,
  ClipboardList,
  PackageSearch,
  ShieldAlert,
  TrendingUp,
} from "lucide-react";

import type { InspecoesEntradaResumo } from "../types/inspecoesEntradaDashboard";
import { formatAverageTime, formatPercent } from "../utils/format";
import { KpiCard } from "./KpiCard";

type SummaryCardsProps = {
  resumo: InspecoesEntradaResumo | null;
  loading: boolean;
  error: string | null;
};

export function SummaryCards({ resumo, loading, error }: SummaryCardsProps) {
  if (!loading && error) {
    return (
      <div className="ie-alert ie-alert--error" role="alert">
        <p>{error}</p>
      </div>
    );
  }

  const pending = resumo?.pending_inspections ?? 0;
  const rejected = resumo?.rejected_inspections ?? 0;

  return (
    <div className="ie-dashboard-kpis">
      <section className="ie-kpi-grid ie-kpi-grid--primary" aria-label="Indicadores principais">
        <KpiCard
          title="Pendentes"
          value={pending.toLocaleString("pt-BR")}
          subtitle="Aguardando laudo"
          icon={<PackageSearch size={16} />}
          loading={loading}
          variant={pending > 0 ? "warning" : "default"}
        />
        <KpiCard
          title="Já inspecionadas"
          value={(resumo?.inspected ?? 0).toLocaleString("pt-BR")}
          subtitle="Total processadas"
          icon={<ClipboardList size={16} />}
          loading={loading}
          variant="info"
        />
        <KpiCard
          title="Aprovadas"
          value={(resumo?.approved_inspections ?? 0).toLocaleString("pt-BR")}
          subtitle="Conformes"
          icon={<CheckCircle2 size={16} />}
          loading={loading}
          variant="success"
        />
        <KpiCard
          title="Rejeitadas"
          value={rejected.toLocaleString("pt-BR")}
          subtitle={
            rejected > 0
              ? rejected <= 3
                ? "Para acompanhamento"
                : "Requer atenção"
              : "Sem ocorrências"
          }
          icon={<ShieldAlert size={16} />}
          loading={loading}
          variant={rejected > 3 ? "danger" : rejected > 0 ? "warning" : "default"}
        />
      </section>

      <section className="ie-kpi-grid ie-kpi-grid--secondary" aria-label="Indicadores complementares">
        <KpiCard
          title="Taxa de aprovação"
          value={resumo ? formatPercent(resumo.approval_rate) : "0,00%"}
          subtitle={
            resumo
              ? `${resumo.inspections_with_time.toLocaleString("pt-BR")} inspeções com tempo registrado`
              : undefined
          }
          icon={<TrendingUp size={16} />}
          loading={loading}
          variant="success"
        />
        <KpiCard
          title="Tempo médio"
          value={
            resumo
              ? formatAverageTime(resumo.average_time_days, resumo.average_time_hours)
              : "—"
          }
          subtitle="Do recebimento à conclusão"
          icon={<Clock3 size={16} />}
          loading={loading}
          variant="info"
        />
      </section>
    </div>
  );
}
