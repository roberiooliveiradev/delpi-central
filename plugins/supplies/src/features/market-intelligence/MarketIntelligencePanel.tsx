/** Single analysis panel for one market-intelligence perspective
 * (PROC-0076 R3).
 *
 * One panel = contextual KPIs + one view mode (chart XOR table, never
 * both rendered) + exports + source/methodology footer. Rendering-only:
 * every metric comes from the BFF ``summary`` read model — the MFE
 * never recomputes variations, averages or coverage.
 */

import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  AlertTriangle,
  BarChart3,
  CalendarDays,
  Database,
  History,
  Layers,
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
import type {
  MarketFeedIngestion,
  MarketFreshness,
  MarketGranularity,
  MarketSeriesSummary,
} from "./api";
import {
  mapMarketIntelligenceError,
  MARKET_INTELLIGENCE_CONTENT,
} from "./content";
import {
  formatMarketDate,
  formatMarketDateTime,
  formatMarketDecimal,
  formatMarketPercent,
  marketCoverageLabel,
  marketDataStatusBadgeVariant,
  marketRunOutcomeLabel,
  marketUnavailableReasonLabel,
  parsePointValue,
} from "./marketLabels";
import { formatMarketUnit } from "./marketUnits";
import type { MarketViewMode } from "./marketIntelligenceUrl";

const CHART_HEIGHT = 300;

export type PanelRow = {
  period: string;
  value: string | null;
  coverage: string;
};

export type PerspectiveFetchResult = {
  points: PanelRow[];
  summary: MarketSeriesSummary | null;
  meta: {
    data_status: string;
    freshness: MarketFreshness | null;
    source_id: string | null;
    feed_ingestion?: MarketFeedIngestion | null;
    last_successful_ingestion_at: string | null;
  };
};

export type PanelFetchArgs = {
  selection: string;
  granularity: MarketGranularity;
  date_from: string;
  date_to: string;
  signal?: AbortSignal;
};

/** KPI layout per metric kind — the BFF decides which fields exist;
 * the layout only picks which ones to surface. */
export type KpiLayout = "index" | "percent" | "fx" | "import";

type MarketIntelligencePanelProps<R extends PanelRow> = {
  title: string;
  hint?: string;
  enabled: boolean;
  /** Whether the perspective has a selectable series/NCM — an empty
   * allowlist renders the compact configuration state, not a blank
   * module (R3-07). */
  configured: boolean;
  configState?: {
    title: string;
    message: string;
    /** Honest preview of the metrics the perspective will render once
     * configured — labels/hints only, values stay ``—`` (R5.S2). */
    preview?: { title: string; hint: string }[];
    nextSteps?: string;
  };
  /** Semantic section icon rendered in the header actions (R5.S2). */
  sectionIcon?: ReactNode;
  /** Friendly label of the active granularity (context cards). */
  granularityLabel?: string;
  /** Extra unit context (e.g. IPP base reference). */
  unitDetail?: string;
  selection: string;
  from: string;
  to: string;
  granularity: MarketGranularity;
  mode: MarketViewMode;
  onModeChange: (mode: MarketViewMode) => void;
  fetchSeries: (args: PanelFetchArgs) => Promise<PerspectiveFetchResult>;
  columns: DataTableColumn<R>[];
  kpiLayout: KpiLayout;
  unitLabel: string;
  valueLegend: string;
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
  alert: (
    <AlertTriangle size={22} strokeWidth={1.75} aria-hidden="true" />
  ),
  history: <History size={22} strokeWidth={1.75} aria-hidden="true" />,
  database: <Database size={22} strokeWidth={1.75} aria-hidden="true" />,
  calendar: (
    <CalendarDays size={22} strokeWidth={1.75} aria-hidden="true" />
  ),
  series: <Layers size={22} strokeWidth={1.75} aria-hidden="true" />,
};

