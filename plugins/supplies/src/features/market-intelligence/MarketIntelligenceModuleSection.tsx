/** Generic market-intelligence module section (PROC-0076 R2).
 *
 * One source module = selector + series chart + accessible table.
 * Rendering-only: values, coverage and freshness come from the
 * supplies-api BFF; the MFE never recomputes metrics.
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
  SuppliesDataTable,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesSectionCard,
  SuppliesSelectField,
  SuppliesStateBanner,
  SuppliesTabularExportButtons,
  SP_PORTAL_SCOPE,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_CHART_SERIES_HINTS } from "../../content/helpTooltips";
import type { MarketGranularity } from "./api";
import {
  mapMarketIntelligenceError,
  MARKET_INTELLIGENCE_CONTENT,
} from "./content";

const CHART_HEIGHT = 300;

export type ModuleSeriesResult<R> = {
  points: R[];
  dataStatus: string;
};

export type ModuleFetchArgs = {
  selection: string;
  granularity: MarketGranularity;
  date_from: string;
  date_to: string;
  signal?: AbortSignal;
};

type MarketIntelligenceModuleSectionProps<
  R extends { period: string; value: string | null },
> = {
  title: string;
  hint?: string;
  selectorLabel: string;
  selectorHint?: string;
  options: { value: string; label: string }[];
  selection: string;
  onSelectionChange: (value: string) => void;
  enabled: boolean;
  unavailableLabel?: string;
  from: string;
  to: string;
  granularity: MarketGranularity;
  fetchSeries: (args: ModuleFetchArgs) => Promise<ModuleSeriesResult<R>>;
  columns: DataTableColumn<R>[];
  valueAxisLabel: string;
  valueLegend: string;
  tableAriaLabel: string;
  storageKey: string;
};

function parsePointValue(raw: string | null): number | null {
  if (raw === null || raw === undefined) return null;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : null;
}

export function MarketIntelligenceModuleSection<
  R extends { period: string; value: string | null },
>({
  title,
  hint,
  selectorLabel,
  selectorHint,
  options,
  selection,
  onSelectionChange,
  enabled,
  unavailableLabel,
  from,
  to,
  granularity,
  fetchSeries,
  columns,
  valueAxisLabel,
  valueLegend,
  tableAriaLabel,
  storageKey,
}: MarketIntelligenceModuleSectionProps<R>) {
  const { preferences, setPreferences, setChartType } =
    usePersistedChartPreferences({
      storageKey,
      defaults: { chartType: "line" },
      allowedChartTypes: TIME_MULTI_SERIES_TYPES,
    });
  const chartType = preferences.chartType ?? "line";

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<R[]>([]);
  const [dataStatus, setDataStatus] = useState<string>("ok");

  const hasOptions = options.length > 0 && Boolean(selection);

  useEffect(() => {
    if (!enabled || !hasOptions) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    // Never render the previous query's rows while a new fetch runs.
    setRows([]);
    fetchSeries({
      selection,
      granularity,
      date_from: from,
      date_to: to,
      signal: controller.signal,
    })
      .then((result) => {
        setRows(result.points);
        setDataStatus(result.dataStatus);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setRows([]);
        setError(mapMarketIntelligenceError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [enabled, hasOptions, selection, granularity, from, to]);

  const chartPoints = useMemo(
    () =>
      rows.map((row) => ({
        period: row.period,
        value: parsePointValue(row.value),
      })),
    [rows],
  );

  const baseSeries = useMemo<MultiTypeSeriesSpec[]>(
    () => [
      {
        dataKey: "value",
        name: valueLegend,
        fill: "var(--delpi-chart-series-1, #2563eb)",
      },
    ],
    [valueLegend],
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
  const showPartialNote = !loading && !error && dataStatus === "partial";

  return (
    <SuppliesSectionCard title={title} hint={hint}>
      <div className="sp-module-filters">
        <SuppliesSelectField
          label={selectorLabel}
          hint={selectorHint}
          value={selection}
          options={options}
          onChange={onSelectionChange}
        />
      </div>
      {!hasOptions ? (
        <SuppliesStateBanner>
          {unavailableLabel ??
            MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable}
        </SuppliesStateBanner>
      ) : null}
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
          {MARKET_INTELLIGENCE_CONTENT.states.partialNote}
        </SuppliesStateBanner>
      ) : null}
      {hasOptions && !loading && !error && !hasData ? (
        <SuppliesEmptyState
          title={MARKET_INTELLIGENCE_CONTENT.chart.emptyTitle}
          message={MARKET_INTELLIGENCE_CONTENT.chart.emptyMessage}
        />
      ) : null}
      {hasOptions && !loading && !error && hasData ? (
        <>
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
                idPrefix={`${storageKey}-type`}
                prefix="sp"
                portalScopeClassName={SP_PORTAL_SCOPE}
              />
            }
            seriesColors={
              <ChartSeriesColorsPopover
                idPrefix={`${storageKey}-colors`}
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
                resetLabel={
                  MARKET_INTELLIGENCE_CONTENT.chart.seriesColorsReset
                }
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
                  setPreferences((prev) => ({
                    ...prev,
                    seriesFills: undefined,
                  }))
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
                      title,
                      columns: [
                        { key: "period", label: "Período" },
                        { key: "value", label: valueAxisLabel },
                      ],
                      rows: chartPoints.map((point) => ({
                        period: point.period,
                        value:
                          point.value === null
                            ? "—"
                            : formatValue(point.value),
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
          <div
            className="sp-list-table-region"
            role="region"
            aria-label={tableAriaLabel}
            tabIndex={0}
          >
            <SuppliesDataTable
              layout="section"
              columns={columns}
              rows={rows}
              rowKey={(row) => row.period}
              loading={false}
            />
          </div>
        </>
      ) : null}
    </SuppliesSectionCard>
  );
}
