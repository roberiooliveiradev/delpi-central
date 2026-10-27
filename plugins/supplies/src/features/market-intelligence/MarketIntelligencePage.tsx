/** Market intelligence page — three exclusive perspectives
 * (PROC-0076 R4).
 *
 * Composition only: perspective switcher → contextual filters → one
 * analysis panel. All metrics, conversions, coverage, availability
 * and comparability semantics come from the supplies-api BFF.
 */

import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeftRight,
  Boxes,
  Factory,
  RefreshCw,
  Ship,
} from "lucide-react";

import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import {
  SuppliesActionButton,
  SuppliesDateField,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSegmentToggle,
  SuppliesSelectField,
  SuppliesStateBanner,
  SuppliesTitleWithHelp,
  spFiltersKit,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import {
  getMarketFxSeries,
  getMarketImportSeries,
  getMarketIntelligenceFilters,
  getMarketProducerPriceSeries,
  type MarketFxKind,
  type MarketGranularity,
  type MarketImportPoint,
  type MarketProducerPricePoint,
  type MarketSeriesPoint,
} from "./api";
import {
  mapMarketIntelligenceError,
  MARKET_INTELLIGENCE_CONTENT,
} from "./content";
import { MarketInstrumentCard } from "./MarketInstrumentCard";
import { MarketIntelligencePanel } from "./MarketIntelligencePanel";
import { MarketMetalsPanel } from "./MarketMetalsPanel";
import { formatMarketUnit } from "./marketUnits";
import {
  formatMarketDate,
  formatMarketDecimal,
  marketCoverageLabel,
} from "./marketLabels";
import type {
  MarketIndicatorKind,
  MarketPerspective,
} from "./marketIntelligenceUrl";
import { useMarketIntelligenceFilters } from "./useMarketIntelligenceFilters";

type MarketIntelligencePageProps = {
  basePath: string;
};

const GRANULARITY_LABELS: Record<MarketGranularity, string> = {
  day: MARKET_INTELLIGENCE_CONTENT.filters.granularityDay,
  week: MARKET_INTELLIGENCE_CONTENT.filters.granularityWeek,
  month: MARKET_INTELLIGENCE_CONTENT.filters.granularityMonth,
  year: MARKET_INTELLIGENCE_CONTENT.filters.granularityYear,
};

const ALL_GRANULARITIES: MarketGranularity[] = [
  "day",
  "week",
  "month",
  "year",
];

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

const PERSPECTIVE_OPTIONS: { value: MarketPerspective; label: string }[] = [
  {
    value: "metals",
    label: MARKET_INTELLIGENCE_CONTENT.perspectives.metals,
  },
  {
    value: "fx",
    label: MARKET_INTELLIGENCE_CONTENT.perspectives.fx,
  },
  {
    value: "indicators",
    label: MARKET_INTELLIGENCE_CONTENT.perspectives.indicators,
  },
];

const INDICATOR_OPTIONS: { value: MarketIndicatorKind; label: string }[] = [
  {
    value: "ipp",
    label: MARKET_INTELLIGENCE_CONTENT.filters.indicatorIpp,
  },
  {
    value: "comex",
    label: MARKET_INTELLIGENCE_CONTENT.filters.indicatorComex,
  },
];


export function MarketIntelligencePage({
  basePath,
}: MarketIntelligencePageProps) {
  const { FiltersRow } = spFiltersKit;
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [instruments, setInstruments] = useState<
    Awaited<ReturnType<typeof getMarketIntelligenceFilters>>["instruments"]
  >([]);
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

  /** Metal instruments stay UI-selectable while source rights are
   * pending (D-04) — ``selectable_in_ui`` is catalog presence, never
   * a display grant. */
  const metalCards = useMemo(
    () =>
      instruments.filter(
        (entry) =>
          entry.kind === "metal" && entry.selectable_in_ui === true,
      ),
    [instruments],
  );

  // Same default-deny posture as legacy instruments — absent/null is
  // never a permission.
  const selectableNcms = useMemo(
    () => importNcms.filter((entry) => entry.selectable === true),
    [importNcms],
  );
  const selectableIpp = useMemo(
    () => ippSeriesOptions.filter((entry) => entry.selectable === true),
    [ippSeriesOptions],
  );
  const fxInstrument = useMemo(
    () =>
      instruments.find(
        (entry) => entry.code === "usd-brl" && entry.selectable === true,
      ),
    [instruments],
  );

  /** Default perspective is data-driven — metals first (R4 landing),
   * otherwise the first perspective with usable observations. */
  const defaultView = useMemo<MarketPerspective>(() => {
    if (metalCards.length > 0) return "metals";
    const hasObservations = (
      list?: { selectable?: boolean; latest_observation_date: string | null }[],
    ) =>
      (list ?? []).some(
        (entry) =>
          entry.selectable === true && entry.latest_observation_date,
      );
    if (hasObservations(ippSeriesOptions)) return "indicators";
    if (fxInstrument?.latest_observation_date) return "fx";
    return "indicators";
  }, [metalCards, ippSeriesOptions, fxInstrument]);

  const filters = useMarketIntelligenceFilters(defaultView);
  const view = filters.state.view;
  const indicator = filters.state.indicator;

  /** URL selection is catalog-validated — unknown codes never reach
   * the BFF. Order follows the catalog, not the query string. */
  const selectedMetals = useMemo(
    () =>
      metalCards
        .map((entry) => entry.code)
        .filter((code) => filters.state.metals.includes(code)),
    [metalCards, filters.state.metals],
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
    selectableNcms.find((entry) => entry.ncm_code === filters.state.ncm)
      ?.ncm_code ??
    selectableNcms[0]?.ncm_code ??
    "";
  const selectedIppEntry =
    selectableIpp.find(
      (entry) => entry.series_id === filters.state.ippSeries,
    ) ?? selectableIpp[0];
  const selectedIpp = selectedIppEntry?.series_id ?? "";

  /** The four frequencies stay visible as product capability —
   * unsupported ones are disabled per the real catalog contract
   * (never silently dropped). */
  const supportedGranularities = useMemo(() => {
    const supported = new Set<MarketGranularity>();
    if (view === "fx") {
      for (const value of fxInstrument?.granularities ?? []) {
        supported.add(value);
      }
      // PTAX is a daily series — weekly aggregation is a BFF
      // contract capability on top of daily observations.
      supported.add("week");
      if (supported.size === 0) ALL_GRANULARITIES.forEach((g) => supported.add(g));
    } else if (view === "metals") {
      const selected = selectedMetals.length
        ? metalCards.filter((entry) =>
            selectedMetals.includes(entry.code),
          )
        : metalCards;
      for (const entry of selected) {
        for (const value of entry.granularities ?? []) {
          supported.add(value);
        }
      }
    } else {
      const entries =
        indicator === "comex" ? selectableNcms : selectableIpp;
      for (const entry of entries) {
        for (const value of entry.granularities ?? []) {
          supported.add(value);
        }
      }
    }
    if (supported.size === 0) {
      supported.add("month");
      supported.add("year");
    }
    return supported;
  }, [
    view,
    indicator,
    fxInstrument,
    metalCards,
    selectedMetals,
    selectableNcms,
    selectableIpp,
  ]);

  const granularityOptions = useMemo(
    () =>
      ALL_GRANULARITIES.map((value) => ({
        value,
        label: GRANULARITY_LABELS[value],
        disabled: !supportedGranularities.has(value),
        ariaLabel: supportedGranularities.has(value)
          ? GRANULARITY_LABELS[value]
          : `${GRANULARITY_LABELS[value]} — ${MARKET_INTELLIGENCE_CONTENT.metals.frequencyUnsupported}`,
      })),
    [supportedGranularities],
  );

  /** Attribution/license of the active perspective's source. */
  const activeSourceId = useMemo(() => {
    if (view === "metals") {
      const first = metalCards.find((entry) =>
        selectedMetals.includes(entry.code),
      );
      return first?.source_id ?? metalCards[0]?.source_id;
    }
    if (view === "fx") return "bcb-ptax";
    if (indicator === "ipp") return selectedIppEntry?.source_id;
    return (
      selectableNcms.find((n) => n.ncm_code === selectedNcm)
        ?.source_id ?? "mdic-comex-stat"
    );
  }, [
    view,
    indicator,
    metalCards,
    selectedMetals,
    selectedIppEntry,
    selectableNcms,
    selectedNcm,
  ]);

  const attribution = useMemo(() => {
    const source = sources.find((s) => s.source_id === activeSourceId);
    return source
      ? `${source.attribution} · ${source.license_reference}`
      : null;
  }, [sources, activeSourceId]);

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
        actions={
          <SuppliesActionButton
            type="button"
            variant="ghost"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />{" "}
            {MARKET_INTELLIGENCE_CONTENT.reloadLabel}
          </SuppliesActionButton>
        }
      >
        <SuppliesSegmentToggle
          ariaLabel={
            MARKET_INTELLIGENCE_CONTENT.perspectives.switcherAriaLabel
          }
          idPrefix="market-intelligence-view"
          size="sm"
          value={view}
          options={PERSPECTIVE_OPTIONS}
          onChange={(value) => filters.setView(value as MarketPerspective)}
        />
      </SuppliesPageHero>

      {catalogError ? (
        <SuppliesStateBanner variant="error">{catalogError}</SuppliesStateBanner>
      ) : null}
      {!catalogLoading &&
      !catalogError &&
      metalCards.length === 0 &&
      selectableIpp.length === 0 &&
      selectableNcms.length === 0 &&
      !fxInstrument ? (
        <SuppliesStateBanner variant="error">
          {MARKET_INTELLIGENCE_CONTENT.states.noSelectableInstruments}
        </SuppliesStateBanner>
      ) : null}

      {view === "metals" ? (
        <section
          className="sp-market-instruments"
          aria-label={MARKET_INTELLIGENCE_CONTENT.metals.cardsLabel}
        >
          <div
            className="sp-market-instruments-grid"
            role="group"
            aria-label={MARKET_INTELLIGENCE_CONTENT.metals.cardsLabel}
          >
            {metalCards.map((entry) => (
              <MarketInstrumentCard
                key={entry.code}
                code={entry.code}
                label={entry.label}
                unit={entry.unit}
                context={
                  [
                    MARKET_INTELLIGENCE_CONTENT.quoteBasis[
                      entry.quote_basis ?? ""
                    ] ?? entry.quote_basis,
                    entry.latest_observation_date
                      ? MARKET_INTELLIGENCE_CONTENT.metals.latestRefLabel(
                          entry.latest_observation_date,
                        )
                      : null,
                  ]
                    .filter(Boolean)
                    .join(" · ") || null
                }
                selected={selectedMetals.includes(entry.code)}
                selectable={entry.selectable_in_ui === true}
                dataAccessAllowed={
                  entry.data_access_allowed === true
                }
                pendingLabel={
                  MARKET_INTELLIGENCE_CONTENT.metals.pendingLabel
                }
                selectedLabel={
                  MARKET_INTELLIGENCE_CONTENT.metals.selectedLabel
                }
                onToggle={filters.toggleMetal}
              />
            ))}
          </div>
        </section>
      ) : null}

      <FiltersRow variant="extended">
        {view === "indicators" ? (
          <SuppliesSegmentToggle
            ariaLabel={
              MARKET_INTELLIGENCE_CONTENT.filters.indicatorLabel
            }
            idPrefix="market-intelligence-indicator"
            size="sm"
            widthMode="content"
            value={indicator}
            options={INDICATOR_OPTIONS}
            onChange={(value) =>
              filters.setIndicator(value as MarketIndicatorKind)
            }
          />
        ) : null}
        {view === "indicators" && indicator === "ipp" ? (
          <SuppliesSelectField
            label={MARKET_INTELLIGENCE_CONTENT.filters.seriesLabel}
            hint={SP_HELP.marketIntelligenceIpp}
            value={selectedIpp}
            options={ippOptions}
            onChange={filters.setIppSeries}
          />
        ) : null}
        {view === "indicators" &&
        indicator === "comex" &&
        ncmOptions.length > 0 ? (
          <SuppliesSelectField
            label={MARKET_INTELLIGENCE_CONTENT.filters.ncmLabel}
            hint={
              MARKET_INTELLIGENCE_CONTENT.modules.importsNcmHint
            }
            value={selectedNcm}
            options={ncmOptions}
            onChange={filters.setNcm}
          />
        ) : null}
        {view === "fx" ? (
          <SuppliesSelectField
            label={MARKET_INTELLIGENCE_CONTENT.filters.fxKindLabel}
            hint={SP_HELP.marketIntelligenceFxKind}
            value={filters.state.fxKind}
            options={FX_KIND_OPTIONS}
            onChange={(value) =>
              filters.setFxKind(value as MarketFxKind)
            }
          />
        ) : null}
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

      {view === "metals" ? (
        <MarketMetalsPanel
          title={MARKET_INTELLIGENCE_CONTENT.metals.sectionTitle}
          hint={MARKET_INTELLIGENCE_CONTENT.metals.sectionHint}
          sectionIcon={
            <Boxes size={18} strokeWidth={1.75} aria-hidden="true" />
          }
          enabled={!catalogError && !catalogLoading}
          configured={metalCards.length > 0}
          configState={{
            title:
              MARKET_INTELLIGENCE_CONTENT.states.comexConfigPendingTitle,
            message:
              MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable,
          }}
          selection={selectedMetals}
          from={filters.state.from}
          to={filters.state.to}
          granularity={filters.state.granularity}
          mode={filters.state.mode}
          onModeChange={filters.setMode}
          tableAriaLabel={
            MARKET_INTELLIGENCE_CONTENT.metals.sectionTitle
          }
          storageKey="supplies:market-intelligence:metals"
          exportTitle={
            MARKET_INTELLIGENCE_CONTENT.metals.sectionTitle
          }
          attribution={attribution}
          reloadKey={reloadKey}
        />
      ) : null}

      {view === "indicators" && indicator === "ipp" ? (
        <MarketIntelligencePanel<MarketProducerPricePoint>
          title={MARKET_INTELLIGENCE_CONTENT.modules.ippTitle}
          hint={SP_HELP.marketIntelligenceIpp}
          sectionIcon={
            <Factory size={18} strokeWidth={1.75} aria-hidden="true" />
          }
          granularityLabel={
            GRANULARITY_LABELS[filters.state.granularity]
          }
          unitDetail={
            selectedIppEntry?.base_reference
              ? `base ${selectedIppEntry.base_reference}`
              : undefined
          }
          enabled={!catalogError && !catalogLoading}
          configured={selectableIpp.length > 0}
          configState={{
            title:
              MARKET_INTELLIGENCE_CONTENT.states.comexConfigPendingTitle,
            message:
              MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable,
          }}
          selection={selectedIpp}
          from={filters.state.from}
          to={filters.state.to}
          granularity={filters.state.granularity}
          mode={filters.state.mode}
          onModeChange={filters.setMode}
          fetchSeries={async ({
            selection,
            granularity,
            date_from,
            date_to,
            signal,
          }) => {
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
              points: payload.points,
              summary: payload.summary ?? null,
              meta: payload.meta,
            };
          }}
          columns={[
            {
              key: "period",
              header:
                MARKET_INTELLIGENCE_CONTENT.modules.ippPeriodColumn,
              render: (row) => formatMarketDate(row.period),
            },
            {
              key: "value",
              header: MARKET_INTELLIGENCE_CONTENT.modules.ippValueColumn,
              render: (row) => formatMarketDecimal(row.value),
              align: "right",
            },
            {
              key: "coverage",
              header: MARKET_INTELLIGENCE_CONTENT.table.coverageColumn,
              render: (row) => marketCoverageLabel(row.coverage),
            },
          ]}
          kpiLayout={
            selectedIppEntry?.metric_kind === "ipp_index"
              ? "index"
              : "percent"
          }
          unitLabel={formatMarketUnit(selectedIppEntry?.unit ?? "")}
          valueLegend={selectedIppEntry?.label ?? "IPP"}
          tableAriaLabel={
            MARKET_INTELLIGENCE_CONTENT.modules.ippTitle
          }
          storageKey="supplies:market-intelligence:ipp"
          exportTitle={MARKET_INTELLIGENCE_CONTENT.modules.ippTitle}
          attribution={attribution}
          reloadKey={reloadKey}
        />
      ) : null}

      {view === "indicators" && indicator === "comex" ? (
        <MarketIntelligencePanel<
          MarketImportPoint & { value: string | null }
        >
          title={MARKET_INTELLIGENCE_CONTENT.modules.importsTitle}
          hint={SP_HELP.marketIntelligenceImports}
          sectionIcon={
            <Ship size={18} strokeWidth={1.75} aria-hidden="true" />
          }
          granularityLabel={
            GRANULARITY_LABELS[filters.state.granularity]
          }
          enabled={!catalogError && !catalogLoading}
          configured={selectableNcms.length > 0}
          configState={{
            title:
              MARKET_INTELLIGENCE_CONTENT.states.comexConfigPendingTitle,
            message:
              MARKET_INTELLIGENCE_CONTENT.states.comexConfigPending,
            nextSteps:
              MARKET_INTELLIGENCE_CONTENT.states.comexNextSteps,
            preview: [
              {
                title:
                  MARKET_INTELLIGENCE_CONTENT.kpis.latestUnitValueTitle,
                hint: MARKET_INTELLIGENCE_CONTENT.kpis
                  .latestUnitValueHint,
              },
              {
                title: MARKET_INTELLIGENCE_CONTENT.kpis.fobTotalTitle,
                hint: MARKET_INTELLIGENCE_CONTENT.kpis.fobTotalHint,
              },
              {
                title:
                  MARKET_INTELLIGENCE_CONTENT.kpis.weightTotalTitle,
                hint: MARKET_INTELLIGENCE_CONTENT.kpis
                  .weightTotalHint,
              },
            ],
          }}
          selection={selectedNcm}
          from={filters.state.from}
          to={filters.state.to}
          granularity={filters.state.granularity}
          mode={filters.state.mode}
          onModeChange={filters.setMode}
          fetchSeries={async ({
            selection,
            granularity,
            date_from,
            date_to,
            signal,
          }) => {
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
              points: payload.points.map((point) => ({
                ...point,
                value: point.unit_value_usd_per_t,
              })),
              summary: payload.summary ?? null,
              meta: payload.meta,
            };
          }}
          columns={[
            {
              key: "period",
              header:
                MARKET_INTELLIGENCE_CONTENT.modules.importsPeriodColumn,
              render: (row) => formatMarketDate(row.period),
            },
            {
              key: "fob",
              header: MARKET_INTELLIGENCE_CONTENT.modules.importsFobColumn,
              render: (row) => formatMarketDecimal(row.fob_usd_total),
              align: "right",
            },
            {
              key: "weight",
              header:
                MARKET_INTELLIGENCE_CONTENT.modules.importsWeightColumn,
              render: (row) => formatMarketDecimal(row.net_weight_t),
              align: "right",
            },
            {
              key: "unit",
              header: MARKET_INTELLIGENCE_CONTENT.modules.importsUnitColumn,
              render: (row) => formatMarketDecimal(row.unit_value_usd_per_t),
              align: "right",
            },
            {
              key: "coverage",
              header: MARKET_INTELLIGENCE_CONTENT.table.coverageColumn,
              render: (row) => marketCoverageLabel(row.coverage),
            },
          ]}
          kpiLayout="import"
          unitLabel={formatMarketUnit(
            selectableNcms.find(
              (entry) => entry.ncm_code === selectedNcm,
            )?.unit ?? "US$/t",
          )}
          valueLegend={
            MARKET_INTELLIGENCE_CONTENT.modules.importsUnitColumn
          }
          tableAriaLabel={
            MARKET_INTELLIGENCE_CONTENT.modules.importsTitle
          }
          storageKey="supplies:market-intelligence:imports"
          exportTitle={MARKET_INTELLIGENCE_CONTENT.modules.importsTitle}
          attribution={attribution}
          reloadKey={reloadKey}
        />
      ) : null}

      {view === "fx" ? (
        <MarketIntelligencePanel<MarketSeriesPoint>
          title={MARKET_INTELLIGENCE_CONTENT.modules.fxTitle}
          hint={SP_HELP.marketIntelligenceFx}
          sectionIcon={
            <ArrowLeftRight
              size={18}
              strokeWidth={1.75}
              aria-hidden="true"
            />
          }
          granularityLabel={
            GRANULARITY_LABELS[filters.state.granularity]
          }
          enabled={!catalogError && !catalogLoading}
          configured={Boolean(fxInstrument)}
          configState={{
            title:
              MARKET_INTELLIGENCE_CONTENT.states.comexConfigPendingTitle,
            message:
              MARKET_INTELLIGENCE_CONTENT.states.moduleUnavailable,
          }}
          selection={filters.state.fxKind}
          from={filters.state.from}
          to={filters.state.to}
          granularity={filters.state.granularity}
          mode={filters.state.mode}
          onModeChange={filters.setMode}
          fetchSeries={async ({
            selection,
            granularity,
            date_from,
            date_to,
            signal,
          }) => {
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
              points: payload.points,
              summary: payload.summary ?? null,
              meta: payload.meta,
            };
          }}
          columns={[
            {
              key: "period",
              header:
                MARKET_INTELLIGENCE_CONTENT.modules.fxPeriodColumn,
              render: (row) => formatMarketDate(row.period),
            },
            {
              key: "value",
              header: MARKET_INTELLIGENCE_CONTENT.modules.fxValueColumn,
              render: (row) => formatMarketDecimal(row.value),
              align: "right",
            },
            {
              key: "coverage",
              header: MARKET_INTELLIGENCE_CONTENT.table.coverageColumn,
              render: (row) => marketCoverageLabel(row.coverage),
            },
          ]}
          kpiLayout="fx"
          unitLabel={formatMarketUnit(fxInstrument?.unit ?? "R$/US$")}
          valueLegend={MARKET_INTELLIGENCE_CONTENT.modules.fxValueColumn}
          tableAriaLabel={MARKET_INTELLIGENCE_CONTENT.modules.fxTitle}
          storageKey="supplies:market-intelligence:fx"
          exportTitle={MARKET_INTELLIGENCE_CONTENT.modules.fxTitle}
          attribution={attribution}
          reloadKey={reloadKey}
        />
      ) : null}
    </div>
  );
}
