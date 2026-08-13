import { useEffect, useMemo, useRef, useState, type ComponentProps } from "react";
import {
  EmptyState,
  NativeCheckboxControl,
  runTabularExport,
  type ChartGranularity,
} from "@delpi/plugin-ui/index";
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

import { getSalesConversionRateSeries } from "../../../api/analyticsApi";
import {
  cmEmptyStateClassNames,
  CommercialChartToolbar,
  CommercialLoadingCard,
  CommercialTabularExportButtons,
  useChartGranularitySelection,
} from "../../../app/commercialUi";
import { buildOverviewClosingRateSeriesPayload } from "../../overview/overviewExportBuilders";
import { ANALYTICS_CONTENT } from "../../../content/analyticsContent";
import { CM_HELP } from "../../../content/helpTooltips";
import type {
  AnalyticsFilterParams,
  SalesConversionRateSeriesPoint,
} from "../../../types/analytics";
import { ANALYTICS_CONVERSION_SERIES_LABELS } from "../utils/analyticsBranchFilters";
import {
  isPriorYearCompareAllowed,
  mergeSeriesWithPriorYear,
  shiftPeriodRangeByYears,
} from "../utils/periodShift";

const CHART_HEIGHT = 320;

const CONVERSION_GRANULARITY_OPTIONS: { value: ChartGranularity; label: string }[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
];

type ClosingRateChartPoint = SalesConversionRateSeriesPoint & {
  conversion_filial_01_prior?: number | null;
  conversion_filial_02_prior?: number | null;
};

type ClosingRateSeriesChartProps = {
  filters: Pick<
    AnalyticsFilterParams,
    "start_date" | "end_date" | "customer_segment" | "seller_id"
  >;
  onDrillDown?: (dateStart: string, dateEnd: string) => void;
  onPointsChange?: (points: SalesConversionRateSeriesPoint[]) => void;
};

function formatChartPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${Number(value).toLocaleString("pt-BR", { maximumFractionDigits: 2 })}%`;
}

/**
 * Evolução da taxa de conversão (hit rate) — séries SC/ES, toolbar Dia–Ano,
 * overlay opcional ano anterior e drill no período atual.
 */
export function AnalyticsClosingRateSeriesChart({
  filters,
  onDrillDown,
  onPointsChange,
}: ClosingRateSeriesChartProps) {
  const { granularity, setGranularity } = useChartGranularitySelection(
    filters.start_date,
    filters.end_date,
  );
  const [comparePriorYear, setComparePriorYear] = useState(false);
  const [points, setPoints] = useState<ClosingRateChartPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const emptyCopy = ANALYTICS_CONTENT.overview.chartEmpty;
  const onPointsChangeRef = useRef(onPointsChange);
  onPointsChangeRef.current = onPointsChange;

  const yoyAllowed = isPriorYearCompareAllowed(granularity);
  const yoyActive = comparePriorYear && yoyAllowed;

  useEffect(() => {
    if (!yoyAllowed && comparePriorYear) {
      setComparePriorYear(false);
    }
  }, [comparePriorYear, yoyAllowed]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    const currentPromise = getSalesConversionRateSeries(
      { ...filters, granularity },
      controller.signal,
    );

    const priorRange =
      yoyActive && filters.start_date && filters.end_date
        ? shiftPeriodRangeByYears(
            { start_date: filters.start_date, end_date: filters.end_date },
            -1,
          )
        : null;

    const priorPromise = priorRange
      ? getSalesConversionRateSeries(
          {
            ...filters,
            start_date: priorRange.start_date,
            end_date: priorRange.end_date,
            granularity,
          },
          controller.signal,
        )
      : Promise.resolve(null);

    void Promise.all([currentPromise, priorPromise])
      .then(([currentData, priorData]) => {
        if (controller.signal.aborted) return;
        const current = currentData.points ?? [];
        const prior = priorData?.points ?? [];
        const next: ClosingRateChartPoint[] = yoyActive
          ? mergeSeriesWithPriorYear(current, prior, (p) => ({
              conversion_filial_01_prior: p?.conversion_filial_01 ?? null,
              conversion_filial_02_prior: p?.conversion_filial_02 ?? null,
            }))
          : current;
        setPoints(next);
        onPointsChangeRef.current?.(current);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : emptyCopy.conversionError);
        setPoints([]);
        onPointsChangeRef.current?.([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    emptyCopy.conversionError,
    filters.start_date,
    filters.end_date,
    filters.customer_segment,
    filters.seller_id,
    granularity,
    yoyActive,
  ]);

  const exportIncludePrior = yoyActive;

  const priorLabels = useMemo(
    () => ({
      unit01: `${ANALYTICS_CONVERSION_SERIES_LABELS.unit01} (ano ant.)`,
      unit02: `${ANALYTICS_CONVERSION_SERIES_LABELS.unit02} (ano ant.)`,
    }),
    [],
  );

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
      <div className="cm-rol-series__toolbar">
        <p className="cm-rol-series__hint">{CM_HELP.overview.closingRateSeries}</p>
        <CommercialTabularExportButtons
          compact
          disabled={points.length === 0 || loading}
          onExport={(format) => {
            runTabularExport({
              kind: "table",
              format,
              payload: buildOverviewClosingRateSeriesPayload(points, {
                includePriorYear: exportIncludePrior,
              }),
            });
          }}
        />
      </div>
      <div className="cm-rol-series__toolbar">
        <CommercialChartToolbar
          granularity={granularity}
          onGranularityChange={setGranularity}
          options={CONVERSION_GRANULARITY_OPTIONS}
          modes={["day", "week", "month", "year"]}
        />
        <NativeCheckboxControl
          id="overview-closing-rate-yoy"
          checked={yoyActive}
          disabled={!yoyAllowed}
          onChange={setComparePriorYear}
          label={ANALYTICS_CONTENT.overview.comparePriorYear}
          hint={
            yoyAllowed
              ? CM_HELP.overview.closingRateSeriesYoy
              : CM_HELP.overview.closingRateSeriesYoyDisabledDay
          }
        />
      </div>
      {loading ? (
        <CommercialLoadingCard title={emptyCopy.conversionLoading} variant="panel" />
      ) : null}
      {error ? (
        <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={error} role="alert" />
      ) : null}
      {!loading && !error && points.length === 0 ? (
        <EmptyState
          classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
          defaultTitle={emptyCopy.conversionTitle}
          defaultMessage={emptyCopy.conversionMessage}
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
                tickFormatter={(value) => formatChartPct(Number(value))}
                width={72}
                domain={[0, "auto"]}
              />
              <Tooltip
                formatter={(value, name) => [formatChartPct(Number(value)), name]}
                labelFormatter={(label) => String(label)}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="conversion_filial_01"
                name={ANALYTICS_CONVERSION_SERIES_LABELS.unit01}
                stroke="var(--chart-1, #089bdb)"
                strokeWidth={2}
                connectNulls
                dot={{ r: 4, cursor: onDrillDown ? "pointer" : "default" }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="conversion_filial_02"
                name={ANALYTICS_CONVERSION_SERIES_LABELS.unit02}
                stroke="var(--chart-2, #10b981)"
                strokeWidth={2}
                connectNulls
                dot={{ r: 4, cursor: onDrillDown ? "pointer" : "default" }}
                activeDot={{ r: 6 }}
              />
              {yoyActive ? (
                <>
                  <Line
                    type="monotone"
                    dataKey="conversion_filial_01_prior"
                    name={priorLabels.unit01}
                    stroke="var(--chart-3, #94a3b8)"
                    strokeWidth={2}
                    strokeDasharray="6 4"
                    connectNulls
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="conversion_filial_02_prior"
                    name={priorLabels.unit02}
                    stroke="var(--chart-4, #64748b)"
                    strokeWidth={2}
                    strokeDasharray="6 4"
                    connectNulls
                    dot={false}
                  />
                </>
              ) : null}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : null}
    </div>
  );
}
