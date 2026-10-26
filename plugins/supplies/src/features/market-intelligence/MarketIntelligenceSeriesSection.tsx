/** Series chart + accessible monthly-averages table (PROC-0076).

Rendering-only: values, coverage and FX pairing come from the BFF —
the MFE never recomputes quotes or conversions.
*/

import { useEffect, useMemo, useState } from "react";
import {
  ChartSeriesColorsPopover,
  ChartTypeSegmentToggle,
  ChartViewShell,
  MultiTypeSeriesChart,
  TIME_MULTI_SERIES_TYPES,
  applySeriesFillPreferences,
  runTabularExport,
  usePersistedChartPreferences,
  type MultiTypeSeriesSpec,
} from "@delpi/plugin-ui/index";

import {
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesSectionCard,
  SuppliesStateBanner,
  SuppliesTabularExportButtons,
  SP_PORTAL_SCOPE,
} from "../../app/suppliesUi";
import { SP_CHART_SERIES_HINTS, SP_HELP } from "../../content/helpTooltips";
import {
  getMarketIntelligenceSeries,
  type MarketGranularity,
  type MarketQueryParams,
  type MarketSeriesPoint,
} from "./api";
import {
  mapMarketIntelligenceError,
  MARKET_INTELLIGENCE_CONTENT,
} from "./content";

const CHART_HEIGHT = 320;
const STORAGE_KEY = "supplies:market-intelligence:series";

type MarketIntelligenceSeriesSectionProps = {
  params: MarketQueryParams;
  granularity: MarketGranularity;
  currencySymbol: string;
  enabled: boolean;
};

type ChartPoint = {
  period: string;
  value: number | null;
};

function parsePointValue(raw: string | null): number | null {
  if (raw === null || raw === undefined) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

export function MarketIntelligenceSeriesSection({
  params,
  granularity,
  currencySymbol,
  enabled,
}: MarketIntelligenceSeriesSectionProps) {
  const { preferences, setPreferences, setChartType } =
    usePersistedChartPreferences({
      storageKey: STORAGE_KEY,
      defaults: { chartType: "line" },
      allowedChartTypes: TIME_MULTI_SERIES_TYPES,
    });
  const chartType = preferences.chartType ?? "line";

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [points, setPoints] = useState<MarketSeriesPoint[]>([]);
  const [dataStatus, setDataStatus] = useState<string>("ok");
  const [partialReason, setPartialReason] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || !params.instrument) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getMarketIntelligenceSeries(
      { ...params, granularity },
      controller.signal,
    )
      .then((payload) => {
        setPoints(payload.points);
        setDataStatus(payload.meta.data_status);
        setPartialReason(payload.meta.partial_reason);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setPoints([]);
        setError(mapMarketIntelligenceError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [enabled, params, granularity]);

  const chartPoints = useMemo<ChartPoint[]>(
    () =>
      points.map((point) => ({
        period: point.period,
        value: parsePointValue(point.value),
      })),
    [points],
  );

  const baseSeries = useMemo<MultiTypeSeriesSpec[]>(
    () => [
      {
        dataKey: "value",
        name: currencySymbol,
        fill: "var(--delpi-chart-series-1, #2563eb)",
      },
    ],
    [currencySymbol],
  );

  const series = useMemo(
    () => applySeriesFillPreferences(baseSeries, preferences.seriesFills),
    [baseSeries, preferences.seriesFills],
  );

  const formatValue = (value: number) =>
    value.toLocaleString("pt-BR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 4,
    });

  const hasData = chartPoints.some((point) => point.value !== null);
  const showPartialNote =
    !loading && !error && (dataStatus === "partial" || partialReason);

  return (
    <SuppliesSectionCard
      title={MARKET_INTELLIGENCE_CONTENT.chart.sectionTitle}
      hint={SP_HELP.marketIntelligenceSeries}
    >
      {loading ? (
        <SuppliesLoadingCard
          title={MARKET_INTELLIGENCE_CONTENT.chart.loading}
          variant="panel"
        />
      ) : null}
      {error ? (
        <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
      ) : null}
      {showPartialNote ? (
        <SuppliesStateBanner>
          {partialReason?.startsWith("fx_missing")
            ? MARKET_INTELLIGENCE_CONTENT.states.fxMissingNote
            : MARKET_INTELLIGENCE_CONTENT.states.partialNote}
        </SuppliesStateBanner>
      ) : null}
      {!loading && !error && !hasData ? (
        <SuppliesEmptyState
          title={MARKET_INTELLIGENCE_CONTENT.chart.emptyTitle}
          message={MARKET_INTELLIGENCE_CONTENT.chart.emptyMessage}
        />
      ) : null}
      {!loading && !error && hasData ? (
        <ChartViewShell
          prefix="sp"
          typeToggleLabel={MARKET_INTELLIGENCE_CONTENT.chart.typeLabel}
          seriesColorsLabel={
            MARKET_INTELLIGENCE_CONTENT.chart.seriesColorsLabel
          }
          typeToggle={
            <ChartTypeSegmentToggle
              family="time_multi_series"
              value={chartType}
              onChange={setChartType}
              idPrefix="supplies-market-type"
              prefix="sp"
              portalScopeClassName={SP_PORTAL_SCOPE}
            />
          }
          seriesColors={
            <ChartSeriesColorsPopover
              idPrefix="supplies-market-colors"
              portalScopeClassName={SP_PORTAL_SCOPE}
              series={series}
              values={preferences.seriesFills}
              summaryLabel={
                MARKET_INTELLIGENCE_CONTENT.chart.seriesColorsEmpty
              }
              panelTitle={
                MARKET_INTELLIGENCE_CONTENT.chart.seriesColorsPanelTitle
              }
              triggerAriaLabel={
                MARKET_INTELLIGENCE_CONTENT.chart.seriesColorsTriggerAria
              }
              resetLabel={MARKET_INTELLIGENCE_CONTENT.chart.seriesColorsReset}
              hints={SP_CHART_SERIES_HINTS}
              onChange={(dataKey: string, color: string) =>
                setPreferences((prev) => ({
                  ...prev,
                  seriesFills: {
                    ...(prev.seriesFills ?? {}),
                    [dataKey]: color,
                  },
                }))
              }
              onReset={() =>
                setPreferences((prev) => ({ ...prev, seriesFills: undefined }))
              }
            />
          }
          exportActions={
            <SuppliesTabularExportButtons
              compact
              disabled={!hasData || loading}
              onExport={(format) => {
                runTabularExport({
                  kind: "table",
                  format,
                  payload: {
                    title: MARKET_INTELLIGENCE_CONTENT.chart.sectionTitle,
                    columns: [
                      { key: "period", label: "Período" },
                      {
                        key: "value",
                        label: `${MARKET_INTELLIGENCE_CONTENT.summary.lastQuoteTitle} (${currencySymbol})`,
                      },
                    ],
                    rows: chartPoints.map((point) => ({
                      period: point.period,
                      value:
                        point.value === null ? "—" : formatValue(point.value),
                    })),
                  },
                });
              }}
            />
          }
        >
          <MultiTypeSeriesChart
            data={chartPoints}
            categoryKey="period"
            series={series}
            chartType={chartType}
            height={CHART_HEIGHT}
            formatY={formatValue}
            formatTooltipValue={formatValue}
            showLegend
          />
        </ChartViewShell>
      ) : null}
    </SuppliesSectionCard>
  );
}
