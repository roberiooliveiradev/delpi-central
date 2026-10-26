/** Market intelligence page — metals & FX quotations (PROC-0076).

Composition only: filters → BFF calls → kit components. All quotes,
conversions and coverage semantics come from the supplies-api BFF.
*/

import { useEffect, useMemo, useState } from "react";
import { LineChart, RefreshCw } from "lucide-react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { SuppliesKpiCard } from "../../app/suppliesKpiCard";
import {
  SuppliesActionButton,
  SuppliesDataCardsGrid,
  SuppliesDateField,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSelectField,
  SuppliesSegmentToggle,
  SuppliesStateBanner,
  SuppliesStatusBadge,
  SuppliesTitleWithHelp,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  getMarketFxSeries,
  getMarketImportSeries,
  getMarketIntelligenceFilters,
  getMarketIntelligenceSummary,
  getMarketProducerPriceSeries,
  type MarketCurrency,
  type MarketFxKind,
  type MarketGranularity,
  type MarketImportPoint,
  type MarketProducerPricePoint,
  type MarketSeriesPoint,
  type MarketSummaryResponse,
} from "./api";
import {
  mapMarketIntelligenceError,
  MARKET_INTELLIGENCE_CONTENT,
} from "./content";
import { MarketIntelligenceModuleSection } from "./MarketIntelligenceModuleSection";
import { MarketIntelligenceMonthlyTable } from "./MarketIntelligenceMonthlyTable";
import { MarketIntelligenceSeriesSection } from "./MarketIntelligenceSeriesSection";
import { useMarketIntelligenceFilters } from "./useMarketIntelligenceFilters";

type MarketIntelligencePageProps = {
  basePath: string;
};

const CURRENCY_OPTIONS = [
  { value: "USD", label: "USD" },
  { value: "BRL", label: "BRL" },
];

const GRANULARITY_LABELS: Record<MarketGranularity, string> = {
  day: MARKET_INTELLIGENCE_CONTENT.filters.granularityDay,
  month: MARKET_INTELLIGENCE_CONTENT.filters.granularityMonth,
  year: MARKET_INTELLIGENCE_CONTENT.filters.granularityYear,
};

const FX_KIND_OPTIONS = [
  {
    value: "ptax_closing_sell",
    label: MARKET_INTELLIGENCE_CONTENT.filters.fxKindSell,
  },
  {
    value: "ptax_closing_buy",
    label: MARKET_INTELLIGENCE_CONTENT.filters.fxKindBuy,
  },
];

function formatQuote(raw: string | null, currency: MarketCurrency): string {
  if (raw === null) return MARKET_INTELLIGENCE_CONTENT.summary.unavailable;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed))
    return MARKET_INTELLIGENCE_CONTENT.summary.unavailable;
  return `${currency === "BRL" ? "R$" : "US$"} ${parsed.toLocaleString(
    "pt-BR",
    { minimumFractionDigits: 2, maximumFractionDigits: 4 },
  )}`;
}

