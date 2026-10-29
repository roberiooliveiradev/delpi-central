/** Multi-instrument metals panel (PROC-0076 R4).
 *
 * One panel = contextual KPIs + one view mode (chart / table /
 * compare, never more than one rendered) + exports + source footer.
 * Rendering-only: every metric, availability flag and comparability
 * verdict comes from the supplies-api BFF — the MFE never recomputes
 * summaries and never turns a visual selection into a data grant
 * (D-04).
 */

import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  BarChart3,
  Boxes,
  GitCompareArrows,
  LineChart,
  Table2,
} from "lucide-react";
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

import { SuppliesKpiCard } from "../../app/suppliesKpiCard";
import {
  SuppliesDataCardsGrid,
  SuppliesDataTable,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesSectionCard,
  SuppliesSegmentToggle,
  SuppliesStateBanner,
  SuppliesStatusBadge,
  SuppliesTabularExportButtons,
  SP_PORTAL_SCOPE,
  type DataTableColumn,
} from "../../app/suppliesUi";
import { SP_CHART_SERIES_HINTS } from "../../content/helpTooltips";
import {
  getMarketQuoteCompare,
  getMarketQuoteSeries,
  type MarketGranularity,
  type MarketQuoteCompareResponse,
  type MarketQuoteSeriesResponse,
} from "./api";
import {
  mapMarketIntelligenceError,
  MARKET_INTELLIGENCE_CONTENT,
} from "./content";
import {
  formatMarketDate,
  formatMarketDecimal,
  formatMarketPercent,
  marketCoverageLabel,
  marketDataStatusBadgeVariant,
  marketUnavailableReasonLabel,
  parsePointValue,
} from "./marketLabels";
import { formatMarketUnit } from "./marketUnits";
import type { MarketViewMode } from "./marketIntelligenceUrl";

const CHART_HEIGHT = 300;

/** Canonical series-token chain — hexes live only in the scoped
 * token layer (``index.css``), never inline in the component. */
const SERIES_FILL_TOKENS = [
  "var(--sp-chart-series-1)",
  "var(--sp-chart-series-2)",
  "var(--sp-chart-series-3)",
  "var(--sp-chart-series-4)",
  "var(--sp-chart-series-5)",
  "var(--sp-chart-series-6)",
];

export type MetalsPanelRow = {
  period: string;
  [instrument: string]: string | null;
};

/** Union-of-periods rows for a set of quote series — gaps stay null,
 * never interpolated. */
function buildSeriesRows(
  entries: MarketQuoteSeriesResponse["series"],
): Record<string, string | number | null>[] {
  const periods = new Set<string>();
  for (const entry of entries) {
    for (const point of entry.points) periods.add(point.period);
  }
  const sorted = [...periods].sort();
  return sorted.map((period) => {
    const row: Record<string, string | number | null> = {
      period: formatMarketDate(period),
    };
    for (const entry of entries) {
      const point = entry.points.find((p) => p.period === period);
      row[entry.instrument.code] = point
        ? parsePointValue(point.value)
        : null;
    }
    return row;
  });
}

export type MarketMetalsPanelProps = {
  title: string;
  hint?: string;
  enabled: boolean;
  /** Selected instrument codes (already catalog-validated). */
  selection: string[];
  /** Total instruments in the catalog — zero renders the compact
   * configuration state, not a blank module. */
  configured: boolean;
  configState?: { title: string; message: string };
  /** Semantic section icon rendered in the header actions (R5.S2). */
  sectionIcon?: ReactNode;
  from: string;
  to: string;
  granularity: MarketGranularity;
  mode: MarketViewMode;
  onModeChange: (mode: MarketViewMode) => void;
  tableAriaLabel: string;
  storageKey: string;
  exportTitle: string;
  attribution: string | null;
  reloadKey: number;
};

