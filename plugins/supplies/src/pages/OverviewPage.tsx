import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  AlertTriangle,
  BarChart3,
  Boxes,
  Package,
  Percent,
  RefreshCw,
  ShoppingCart,
  Timer,
  Wallet,
} from "lucide-react";

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
  SuppliesSectionHintLabel,
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
} from "../features/overview/overviewContent";
import { buildOverviewKpiPresentation } from "../features/overview/overviewKpiPresentation";
import { resolvePeriodKindChip } from "../features/overview/periodPreset";
import { useOverviewFilters } from "../features/overview/useOverviewFilters";

type OverviewPageProps = {
  basePath: string;
};

const KPI_ICONS: Record<string, ReactNode> = {
  "KPI-OTD": <Timer size={22} strokeWidth={1.75} aria-hidden="true" />,
  "KPI-STOCK-VALUE": <Boxes size={22} strokeWidth={1.75} aria-hidden="true" />,
  "KPI-TURNOVER": <Package size={22} strokeWidth={1.75} aria-hidden="true" />,
  "KPI-CPV": <Percent size={22} strokeWidth={1.75} aria-hidden="true" />,
  "KPI-SAVINGS": <Wallet size={22} strokeWidth={1.75} aria-hidden="true" />,
  "KPI-SC-OPEN": <ShoppingCart size={22} strokeWidth={1.75} aria-hidden="true" />,
  "KPI-CRITICAL-MP": <AlertTriangle size={22} strokeWidth={1.75} aria-hidden="true" />,
};

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
  const periodKindBadge = resolvePeriodKindChip(filters.period);
  const kpiGoalContext = useMemo(
    () => ({
      from: filters.from,
      to: filters.to,
      scopeLabel: filters.scopeBadge,
      branch: filters.apiParams.branch,
      consolidated: !filters.apiParams.branch,
    }),
    [filters.apiParams.branch, filters.from, filters.scopeBadge, filters.to],
  );

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
          <SuppliesSectionHintLabel
            label={OVERVIEW_CONTENT.title}
            hint={SP_HELP.overviewTemporal}
          />
        }
        description={OVERVIEW_CONTENT.description}
        badge={<SuppliesStatusBadge label={scopeBadge} variant="info" />}
        actions={
          <SuppliesActionButton
            type="button"
            variant="ghost"
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

      {error ? <SuppliesStateBanner variant="error">{error}</SuppliesStateBanner> : null}
      {!loading && !error && hasPartial ? (
        <SuppliesStateBanner>{OVERVIEW_CONTENT.partialNote}</SuppliesStateBanner>
      ) : null}

      <SuppliesSectionCard
        title={OVERVIEW_CONTENT.indicatorsTitle}
        hint={OVERVIEW_CONTENT.indicatorsHint}
      >
        {loading ? (
          <SuppliesLoadingCard title={OVERVIEW_CONTENT.loadingKpisTitle} variant="panel" />
        ) : null}
        {!loading && !error && availableCount === 0 ? (
          <SuppliesEmptyState
            title={OVERVIEW_CONTENT.empty}
            message={OVERVIEW_CONTENT.description}
          />
        ) : null}
        {!loading && !error && kpis.length > 0 ? (
          <ul className="sp-overview__grid sp-overview-kpi-grid" aria-label="KPIs da visão geral">
            {kpis.map((kpi) => (
              <li key={kpi.id}>
                <OverviewKpiItem
                  kpi={kpi}
                  periodKindBadge={periodKindBadge}
                  goalContext={kpiGoalContext}
                />
              </li>
            ))}
          </ul>
        ) : null}
      </SuppliesSectionCard>

      <div className="sp-gestao-charts-grid">
        <SuppliesSectionCard
          title={OVERVIEW_CONTENT.otdChartTitle}
          hint={OVERVIEW_CONTENT.otdChartHint}
          actions={
            <SuppliesActionButton
              type="button"
              variant="ghost"
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
    </div>
  );
}

function OverviewKpiItem({
  kpi,
  periodKindBadge,
  goalContext,
}: {
  kpi: OverviewKpiCard;
  periodKindBadge: "MTD" | "YTD" | null;
  goalContext: {
    from: string;
    to: string;
    scopeLabel: string;
    branch?: string;
    consolidated: boolean;
  };
}) {
  const unavailable = kpi.status === "unavailable";
  const presentation = buildOverviewKpiPresentation(kpi, goalContext);
  const showPeriodBadge =
    kpi.temporalNature === "interval" ? periodKindBadge ?? undefined : undefined;
  const performance = presentation.goalPerformanceBadge;

  return (
    <SuppliesKpiCard
      title={kpi.title}
      titleHint={kpi.description}
      value={unavailable ? OVERVIEW_CONTENT.unavailable : kpi.displayValue ?? "—"}
      contextLabel={
        unavailable ? OVERVIEW_CONTENT.partialNote : presentation.contextLabel
      }
      goalPrefix={presentation.goalPrefix}
      goalLabel={presentation.goalLabel}
      goalHint={presentation.goalHint}
      monthlyGoalLabel={presentation.monthlyGoalLabel}
      monthlyGoalPrefix={presentation.monthlyGoalPrefix}
      monthlyGoalHint={presentation.monthlyGoalHint}
      periodKindBadge={showPeriodBadge}
      goalScopeBadge={presentation.goalScopeBadge}
      goalScopeHint={presentation.goalScopeHint}
      goalPerformanceBadge={performance}
      iddScoreLabel={presentation.iddScoreLabel}
      icon={KPI_ICONS[kpi.id] ?? <BarChart3 size={22} strokeWidth={1.75} aria-hidden="true" />}
      className={unavailable ? "sp-overview__kpi--unavailable" : undefined}
    />
  );
}
