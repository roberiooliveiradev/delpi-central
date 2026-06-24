import { DASHBOARD_KPIS } from "../../constants/dashboardKpis";
import type { DashboardSummary } from "../../types/actionPlan";
import { KpiCard } from "../ui/KpiCard";

type Props = {
  summary: DashboardSummary;
  loading?: boolean;
};

export function DashboardKpis({ summary, loading = false }: Props) {
  return (
    <div className="pac-dashboard-grid">
      {DASHBOARD_KPIS.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <KpiCard
            key={kpi.key}
            label={kpi.label}
            value={summary[kpi.key]}
            tone={kpi.tone}
            loading={loading}
            icon={<Icon size={22} strokeWidth={1.75} />}
          />
        );
      })}
    </div>
  );
}
