import { useEffect, useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";

import { getOtdAggregate, type OtdAggregateResponse } from "../../api/otd";
import { navigatePluginView } from "../../app/pluginNavigation";
import { buildPluginPath } from "../../app/pluginRoutes";
import { useSuppliesSession } from "../../app/SuppliesSessionContext";
import {
  SuppliesTitleWithHelp,
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesSpeedometerGauge,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../../app/suppliesUi";
import { SP_HELP } from "../../content/helpTooltips";
import { OverviewFilters } from "../overview/OverviewFilters";
import { OverviewOtdSeriesChart } from "../overview/OverviewOtdSeriesChart";
import {
  mapOverviewFetchError,
  OVERVIEW_CONTENT,
} from "../overview/overviewContent";
import { formatOperationalUnitCode } from "../overview/suppliesBranchFilters";
import { useOverviewFilters } from "../overview/useOverviewFilters";
import { OTD_ANALYTICS_CONTENT } from "./otdAnalyticsContent";

type OtdAnalyticsPageProps = {
  basePath: string;
};

export function OtdAnalyticsPage({ basePath }: OtdAnalyticsPageProps) {
  const session = useSuppliesSession();
  const filters = useOverviewFilters(session.allowedUnits);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<OtdAggregateResponse | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getOtdAggregate(filters.apiParams, controller.signal)
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        const message = err instanceof Error ? err.message : OTD_ANALYTICS_CONTENT.error;
        setError(mapOverviewFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters.apiParams, reloadKey]);

  const overviewSearch =
    typeof window !== "undefined" ? window.location.search : undefined;
  const overviewHref = buildPluginPath("overview", basePath, overviewSearch);

  const hasPartial = (data?.partialFailures.length ?? 0) > 0;

  const gaugeUnits = useMemo(() => {
    if (data?.byBranch) {
      const fromPayload = Object.keys(data.byBranch);
      if (fromPayload.length > 0) return fromPayload;
    }
    return filters.effectiveUnits;
  }, [data?.byBranch, filters.effectiveUnits]);

  return (
    <div className="sp-page-stack sp-otd-analytics">
      <SuppliesPagePath
        back={{
          label: OVERVIEW_CONTENT.title,
          href: overviewHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("overview", {
              basePath,
              search: typeof window !== "undefined" ? window.location.search : undefined,
            });
          },
        }}
        items={[]}
        current={OTD_ANALYTICS_CONTENT.title}
      />

      <SuppliesPageHero
        eyebrow={OTD_ANALYTICS_CONTENT.eyebrow}
        title={
          <SuppliesTitleWithHelp
            title={OTD_ANALYTICS_CONTENT.title}
            hint={SP_HELP.otdAnalyticsPage}
          />
        }
        description={OTD_ANALYTICS_CONTENT.description}
        badge={<SuppliesStatusBadge label={filters.scopeBadge} variant="info" />}
        actions={
          <>
            <SuppliesActionButton
              type="button"
              variant="default"
              onClick={() =>
                navigatePluginView("overview", {
                  basePath,
                  search: typeof window !== "undefined" ? window.location.search : undefined,
                })
              }
            >
              {OTD_ANALYTICS_CONTENT.openOverviewLabel}
            </SuppliesActionButton>
            <SuppliesActionButton
              type="button"
              variant="default"
              onClick={() => setReloadKey((value) => value + 1)}
            >
              <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />{" "}
              {OVERVIEW_CONTENT.reloadLabel}
            </SuppliesActionButton>
          </>
        }
      >
        <OverviewFilters
          period={filters.period}
          from={filters.from}
          to={filters.to}
          branches={filters.branches}
          unitOptions={filters.unitOptions}
          onPeriod={filters.setPeriod}
          onFrom={filters.setFrom}
          onTo={filters.setTo}
          onBranches={filters.setBranches}
        />
      </SuppliesPageHero>

      {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
      {!loading && !error && hasPartial ? (
        <SuppliesStateBanner>{OVERVIEW_CONTENT.partialNote}</SuppliesStateBanner>
      ) : null}

      <SuppliesSectionCard
        title={OTD_ANALYTICS_CONTENT.gaugesTitle}
        hint={OTD_ANALYTICS_CONTENT.gaugesHint}
      >
        {loading ? (
          <SuppliesLoadingCard title={OTD_ANALYTICS_CONTENT.gaugesLoading} variant="panel" />
        ) : null}
        {!loading && !error && gaugeUnits.length === 0 ? (
          <SuppliesEmptyState
            title={OTD_ANALYTICS_CONTENT.gaugesEmptyTitle}
            message={OTD_ANALYTICS_CONTENT.gaugesEmptyMessage}
          />
        ) : null}
        {!loading && !error && gaugeUnits.length > 0 ? (
          <div className="sp-otd-analytics__gauges">
            {gaugeUnits.map((unit) => {
              const entry = data?.byBranch?.[unit];
              const label = formatOperationalUnitCode(unit, unit);
              return (
                <div key={unit} className="sp-otd-analytics__gauge-card">
                  <h3 className="sp-otd-analytics__gauge-title">{label}</h3>
                  <p className="sp-otd-analytics__gauge-period">
                    {data?.period?.label ?? `${filters.from} → ${filters.to}`}
                  </p>
                  <SuppliesSpeedometerGauge
                    size={280}
                    value={entry?.otdPct ?? null}
                    goal={entry?.goal ?? data?.goal ?? null}
                    showZonesLegend
                    tip={`${label} · OTD`}
                  />
                  <p className="sp-otd-analytics__gauge-meta">
                    OTD{" "}
                    {entry?.otdPct != null
                      ? `${entry.otdPct.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`
                      : "—"}
                    {" · "}
                    Meta{" "}
                    {(entry?.goal ?? data?.goal) != null
                      ? `${Number(entry?.goal ?? data?.goal).toLocaleString("pt-BR", {
                          maximumFractionDigits: 1,
                        })}%`
                      : "—"}
                  </p>
                </div>
              );
            })}
          </div>
        ) : null}
      </SuppliesSectionCard>

      <SuppliesSectionCard
        title={OVERVIEW_CONTENT.otdChartTitle}
        hint={OVERVIEW_CONTENT.otdChartHint}
      >
        <OverviewOtdSeriesChart
          filters={filters.apiParams}
          storageKey="supplies:analytics-otd:otd-series"
        />
      </SuppliesSectionCard>
    </div>
  );
}
