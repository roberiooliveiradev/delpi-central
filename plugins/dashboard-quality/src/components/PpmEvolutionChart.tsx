import type React from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CHART_COLORS } from "../constants/chartColors";
import type { PpmChartReferenceLine } from "../constants/ppmReferenceLines";
import type { PpmSeriesPoint } from "../hooks/usePpmChartSeries";
import type { DualPpmSeriesPoint } from "../utils/mergePpmSeries";
import { formatDecimal } from "../utils/format";

const CHART_HEIGHT = 320;

type PpmEvolutionChartProps = {
  compare: boolean;
  singleData: PpmSeriesPoint[];
  compareData: DualPpmSeriesPoint[];
  referenceLines: PpmChartReferenceLine[];
  loading?: boolean;
  onDrillDown: (dateStart: string, dateEnd: string) => void;
};

export function PpmEvolutionChart({
  compare,
  singleData,
  compareData,
  referenceLines,
  loading = false,
  onDrillDown,
}: PpmEvolutionChartProps) {
  const data: Array<PpmSeriesPoint | DualPpmSeriesPoint> = compare
    ? compareData
    : singleData;

  if (loading && data.length === 0) {
    return (
      <div className="dq-state-box" aria-busy="true">
        Carregando gráfico…
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="dq-state-box">Sem dados para o gráfico no período.</div>
    );
  }

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

    if (compare) {
      const point = compareData[index];
      if (point?.dateStart && point?.dateEnd) {
        onDrillDown(point.dateStart, point.dateEnd);
      }
      return;
    }

    const point = singleData[index];
    if (point?.dateStart && point?.dateEnd) {
      onDrillDown(point.dateStart, point.dateEnd);
    }
  };

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
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value, name) => [
            formatDecimal(Number(value)),
            String(name),
          ]}
        />
        {referenceLines.map((line) => (
          <ReferenceLine
            key={line.label}
            y={line.value}
            stroke={line.stroke}
            strokeDasharray={line.strokeDasharray}
            label={{
              value: `${line.label} (${formatDecimal(line.value)})`,
              position: "insideTopRight",
              fontSize: 11,
            }}
          />
        ))}
        {compare ? (
          <>
            <Legend />
            <Line
              type="monotone"
              dataKey="ppmInternal"
              name="PPM interno"
              stroke={CHART_COLORS[0]}
              strokeWidth={2}
              dot={{ r: 4, cursor: "pointer" }}
              activeDot={{ r: 6, cursor: "pointer" }}
            />
            <Line
              type="monotone"
              dataKey="ppmExternal"
              name="PPM externo"
              stroke={CHART_COLORS[1]}
              strokeWidth={2}
              dot={{ r: 4, cursor: "pointer" }}
              activeDot={{ r: 6, cursor: "pointer" }}
            />
          </>
        ) : (
          <Line
            type="monotone"
            dataKey="ppm"
            name="PPM"
            stroke={CHART_COLORS[0]}
            strokeWidth={2}
            dot={{ r: 4, cursor: "pointer" }}
            activeDot={{ r: 6, cursor: "pointer" }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