const KPI_ICONS = {
  chart: <LineChart size={22} strokeWidth={1.75} aria-hidden="true" />,
  bar: <BarChart3 size={22} strokeWidth={1.75} aria-hidden="true" />,
  table: <Table2 size={22} strokeWidth={1.75} aria-hidden="true" />,
  metal: <Boxes size={22} strokeWidth={1.75} aria-hidden="true" />,
  compare: (
    <GitCompareArrows size={22} strokeWidth={1.75} aria-hidden="true" />
  ),
};

export function MarketMetalsPanel({
  title,
  hint,
  enabled,
  configured,
  configState,
  sectionIcon,
  selection,
  from,
  to,
  granularity,
  mode,
  onModeChange,
  tableAriaLabel,
  storageKey,
  exportTitle,
  attribution,
  reloadKey,
}: MarketMetalsPanelProps) {
  const { preferences, setPreferences, setChartType } =
    usePersistedChartPreferences({
      storageKey,
      defaults: { chartType: "line" },
      allowedChartTypes: TIME_MULTI_SERIES_TYPES,
    });
  const chartType = preferences.chartType ?? "line";

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<MarketQuoteSeriesResponse | null>(
    null,
  );
  const [comparePayload, setComparePayload] =
    useState<MarketQuoteCompareResponse | null>(null);

  const selectionKey = selection.join(",");

  useEffect(() => {
    if (!enabled || !configured || selection.length === 0) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    // Never render the previous query's data while a new fetch runs —
    // a denied/blocked response must not resurrect stale values.
    setPayload(null);
    setComparePayload(null);
    const params = {
      instruments: selectionKey,
      granularity,
      currency: "USD" as const,
      date_from: from,
      date_to: to,
    };
    const request =
      mode === "compare"
        ? getMarketQuoteCompare(params, controller.signal).then(
            (result) => ({ compare: result }),
          )
        : getMarketQuoteSeries(params, controller.signal).then(
            (result) => ({ series: result }),
          );
    request
      .then((result) => {
        if ("compare" in result) setComparePayload(result.compare);
        else setPayload(result.series);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(mapMarketIntelligenceError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [
    enabled,
    configured,
    selectionKey,
    selection.length,
    granularity,
    from,
    to,
    mode,
    reloadKey,
  ]);

  /** Authorized series — availability comes from the BFF, never
   * inferred client-side. */
  const authorized = useMemo(
    () =>
      (payload?.series ?? []).filter(
        (entry) => entry.availability.data_access_allowed === true,
      ),
    [payload],
  );
  /** Selected-but-denied instruments stay explicit (R5.S2) — their
   * unavailability is named with the BFF reason, never dropped
   * silently from the view. */
  const denied = useMemo(
    () =>
      (payload?.series ?? []).filter(
        (entry) => entry.availability.data_access_allowed !== true,
      ),
    [payload],
  );
  const withData = useMemo(
    () =>
      authorized.filter(
        (entry) => (entry.summary?.observed ?? 0) > 0,
      ),
    [authorized],
  );
  const allPending =
    payload !== null &&
    payload.series.length > 0 &&
    authorized.length === 0;

  /** Union of periods across authorized series — gaps stay null,
   * never interpolated. */
  const chartRows = useMemo(() => buildSeriesRows(authorized), [authorized]);

  /** One chart per display unit (R5.S2) — series with incompatible
   * units (e.g. US$/lb vs US$/t) are never drawn on the same axis. */
  const chartGroups = useMemo(() => {
    const groups = new Map<string, typeof authorized>();
    for (const entry of authorized) {
      const key = entry.unit ?? "";
      const bucket = groups.get(key);
      if (bucket) bucket.push(entry);
      else groups.set(key, [entry]);
    }
    return [...groups.entries()].map(([unit, entries]) => ({
      unit,
      entries,
      rows: buildSeriesRows(entries),
    }));
  }, [authorized]);

  const tableRows = useMemo<MetalsPanelRow[]>(
    () =>
      chartRows.map((row) => {
        const out: MetalsPanelRow = { period: String(row.period) };
        for (const entry of authorized) {
          const raw = row[entry.instrument.code];
          out[entry.instrument.code] =
            raw === null || raw === undefined ? null : String(raw);
        }
        return out;
      }),
    [chartRows, authorized],
  );

  const baseSeries = useMemo<MultiTypeSeriesSpec[]>(
    () =>
      authorized.map((entry, index) => ({
        dataKey: entry.instrument.code,
        name: `${entry.instrument.label} (${formatMarketUnit(entry.unit) || "—"})`,
        fill: SERIES_FILL_TOKENS[index % SERIES_FILL_TOKENS.length],
      })),
    [authorized],
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

  /** Distinct display units across authorized series — the note names
   * every native unit present, never just the first (R5.S2). */
  const distinctUnits = useMemo(() => {
    const set = new Set<string>();
    for (const entry of authorized) {
      set.add(formatMarketUnit(entry.unit) || "—");
    }
    return [...set].join(" · ");
  }, [authorized]);
  const hasData = chartRows.some((row) =>
    authorized.some(
      (entry) => row[entry.instrument.code] !== null,
    ),
  );
  const meta = payload?.meta ?? comparePayload?.meta ?? null;
  const showPartialNote =
    !loading && !error && meta?.data_status === "partial";

  const compareSeries = useMemo(
    () => comparePayload?.series ?? [],
    [comparePayload],
  );
  const comparable = comparePayload?.comparison.comparable === true;
  const compareChartRows = useMemo(() => {
    if (!comparePayload || !comparable) return [];
    return comparePayload.periods.map((period, index) => {
      const row: Record<string, string | number | null> = {
        period: formatMarketDate(period),
      };
      for (const entry of compareSeries) {
        const raw = entry.values?.[index] ?? null;
        row[entry.instrument.code] =
          raw === null ? null : Number(raw);
      }
      return row;
    });
  }, [comparePayload, compareSeries, comparable]);

  const compareSeriesSpecs = useMemo<MultiTypeSeriesSpec[]>(
    () =>
      compareSeries.map((entry, index) => ({
        dataKey: entry.instrument.code,
        name: entry.instrument.label,
        fill: SERIES_FILL_TOKENS[index % SERIES_FILL_TOKENS.length],
      })),
    [compareSeries],
  );

  /** Contextual KPIs — single selection renders the classic trio;
   * multi-selection renders one "latest reference" card per
   * authorized series (each labelled with its instrument). */
  const kpis = useMemo(() => {
    const content = MARKET_INTELLIGENCE_CONTENT.kpis;
    const items: {
      title: string;
      hint: string;
      value: string;
      context: string;
      icon: ReactNode;
    }[] = [];
    if (withData.length === 1) {
      const entry = withData[0];
      const summary = entry.summary;
      if (!summary) return items;
      const unitLabel = formatMarketUnit(entry.unit);
      items.push(
        {
          title: content.latestValueTitle,
          hint: content.latestValueHint,
          value: `${formatMarketDecimal(summary.latest?.value)} ${unitLabel}`,
          context: summary.latest
            ? [
                entry.instrument.label,
                formatMarketDate(summary.latest.period),
                summary.latest.quote_basis
                  ? MARKET_INTELLIGENCE_CONTENT.quoteBasis[
                      summary.latest.quote_basis
                    ] ?? summary.latest.quote_basis
                  : null,
              ]
                .filter(Boolean)
                .join(" · ")
            : entry.instrument.label,
          icon: KPI_ICONS.metal,
        },
        {
          title: content.averageTitle,
          hint: content.averageHint,
          value: `${formatMarketDecimal(summary.period_average)} ${unitLabel}`,
          context: `${summary.observed} ${MARKET_INTELLIGENCE_CONTENT.summary.validObservations}`,
          icon: KPI_ICONS.bar,
        },
        {
          title: content.variationTitle,
          hint: content.variationHint,
          value: formatMarketPercent(summary.period_change_pct),
          context: `${from} → ${to}`,
          icon: KPI_ICONS.chart,
        },
        {
          title: content.coverageTitle,
          hint: content.coverageHint,
          value: `${summary.observed}/${summary.expected}`,
          context: marketCoverageLabel(summary.coverage),
          icon: KPI_ICONS.table,
        },
      );
    } else {
      for (const entry of withData) {
        const summary = entry.summary;
        items.push({
          title: `${content.latestReferenceTitle} — ${entry.instrument.label}`,
          hint: content.latestReferenceHint,
          value: `${formatMarketDecimal(summary?.latest?.value)} ${formatMarketUnit(entry.unit)}`,
          context: [
            summary?.latest?.period
              ? formatMarketDate(summary.latest.period)
              : "",
            summary?.latest?.quote_basis
              ? MARKET_INTELLIGENCE_CONTENT.quoteBasis[
                  summary.latest.quote_basis
                ] ?? summary.latest.quote_basis
              : "",
            `${MARKET_INTELLIGENCE_CONTENT.kpis.variationTitle}: ${formatMarketPercent(summary?.period_change_pct)}`,
          ]
            .filter(Boolean)
            .join(" · "),
          icon: KPI_ICONS.metal,
        });
      }
    }
    return items;
  }, [withData, from, to]);

  const compareEligible = authorized.length >= 2;
  const compareDisabledHint = !compareEligible
    ? MARKET_INTELLIGENCE_CONTENT.panel.compareNeedTwoSeries
    : undefined;

  const modeOptions = [
    {
      value: "chart" as MarketViewMode,
      label: MARKET_INTELLIGENCE_CONTENT.panel.chartMode,
    },
    {
      value: "table" as MarketViewMode,
      label: MARKET_INTELLIGENCE_CONTENT.panel.tableMode,
    },
    {
      value: "compare" as MarketViewMode,
      label: MARKET_INTELLIGENCE_CONTENT.panel.compareMode,
      disabled: !compareEligible,
      ariaLabel:
        compareDisabledHint ??
        MARKET_INTELLIGENCE_CONTENT.panel.compareMode,
    },
  ];

  const tableColumns = useMemo<DataTableColumn<MetalsPanelRow>[]>(
    () => [
      {
        key: "period",
        header: MARKET_INTELLIGENCE_CONTENT.metals.periodColumn,
        render: (row) => formatMarketDate(row.period),
      },
      ...authorized.map(
        (entry): DataTableColumn<MetalsPanelRow> => ({
          key: entry.instrument.code,
          header: `${entry.instrument.label} (${formatMarketUnit(entry.unit) || "—"})`,
          render: (row) => formatMarketDecimal(row[entry.instrument.code]),
          align: "right",
        }),
      ),
    ],
    [authorized],
  );

  const handleExport = (format: string) => {
    runTabularExport({
      kind: "table",
      format,
      payload: {
        title: exportTitle,
        columns: tableColumns.map((col) => ({
          key: col.key,
          label:
            typeof col.header === "string" ? col.header : String(col.key),
        })),
        rows: tableRows.map((row) =>
          Object.fromEntries(
            tableColumns.map((col) => {
              const cell = col.render(row);
              return [
                col.key,
                typeof cell === "string" || typeof cell === "number"
                  ? cell
                  : String(cell ?? "—"),
              ];
            }),
          ),
        ),
      },
    });
  };

  return (
    <SuppliesSectionCard
      title={title}
      hint={hint}
      actions={
        <div className="sp-panel-actions">
          {sectionIcon ? (
            <span className="sp-section-icon" aria-hidden="true">
              {sectionIcon}
            </span>
          ) : null}
          <SuppliesSegmentToggle
            ariaLabel={
              MARKET_INTELLIGENCE_CONTENT.panel.viewSwitcherAriaLabel
            }
            idPrefix={`${storageKey}-mode`}
            size="sm"
            widthMode="content"
            value={mode}
            options={modeOptions}
            onChange={(value) => onModeChange(value as MarketViewMode)}
          />
          <SuppliesTabularExportButtons
            compact
            disabled={tableRows.length === 0 || loading || !configured}
            onExport={handleExport}
          />
          {meta?.feed_ingestion?.feed ? (
            <SuppliesStatusBadge
              label={`${MARKET_INTELLIGENCE_CONTENT.states.sourceLabel}: ${meta.feed_ingestion.feed}`}
              variant={marketDataStatusBadgeVariant(meta.data_status)}
            />
          ) : null}
        </div>
      }
    >
      {!configured ? (
        <SuppliesStateBanner>
          <strong>{configState?.title ?? ""}</strong>{" "}
          {configState?.message ??
            MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable}
        </SuppliesStateBanner>
      ) : null}
      {configured && selection.length === 0 ? (
        <SuppliesEmptyState
          title={MARKET_INTELLIGENCE_CONTENT.metals.emptySelectionTitle}
          message={
            MARKET_INTELLIGENCE_CONTENT.metals.emptySelectionMessage
          }
        />
      ) : null}
      {loading ? (
        <SuppliesLoadingCard
          title={MARKET_INTELLIGENCE_CONTENT.panel.loading}
          variant="panel"
        />
      ) : null}
      {error ? (
        <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
      ) : null}

      {configured && !loading && !error && selection.length > 0 ? (
        <>
          {allPending ? (
            <SuppliesStateBanner>
              {MARKET_INTELLIGENCE_CONTENT.metals.pendingSource}
            </SuppliesStateBanner>
          ) : null}
          {denied.length > 0 ? (
            <SuppliesStateBanner>
              <strong>
                {
                  MARKET_INTELLIGENCE_CONTENT.metals
                    .unavailableSelectionLabel
                }
                :
              </strong>{" "}
              {denied
                .map(
                  (entry) =>
                    `${entry.instrument.label} (${marketUnavailableReasonLabel(entry.availability.unavailable_reason)})`,
                )
                .join("; ")}
            </SuppliesStateBanner>
          ) : null}
          {showPartialNote ? (
            <SuppliesStateBanner>
              {MARKET_INTELLIGENCE_CONTENT.states.partialNote}
            </SuppliesStateBanner>
          ) : null}
          {mode === "compare" && comparePayload && !comparable ? (
            <SuppliesStateBanner>
              {comparePayload.comparison.reason === "incompatible_units"
                ? MARKET_INTELLIGENCE_CONTENT.panel.compareDisabledHint
                : MARKET_INTELLIGENCE_CONTENT.panel
                    .compareNeedTwoSeries}
            </SuppliesStateBanner>
          ) : null}

          {kpis.length > 0 ? (
            <SuppliesDataCardsGrid>
              {kpis.map((kpi) => (
                <SuppliesKpiCard
                  key={kpi.title}
                  title={kpi.title}
                  titleHint={kpi.hint}
                  value={kpi.value}
                  contextLabel={kpi.context}
                  icon={kpi.icon}
                />
              ))}
            </SuppliesDataCardsGrid>
          ) : null}

          {!allPending && !hasData && mode === "chart" ? (
            <SuppliesEmptyState
              title={MARKET_INTELLIGENCE_CONTENT.panel.emptyTitle}
              message={MARKET_INTELLIGENCE_CONTENT.panel.emptyMessage}
            />
          ) : null}
          {!allPending &&
          tableRows.length === 0 &&
          mode === "table" ? (
            <SuppliesEmptyState
              title={MARKET_INTELLIGENCE_CONTENT.panel.emptyTitle}
              message={MARKET_INTELLIGENCE_CONTENT.panel.emptyMessage}
            />
          ) : null}

          {hasData && mode === "chart" ? (
            <ChartViewShell
              prefix="sp"
              typeToggleLabel={
                MARKET_INTELLIGENCE_CONTENT.panel.typeLabel
              }
              seriesColorsLabel={
                MARKET_INTELLIGENCE_CONTENT.panel.seriesColorsLabel
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
                    MARKET_INTELLIGENCE_CONTENT.panel.seriesColorsEmpty
                  }
                  panelTitle={
                    MARKET_INTELLIGENCE_CONTENT.panel.seriesColorsPanelTitle
                  }
                  triggerAriaLabel={
                    MARKET_INTELLIGENCE_CONTENT.panel.seriesColorsTriggerAria
                  }
                  resetLabel={
                    MARKET_INTELLIGENCE_CONTENT.panel.seriesColorsReset
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
            >
              {chartGroups.map((group) => {
                const groupCodes = new Set(
                  group.entries.map((e) => e.instrument.code),
                );
                const groupSeries = series.filter((spec) =>
                  groupCodes.has(spec.dataKey),
                );
                const groupHasData = group.rows.some((row) =>
                  group.entries.some(
                    (e) => row[e.instrument.code] !== null,
                  ),
                );
                if (!groupHasData) return null;
                return (
                  <div
                    key={group.unit || "unknown-unit"}
                    className="sp-market-chart-group"
                  >
                    <p className="delpi-ui-section-hint-label">
                      {formatMarketUnit(group.unit) || "—"}
                    </p>
                    <MultiTypeSeriesChart
                      data={group.rows}
                      categoryKey="period"
                      series={groupSeries}
                      chartType={chartType}
                      height={CHART_HEIGHT}
                      formatY={formatValue}
                      formatTooltipValue={formatValue}
                      showLegend
                    />
                  </div>
                );
              })}
            </ChartViewShell>
          ) : null}

          {mode === "table" && tableRows.length > 0 ? (
            <>
              <div
                className="sp-list-table-region"
                role="region"
                aria-label={tableAriaLabel}
                tabIndex={0}
              >
                <SuppliesDataTable
                  layout="section"
                  columns={tableColumns}
                  rows={tableRows}
                  rowKey={(row) => row.period}
                  loading={false}
                />
              </div>
            </>
          ) : null}

          {mode === "compare" && comparable ? (
            <ChartViewShell
              prefix="sp"
              typeToggleLabel={
                MARKET_INTELLIGENCE_CONTENT.panel.typeLabel
              }
              seriesColorsLabel={
                MARKET_INTELLIGENCE_CONTENT.panel.seriesColorsLabel
              }
              typeToggle={
                <ChartTypeSegmentToggle
                  family="time_multi_series"
                  value={chartType}
                  onChange={setChartType}
                  idPrefix={`${storageKey}-compare-type`}
                  prefix="sp"
                  portalScopeClassName={SP_PORTAL_SCOPE}
                />
              }
            >
              <MultiTypeSeriesChart
                data={compareChartRows}
                categoryKey="period"
                series={compareSeriesSpecs}
                chartType={chartType}
                height={CHART_HEIGHT}
                formatY={formatValue}
                formatTooltipValue={formatValue}
                showLegend
              />
              <p className="delpi-ui-section-hint-label">
                {MARKET_INTELLIGENCE_CONTENT.states.methodLabel}:{" "}
                {comparePayload?.comparison.method ?? "—"}
                {comparePayload?.comparison.unit
                  ? ` · ${formatMarketUnit(comparePayload.comparison.unit)}`
                  : ""}
              </p>
            </ChartViewShell>
          ) : null}

          {distinctUnits ? (
            <p className="delpi-ui-section-hint-label">
              {MARKET_INTELLIGENCE_CONTENT.metals.unitNote(distinctUnits)}
            </p>
          ) : null}
          {attribution ? (
            <p className="delpi-ui-section-hint-label">
              {MARKET_INTELLIGENCE_CONTENT.states.attributionLabel}:{" "}
              {attribution}
            </p>
          ) : null}
        </>
      ) : null}
    </SuppliesSectionCard>
  );
}
