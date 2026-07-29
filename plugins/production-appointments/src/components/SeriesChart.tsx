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

import { CHART_AXIS_TICK, CHART_COLORS, CHART_GRID_STROKE } from "../constants/chartTheme";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { SeriesPoint } from "../types/appointments";
import { formatSeriesBucket, formatQuantity } from "../utils/formatters";
import { ChartCard } from "./ChartCard";
import {
  SeriesChartToolbar,
  type SeriesGranularity,
} from "./chartUi";

type SeriesChartProps = {
  points: SeriesPoint[];
  granularity?: SeriesGranularity;
  onGranularityChange?: (value: SeriesGranularity) => void;
};

export function SeriesChart({
  points,
  granularity = "day",
  onGranularityChange,
}: SeriesChartProps) {
  const data = points.map((point) => ({
    ...point,
    label: formatSeriesBucket(point.appointment_date, granularity),
  }));

  const hint =
    granularity === "month"
      ? "Agregação mensal das quantidades produzida e perdida."
      : "Agregação diária das quantidades produzida e perdida.";

  return (
    <ChartCard
      title="Produção no tempo"
      titleHint={PA_HELP_TOOLTIPS.charts.series}
      hint={hint}
      variant="featured"
    >
      {onGranularityChange ? (
        <SeriesChartToolbar
          idPrefix="pa-series"
          granularity={granularity}
          onGranularityChange={onGranularityChange}
          granularityHelp={PA_HELP_TOOLTIPS.charts.seriesGranularity}
        />
      ) : null}

      {data.length === 0 ? (
        <p className="pa-chart-card__empty">Sem pontos na série para o período.</p>
      ) : (
        <div className="pa-chart-card__body" style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid stroke={CHART_GRID_STROKE} strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={CHART_AXIS_TICK} minTickGap={24} />
              <YAxis tick={CHART_AXIS_TICK} width={64} />
              <Tooltip
                contentStyle={{ borderRadius: 10 }}
                formatter={(value) => formatQuantity(Number(value))}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="qty_produced"
                name={"Produzida"}
                stroke={CHART_COLORS.primary}
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="qty_lost"
                name={"Perdida"}
                stroke={CHART_COLORS.accent}
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </ChartCard>
  );
}