export function MarketIntelligencePanel<R extends PanelRow>({
  title,
  hint,
  enabled,
  configured,
  configState,
  sectionIcon,
  granularityLabel,
  unitDetail,
  selection,
  from,
  to,
  granularity,
  mode,
  onModeChange,
  fetchSeries,
  columns,
  kpiLayout,
  unitLabel,
  valueLegend,
  tableAriaLabel,
  storageKey,
  exportTitle,
  attribution,
  reloadKey,
}: MarketIntelligencePanelProps<R>) {
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
  const [summary, setSummary] = useState<MarketSeriesSummary | null>(null);
  const [meta, setMeta] = useState<PerspectiveFetchResult["meta"] | null>(
    null,
  );

  useEffect(() => {
    if (!enabled || !configured || !selection) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    // Never render the previous query's data while a new fetch runs —
    // a denied/blocked response must not resurrect stale values.
    setRows([]);
    setSummary(null);
    fetchSeries({
      selection,
      granularity,
      date_from: from,
      date_to: to,
      signal: controller.signal,
    })
      .then((result) => {
        setRows(result.points as R[]);
        setSummary(result.summary ?? null);
        setMeta(result.meta);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setRows([]);
        setSummary(null);
        setError(mapMarketIntelligenceError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [enabled, configured, selection, granularity, from, to, reloadKey]);

  const chartPoints = useMemo(
    () =>
      rows.map((row) => ({
        period: formatMarketDate(row.period),
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
  const showPartialNote =
    !loading && !error && meta?.data_status === "partial";
  const showStaleNote =
    !loading && !error && meta?.freshness?.status === "delayed";
  const missingPeriods = summary?.missing_periods ?? [];
  const unavailableReason =
    !loading && !error && summary && summary.observed === 0
      ? summary.unavailable_reason
      : null;

  const handleExport = (format: string) => {
    runTabularExport({
      kind: "table",
      format,
      payload: {
        title: exportTitle,
        columns: columns.map((col) => ({
          key: col.key,
          label:
            typeof col.header === "string" ? col.header : String(col.key),
        })),
        rows: rows.map((row) =>
          Object.fromEntries(
            columns.map((col) => {
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

  const friendlyUnit = formatMarketUnit(unitLabel);

  const kpis = useMemo(() => {
    if (!summary || summary.observed === 0) return [];
    const content = MARKET_INTELLIGENCE_CONTENT.kpis;
    const items: {
      title: string;
      hint: string;
      value: string;
      context: string;
      icon: ReactNode;
    }[] = [];
    const latestContext = [
      summary.latest
        ? `Competência ${formatMarketDate(summary.latest.period)}`
        : "",
      unitDetail ?? "",
    ]
      .filter(Boolean)
      .join(" · ");
    if (kpiLayout === "import") {
      items.push(
        {
          title: content.latestUnitValueTitle,
          hint: content.latestUnitValueHint,
          value: `${formatMarketDecimal(summary.latest?.value)} ${friendlyUnit}`,
          context: latestContext,
          icon: KPI_ICONS.chart,
        },
        {
          title: content.fobTotalTitle,
          hint: content.fobTotalHint,
          value: `US$ ${formatMarketDecimal(summary.totals?.fob_usd_total)}`,
          context: `${summary.observed}/${summary.expected} competências`,
          icon: KPI_ICONS.bar,
        },
        {
          title: content.weightTotalTitle,
          hint: content.weightTotalHint,
          value: `${formatMarketDecimal(summary.totals?.net_weight_t)} t`,
          context: `${formatMarketDate(from)} → ${formatMarketDate(to)}`,
          icon: KPI_ICONS.bar,
        },
      );
    } else {
      items.push({
        title:
          kpiLayout === "fx"
            ? content.latestRateTitle
            : content.latestValueTitle,
        hint:
          kpiLayout === "fx"
            ? content.latestRateHint
            : content.latestValueHint,
        value: `${formatMarketDecimal(summary.latest?.value)} ${friendlyUnit}`,
        context: latestContext,
        icon: KPI_ICONS.chart,
      });
      if (kpiLayout === "percent") {
        items.push(
          {
            title: content.minTitle,
            hint: content.minHint,
            value: `${formatMarketPercent(summary.period_min?.value)}`,
            context: summary.period_min
              ? `Competência ${formatMarketDate(summary.period_min.period)}`
              : "",
            icon: KPI_ICONS.bar,
          },
          {
            title: content.maxTitle,
            hint: content.maxHint,
            value: `${formatMarketPercent(summary.period_max?.value)}`,
            context: summary.period_max
              ? `Competência ${formatMarketDate(summary.period_max.period)}`
              : "",
            icon: KPI_ICONS.bar,
          },
        );
      } else {
        if (kpiLayout === "fx" || kpiLayout === "index") {
          items.push({
            title: content.averageTitle,
            hint: content.averageHint,
            value: `${formatMarketDecimal(summary.period_average)} ${friendlyUnit}`,
            context: `${summary.observed} ${MARKET_INTELLIGENCE_CONTENT.summary.validObservations}`,
            icon: KPI_ICONS.bar,
          });
        }
        if (kpiLayout === "index") {
          items.push(
            {
              title: content.minValueTitle,
              hint: content.minValueHint,
              value: `${formatMarketDecimal(summary.period_min?.value)} ${friendlyUnit}`,
              context: summary.period_min
                ? `Competência ${formatMarketDate(summary.period_min.period)}`
                : "",
              icon: KPI_ICONS.bar,
            },
            {
              title: content.maxValueTitle,
              hint: content.maxValueHint,
              value: `${formatMarketDecimal(summary.period_max?.value)} ${friendlyUnit}`,
              context: summary.period_max
                ? `Competência ${formatMarketDate(summary.period_max.period)}`
                : "",
              icon: KPI_ICONS.bar,
            },
          );
        } else {
          items.push({
            title: content.variationTitle,
            hint: content.variationHint,
            value: formatMarketPercent(summary.period_change_pct),
            context: `${formatMarketDate(from)} → ${formatMarketDate(to)}`,
            icon: KPI_ICONS.chart,
          });
        }
      }
    }
    items.push({
      title: content.coverageTitle,
      hint: content.coverageHint,
      value: `${summary.observed}/${summary.expected}`,
      context: marketCoverageLabel(summary.coverage),
      icon: KPI_ICONS.table,
    });
    return items;
  }, [summary, kpiLayout, friendlyUnit, unitDetail, from, to]);

  /** Compact context for zero-observation states (R5.S3): at most
   * three scannable items — last collection attempt, latest persisted
   * observation, period coverage. Long messages belong to the state
   * banner above, never to a KPI value slot; the selected series and
   * the raw filter range are already visible in the filters row. */
  const statusKpis = useMemo(() => {
    if (!summary || summary.observed > 0) return [];
    const sc = MARKET_INTELLIGENCE_CONTENT.statusCards;
    const feed = meta?.feed_ingestion;
    return [
      {
        title: sc.lastAttemptTitle,
        hint: sc.lastAttemptHint,
        value: formatMarketDateTime(
          feed?.last_run_started_at ?? feed?.last_successful_at,
        ),
        context: marketRunOutcomeLabel(feed?.last_run_outcome),
        icon: KPI_ICONS.history,
      },
      {
        title: sc.latestObservationTitle,
        hint: sc.latestObservationHint,
        value: formatMarketDate(
          feed?.latest_observation_date ??
            meta?.freshness?.latest_observation_date,
        ),
        context: "",
        icon: KPI_ICONS.database,
      },
      {
        title: sc.coverageTitle,
        hint: sc.coverageHint,
        value: `${summary.observed}/${summary.expected}`,
        context: [
          marketCoverageLabel(summary.coverage),
          granularityLabel ?? "",
        ]
          .filter(Boolean)
          .join(" · "),
        icon: KPI_ICONS.table,
      },
    ];
  }, [summary, meta, granularityLabel]);

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
      // R3: comparison is only valid between same-unit series — no
      // approved pair exists yet, so the mode is explicit but disabled.
      value: "compare" as MarketViewMode,
      label: MARKET_INTELLIGENCE_CONTENT.panel.compareMode,
      disabled: true,
      ariaLabel: MARKET_INTELLIGENCE_CONTENT.panel.compareDisabledHint,
    },
  ];

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
            disabled={rows.length === 0 || loading || !configured}
            onExport={handleExport}
          />
          {meta?.source_id ? (
            <SuppliesStatusBadge
              label={`${MARKET_INTELLIGENCE_CONTENT.states.sourceLabel}: ${meta.source_id}`}
              variant={marketDataStatusBadgeVariant(meta.data_status)}
            />
          ) : null}
        </div>
      }
    >
      {!configured ? (
        <>
          <SuppliesStateBanner>
            <strong>{configState?.title ?? ""}</strong>{" "}
            {configState?.message ??
              MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable}
          </SuppliesStateBanner>
          {configState?.nextSteps ? (
            <p className="delpi-ui-section-hint-label">
              <strong>
                {MARKET_INTELLIGENCE_CONTENT.panel.nextStepsLabel}:
              </strong>{" "}
              {configState.nextSteps}
            </p>
          ) : null}
          {configState?.preview?.length ? (
            <>
              <p className="delpi-ui-section-hint-label">
                {MARKET_INTELLIGENCE_CONTENT.panel.configPreviewLabel}
              </p>
              <SuppliesDataCardsGrid>
                {configState.preview.map((card) => (
                  <SuppliesKpiCard
                    key={card.title}
                    title={card.title}
                    titleHint={card.hint}
                    value={
                      MARKET_INTELLIGENCE_CONTENT.statusCards.emptyValue
                    }
                    contextLabel=""
                    icon={KPI_ICONS.table}
                  />
                ))}
              </SuppliesDataCardsGrid>
            </>
          ) : null}
        </>
      ) : null}
      {loading && configured ? (
        <SuppliesLoadingCard
          title={MARKET_INTELLIGENCE_CONTENT.panel.loading}
          variant="panel"
        />
      ) : null}
      {error ? (
        <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner>
      ) : null}

      {configured && !loading && !error ? (
        <>
          {unavailableReason ? (
            <SuppliesStateBanner>
              {marketUnavailableReasonLabel(unavailableReason)}
            </SuppliesStateBanner>
          ) : null}
          {showStaleNote ? (
            <SuppliesStateBanner>
              {MARKET_INTELLIGENCE_CONTENT.states.staleNote}
              {` ${MARKET_INTELLIGENCE_CONTENT.states.staleEvidence(
                formatMarketDate(
                  meta?.freshness?.latest_observation_date ?? null,
                ),
                formatMarketDate(
                  meta?.freshness?.expected_latest_period ?? null,
                ),
              )}`}
            </SuppliesStateBanner>
          ) : null}
          {showPartialNote ? (
            <SuppliesStateBanner>
              {MARKET_INTELLIGENCE_CONTENT.states.partialNote}
            </SuppliesStateBanner>
          ) : null}

          {summary ? (
            <SuppliesDataCardsGrid>
              {(summary.observed > 0 ? kpis : statusKpis).map((kpi) => (
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

          {!hasData && !unavailableReason && mode === "chart" ? (
            <SuppliesEmptyState
              title={MARKET_INTELLIGENCE_CONTENT.panel.emptyTitle}
              message={MARKET_INTELLIGENCE_CONTENT.panel.emptyMessage}
            />
          ) : null}
          {rows.length === 0 &&
          !unavailableReason &&
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

          {mode === "table" && rows.length > 0 && !unavailableReason ? (
            <>
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

          {missingPeriods.length > 0 && !unavailableReason ? (
            <p className="delpi-ui-section-hint-label">
              {MARKET_INTELLIGENCE_CONTENT.panel.missingPeriodsNote(
                missingPeriods.map(formatMarketDate),
              )}{" "}
              {MARKET_INTELLIGENCE_CONTENT.panel.missingPeriodsExplanation}
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
