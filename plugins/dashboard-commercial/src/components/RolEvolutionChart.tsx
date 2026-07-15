import type { ComponentProps } from "react";
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
import { COMMERCIAL_ROL_SERIES_LABELS } from "../constants/commercialIndicators";
import type { RolSeriesPoint } from "../hooks/useCommercialRolSeries";
import { formatChartCurrency } from "../utils/format";
import { STATE_BOX_EMPTY } from "../ui/stateChrome";

const CHART_HEIGHT = 320;

type RolEvolutionChartProps = {
  data: RolSeriesPoint[];
  loading?: boolean;
  onDrillDown: (dateStart: string, dateEnd: string) => void;
};

export function RolEvolutionChart({
  data,
  loading = false,
  onDrillDown,
}: RolEvolutionChartProps) {
  const handleClick: ComponentProps<typeof LineChart>["onClick"] = (state) => {
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

  return (
    <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
      <LineChart
        data={data as Record<string, string | number>[]}
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
          tickFormatter={(value) => formatChartCurrency(value)}
          width={88}
        />
        <Tooltip
          formatter={(value, name) => [
            formatChartCurrency(
              typeof value === "number" ? value : Number(value),
            ),
            String(name),
          ]}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="rolMatrix"
          name={COMMERCIAL_ROL_SERIES_LABELS.filial01}
          stroke={CHART_COLORS[0]}
          strokeWidth={2}
          dot={{ r: 4, cursor: "pointer" }}
          activeDot={{ r: 6, cursor: "pointer" }}
        />
        <Line
          type="monotone"
          dataKey="rolBranch"
          name={COMMERCIAL_ROL_SERIES_LABELS.filial02}
          stroke={CHART_COLORS[1]}
          strokeWidth={2}
          dot={{ r: 4, cursor: "pointer" }}
          activeDot={{ r: 6, cursor: "pointer" }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
