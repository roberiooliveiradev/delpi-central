import type React from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CHART_COLORS } from "../constants/chartColors";
import { PRODUCTION_OTD_SERIES_LABELS } from "../constants/productionIndicators";
import type { OtdSeriesPoint } from "../hooks/useProductionOtdSeries";
import { formatPercent } from "../utils/format";
import { STATE_BOX_EMPTY } from "../ui/stateChrome";

const CHART_HEIGHT = 320;

type OtdEvolutionChartProps = {
  data: OtdSeriesPoint[];
  branch?: string;
  loading?: boolean;
  onDrillDown: (dateStart: string, dateEnd: string) => void;
};

function formatChartPercent(value: number | string | undefined): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (num == null || Number.isNaN(num)) return "—";
  return formatPercent(num);
}

export function OtdEvolutionChart({
  data,
  branch,
  loading = false,
  onDrillDown,
}: OtdEvolutionChartProps) {
  if (loading && data.length === 0) {
    return (
      <div className={STATE_BOX_EMPTY} aria-busy="true">
        Carregando gráfico…
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className={STATE_BOX_EMPTY}>Sem dados para o gráfico no período.</div>
    );
  }

  const showFilial01 = !branch || branch === "01";
  const showFilial02 = !branch || branch === "02";

  const handleClick: React.ComponentProps<typeof LineChart>["onClick"] = (
    state
  ) => {
    if (!state) return;
    const rawIndex = state.activeTooltipIndex;
    const index =
      typeof rawIndex === "number"
        ? rawIndex
        : typeof rawIndex === "string"
          ? Number(rawIndex)
          : -1;
    if (!Number.isFinite(index) || index < 0) return;

    const point = data[index];
    if (point?.dateStart && point?.dateEnd) {
      onDrillDown(point.dateStart, point.dateEnd);
    }
  };

  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <LineChart
        data={data as Record<string, string | number | null>[]}
        onClick={handleClick}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="periodo"
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickFormatter={(value) => formatChartPercent(value)}
          domain={[0, 100]}
          width={64}
          unit="%"
        />
        <Tooltip
          formatter={(value, name) => [
            formatChartPercent(typeof value === "number" ? value : Number(value)),
            String(name),
          ]}
        />
        <Legend />
        {showFilial01 ? (
          <Line
            type="monotone"
            dataKey="otdFilial01"
            name={PRODUCTION_OTD_SERIES_LABELS.filial01}
            stroke={CHART_COLORS[4]}
            strokeWidth={2}
            connectNulls
            dot={{ r: 4, cursor: "pointer" }}
            activeDot={{ r: 6, cursor: "pointer" }}
          />
        ) : null}
        {showFilial02 ? (
          <Line
            type="monotone"
            dataKey="otdFilial02"
            name={PRODUCTION_OTD_SERIES_LABELS.filial02}
            stroke={CHART_COLORS[5] ?? CHART_COLORS[1]}
            strokeWidth={2}
            connectNulls
            dot={{ r: 4, cursor: "pointer" }}
            activeDot={{ r: 6, cursor: "pointer" }}
          />
        ) : null}
      </LineChart>
    </ResponsiveContainer>
  );
}
