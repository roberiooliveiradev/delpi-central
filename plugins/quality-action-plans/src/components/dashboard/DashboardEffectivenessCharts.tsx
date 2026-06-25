import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CheckCircle2 } from "lucide-react";

import { CHART_HEIGHT } from "../../constants/chartColors";
import type { DashboardEffectivenessByActionType } from "../../types/actionPlan";
import { buildEffectivenessByActionTypeData } from "../../utils/chartData";
import { ChartCard } from "../ui/ChartCard";
import { KpiCard } from "../ui/KpiCard";

type Props = {
  effectiveness?: DashboardEffectivenessByActionType | null;
  loading?: boolean;
};

type ChartPoint = {
  name: string;
  fullName?: string;
  value: number;
  reviewedPlans: number;
  effectivePlans: number;
  fill: string;
};

export function DashboardEffectivenessCharts({ effectiveness, loading = false }: Props) {
  if (!effectiveness && !loading) {
    return null;
  }

  const windowMonths = effectiveness?.window_months ?? 12;
  const overall = effectiveness?.overall;
  const chartData = buildEffectivenessByActionTypeData(effectiveness?.by_action_type ?? []);

  return (
    <section className="pac-effectiveness-section">
      <div className="pac-dashboard-grid pac-dashboard-grid--effectiveness">
        <KpiCard
          label="Taxa geral de eficácia"
          value={
            loading
              ? "…"
              : overall?.effectiveness_rate !== null && overall?.effectiveness_rate !== undefined
                ? `${overall.effectiveness_rate}%`
                : "—"
          }
          tone={
            overall?.effectiveness_rate !== null &&
            overall?.effectiveness_rate !== undefined &&
            overall.effectiveness_rate >= 70
              ? "success"
              : overall?.effectiveness_rate !== null &&
                  overall?.effectiveness_rate !== undefined &&
                  overall.effectiveness_rate > 0
                ? "warning"
                : "default"
          }
          icon={<CheckCircle2 size={22} strokeWidth={1.75} />}
          hint={
            loading
              ? undefined
              : overall?.reviewed_plans
                ? `${overall.effective_plans}/${overall.reviewed_plans} planos revisados (${windowMonths} meses)`
                : `Sem revisões de eficácia no período`
          }
          loading={loading}
        />
      </div>

      <ChartCard
        title="Eficácia por tipo de ação"
        hint={`% de planos eficazes entre os revisados com cada tipo de ação (${windowMonths} meses).`}
      >
        {loading ? (
          <div className="pac-state-box">Carregando taxas de eficácia…</div>
        ) : chartData.length ? (
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--pac-card-border)" />
              <XAxis
                type="number"
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
                tick={{ fontSize: 12 }}
              />
              <YAxis type="category" dataKey="name" width={132} tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value, _name, item) => {
                  const payload = item?.payload as ChartPoint | undefined;
                  return [
                    `${value ?? 0}%`,
                    payload
                      ? `${payload.effectivePlans}/${payload.reviewedPlans} eficazes`
                      : "Taxa",
                  ];
                }}
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid var(--pac-card-border)",
                  background: "var(--pac-card-bg)",
                }}
              />
              <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={18}>
                {chartData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="pac-state-box">Sem revisões de eficácia vinculadas a tipos de ação no período.</div>
        )}
      </ChartCard>
    </section>
  );
}
