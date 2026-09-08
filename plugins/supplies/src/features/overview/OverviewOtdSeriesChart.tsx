import { useEffect, useMemo, useState } from "react";
import {
  ChartTypeSegmentToggle,
  ChartViewShell,
  MultiTypeSeriesChart,
  TIME_MULTI_SERIES_TYPES,
  runTabularExport,
  usePersistedChartPreferences,
} from "@delpi/plugin-ui/index";

import { getOtdSeries } from "../../api/otdSeries";
import {
  SuppliesChartGranularityToggle,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesStateBanner,
  SuppliesTabularExportButtons,
  SP_PORTAL_SCOPE,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { mapOverviewFetchError, OVERVIEW_CONTENT } from "./overviewContent";
import type { OverviewApiParams } from "./useOverviewFilters";

type OverviewOtdSeriesChartProps = {
  filters: OverviewApiParams;
  storageKey?: string;
};

const CHART_HEIGHT = 280;

type ChartGranularity = "day" | "week" | "month";

const GRANULARITY_OPTIONS: { value: ChartGranularity; label: string }[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
];

export function OverviewOtdSeriesChart({
  filters,
  storageKey = "supplies:overview:otd-series",
}: OverviewOtdSeriesChartProps) {
  const [granularity, setGranularity] = useState<ChartGranularity>("month");
  const { preferences, setChartType } = usePersistedChartPreferences({
    storageKey,
    defaults: { chartType: "line" },
    allowedChartTypes: TIME_MULTI_SERIES_TYPES,
  });
  const chartType = preferences.chartType ?? "line";

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [partialNote, setPartialNote] = useState<string | null>(null);
  const [points, setPoints] = useState<Array<{ period: string; otdPct: number }>>([]);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setPartialNote(null);
    getOtdSeries(
      {
        branch: filters.branch,
        from: filters.from,
        to: filters.to,
        granularity,
      },
      controller.signal,
    )
      .then((payload) => {
        const next = (payload.points ?? [])
          .filter((point) => point.otdPct != null && Number.isFinite(point.otdPct))
          .map((point) => ({
            period: point.period,
            otdPct: Number(point.otdPct),
          }));
        setPoints(next);
        if ((payload.partialFailures?.length ?? 0) > 0) {
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
  }, [filters.branch, filters.from, filters.to, granularity]);

  const series = useMemo(
    () => [
      {
        dataKey: "otdPct",
        name: OVERVIEW_CONTENT.otdSeriesLabel,
        fill: "var(--delpi-chart-series-1, #2563eb)",
      },
    ],
    [],
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
          granularityLabel="Granularidade"
          typeToggleLabel="Tipo"
          granularity={
            <SuppliesChartGranularityToggle
              value={granularity}
              onChange={(value) => setGranularity(value as ChartGranularity)}
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
          exportActions={
            <SuppliesTabularExportButtons
              compact
              disabled={points.length === 0 || loading}
              onExport={(format) => {
                runTabularExport({
                  kind: "table",
                  format,
                  payload: {
                    title: OVERVIEW_CONTENT.otdChartTitle,
                    columns: [
                      { key: "period", label: "Período" },
                      { key: "otdPct", label: OVERVIEW_CONTENT.otdSeriesLabel },
                    ],
                    rows: points.map((point) => ({
                      period: point.period,
                      otdPct: formatPct(point.otdPct),
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
