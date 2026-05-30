import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  AXIS_TICK,
  CHART_COLORS,
  CHART_HEIGHT,
  NC_STATUS_COLORS,
  REFERENCE_LINE_100,
  SENSO_COLORS,
  TOOLTIP_STYLE,
} from "../constants/chartTheme";
import { ncStatusLabel, sensoName } from "../constants/audit5s";
import type { AuditDashboardCharts } from "../types/auditDashboard";
import { formatChartAxisDate, formatPercent } from "../utils/dates";
import { ChartCard } from "./ChartCard";

type Props = {
  charts: AuditDashboardCharts;
  filteredSensoOrder?: number | null;
  filteredSensoName?: string | null;
};

function EmptyChart({ message }: { message: string }) {
  return <p className="a5s-chart-empty">{message}</p>;
}

export function AuditDashboardCharts({
  charts,
  filteredSensoOrder,
  filteredSensoName,
}: Props) {
  const sensoLabel =
    filteredSensoOrder != null
      ? sensoName(filteredSensoOrder, filteredSensoName ?? undefined)
      : null;
  const evolutionTitle = sensoLabel
    ? `Evolução — ${sensoLabel}`
    : "Evolução da nota média";
  const evolutionSubtitle = sensoLabel
    ? `Percentual do senso por período`
    : "Percentual geral por período";
  const areaTitle = sensoLabel ? `Nota por área — ${sensoLabel}` : "Nota média por área";
  const areaSubtitle = sensoLabel ? "Média do senso selecionado" : "Top áreas auditadas";
  const sensoChartTitle = sensoLabel ? `Senso selecionado — ${sensoLabel}` : "Nota média por senso";
  const sensoChartSubtitle = sensoLabel
    ? "Média consolidada no período"
    : "Média dos 5 sensos";
  const lineName = sensoLabel ? `Nota — ${sensoLabel}` : "Nota média";
  const ncChartData = useMemo(
    () =>
      charts.nc_by_status.map((item) => ({
        ...item,
        label: ncStatusLabel(item.status),
      })),
    [charts.nc_by_status],
  );

  return (
    <div className="a5s-analytics-charts">
      <div className="a5s-analytics-charts__row a5s-analytics-charts__row--wide">
        <ChartCard title={evolutionTitle} subtitle={evolutionSubtitle}>
          {charts.score_by_period.length === 0 ? (
            <EmptyChart message="Sem auditorias com nota no período." />
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <LineChart data={charts.score_by_period}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis
                  dataKey="period"
                  tick={AXIS_TICK}
                  tickFormatter={formatChartAxisDate}
                />
                <YAxis domain={[0, 100]} tick={AXIS_TICK} unit="%" />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(value) => formatPercent(Number(value))}
                  labelFormatter={(label) => formatChartAxisDate(String(label ?? ""))}
                />
                <ReferenceLine {...REFERENCE_LINE_100} />
                <Line
                  type="monotone"
                  dataKey="average_score_pct"
                  name={lineName}
                  stroke={CHART_COLORS.primary}
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <div className="a5s-analytics-charts__row a5s-analytics-charts__row--triple">
        <ChartCard title={areaTitle} subtitle={areaSubtitle}>
          {charts.score_by_area.length === 0 ? (
            <EmptyChart message="Sem dados por área." />
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={charts.score_by_area} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis type="number" domain={[0, 100]} tick={AXIS_TICK} unit="%" />
                <YAxis
                  type="category"
                  dataKey="area_name"
                  width={100}
                  tick={AXIS_TICK}
                />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(value) => formatPercent(Number(value))}
                />
                <Bar dataKey="average_score_pct" name="Nota média" fill={CHART_COLORS.primary} radius={4} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title={sensoChartTitle} subtitle={sensoChartSubtitle}>
          {charts.score_by_senso.length === 0 ? (
            <EmptyChart message="Sem dados por senso." />
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={charts.score_by_senso}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="senso_name" tick={AXIS_TICK} />
                <YAxis domain={[0, 100]} tick={AXIS_TICK} unit="%" />
                <Tooltip
                  contentStyle={TOOLTIP_STYLE}
                  formatter={(value) => formatPercent(Number(value))}
                />
                <Bar dataKey="average_score_pct" name="Nota média" radius={4}>
                  {charts.score_by_senso.map((entry, index) => (
                    <Cell key={entry.senso_order} fill={SENSO_COLORS[index % SENSO_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="NC por status" subtitle={sensoLabel ? `NC do senso ${sensoLabel}` : "Distribuição no período"}>
          {ncChartData.length === 0 ? (
            <EmptyChart message="Nenhuma NC no período." />
          ) : (
            <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
              <BarChart data={ncChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" tick={AXIS_TICK} />
                <YAxis allowDecimals={false} tick={AXIS_TICK} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend />
                <Bar dataKey="count" name="Quantidade" radius={4}>
                  {ncChartData.map((entry) => (
                    <Cell
                      key={entry.status}
                      fill={NC_STATUS_COLORS[entry.status] ?? CHART_COLORS.muted}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>
    </div>
  );
}
