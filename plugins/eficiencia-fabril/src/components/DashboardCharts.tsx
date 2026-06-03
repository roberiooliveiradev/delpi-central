import { useMemo, useState } from "react";
import { Maximize2 } from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  LabelList,
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
  CHART_EXPANDED_HEIGHT,
  CHART_FONT_SIZE,
  CHART_HEIGHT,
  getEfficiencyByCtBarColor,
  getModResultByCtBarColor,
  REFERENCE_LINE_100,
  TOOLTIP_STYLE,
} from "../constants/chartTheme";
import type { EficienciaFabrilCharts } from "../types/eficienciaFabril";
import { formatChartAxisDate } from "../utils/dates";
import {
  formatCurrency,
  formatNumber,
  formatPercent,
  getOperatorFirstName,
} from "../utils/format";
import { ChartCard } from "./ChartCard";
import { ChartModal } from "./ChartModal";

type DashboardChartsProps = {
  charts: EficienciaFabrilCharts;
};

function ChartEmpty({ message }: { message: string }) {
  return <p className="ef-chart-empty">{message}</p>;
}

export function DashboardCharts({ charts }: DashboardChartsProps) {
  const [expandedChart, setExpandedChart] = useState<
    | "efficiency"
    | "mod"
    | "operators"
    | "efficiencyByCt"
    | "modByCt"
    | "workCenters"
    | null
  >(null);

  const efficiencySeries = useMemo(
    () =>
      charts.efficiency_by_day.map((row) => ({
        date: formatChartAxisDate(String(row.date)),
        efficiency: row.efficiency_pct ?? 0,
        appointments: row.appointment_count,
      })),
    [charts.efficiency_by_day]
  );

  const modSeries = useMemo(
    () =>
      charts.mod_result_by_day.map((row) => ({
        date: formatChartAxisDate(String(row.date)),
        lucro: row.profit ?? 0,
        prejuizo: Math.abs(row.loss ?? 0),
        liquido: row.net_result ?? 0,
      })),
    [charts.mod_result_by_day]
  );

  const operatorSeries = useMemo(
    () =>
      [...charts.efficiency_by_operator]
        .sort((a, b) => (b.efficiency_pct ?? 0) - (a.efficiency_pct ?? 0))
        .slice(0, 10)
        .map((row) => {
          const fullName =
            row.operator_name ?? row.operator_login ?? row.operator_code ?? "—";
          return {
            fullName,
            shortName: getOperatorFirstName(fullName),
            eficiencia: row.efficiency_pct ?? 0,
            mod: row.mod_result ?? 0,
          };
        }),
    [charts.efficiency_by_operator]
  );

  const efficiencyByWorkCenterSeries = useMemo(
    () =>
      charts.efficiency_by_work_center.map((row) => ({
        centro: row.work_center ?? "—",
        eficiencia: row.efficiency_pct ?? 0,
        apontamentos: row.appointment_count,
      })),
    [charts.efficiency_by_work_center]
  );

  const modByWorkCenterSeries = useMemo(
    () =>
      charts.mod_result_by_work_center.map((row) => ({
        centro: row.work_center ?? "—",
        mod: row.mod_result ?? 0,
        apontamentos: row.appointment_count,
      })),
    [charts.mod_result_by_work_center]
  );

  const workCenterSeries = useMemo(
    () =>
      [...charts.hours_by_work_center]
        .sort((a, b) => (b.real_hours ?? 0) - (a.real_hours ?? 0))
        .slice(0, 12)
        .map((row) => ({
          centro: row.work_center ?? "—",
          real: row.real_hours ?? 0,
          previsto: row.planned_hours ?? 0,
        })),
    [charts.hours_by_work_center]
  );

  const renderEfficiencyChart = (height: number) =>
    efficiencySeries.length === 0 ? (
      <ChartEmpty message="Sem dados de eficiência no período." />
    ) : (
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={efficiencySeries}>
          <XAxis dataKey="date" tick={AXIS_TICK} />
          <YAxis tick={AXIS_TICK} unit="%" />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value) => formatPercent(Number(value))}
          />
          <ReferenceLine {...REFERENCE_LINE_100} />
          <Line
            type="monotone"
            dataKey="efficiency"
            name="Eficiência"
            stroke={CHART_COLORS.primary}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    );

  const renderModChart = (height: number) =>
    modSeries.length === 0 ? (
      <ChartEmpty message="Sem dados de MOD no período." />
    ) : (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={modSeries}>
          <XAxis dataKey="date" tick={AXIS_TICK} />
          <YAxis tick={AXIS_TICK} tickFormatter={(v) => formatCurrency(Number(v))} />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value, name) => {
              const isLucro = String(name).toLowerCase().startsWith("lucro");
              return [formatCurrency(Number(value)), isLucro ? "Lucro" : "Prejuízo"];
            }}
          />
          <Legend wrapperStyle={TOOLTIP_STYLE} />
          <Bar
            dataKey="lucro"
            name="Lucro"
            stackId="mod"
            fill={CHART_COLORS.success}
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="prejuizo"
            name="Prejuízo"
            stackId="mod"
            fill={CHART_COLORS.danger}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    );

  const renderOperatorsChart = (height: number, useFullNames = false) => {
    const chartData = operatorSeries.map((row) => ({
      name: useFullNames ? row.fullName : row.shortName,
      fullName: row.fullName,
      eficiencia: row.eficiencia,
      mod: row.mod,
    }));

    return chartData.length === 0 ? (
      <ChartEmpty message="Sem operadores no período." />
    ) : (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 12 }}>
          <XAxis type="number" tick={AXIS_TICK} unit="%" />
          <YAxis
            type="category"
            dataKey="name"
            width={useFullNames ? 220 : 72}
            tick={AXIS_TICK}
          />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            labelFormatter={(_, payload) => {
              const entry = payload?.[0]?.payload as { fullName?: string } | undefined;
              return entry?.fullName ?? "";
            }}
            formatter={(value) => formatPercent(Number(value))}
          />
          <Bar
            dataKey="eficiencia"
            name="Eficiência"
            fill={CHART_COLORS.primary}
            radius={[0, 4, 4, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    );
  };

  const renderEfficiencyByWorkCenterChart = (height: number, showBarLabels = false) =>
    efficiencyByWorkCenterSeries.length === 0 ? (
      <ChartEmpty message="Sem eficiência por centro de trabalho." />
    ) : (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={efficiencyByWorkCenterSeries}
          margin={{ top: showBarLabels ? 28 : 8, right: 8, left: 8, bottom: 8 }}
        >
          <XAxis
            dataKey="centro"
            tick={AXIS_TICK}
            interval={0}
            angle={-25}
            textAnchor="end"
            height={70}
          />
          <YAxis tick={AXIS_TICK} unit="%" />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value) => formatPercent(Number(value))}
          />
          <ReferenceLine {...REFERENCE_LINE_100} />
          <Bar dataKey="eficiencia" name="Eficiência" radius={[4, 4, 0, 0]}>
            {showBarLabels ? (
              <LabelList
                dataKey="eficiencia"
                position="top"
                formatter={(value) => formatPercent(Number(value))}
                style={{ fontSize: CHART_FONT_SIZE, fill: CHART_COLORS.secondary }}
              />
            ) : null}
            {efficiencyByWorkCenterSeries.map((entry, index) => (
              <Cell
                key={`ef-ct-${entry.centro}-${index}`}
                fill={getEfficiencyByCtBarColor(entry.eficiencia)}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );

  const renderModByWorkCenterChart = (height: number, showBarLabels = false) =>
    modByWorkCenterSeries.length === 0 ? (
      <ChartEmpty message="Sem resultado MOD por centro de trabalho." />
    ) : (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={modByWorkCenterSeries}
          margin={{ top: showBarLabels ? 28 : 8, right: 8, left: 8, bottom: 8 }}
        >
          <XAxis
            dataKey="centro"
            tick={AXIS_TICK}
            interval={0}
            angle={-25}
            textAnchor="end"
            height={70}
          />
          <YAxis tick={AXIS_TICK} tickFormatter={(v) => formatCurrency(Number(v))} />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value) => formatCurrency(Number(value))}
          />
          <ReferenceLine
            y={0}
            stroke={CHART_COLORS.secondary}
            strokeDasharray="4 4"
            strokeOpacity={0.4}
          />
          <Bar dataKey="mod" name="Resultado MOD" radius={[4, 4, 0, 0]}>
            {showBarLabels ? (
              <LabelList
                dataKey="mod"
                position="top"
                formatter={(value) => formatCurrency(Number(value))}
                style={{ fontSize: CHART_FONT_SIZE, fill: CHART_COLORS.secondary }}
              />
            ) : null}
            {modByWorkCenterSeries.map((entry, index) => (
              <Cell
                key={`mod-ct-${entry.centro}-${index}`}
                fill={getModResultByCtBarColor(entry.mod)}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );

  const renderWorkCentersChart = (height: number) =>
    workCenterSeries.length === 0 ? (
      <ChartEmpty message="Sem horas por centro de trabalho." />
    ) : (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={workCenterSeries}>
          <XAxis
            dataKey="centro"
            tick={AXIS_TICK}
            interval={0}
            angle={-25}
            textAnchor="end"
            height={70}
          />
          <YAxis tick={AXIS_TICK} tickFormatter={(v) => formatNumber(Number(v), 1)} />
          <Tooltip
            contentStyle={TOOLTIP_STYLE}
            formatter={(value) => `${formatNumber(Number(value), 2)} h`}
          />
          <Legend wrapperStyle={TOOLTIP_STYLE} />
          <Bar
            dataKey="previsto"
            name="Previsto"
            fill={CHART_COLORS.planned}
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="real"
            name="Real"
            fill={CHART_COLORS.secondary}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    );

  const modalTitle =
    expandedChart === "efficiency"
      ? "Eficiência por dia"
      : expandedChart === "mod"
        ? "Lucro vs prejuízo MOD por dia"
        : expandedChart === "operators"
          ? "Top operadores (eficiência)"
          : expandedChart === "efficiencyByCt"
            ? "Eficiência por centro de trabalho"
            : expandedChart === "modByCt"
              ? "Resultado MOD por centro de trabalho"
              : expandedChart === "workCenters"
              ? "Horas por centro de trabalho"
              : "";

  const modalSubtitle =
    expandedChart === "efficiency"
      ? "Média diária (%)"
      : expandedChart === "mod"
        ? "Valores agregados por data de produção"
        : expandedChart === "operators"
          ? "10 maiores eficiências no período"
          : expandedChart === "efficiencyByCt"
            ? "Média da eficiência (%) por CT no período"
            : expandedChart === "modByCt"
              ? "Soma do resultado MOD por CT no período"
              : expandedChart === "workCenters"
              ? "Tempo real vs previsto (top 12 centros)"
              : undefined;

  return (
    <section className="ef-charts-grid" aria-label="Gráficos analíticos">
      <ChartModal
        open={expandedChart !== null}
        title={modalTitle}
        subtitle={modalSubtitle}
        onClose={() => setExpandedChart(null)}
      >
        {expandedChart === "efficiency"
          ? renderEfficiencyChart(CHART_EXPANDED_HEIGHT)
          : expandedChart === "mod"
            ? renderModChart(CHART_EXPANDED_HEIGHT)
            : expandedChart === "operators"
              ? renderOperatorsChart(CHART_EXPANDED_HEIGHT, true)
              : expandedChart === "efficiencyByCt"
                ? renderEfficiencyByWorkCenterChart(CHART_EXPANDED_HEIGHT, true)
                : expandedChart === "modByCt"
                  ? renderModByWorkCenterChart(CHART_EXPANDED_HEIGHT, true)
                  : expandedChart === "workCenters"
                  ? renderWorkCentersChart(CHART_EXPANDED_HEIGHT)
                  : null}
      </ChartModal>

      <div className="ef-charts-grid__row ef-charts-grid__row--3">
        <ChartCard
          title="Eficiência por dia"
          subtitle="Média diária (%)"
          actions={
            <button
              type="button"
              className="ef-chart-action"
              onClick={() => setExpandedChart("efficiency")}
              aria-label="Expandir gráfico"
            >
              <Maximize2 size={16} aria-hidden />
            </button>
          }
        >
          {renderEfficiencyChart(CHART_HEIGHT)}
        </ChartCard>

        <ChartCard
          title="Lucro vs prejuízo MOD por dia"
          subtitle="Valores agregados por data de produção"
          actions={
            <button
              type="button"
              className="ef-chart-action"
              onClick={() => setExpandedChart("mod")}
              aria-label="Expandir gráfico"
            >
              <Maximize2 size={16} aria-hidden />
            </button>
          }
        >
          {renderModChart(CHART_HEIGHT)}
        </ChartCard>

        <ChartCard
          title="Top operadores (eficiência)"
          subtitle="10 maiores eficiências no período"
          actions={
            <button
              type="button"
              className="ef-chart-action"
              onClick={() => setExpandedChart("operators")}
              aria-label="Expandir gráfico"
            >
              <Maximize2 size={16} aria-hidden />
            </button>
          }
        >
          {renderOperatorsChart(CHART_HEIGHT)}
        </ChartCard>
      </div>

      <div className="ef-charts-grid__row ef-charts-grid__row--3">
        <ChartCard
          title="Eficiência por CT"
          subtitle="Média da eficiência (%) por centro de trabalho"
          actions={
            <button
              type="button"
              className="ef-chart-action"
              onClick={() => setExpandedChart("efficiencyByCt")}
              aria-label="Expandir gráfico"
            >
              <Maximize2 size={16} aria-hidden />
            </button>
          }
        >
          {renderEfficiencyByWorkCenterChart(CHART_HEIGHT)}
        </ChartCard>

        <ChartCard
          title="Resultado MOD por CT"
          subtitle="Soma do resultado MOD por centro de trabalho"
          actions={
            <button
              type="button"
              className="ef-chart-action"
              onClick={() => setExpandedChart("modByCt")}
              aria-label="Expandir gráfico"
            >
              <Maximize2 size={16} aria-hidden />
            </button>
          }
        >
          {renderModByWorkCenterChart(CHART_HEIGHT)}
        </ChartCard>

        <ChartCard
          title="Horas por centro de trabalho"
          subtitle="Tempo real vs previsto (top 12 centros)"
          actions={
            <button
              type="button"
              className="ef-chart-action"
              onClick={() => setExpandedChart("workCenters")}
              aria-label="Expandir gráfico"
            >
              <Maximize2 size={16} aria-hidden />
            </button>
          }
        >
          {renderWorkCentersChart(CHART_HEIGHT)}
        </ChartCard>
      </div>
    </section>
  );
}
