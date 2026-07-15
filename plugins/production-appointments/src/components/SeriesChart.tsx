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
import { formatProtheusDate, formatQuantity } from "../utils/formatters";
import { ChartCard } from "./ChartCard";

type SeriesChartProps = {
  points: SeriesPoint[];
};

export function SeriesChart({ points }: SeriesChartProps) {
  const data = points.map((point) => ({
    ...point,
    label: formatProtheusDate(point.appointment_date),
  }));

  return (
    <ChartCard
      title="Produção no tempo"
      titleHint={PA_HELP_TOOLTIPS.charts.series}
      variant="featured"
    >
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
