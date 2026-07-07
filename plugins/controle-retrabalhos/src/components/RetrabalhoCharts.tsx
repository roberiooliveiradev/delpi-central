import { useState } from "react";
import { Maximize2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  CHART_AXIS_TICK,
  CHART_COLORS,
  CHART_EXPANDED_HEIGHT,
  CHART_GRID_STROKE,
  CHART_HEIGHT,
  CHART_RANKING_HEIGHT,
  LABEL_LIST_STYLE,
} from "../constants/chartTheme";
import type {
  RetrabalhoColaboradorItem,
  RetrabalhoMensalItem,
  RetrabalhoRecursoItem,
} from "../types/retrabalho";
import {
  formatCurrencyBrl,
  formatHours,
  formatMonthLabel,
  formatShortLabel,
} from "../utils/formatters";
import { ChartCard } from "./ChartCard";
import { ChartModal } from "./ChartModal";

type RetrabalhoChartsProps = {
  mensal: RetrabalhoMensalItem[];
  recursos: RetrabalhoRecursoItem[];
  colaboradores: RetrabalhoColaboradorItem[];
};

type ExpandedChartKey = "recursos" | "colaboradores";

const MONTHLY_X_AXIS = {
  dataKey: "label" as const,
  interval: 0 as const,
  angle: 0 as const,
  textAnchor: "middle" as const,
  height: 36,
  tick: CHART_AXIS_TICK,
};

const CHART_GRID = (
  <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" vertical={false} />
);

function sortMensalChronological(items: RetrabalhoMensalItem[]): RetrabalhoMensalItem[] {
  return [...items].sort((a, b) => {
    const keyA = a.anoMes ?? `${a.ano ?? 0}${String(a.mesNumero ?? 0).padStart(2, "0")}`;
    const keyB = b.anoMes ?? `${b.ano ?? 0}${String(b.mesNumero ?? 0).padStart(2, "0")}`;
    return keyA.localeCompare(keyB);
  });
}

function ExpandChartButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      className="cr-chart-action"
      onClick={onClick}
      aria-label="Expandir gráfico"
    >
      <Maximize2 size={16} aria-hidden />
    </button>
  );
}

