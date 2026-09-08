import { useEffect, useMemo, useState } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";
import { BarChart3, RefreshCw } from "lucide-react";

import { getOverview, type OverviewKpiCard, type OverviewResponse } from "../api/overview";
import { navigatePluginView } from "../app/pluginNavigation";
import { buildPluginPath } from "../app/pluginRoutes";
import { useSuppliesSession } from "../app/SuppliesSessionContext";
import { SuppliesKpiCard } from "../app/suppliesKpiCard";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesPageHero,
  SuppliesPagePath,
  SuppliesSectionCard,
  SuppliesStateBanner,
  SuppliesStatusBadge,
} from "../app/suppliesUi";
import { SP_HELP } from "../content/helpTooltips";
import { OverviewCompareChart } from "../features/overview/OverviewCompareChart";
import { OverviewFilters } from "../features/overview/OverviewFilters";
import { OverviewOtdSeriesChart } from "../features/overview/OverviewOtdSeriesChart";
import {
  mapOverviewFetchError,
  OVERVIEW_CONTENT,
  temporalNatureLabel,
} from "../features/overview/overviewContent";
import { useOverviewFilters } from "../features/overview/useOverviewFilters";

type OverviewPageProps = {
  basePath: string;
};

function formatMeta(meta: number | null, unit: string | null): string | null {
  if (meta == null) return null;
  if (unit === "%") return `${meta.toFixed(1)}%`;
  if (unit === "R$") {
    return `R$ ${meta.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return String(meta);
}

export function OverviewPage({ basePath }: OverviewPageProps) {
  const session = useSuppliesSession();
  const units = session.allowedUnits;
  const filters = useOverviewFilters(units);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    getOverview(filters.apiParams, controller.signal)
      .then((payload) => setData(payload))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        const message = err instanceof Error ? err.message : OVERVIEW_CONTENT.error;
        setError(mapOverviewFetchError(message));
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [filters.apiParams, reloadKey]);

  const kpis = data?.kpis ?? [];
  const availableCount = useMemo(
    () => kpis.filter((kpi) => kpi.status === "available").length,
    [kpis],
  );
  const hasPartial = (data?.partialFailures.length ?? 0) > 0;

  const homeHref = buildPluginPath("home", basePath);
  const scopeBadge = filters.scopeBadge;

  return (
    <div className="sp-page-stack sp-overview">
      <SuppliesPagePath
        back={{
          label: "Início",
          href: homeHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigatePluginView("home", { basePath });
          },
        }}
        items={[]}
        current={OVERVIEW_CONTENT.title}
      />

      <SuppliesPageHero
        eyebrow={OVERVIEW_CONTENT.eyebrow}
        title={
          <>
            {OVERVIEW_CONTENT.title}{" "}
            <HelpTooltip
              content={SP_HELP.overviewTemporal}
              ariaLabel={OVERVIEW_CONTENT.helpAriaLabel}
            />
          </>
        }
        description={OVERVIEW_CONTENT.description}
        badge={<SuppliesStatusBadge label={scopeBadge} variant="info" />}
        actions={
          <SuppliesActionButton
            type="button"
            variant="default"
            onClick={() => setReloadKey((value) => value + 1)}
          >
            <RefreshCw size={16} strokeWidth={1.75} aria-hidden="true" />{" "}
            {OVERVIEW_CONTENT.reloadLabel}
          </SuppliesActionButton>
        }
        aria-label={OVERVIEW_CONTENT.filtersAriaLabel}
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

      {loading ? (
        <SuppliesLoadingCard title={OVERVIEW_CONTENT.loadingKpisTitle} variant="panel" />
      ) : null}
      {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
      {!loading && !error && hasPartial ? (
        <SuppliesStateBanner>{OVERVIEW_CONTENT.partialNote}</SuppliesStateBanner>
      ) : null}

      {!loading && !error && availableCount === 0 ? (
        <SuppliesEmptyState
          title={OVERVIEW_CONTENT.empty}
          message={OVERVIEW_CONTENT.description}
        />
      ) : null}

      {!loading && !error && kpis.length > 0 ? (
        <SuppliesSectionCard
          title={OVERVIEW_CONTENT.indicatorsTitle}
          hint={OVERVIEW_CONTENT.indicatorsHint}
        >
          <ul className="sp-overview__grid">
            {kpis.map((kpi) => (
              <li key={kpi.id}>
                <OverviewKpiItem kpi={kpi} />
              </li>
            ))}
          </ul>
        </SuppliesSectionCard>
      ) : null}

      <SuppliesSectionCard
        title={OVERVIEW_CONTENT.otdChartTitle}
        hint={OVERVIEW_CONTENT.otdChartHint}
        actions={
          <SuppliesActionButton
            type="button"
            variant="default"
            onClick={() =>
              navigatePluginView("analytics_otd", {
                basePath,
                search: typeof window !== "undefined" ? window.location.search : undefined,
              })
            }
          >
            {OVERVIEW_CONTENT.openOtdLabel}
          </SuppliesActionButton>
        }
      >
        <OverviewOtdSeriesChart filters={filters.apiParams} />
      </SuppliesSectionCard>

      {!loading && !error ? (
        <SuppliesSectionCard
          title={OVERVIEW_CONTENT.compareTitle}
          hint={OVERVIEW_CONTENT.compareHint}
        >
          <OverviewCompareChart kpis={kpis} />
        </SuppliesSectionCard>
      ) : null}
    </div>
  );
}

function OverviewKpiItem({ kpi }: { kpi: OverviewKpiCard }) {
  const unavailable = kpi.status === "unavailable";
  const nature = temporalNatureLabel(kpi.temporalNature);
  return (
    <SuppliesKpiCard
      title={kpi.title}
      titleHint={kpi.description}
      value={unavailable ? OVERVIEW_CONTENT.unavailable : kpi.displayValue ?? "—"}
      contextLabel={`${nature} · ${kpi.periodLabel}`}
      goalLabel={formatMeta(kpi.meta, kpi.unit)}
      subtitle={unavailable ? OVERVIEW_CONTENT.partialNote : undefined}
      icon={<BarChart3 size={18} strokeWidth={1.75} aria-hidden="true" />}
      className={unavailable ? "sp-overview__kpi--unavailable" : undefined}
    />
  );
}
