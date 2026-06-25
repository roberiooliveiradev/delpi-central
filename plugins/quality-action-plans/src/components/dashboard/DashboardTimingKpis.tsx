import { CalendarClock, Hourglass } from "lucide-react";

import type { DashboardTiming } from "../../types/actionPlan";
import { KpiCard } from "../ui/KpiCard";

type Props = {
  timing?: DashboardTiming | null;
  loading?: boolean;
};

function formatDays(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} d`;
}

function sampleHint(count: number, windowMonths: number): string {
  if (count === 0) return `Últimos ${windowMonths} meses · sem amostra`;
  const label = count === 1 ? "plano" : "planos";
  return `Últimos ${windowMonths} meses · ${count} ${label}`;
}

export function DashboardTimingKpis({ timing, loading = false }: Props) {
  if (!timing && !loading) {
    return null;
  }

  const windowMonths = timing?.window_months ?? 12;

  return (
    <div className="pac-dashboard-grid pac-dashboard-grid--timing">
      <KpiCard
        label="Tempo médio de fechamento"
        value={formatDays(timing?.avg_closure_days)}
        icon={<CalendarClock size={22} strokeWidth={1.75} />}
        hint={sampleHint(timing?.closure_sample_size ?? 0, windowMonths)}
        loading={loading}
      />
      <KpiCard
        label="Tempo médio até eficácia"
        value={formatDays(timing?.avg_time_to_effectiveness_days)}
        icon={<Hourglass size={22} strokeWidth={1.75} />}
        hint={sampleHint(timing?.effectiveness_sample_size ?? 0, windowMonths)}
        loading={loading}
      />
    </div>
  );
}