export function RetrabalhoCharts({ mensal, recursos, colaboradores }: RetrabalhoChartsProps) {
  const [expandedChart, setExpandedChart] = useState<ExpandedChartKey | null>(null);

  const mensalChart = sortMensalChronological(mensal).map((item) => ({
    label: formatMonthLabel(item),
    horas: item.totalHoras,
    custo: item.totalCusto,
  }));

  const recursosChart = recursos.map((item) => ({
    label: formatShortLabel(item.recurso, 18),
    horas: item.totalHoras,
    fullLabel: item.recurso,
  }));

  const colaboradoresChart = colaboradores.map((item) => ({
    label: formatShortLabel(item.nomeOperador, 18),
    horas: item.totalHoras,
    fullLabel: item.nomeOperador,
  }));

  const renderCustoMensalChart = (height: number) => (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={mensalChart} margin={{ top: 28, right: 16, left: 8, bottom: 4 }}>
        {CHART_GRID}
        <XAxis {...MONTHLY_X_AXIS} />
        <YAxis tickFormatter={(value) => formatCurrencyBrl(Number(value))} />
        <Tooltip formatter={(value) => formatCurrencyBrl(Number(value))} />
        <Line
          type="monotone"
          dataKey="custo"
          stroke={CHART_COLORS.primary}
          strokeWidth={2}
          dot={{ r: 3, fill: CHART_COLORS.primary }}
          activeDot={{ r: 5 }}
        >
          <LabelList
            dataKey="custo"
            position="top"
            formatter={(value) => formatCurrencyBrl(Number(value))}
            style={LABEL_LIST_STYLE}
          />
        </Line>
      </LineChart>
    </ResponsiveContainer>
  );

  const renderHorasMensalChart = (height: number) => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={mensalChart} margin={{ top: 28, right: 16, left: 8, bottom: 4 }}>
        {CHART_GRID}
        <XAxis {...MONTHLY_X_AXIS} />
        <YAxis tickFormatter={(value) => formatHours(Number(value))} />
        <Tooltip formatter={(value) => formatHours(Number(value))} />
        <Bar dataKey="horas" fill={CHART_COLORS.primary} radius={[4, 4, 0, 0]}>
          <LabelList
            dataKey="horas"
            position="top"
            formatter={(value) => formatHours(Number(value))}
            style={LABEL_LIST_STYLE}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );

  const renderRecursosChart = (height: number, useFullLabels = false) => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={recursosChart}
        layout="vertical"
        margin={{ left: 8, right: useFullLabels ? 72 : 56, top: 8, bottom: 8 }}
      >
        {CHART_GRID}
        <XAxis type="number" tickFormatter={(value) => formatHours(Number(value))} />
        <YAxis
          type="category"
          dataKey="label"
          width={useFullLabels ? 220 : 120}
          tick={CHART_AXIS_TICK}
        />
        <Tooltip
          formatter={(value) => formatHours(Number(value))}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.fullLabel ?? ""}
        />
        <Bar dataKey="horas" fill={CHART_COLORS.primary} radius={[0, 4, 4, 0]}>
          <LabelList
            dataKey="horas"
            position="right"
            formatter={(value) => formatHours(Number(value))}
            style={LABEL_LIST_STYLE}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );

  const renderColaboradoresChart = (height: number, useFullLabels = false) => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={colaboradoresChart}
        layout="vertical"
        margin={{ left: 8, right: useFullLabels ? 72 : 56, top: 8, bottom: 8 }}
      >
        {CHART_GRID}
        <XAxis type="number" tickFormatter={(value) => formatHours(Number(value))} />
        <YAxis
          type="category"
          dataKey="label"
          width={useFullLabels ? 220 : 120}
          tick={CHART_AXIS_TICK}
        />
        <Tooltip
          formatter={(value) => formatHours(Number(value))}
          labelFormatter={(_, payload) => payload?.[0]?.payload?.fullLabel ?? ""}
        />
        <Bar dataKey="horas" fill={CHART_COLORS.accent} radius={[0, 4, 4, 0]}>
          <LabelList
            dataKey="horas"
            position="right"
            formatter={(value) => formatHours(Number(value))}
            style={LABEL_LIST_STYLE}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );

  const modalTitle =
    expandedChart === "recursos"
      ? "Ranking de recursos"
      : expandedChart === "colaboradores"
        ? "Ranking de colaboradores"
        : "";

  const modalSubtitle =
    expandedChart === "recursos" || expandedChart === "colaboradores"
      ? "Top 10 por horas"
      : undefined;

  return (
    <div className="cr-charts-layout">
      <ChartModal
        open={expandedChart !== null}
        title={modalTitle}
        subtitle={modalSubtitle}
        onClose={() => setExpandedChart(null)}
      >
        {expandedChart === "recursos"
          ? renderRecursosChart(CHART_EXPANDED_HEIGHT, true)
          : expandedChart === "colaboradores"
            ? renderColaboradoresChart(CHART_EXPANDED_HEIGHT, true)
            : null}
      </ChartModal>

      <ChartCard title="Evolução mensal — custo" variant="featured">
        {renderCustoMensalChart(CHART_HEIGHT)}
      </ChartCard>

      <ChartCard title="Evolução mensal — horas" variant="featured">
        {renderHorasMensalChart(CHART_HEIGHT)}
      </ChartCard>

      <div className="cr-charts-grid">
        <ChartCard
          title="Ranking de recursos"
          hint="Top 10 por horas"
          actions={<ExpandChartButton onClick={() => setExpandedChart("recursos")} />}
        >
          {renderRecursosChart(CHART_RANKING_HEIGHT)}
        </ChartCard>

        <ChartCard
          title="Ranking de colaboradores"
          hint="Top 10 por horas"
          actions={<ExpandChartButton onClick={() => setExpandedChart("colaboradores")} />}
        >
          {renderColaboradoresChart(CHART_RANKING_HEIGHT)}
        </ChartCard>
      </div>
    </div>
  );
}
