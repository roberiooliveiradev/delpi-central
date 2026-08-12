import { useEffect, useRef, useState, type ComponentProps } from "react";
import { EmptyState } from "@delpi/plugin-ui/index";
import type { ChartGranularity } from "@delpi/plugin-ui/index";
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

import { getCommercialRolSeries } from "../../../api/analyticsApi";
import {
  cmEmptyStateClassNames,
  CommercialChartToolbar,
  CommercialLoadingCard,
  useChartGranularitySelection,
} from "../../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { CM_HELP } from "../../../content/helpTooltips";
import type {
  AnalyticsFilterParams,
  CommercialRolSeriesPoint,
} from "../../../types/analytics";
import { formatCurrency } from "../../../utils/format";
import { ANALYTICS_ROL_SERIES_LABELS } from "../utils/analyticsBranchFilters";

const CHART_HEIGHT = 320;

const ROL_GRANULARITY_OPTIONS: { value: ChartGranularity; label: string }[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
];

type RolSeriesChartProps = {
  filters: Pick<
    AnalyticsFilterParams,
    "start_date" | "end_date" | "customer_segment" | "seller_id"
  >;
  /** Clique no ponto → filtra o período analytics ao intervalo do bucket. */
  onDrillDown?: (dateStart: string, dateEnd: string) => void;
  /** Expõe pontos carregados (export / testes). */
  onPointsChange?: (points: CommercialRolSeriesPoint[]) => void;
};

function formatChartCurrency(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return formatCurrency(value);
}

/**
 * Evolução de ROL — séries Santa Catarina / Espírito Santo, toolbar Dia–Ano e drill.
 */
export function AnalyticsRolSeriesChart({
  filters,
  onDrillDown,
  onPointsChange,
}: RolSeriesChartProps) {
  const { granularity, setGranularity } = useChartGranularitySelection(
    filters.start_date,
    filters.end_date,
  );
  const [points, setPoints] = useState<CommercialRolSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const emptyCopy = ANALYTICS_CONTENT.overview.chartEmpty;
  const onPointsChangeRef = useRef(onPointsChange);
  onPointsChangeRef.current = onPointsChange;

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getCommercialRolSeries({ ...filters, granularity }, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const next = data.points ?? [];
        setPoints(next);
        onPointsChangeRef.current?.(next);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : emptyCopy.rolError);
        setPoints([]);
        onPointsChangeRef.current?.([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    emptyCopy.rolError,
    filters.start_date,
    filters.end_date,
    filters.customer_segment,
    filters.seller_id,
    granularity,
  ]);

  const handleClick: ComponentProps<typeof LineChart>["onClick"] = (state) => {
    if (!onDrillDown || !state) return;
    const rawIndex = state.activeTooltipIndex;
    const index =
      typeof rawIndex === "number"
        ? rawIndex
        : typeof rawIndex === "string"
          ? Number(rawIndex)
          : -1;
    if (!Number.isFinite(index) || index < 0) return;
    const point = points[index];
    if (point?.start_date && point?.end_date) {
      onDrillDown(point.start_date, point.end_date);
    }
  };

  return (
    <div className="cm-rol-series">
      <p className="cm-rol-series__hint">{CM_HELP.overview.rolSeries}</p>
      <CommercialChartToolbar
        granularity={granularity}
        onGranularityChange={setGranularity}
        options={ROL_GRANULARITY_OPTIONS}
        modes={["day", "week", "month", "year"]}
      />
      {loading ? (
        <CommercialLoadingCard title={emptyCopy.rolLoading} variant="panel" />
      ) : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}
      {!loading && !error && points.length === 0 ? (
        <EmptyState
          classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
          defaultTitle={emptyCopy.rolTitle}
          defaultMessage={emptyCopy.rolMessage}
        />
      ) : null}
      {!loading && !error && points.length > 0 ? (
        <div className="cm-chart-wrap" style={{ width: "100%", height: CHART_HEIGHT }}>
          <ResponsiveContainer>
            <LineChart data={points} onClick={handleClick}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="periodo" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
              <YAxis
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => formatChartCurrency(Number(value))}
                width={90}
              />
              <Tooltip
                formatter={(value) => formatChartCurrency(Number(value))}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="rol_matrix"
                name={ANALYTICS_ROL_SERIES_LABELS.unit01}
                stroke="var(--chart-1, #089bdb)"
                strokeWidth={2}
                dot={{ r: 4, cursor: onDrillDown ? "pointer" : "default" }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="rol_branch"
                name={ANALYTICS_ROL_SERIES_LABELS.unit02}
                stroke="var(--chart-2, #10b981)"
                strokeWidth={2}
                dot={{ r: 4, cursor: onDrillDown ? "pointer" : "default" }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </div>
  );
}
