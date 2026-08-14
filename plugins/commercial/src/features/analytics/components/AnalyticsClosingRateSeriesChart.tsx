import { useEffect, useMemo, useRef, useState } from "react";
import {
  ChartTypeSegmentToggle,
  ChartViewShell,
  EmptyState,
  MultiTypeSeriesChart,
  NativeCheckboxControl,
  TIME_MULTI_SERIES_TYPES,
  runTabularExport,
  usePersistedChartPreferences,
  type ChartGranularity,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

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
  mergeSeriesWithPriorYear,
  shiftPeriodRangeByYears,
} from "../utils/periodShift";

const CHART_HEIGHT = 320;
const STORAGE_KEY = "commercial:overview:closing-rate-series";

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
 * Evolução hit rate — Chart View Shell (tipo + YoY persistidos).
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
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey: STORAGE_KEY,
    defaults: { chartType: "line", comparePriorYear: false },
    allowedChartTypes: TIME_MULTI_SERIES_TYPES,
  });
  const yoyActive = Boolean(preferences.comparePriorYear);
  const chartType = preferences.chartType ?? "line";

  const [points, setPoints] = useState<ClosingRateChartPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const emptyCopy = ANALYTICS_CONTENT.overview.chartEmpty;
  const onPointsChangeRef = useRef(onPointsChange);
  onPointsChangeRef.current = onPointsChange;

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

  const priorLabels = useMemo(
    () => ({
      unit01: `${ANALYTICS_CONVERSION_SERIES_LABELS.unit01} (ano ant.)`,
      unit02: `${ANALYTICS_CONVERSION_SERIES_LABELS.unit02} (ano ant.)`,
    }),
    [],
  );

  const series = useMemo((): MultiTypeSeriesSpec[] => {
    const list: MultiTypeSeriesSpec[] = [
      {
        dataKey: "conversion_filial_01",
        name: ANALYTICS_CONVERSION_SERIES_LABELS.unit01,
        fill: "var(--chart-1, #089bdb)",
      },
      {
        dataKey: "conversion_filial_02",
        name: ANALYTICS_CONVERSION_SERIES_LABELS.unit02,
        fill: "var(--chart-2, #10b981)",
      },
    ];
    if (yoyActive) {
      list.push(
        {
          dataKey: "conversion_filial_01_prior",
          name: priorLabels.unit01,
          fill: "var(--chart-3, #94a3b8)",
        },
        {
          dataKey: "conversion_filial_02_prior",
          name: priorLabels.unit02,
          fill: "var(--chart-4, #64748b)",
        },
      );
    }
    return list;
  }, [priorLabels.unit01, priorLabels.unit02, yoyActive]);

  const chartData = useMemo(
    () =>
      points.map((point) => ({
        periodo: point.periodo,
        conversion_filial_01: Number(point.conversion_filial_01) || 0,
        conversion_filial_02: Number(point.conversion_filial_02) || 0,
        conversion_filial_01_prior:
          point.conversion_filial_01_prior == null
            ? null
            : Number(point.conversion_filial_01_prior) || 0,
        conversion_filial_02_prior:
          point.conversion_filial_02_prior == null
            ? null
            : Number(point.conversion_filial_02_prior) || 0,
      })),
    [points],
  );

  return (
    <div className="cm-rol-series">
      <p className="cm-rol-series__hint">{CM_HELP.overview.closingRateSeries}</p>
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
        <ChartViewShell
          prefix="cm"
          granularity={
            <CommercialChartToolbar
              granularity={granularity}
              onGranularityChange={setGranularity}
              options={CONVERSION_GRANULARITY_OPTIONS}
              modes={["day", "week", "month", "year"]}
            />
          }
          typeToggle={
            <ChartTypeSegmentToggle
              family="time_multi_series"
              value={chartType}
              onChange={setChartType}
              idPrefix="overview-closing-type"
              prefix="cm"
            />
          }
          exportActions={
            <CommercialTabularExportButtons
              compact
              disabled={points.length === 0 || loading}
              onExport={(format) => {
                runTabularExport({
                  kind: "table",
                  format,
                  payload: buildOverviewClosingRateSeriesPayload(points, {
                    includePriorYear: yoyActive,
                  }),
                });
              }}
            />
          }
          overlays={
            <NativeCheckboxControl
              id="overview-closing-rate-yoy"
              checked={yoyActive}
              onChange={(checked) => setPreferences({ comparePriorYear: checked })}
              label={ANALYTICS_CONTENT.overview.comparePriorYear}
              hint={CM_HELP.overview.closingRateSeriesYoy}
              hintPlacement="tooltip"
              hintAriaLabel="Ajuda: comparar ano anterior"
            />
          }
        >
          <MultiTypeSeriesChart
            data={chartData}
            categoryKey="periodo"
            series={series}
            chartType={chartType}
            height={CHART_HEIGHT}
            formatY={(value) => formatChartPct(value)}
            formatTooltipValue={(value) => formatChartPct(value)}
            onCategoryClick={
              onDrillDown
                ? (category) => {
                    const point = points.find((entry) => entry.periodo === category);
                    if (point?.start_date && point?.end_date) {
                      onDrillDown(point.start_date, point.end_date);
                    }
                  }
                : undefined
            }
          />
        </ChartViewShell>
      ) : null}
    </div>
  );
}