function formatPercent(raw: string | null): string {
  if (raw === null) return MARKET_INTELLIGENCE_CONTENT.summary.unavailable;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed))
    return MARKET_INTELLIGENCE_CONTENT.summary.unavailable;
  const sign = parsed > 0 ? "+" : "";
  return `${sign}${parsed.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

function formatDecimal(raw: string | null | undefined): string {
  if (raw === null || raw === undefined) return "—";
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) return "—";
  return parsed.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

function coverageLabel(coverage: string): string {
  return (
    MARKET_INTELLIGENCE_CONTENT.table.coverageLabels[coverage] ?? coverage
  );
}

function dataStatusBadgeVariant(
  status: string | undefined,
): "success" | "warning" | "danger" | "info" | "neutral" {
  if (status === "ok") return "success";
  if (status === "partial") return "warning";
  if (status === "no_data") return "neutral";
  return "info";
}

export function MarketIntelligencePage({
  basePath,
}: MarketIntelligencePageProps) {
  const { FiltersRow } = spFiltersKit;
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [instruments, setInstruments] = useState<
    Awaited<ReturnType<typeof getMarketIntelligenceFilters>>["instruments"]
  >([]);
  const [defaultInstrument, setDefaultInstrument] = useState<string | null>(
    null,
  );
  const [sources, setSources] = useState<
    Awaited<ReturnType<typeof getMarketIntelligenceFilters>>["sources"]
  >([]);
  const [importNcms, setImportNcms] = useState<
    NonNullable<
      Awaited<
        ReturnType<typeof getMarketIntelligenceFilters>
      >["import_ncms"]
    >
  >([]);
  const [ippSeriesOptions, setIppSeriesOptions] = useState<
    NonNullable<
      Awaited<
        ReturnType<typeof getMarketIntelligenceFilters>
      >["producer_price_series"]
    >
  >([]);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setCatalogLoading(true);
    setCatalogError(null);
    getMarketIntelligenceFilters(controller.signal)
      .then((payload) => {
        setInstruments(payload.instruments);
        setDefaultInstrument(payload.default_instrument);
        setSources(payload.sources);
        setImportNcms(payload.import_ncms ?? []);
        setIppSeriesOptions(payload.producer_price_series ?? []);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setCatalogError(mapMarketIntelligenceError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setCatalogLoading(false);
      });
    return () => controller.abort();
  }, [reloadKey]);

  const selectableInstruments = useMemo(
    // Default-deny: only an explicit selectable === true offers the
    // instrument — absent/null/legacy payloads are never permission.
    () => instruments.filter((entry) => entry.selectable === true),
    [instruments],
  );

  const filters = useMarketIntelligenceFilters(
    selectableInstruments,
    defaultInstrument,
  );
  const ready = Boolean(filters.state.instrument);

  // R2 modules — same default-deny posture as legacy instruments.
  const selectableNcms = useMemo(
    () => importNcms.filter((entry) => entry.selectable === true),
    [importNcms],
  );
  const selectableIpp = useMemo(
    () => ippSeriesOptions.filter((entry) => entry.selectable === true),
    [ippSeriesOptions],
  );

  const ncmOptions = useMemo(
    () =>
      selectableNcms.map((entry) => ({
        value: entry.ncm_code,
        label: `${entry.ncm_code} — ${entry.description}`,
      })),
    [selectableNcms],
  );
  const ippOptions = useMemo(
    () =>
      selectableIpp.map((entry) => ({
        value: entry.series_id,
        label: entry.label,
      })),
    [selectableIpp],
  );

  const selectedNcm =
    selectableNcms.find(
      (entry) => entry.ncm_code === filters.state.ncm,
    )?.ncm_code ??
    selectableNcms[0]?.ncm_code ??
    "";
  const selectedIpp =
    selectableIpp.find(
      (entry) => entry.series_id === filters.state.ippSeries,
    )?.series_id ??
    selectableIpp[0]?.series_id ??
    "";

  const [summary, setSummary] = useState<MarketSummaryResponse | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    const controller = new AbortController();
    setSummaryLoading(true);
    setSummaryError(null);
    // Never render the previous query's data while a new fetch runs —
    // a denied/blocked response must not resurrect stale quotes.
    setSummary(null);
    getMarketIntelligenceSummary(filters.apiParams, controller.signal)
      .then(setSummary)
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setSummary(null);
        setSummaryError(mapMarketIntelligenceError(err));
      })
      .finally(() => {
        if (!controller.signal.aborted) setSummaryLoading(false);
      });
    return () => controller.abort();
  }, [ready, filters.apiParams, reloadKey]);

  const instrumentOptions = useMemo(
    () =>
      selectableInstruments.map((entry) => ({
        value: entry.code,
        label: entry.label,
      })),
    [selectableInstruments],
  );

  const granularityOptions = useMemo(
    () =>
      (filters.instrument?.granularities ?? ["month"]).map((value) => ({
        value,
        label: GRANULARITY_LABELS[value],
      })),
    [filters.instrument],
  );

  const currencyOptions = useMemo(
    () =>
      CURRENCY_OPTIONS.filter((option) =>
        (filters.instrument?.currencies ?? ["USD"]).includes(
          option.value as MarketCurrency,
        ),
      ),
    [filters.instrument],
  );

  const isMetalBrl =
    filters.instrument?.kind === "metal" && filters.state.currency === "BRL";
  const isFxInstrument = filters.instrument?.kind === "fx";

  const sourceAttribution = useMemo(() => {
    const sourceId = summary?.meta.source_id;
    if (!sourceId) return null;
    return sources.find((source) => source.source_id === sourceId) ?? null;
  }, [sources, summary]);

  const homeHref = buildPluginPath("home", basePath);

  return (
    <div className="sp-page-stack sp-market-intelligence">
      <SuppliesPagePath
        back={{
          label: MARKET_INTELLIGENCE_CONTENT.backToHome,
          href: homeHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[]}
        current={MARKET_INTELLIGENCE_CONTENT.title}
      />

      <SuppliesPageHero
        eyebrow={MARKET_INTELLIGENCE_CONTENT.eyebrow}
        title={
          <SuppliesTitleWithHelp
            title={MARKET_INTELLIGENCE_CONTENT.title}
            hint={SP_HELP.marketIntelligencePage}
          />
        }
        description={MARKET_INTELLIGENCE_CONTENT.description}
        badge={
          summary ? (
            <SuppliesStatusBadge
              label={`${MARKET_INTELLIGENCE_CONTENT.states.sourceLabel}: ${summary.meta.source_id ?? "—"}`}
              variant={dataStatusBadgeVariant(summary.meta.data_status)}
            />
          ) : undefined
        }
        actions={
          <SuppliesActionButton
            type="button"
            variant="default"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />{" "}
            {MARKET_INTELLIGENCE_CONTENT.reloadLabel}
          </SuppliesActionButton>
        }
      >
        <FiltersRow variant="extended">
          <SuppliesSelectField
            label={MARKET_INTELLIGENCE_CONTENT.filters.instrumentLabel}
            hint={SP_HELP.marketIntelligenceInstrument}
            value={filters.state.instrument}
            options={instrumentOptions}
            onChange={filters.setInstrument}
          />
          <SuppliesSelectField
            label={MARKET_INTELLIGENCE_CONTENT.filters.currencyLabel}
            hint={SP_HELP.marketIntelligenceCurrency}
            value={filters.state.currency}
            options={currencyOptions}
            onChange={(value) =>
              filters.setCurrency(value as MarketCurrency)
            }
          />
          <SuppliesSegmentToggle
            ariaLabel={MARKET_INTELLIGENCE_CONTENT.filters.granularityLabel}
            idPrefix="market-intelligence-granularity"
            size="sm"
            value={filters.state.granularity}
            options={granularityOptions}
            onChange={(value) =>
              filters.setGranularity(value as MarketGranularity)
            }
          />
          {(isMetalBrl || isFxInstrument) && (
            <SuppliesSelectField
              label={MARKET_INTELLIGENCE_CONTENT.filters.fxKindLabel}
              hint={SP_HELP.marketIntelligenceFxKind}
              value={filters.state.fxKind}
              options={FX_KIND_OPTIONS}
              onChange={(value) => filters.setFxKind(value as MarketFxKind)}
            />
          )}
          <SuppliesDateField
            label={MARKET_INTELLIGENCE_CONTENT.filters.fromLabel}
            hint={SP_HELP.marketIntelligencePeriod}
            value={filters.state.from}
            onChange={filters.setFrom}
          />
          <SuppliesDateField
            label={MARKET_INTELLIGENCE_CONTENT.filters.toLabel}
            hint={SP_HELP.marketIntelligencePeriod}
            value={filters.state.to}
            onChange={filters.setTo}
          />
        </FiltersRow>
      </SuppliesPageHero>

      {catalogError ? (
        <SuppliesStateBanner variant="error">{catalogError}</SuppliesStateBanner>
      ) : null}
      {summaryError ? (
        <SuppliesStateBanner variant="error">{summaryError}</SuppliesStateBanner>
      ) : null}
      {!catalogLoading &&
      !catalogError &&
      instruments.length > 0 &&
      selectableInstruments.length === 0 ? (
        <SuppliesStateBanner variant="error">
          {MARKET_INTELLIGENCE_CONTENT.states.noSelectableInstruments}
        </SuppliesStateBanner>
      ) : null}
      {summary && summary.meta.freshness?.status === "delayed" ? (
        <SuppliesStateBanner>
          {MARKET_INTELLIGENCE_CONTENT.states.staleNote}
          {` ${MARKET_INTELLIGENCE_CONTENT.states.staleEvidence(
            summary.meta.freshness.latest_observation_date,
            summary.meta.freshness.expected_latest_period,
          )}`}
        </SuppliesStateBanner>
      ) : null}

      <SuppliesSectionCard
        title={MARKET_INTELLIGENCE_CONTENT.summary.sectionTitle}
        hint={SP_HELP.marketIntelligenceSummary}
      >
        {catalogLoading || summaryLoading ? (
          <SuppliesLoadingCard
            title={MARKET_INTELLIGENCE_CONTENT.states.loading}
            variant="panel"
          />
        ) : null}
        {!catalogLoading && !summaryLoading && summary ? (
          <>
            <SuppliesDataCardsGrid>
              <SuppliesKpiCard
                title={MARKET_INTELLIGENCE_CONTENT.summary.lastQuoteTitle}
                titleHint={
                  MARKET_INTELLIGENCE_CONTENT.summary.lastQuoteHint
                }
                value={formatQuote(
                  summary.last_quote?.value ?? null,
                  filters.state.currency,
                )}
                contextLabel={
                  summary.last_quote
                    ? `${summary.last_quote.reference_date} · ${
                        summary.last_quote.unit ?? summary.instrument.label
                      }`
                    : filters.instrument?.label ?? ""
                }
                icon={
                  <LineChart size={22} strokeWidth={1.75} aria-hidden="true" />
                }
              />
              <SuppliesKpiCard
                title={MARKET_INTELLIGENCE_CONTENT.summary.averageTitle}
                titleHint={MARKET_INTELLIGENCE_CONTENT.summary.averageHint}
                value={formatQuote(
                  summary.period_average.value,
                  filters.state.currency,
                )}
                contextLabel={`${summary.period_average.valid_observations} ${MARKET_INTELLIGENCE_CONTENT.summary.validObservations}`}
                icon={
                  <LineChart size={22} strokeWidth={1.75} aria-hidden="true" />
                }
              />
              <SuppliesKpiCard
                title={MARKET_INTELLIGENCE_CONTENT.summary.variationTitle}
                titleHint={MARKET_INTELLIGENCE_CONTENT.summary.variationHint}
                value={formatPercent(summary.period_variation.percent)}
                contextLabel={`${filters.state.from} → ${filters.state.to}`}
                icon={
                  <LineChart size={22} strokeWidth={1.75} aria-hidden="true" />
                }
              />
              <SuppliesKpiCard
                title={MARKET_INTELLIGENCE_CONTENT.summary.fxReferenceTitle}
                titleHint={MARKET_INTELLIGENCE_CONTENT.summary.fxReferenceHint}
                value={formatQuote(summary.fx_reference.value, "BRL")}
                contextLabel={
                  summary.fx_reference.reference_date
                    ? `${summary.fx_reference.reference_date} · ${summary.fx_reference.rate_kind}`
                    : ""
                }
                icon={
                  <LineChart size={22} strokeWidth={1.75} aria-hidden="true" />
                }
              />
            </SuppliesDataCardsGrid>
            {sourceAttribution ? (
              <p className="delpi-ui-section-hint-label">
                {MARKET_INTELLIGENCE_CONTENT.states.attributionLabel}:{" "}
                {sourceAttribution.attribution} ·{" "}
                {sourceAttribution.license_reference}
              </p>
            ) : null}
          </>
        ) : null}
        {!catalogLoading &&
        !summaryLoading &&
        !summary &&
        !summaryError &&
        !catalogError &&
        !(instruments.length > 0 && selectableInstruments.length === 0) ? (
          <SuppliesEmptyState
            title={MARKET_INTELLIGENCE_CONTENT.chart.emptyTitle}
            message={MARKET_INTELLIGENCE_CONTENT.chart.emptyMessage}
          />
        ) : null}
      </SuppliesSectionCard>

      <MarketIntelligenceModuleSection<
        MarketImportPoint & { value: string | null }
      >
        title={MARKET_INTELLIGENCE_CONTENT.modules.importsTitle}
        hint={SP_HELP.marketIntelligenceImports}
        selectorLabel={MARKET_INTELLIGENCE_CONTENT.modules.importsNcmLabel}
        selectorHint={MARKET_INTELLIGENCE_CONTENT.modules.importsNcmHint}
        options={ncmOptions}
        selection={selectedNcm}
        onSelectionChange={filters.setNcm}
        enabled={!catalogError && !catalogLoading}
        unavailableLabel={
          MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable
        }
        from={filters.state.from}
        to={filters.state.to}
        granularity={filters.state.granularity}
        fetchSeries={async ({ selection, granularity, date_from, date_to, signal }) => {
          const payload = await getMarketImportSeries(
            {
              ncm: selection,
              granularity,
              date_from,
              date_to,
            },
            signal,
          );
          return {
            dataStatus: payload.meta.data_status,
            points: payload.points.map((point) => ({
              ...point,
              value: point.unit_value_usd_per_t,
            })),
          };
        }}
        columns={[
          {
            key: "period",
            header: MARKET_INTELLIGENCE_CONTENT.modules.importsPeriodColumn,
            render: (row) => row.period,
          },
          {
            key: "fob",
            header: MARKET_INTELLIGENCE_CONTENT.modules.importsFobColumn,
            render: (row) => formatDecimal(row.fob_usd_total),
            align: "right",
          },
          {
            key: "weight",
            header: MARKET_INTELLIGENCE_CONTENT.modules.importsWeightColumn,
            render: (row) => formatDecimal(row.net_weight_t),
            align: "right",
          },
          {
            key: "unit",
            header: MARKET_INTELLIGENCE_CONTENT.modules.importsUnitColumn,
            render: (row) => formatDecimal(row.unit_value_usd_per_t),
            align: "right",
          },
          {
            key: "coverage",
            header: MARKET_INTELLIGENCE_CONTENT.table.coverageColumn,
            render: (row) => coverageLabel(row.coverage),
          },
        ]}
        valueAxisLabel="US$/t"
        valueLegend={MARKET_INTELLIGENCE_CONTENT.modules.importsUnitColumn}
        tableAriaLabel={MARKET_INTELLIGENCE_CONTENT.modules.importsTitle}
        storageKey="supplies:market-intelligence:imports"
      />

      <MarketIntelligenceModuleSection<
        MarketProducerPricePoint & { value: string | null }
      >
        title={MARKET_INTELLIGENCE_CONTENT.modules.ippTitle}
        hint={SP_HELP.marketIntelligenceIpp}
        selectorLabel={MARKET_INTELLIGENCE_CONTENT.modules.ippSeriesLabel}
        options={ippOptions}
        selection={selectedIpp}
        onSelectionChange={filters.setIppSeries}
        enabled={!catalogError && !catalogLoading}
        unavailableLabel={
          MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable
        }
        from={filters.state.from}
        to={filters.state.to}
        granularity={filters.state.granularity}
        fetchSeries={async ({ selection, granularity, date_from, date_to, signal }) => {
          const payload = await getMarketProducerPriceSeries(
            {
              series_id: selection,
              granularity,
              date_from,
              date_to,
            },
            signal,
          );
          return {
            dataStatus: payload.meta.data_status,
            points: payload.points,
          };
        }}
        columns={[
          {
            key: "period",
            header: MARKET_INTELLIGENCE_CONTENT.modules.ippPeriodColumn,
            render: (row) => row.period,
          },
          {
            key: "value",
            header: MARKET_INTELLIGENCE_CONTENT.modules.ippValueColumn,
            render: (row) => formatDecimal(row.value),
            align: "right",
          },
          {
            key: "coverage",
            header: MARKET_INTELLIGENCE_CONTENT.table.coverageColumn,
            render: (row) => coverageLabel(row.coverage),
          },
        ]}
        valueAxisLabel={
          selectableIpp.find((s) => s.series_id === selectedIpp)?.unit ??
          MARKET_INTELLIGENCE_CONTENT.modules.ippValueColumn
        }
        valueLegend={
          selectableIpp.find((s) => s.series_id === selectedIpp)?.label ??
          "IPP"
        }
        tableAriaLabel={MARKET_INTELLIGENCE_CONTENT.modules.ippTitle}
        storageKey="supplies:market-intelligence:ipp"
      />

      <MarketIntelligenceModuleSection<MarketSeriesPoint>
        title={MARKET_INTELLIGENCE_CONTENT.modules.fxTitle}
        hint={SP_HELP.marketIntelligenceFx}
        selectorLabel={
          MARKET_INTELLIGENCE_CONTENT.modules.fxKindSelectorLabel
        }
        options={FX_KIND_OPTIONS}
        selection={filters.state.fxKind}
        onSelectionChange={(value) =>
          filters.setFxKind(value as MarketFxKind)
        }
        enabled={!catalogError && !catalogLoading}
        unavailableLabel={
          MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable
        }
        from={filters.state.from}
        to={filters.state.to}
        granularity={filters.state.granularity}
        fetchSeries={async ({ selection, granularity, date_from, date_to, signal }) => {
          const payload = await getMarketFxSeries(
            {
              fx_kind: selection as MarketFxKind,
              granularity,
              date_from,
              date_to,
            },
            signal,
          );
          return {
            dataStatus: payload.meta.data_status,
            points: payload.points,
          };
        }}
        columns={[
          {
            key: "period",
            header: MARKET_INTELLIGENCE_CONTENT.modules.fxPeriodColumn,
            render: (row) => row.period,
          },
          {
            key: "value",
            header: MARKET_INTELLIGENCE_CONTENT.modules.fxValueColumn,
            render: (row) => formatDecimal(row.value),
            align: "right",
          },
          {
            key: "coverage",
            header: MARKET_INTELLIGENCE_CONTENT.table.coverageColumn,
            render: (row) => coverageLabel(row.coverage),
          },
        ]}
        valueAxisLabel="R$/US$"
        valueLegend={MARKET_INTELLIGENCE_CONTENT.modules.fxValueColumn}
        tableAriaLabel={MARKET_INTELLIGENCE_CONTENT.modules.fxTitle}
        storageKey="supplies:market-intelligence:fx"
      />

      <MarketIntelligenceSeriesSection
        params={filters.apiParams}
        granularity={filters.state.granularity}
        currencySymbol={filters.state.currency}
        enabled={ready && !catalogError}
      />

      <MarketIntelligenceMonthlyTable
        params={filters.apiParams}
        showNativeAverage={isMetalBrl}
        enabled={ready && !catalogError}
      />
    </div>
  );
}
