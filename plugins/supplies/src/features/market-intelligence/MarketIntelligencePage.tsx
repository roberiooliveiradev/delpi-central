/** Market intelligence page — three exclusive source perspectives
 * (PROC-0076 R3).
 *
 * Composition only: perspective switcher → contextual filters → one
 * analysis panel. All metrics, conversions, coverage and availability
 * semantics come from the supplies-api BFF.
 */

import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

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
  SuppliesStatusBadge,
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
import { MarketIntelligencePanel } from "./MarketIntelligencePanel";
import type { MarketPerspective } from "./marketIntelligenceUrl";
import { useMarketIntelligenceFilters } from "./useMarketIntelligenceFilters";

type MarketIntelligencePageProps = {
  basePath: string;
};

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

const PERSPECTIVE_OPTIONS: { value: MarketPerspective; label: string }[] = [
  {
    value: "ipp",
    label: MARKET_INTELLIGENCE_CONTENT.perspectives.ipp,
  },
  {
    value: "comex",
    label: MARKET_INTELLIGENCE_CONTENT.perspectives.comex,
  },
  {
    value: "fx",
    label: MARKET_INTELLIGENCE_CONTENT.perspectives.fx,
  },
];

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

  /** Default perspective is data-driven — the first source with
   * selectable, actually-observed data wins (never a hardcoded
   * assumption that IBGE is always up). */
  const defaultView = useMemo<MarketPerspective>(() => {
    const hasObservations = (
      list?: { selectable?: boolean; latest_observation_date: string | null }[],
    ) =>
      (list ?? []).some(
        (entry) =>
          entry.selectable === true && entry.latest_observation_date,
      );
    if (hasObservations(ippSeriesOptions)) return "ipp";
    if (hasObservations(importNcms)) return "comex";
    if (fxInstrument?.latest_observation_date) return "fx";
    return "ipp";
  }, [ippSeriesOptions, importNcms, fxInstrument]);

  const filters = useMarketIntelligenceFilters(defaultView);
  const view = filters.state.view;

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

  const granularityOptions = useMemo(() => {
    const allowed: MarketGranularity[] =
      view === "fx" ? ["day", "month", "year"] : ["month", "year"];
    return allowed.map((value) => ({
      value,
      label: GRANULARITY_LABELS[value],
    }));
  }, [view]);

  /** Attribution/license of the active perspective's source. */
  const attribution = useMemo(() => {
    const sourceId =
      view === "ipp"
        ? selectedIppEntry?.source_id
        : view === "comex"
          ? selectableNcms.find((n) => n.ncm_code === selectedNcm)
              ?.source_id ?? "mdic-comex-stat"
          : "bcb-ptax";
    const source = sources.find((s) => s.source_id === sourceId);
    return source
      ? `${source.attribution} · ${source.license_reference}`
      : null;
  }, [view, sources, selectedIppEntry, selectableNcms, selectedNcm]);

  const activeSourceId =
    view === "ipp"
      ? selectedIppEntry?.source_id
      : view === "comex"
        ? "mdic-comex-stat"
        : "bcb-ptax";

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
          activeSourceId ? (
            <SuppliesStatusBadge
              label={`${MARKET_INTELLIGENCE_CONTENT.states.sourceLabel}: ${activeSourceId}`}
              variant="info"
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
          {view === "ipp" ? (
            <SuppliesSelectField
              label={MARKET_INTELLIGENCE_CONTENT.filters.seriesLabel}
              hint={SP_HELP.marketIntelligenceIpp}
              value={selectedIpp}
              options={ippOptions}
              onChange={filters.setIppSeries}
            />
          ) : null}
          {view === "comex" && ncmOptions.length > 0 ? (
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
      </SuppliesPageHero>

      {catalogError ? (
        <SuppliesStateBanner variant="error">{catalogError}</SuppliesStateBanner>
      ) : null}
      {!catalogLoading &&
      !catalogError &&
      selectableIpp.length === 0 &&
      selectableNcms.length === 0 &&
      !fxInstrument ? (
        <SuppliesStateBanner variant="error">
          {MARKET_INTELLIGENCE_CONTENT.states.noSelectableInstruments}
        </SuppliesStateBanner>
      ) : null}

      {view === "ipp" ? (
        <MarketIntelligencePanel<MarketProducerPricePoint>
          title={MARKET_INTELLIGENCE_CONTENT.modules.ippTitle}
          hint={SP_HELP.marketIntelligenceIpp}
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
          kpiLayout={
            selectedIppEntry?.metric_kind === "ipp_index"
              ? "index"
              : "percent"
          }
          unitLabel={selectedIppEntry?.unit ?? ""}
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

      {view === "comex" ? (
        <MarketIntelligencePanel<
          MarketImportPoint & { value: string | null }
        >
          title={MARKET_INTELLIGENCE_CONTENT.modules.importsTitle}
          hint={SP_HELP.marketIntelligenceImports}
          enabled={!catalogError && !catalogLoading}
          configured={selectableNcms.length > 0}
          configState={{
            title:
              MARKET_INTELLIGENCE_CONTENT.states.comexConfigPendingTitle,
            message:
              MARKET_INTELLIGENCE_CONTENT.states.comexConfigPending,
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
              header:
                MARKET_INTELLIGENCE_CONTENT.modules.importsWeightColumn,
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
          kpiLayout="import"
          unitLabel="US$/t"
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
          kpiLayout="fx"
          unitLabel="R$/US$"
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
