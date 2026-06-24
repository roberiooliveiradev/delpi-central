import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CHART_HEIGHT } from "../../constants/chartColors";
import type { ActionPlanSummary, DashboardSummary } from "../../types/actionPlan";
import {
  buildBranchChartData,
  buildOverviewChartData,
  buildScopeChartData,
  buildSeverityDistribution,
  buildStatusDistribution,
} from "../../utils/chartData";
import { ChartCard } from "../ui/ChartCard";

type Props = {
  summary: DashboardSummary;
  plans: ActionPlanSummary[];
};

function EmptyChart({ message }: { message: string }) {
  return <div className="pac-state-box">{message}</div>;
}

export function DashboardCharts({ summary, plans }: Props) {
  const overviewData = buildOverviewChartData(summary);
  const branchData = buildBranchChartData(summary);
  const statusData = buildStatusDistribution(plans);
  const severityData = buildSeverityDistribution(plans);
  const scopeData = buildScopeChartData(summary);

  const hasOverview = overviewData.some((entry) => entry.value > 0);
  const hasBranch = branchData.length > 0;
  const hasScope = scopeData.length > 0;
  const hasStatus = statusData.length > 0;
  const hasSeverity = severityData.length > 0;

  return (
    <div className="pac-charts-grid">
      <ChartCard title="Panorama operacional" hint="Indicadores consolidados do recorte selecionado.">
        {hasOverview ? (
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={overviewData} layout="vertical" margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--pac-card-border)" />
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} />
              <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value) => [value ?? 0, "Quantidade"]}
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid var(--pac-card-border)",
                  background: "var(--pac-card-bg)",
                }}
              />
              <Bar dataKey="value" radius={[0, 8, 8, 0]} barSize={18}>
                {overviewData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart message="Sem dados para exibir no panorama." />
        )}
      </ChartCard>

      {hasBranch ? (
        <ChartCard title="Abertos por filial" hint="Comparativo de planos abertos e críticos.">
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={branchData} margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--pac-card-border)" />
              <XAxis dataKey="branch" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid var(--pac-card-border)",
                  background: "var(--pac-card-bg)",
                }}
              />
              <Legend />
              <Bar dataKey="abertos" name="Abertos" fill="var(--chart-1, #089bdb)" radius={[8, 8, 0, 0]} />
              <Bar dataKey="criticos" name="Críticos" fill="var(--chart-6, #f2a100)" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      ) : null}

      <ChartCard title="Planos abertos por escopo" hint="Interna (processo/área) vs externa (cliente/fornecedor).">
        {hasScope ? (
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <PieChart>
              <Pie
                data={scopeData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={58}
                outerRadius={96}
                paddingAngle={2}
                stroke="var(--pac-card-bg)"
                strokeWidth={2}
              >
                {scopeData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid var(--pac-card-border)",
                  background: "var(--pac-card-bg)",
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart message="Sem planos abertos por escopo no recorte." />
        )}
      </ChartCard>

      <ChartCard title="Distribuição por status" hint="Baseado nos planos carregados para análise.">
        {hasStatus ? (
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <PieChart>
              <Pie
                data={statusData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={58}
                outerRadius={96}
                paddingAngle={2}
                stroke="var(--pac-card-bg)"
                strokeWidth={2}
              >
                {statusData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid var(--pac-card-border)",
                  background: "var(--pac-card-bg)",
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart message="Nenhum plano disponível para distribuição por status." />
        )}
      </ChartCard>

      <ChartCard title="Distribuição por severidade" hint="Priorização visual dos planos ativos.">
        {hasSeverity ? (
          <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
            <BarChart data={severityData} margin={{ left: 8, right: 16, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--pac-card-border)" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  borderRadius: 12,
                  border: "1px solid var(--pac-card-border)",
                  background: "var(--pac-card-bg)",
                }}
              />
              <Bar dataKey="value" name="Planos" radius={[8, 8, 0, 0]} barSize={36}>
                {severityData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <EmptyChart message="Nenhum plano disponível para distribuição por severidade." />
        )}
      </ChartCard>
    </div>
  );
}
