import { useEffect, useMemo, useState } from "react";
import {
  ChartOverlayOptionsPopover,
  ChartSeriesColorsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  MultiTypeSeriesChart,
  TIME_MULTI_SERIES_TYPES,
  applySeriesFillPreferences,
  runTabularExport,
  usePersistedChartPreferences,
  type ChartGranularity,
  type ChartOverlayOption,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

import { getOtdSeries } from "../../api/otdSeries";
import {
  SuppliesChartGranularityToggle,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesStateBanner,
  SuppliesTabularExportButtons,
  SP_PORTAL_SCOPE,
  useChartGranularitySelection,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { mapOverviewFetchError, OVERVIEW_CONTENT } from "./overviewContent";
import { mergeSeriesWithPriorYear, shiftPeriodRangeByYears } from "./periodShift";
import type { OverviewApiParams } from "./useOverviewFilters";

type OverviewOtdSeriesChartProps = {
  filters: OverviewApiParams;
  storageKey?: string;
};

const CHART_HEIGHT = 320;

const GRANULARITY_OPTIONS: { value: ChartGranularity; label: string }[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
];

type OtdChartPoint = {
  period: string;
  otdPct: number;
  otdPctPrior?: number | null;
};

export function OverviewOtdSeriesChart({
  filters,
  storageKey = "supplies:overview:otd-series",
}: OverviewOtdSeriesChartProps) {
  const { granularity, setGranularity } = useChartGranularitySelection(
    filters.from,
    filters.to,
    {
      resolveAutoGranularity: (suggested) =>
        suggested === "year" ? "month" : (suggested as ChartGranularity),
    },
  );
  const { preferences, setPreferences, setChartType } = usePersistedChartPreferences({
    storageKey,
    defaults: { chartType: "line", comparePriorYear: false },
    allowedChartTypes: TIME_MULTI_SERIES_TYPES,
  });
  const yoyActive = Boolean(preferences.comparePriorYear);
  const chartType = preferences.chartType ?? "line";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [partialNote, setPartialNote] = useState<string | null>(null);
  const [points, setPoints] = useState<OtdChartPoint[]>([]);

  const overlayOptions = useMemo((): ChartOverlayOption[] => {
    return [
      {
        id: "yoy",
        label: OVERVIEW_CONTENT.comparePriorYear,
        summaryLabel: OVERVIEW_CONTENT.comparePriorYear,
        checked: yoyActive,
        onChange: (checked) => setPreferences({ comparePriorYear: checked }),
        hint: OVERVIEW_CONTENT.comparePriorYearHint,
        hintAriaLabel: "Ajuda: comparar ano anterior",
      },
    ];
  }, [setPreferences, yoyActive]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setPartialNote(null);

    const currentPromise = getOtdSeries(
      {
        branch: filters.branch,
        from: filters.from,
        to: filters.to,
        granularity: granularity as "day" | "week" | "month",
      },
      controller.signal,
    );

    const priorRange =
      yoyActive && filters.from && filters.to
        ? shiftPeriodRangeByYears({ from: filters.from, to: filters.to }, -1)
        : null;

    const priorPromise = priorRange
      ? getOtdSeries(
          {
            branch: filters.branch,
            from: priorRange.from,
            to: priorRange.to,
            granularity: granularity as "day" | "week" | "month",
          },
          controller.signal,
        )
      : Promise.resolve(null);

    void Promise.all([currentPromise, priorPromise])
      .then(([currentPayload, priorPayload]) => {
        if (controller.signal.aborted) return;
        const current = (currentPayload.points ?? [])
          .filter((point) => point.otdPct != null && Number.isFinite(point.otdPct))
          .map((point) => ({
            period: point.period,
            otdPct: Number(point.otdPct),
          }));
        const prior = (priorPayload?.points ?? [])
          .filter((point) => point.otdPct != null && Number.isFinite(point.otdPct))
          .map((point) => ({
            period: point.period,
            otdPct: Number(point.otdPct),
          }));
        const next: OtdChartPoint[] = yoyActive
          ? mergeSeriesWithPriorYear(current, prior, (priorPoint) => ({
              otdPctPrior: priorPoint?.otdPct ?? null,
            }))
          : current;
        setPoints(next);
        const failures = [
          ...(currentPayload.partialFailures ?? []),
          ...(priorPayload?.partialFailures ?? []),
        ];
        if (failures.length > 0) {
          setPartialNote(OVERVIEW_CONTENT.partialNote);
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setPoints([]);
        const message = err instanceof Error ? err.message : OVERVIEW_CONTENT.otdChartError;
        setError(mapOverviewFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [filters.branch, filters.from, filters.to, granularity, yoyActive]);

  const baseSeries = useMemo((): MultiTypeSeriesSpec[] => {
    const list: MultiTypeSeriesSpec[] = [
      {
        dataKey: "otdPct",
        name: OVERVIEW_CONTENT.otdSeriesLabel,
        fill: "var(--delpi-chart-series-1, #2563eb)",
      },
    ];
    if (yoyActive) {
      list.push({
        dataKey: "otdPctPrior",
        name: OVERVIEW_CONTENT.otdSeriesPriorLabel,
        fill: "var(--delpi-chart-series-2, #94a3b8)",
      });
    }
    return list;
  }, [yoyActive]);

  const series = useMemo(
    () => applySeriesFillPreferences(baseSeries, preferences.seriesFills),
    [baseSeries, preferences.seriesFills],
  );

  const formatPct = (value: number) =>
    `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

  return (
    <div className="sp-overview__chart">
      <p className="sp-overview__chart-hint">{SP_HELP.overviewOtdChart}</p>
      {loading ? (
        <SuppliesLoadingCard title={OVERVIEW_CONTENT.otdChartLoading} variant="panel" />
      ) : null}
      {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
      {!loading && !error && partialNote ? (
        <SuppliesStateBanner>{partialNote}</SuppliesStateBanner>
      ) : null}
      {!loading && !error && points.length === 0 ? (
        <SuppliesEmptyState
          title={OVERVIEW_CONTENT.otdChartEmptyTitle}
          message={OVERVIEW_CONTENT.otdChartEmptyMessage}
        />
      ) : null}
      {!loading && !error && points.length > 0 ? (
        <ChartViewShell
          prefix="sp"
          granularityLabel={OVERVIEW_CONTENT.chartGranularityLabel}
          typeToggleLabel={OVERVIEW_CONTENT.chartTypeLabel}
          overlaysLabel={OVERVIEW_CONTENT.chartOverlaysLabel}
          seriesColorsLabel={OVERVIEW_CONTENT.chartSeriesColorsLabel}
          granularity={
            <SuppliesChartGranularityToggle
              value={granularity}
              onChange={setGranularity}
              options={GRANULARITY_OPTIONS}
              modes={["day", "week", "month"]}
              idPrefix="supplies-otd-granularity"
            />
          }
          typeToggle={
            <ChartTypeSegmentToggle
              family="time_multi_series"
              value={chartType}
              onChange={setChartType}
              idPrefix="supplies-otd-type"
              prefix="sp"
              portalScopeClassName={SP_PORTAL_SCOPE}
            />
          }
          overlays={
            <ChartOverlayOptionsPopover
              idPrefix="supplies-otd-overlays"
              portalScopeClassName={SP_PORTAL_SCOPE}
              panelTitle={OVERVIEW_CONTENT.chartOverlaysPanelTitle}
              emptySummaryLabel={OVERVIEW_CONTENT.chartOverlaysEmpty}
              options={overlayOptions}
            />
          }
          seriesColors={
            <ChartSeriesColorsPopover
              idPrefix="supplies-otd-colors"
              portalScopeClassName={SP_PORTAL_SCOPE}
              series={series}
              values={preferences.seriesFills}
              summaryLabel={OVERVIEW_CONTENT.chartSeriesColorsEmpty}
              panelTitle={OVERVIEW_CONTENT.chartSeriesColorsPanelTitle}
              triggerAriaLabel={OVERVIEW_CONTENT.chartSeriesColorsTriggerAria}
              resetLabel={OVERVIEW_CONTENT.chartSeriesColorsReset}
              onChange={(dataKey, color) =>
                setPreferences((prev) => ({
                  ...prev,
                  seriesFills: { ...(prev.seriesFills ?? {}), [dataKey]: color },
                }))
              }
              onReset={() => setPreferences((prev) => ({ ...prev, seriesFills: undefined }))}
            />
          }
          exportActions={
            <SuppliesTabularExportButtons
              compact
              disabled={points.length === 0 || loading}
              onExport={(format) => {
                const columns = [
                  { key: "period", label: "Período" },
                  { key: "otdPct", label: OVERVIEW_CONTENT.otdSeriesLabel },
                ];
                if (yoyActive) {
                  columns.push({
                    key: "otdPctPrior",
                    label: OVERVIEW_CONTENT.otdSeriesPriorLabel,
                  });
                }
                runTabularExport({
                  kind: "table",
                  format,
                  payload: {
                    title: OVERVIEW_CONTENT.otdChartTitle,
                    columns,
                    rows: points.map((point) => ({
                      period: point.period,
                      otdPct: formatPct(point.otdPct),
                      ...(yoyActive
                        ? {
                            otdPctPrior:
                              point.otdPctPrior == null
                                ? "—"
                                : formatPct(Number(point.otdPctPrior)),
                          }
                        : {}),
                    })),
                  },
                });
              }}
            />
          }
        >
          <MultiTypeSeriesChart
            data={points}
            categoryKey="period"
            series={series}
            chartType={chartType}
            height={CHART_HEIGHT}
            formatY={formatPct}
            formatTooltipValue={formatPct}
            showLegend
          />
        </ChartViewShell>
      ) : null}
    </div>
  );
}
