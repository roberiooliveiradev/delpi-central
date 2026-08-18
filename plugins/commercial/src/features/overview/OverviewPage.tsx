import { EmptyState, SectionCard, formatOperationalUnitCode } from "@delpi/plugin-ui/index";
import {
  Banknote,
  Building2,
  ClipboardList,
  PackageCheck,
  Percent,
  RefreshCw,
  Sparkles,
  Target,
} from "lucide-react";
import { useMemo } from "react";

import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialDashboardKpiCard,
  CommercialLoadingCard,
  CommercialMetricCard,
  CommercialPageHero,
  CommercialSectionHintLabel,
} from "../../app/commercialUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import { OVERVIEW_METRIC_BY_ID } from "../../content/overviewMetricsCatalog";
import { appendBillingNatureContext } from "../../content/billingNature";
import { formatCurrency } from "../../utils/format";
import {
  buildOpenOrdersHorizonListHref,
  type OpenOrdersHorizonBucketFocus,
} from "../../utils/openOrdersDeepLink";
import { AnalyticsFilters } from "../analytics/components/AnalyticsFilters";
import { AnalyticsClosingRateSeriesChart } from "../analytics/components/AnalyticsClosingRateSeriesChart";
import { AnalyticsFunnelChart } from "../analytics/components/AnalyticsFunnelChart";
import { AnalyticsRolSeriesChart } from "../analytics/components/AnalyticsRolSeriesChart";
import { useAnalyticsDashboard } from "../analytics/hooks/useAnalyticsDashboard";
import { useAnalyticsFilters } from "../analytics/hooks/useAnalyticsFilters";
import { resolvePeriodKindChip } from "../analytics/utils/periodPreset";
import { DepartmentIddBadge } from "./DepartmentIddBadge";
import { pickPrimaryRolTarget, resolveGapToTarget } from "./gapToTarget";
import {
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
} from "./goalDisplay";
import { buildRolPerUnitKpiView } from "./rolPerUnitPresentation";

const HORIZON_BUCKET_LABELS: Record<string, string> = {
  overdue: "Atrasado",
  current_month: "Este mês",
  next_1_3_months: "1–3 meses",
  later: "Depois",
  undated: "Sem data",
};

function formatInteger(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return value.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
}

function formatPeriodLabel(dateStart: string, dateEnd: string): string {
  const fmt = (iso: string) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(iso)) return iso || "—";
    const [y, m, d] = iso.split("-");
    return `${d}/${m}/${y}`;
  };
  return `${fmt(dateStart)} - ${fmt(dateEnd)}`;
}

type OverviewPageProps = {
  basePath: string;
};

export function OverviewPage({ basePath }: OverviewPageProps) {
  const filters = useAnalyticsFilters();
  const dashboard = useAnalyticsDashboard(filters.apiParams);
  const copy = ANALYTICS_CONTENT.overview;
  const activeBranch = filters.apiParams.branch;
  const periodLabel = formatPeriodLabel(filters.dateStart, filters.dateEnd);
  const branchLabel = activeBranch
    ? formatOperationalUnitCode(activeBranch, activeBranch)
    : "Consolidado (todas as unidades)";
  const contextBase = `${branchLabel} · ${periodLabel}`;
  const periodKindBadge = resolvePeriodKindChip(filters.periodPreset);
  const rolPresentationOptions = useMemo(
    () => ({
      periodKindBadge,
      dateStart: filters.dateStart,
      dateEnd: filters.dateEnd,
    }),
    [filters.dateEnd, filters.dateStart, periodKindBadge],
  );

  const primaryRol = useMemo(
    () =>
      pickPrimaryRolTarget(
        dashboard.headOfficeRol,
        dashboard.branchRol,
        activeBranch,
      ),
    [activeBranch, dashboard.branchRol, dashboard.headOfficeRol],
  );
  const gapToTarget = useMemo(() => resolveGapToTarget(primaryRol), [primaryRol]);
  const currentMonthOpen = useMemo(() => {
    const buckets = dashboard.openPortfolioHorizon?.buckets ?? [];
    return buckets.find((b) => b.id === "current_month")?.openValue ?? null;
  }, [dashboard.openPortfolioHorizon]);

  const openHorizonBucket = (bucket: OpenOrdersHorizonBucketFocus) => {
    navigatePluginPath(
      buildOpenOrdersHorizonListHref({
        bucket,
        asOfIso: dashboard.openPortfolioHorizon?.asOf,
        sellerId: filters.apiParams.seller_id,
        basePath,
      }),
    );
  };

  const rolKpi = useMemo(
    () =>
      buildRolPerUnitKpiView(
        dashboard.headOfficeRol,
        dashboard.branchRol,
        contextBase,
        formatCurrency,
        activeBranch,
        rolPresentationOptions,
      ),
    [
      activeBranch,
      contextBase,
      dashboard.branchRol,
      dashboard.headOfficeRol,
      rolPresentationOptions,
    ],
  );

  const wegRolKpi = useMemo(
    () =>
      buildRolPerUnitKpiView(
        dashboard.headOfficeWegRol,
        dashboard.branchWegRol,
        `${contextBase} · WEG`,
        formatCurrency,
        activeBranch,
        rolPresentationOptions,
      ),
    [
      activeBranch,
      contextBase,
      dashboard.branchWegRol,
      dashboard.headOfficeWegRol,
      rolPresentationOptions,
    ],
  );

  const segmentNewBusinessRolKpi = useMemo(
    () =>
      buildRolPerUnitKpiView(
        dashboard.headOfficeNewBusinessRol,
        dashboard.branchNewBusinessRol,
        `${contextBase} · Novos negócios`,
        formatCurrency,
        activeBranch,
        rolPresentationOptions,
      ),
    [
      activeBranch,
      contextBase,
      dashboard.branchNewBusinessRol,
      dashboard.headOfficeNewBusinessRol,
      rolPresentationOptions,
    ],
  );

  return (
    <section className="cm-page-stack">
      <CommercialPageHero
        aria-label={copy.title}
        eyebrow="Portal Comercial"
        title={
          <CommercialSectionHintLabel label={copy.title} hint={CM_HELP.overview.page} />
        }
        description={copy.subtitle}
        badge={
          <DepartmentIddBadge
            filters={{
              competence: filters.competence,
              dateStart: filters.dateStart,
              dateEnd: filters.dateEnd,
              branches: filters.branches,
            }}
          />
        }
        actions={
          <CommercialActionButton variant="ghost" onClick={dashboard.reload}>
            <RefreshCw size={16} aria-hidden="true" /> Atualizar
          </CommercialActionButton>
        }
      >
        <AnalyticsFilters
          dateStart={filters.dateStart}
          dateEnd={filters.dateEnd}
          competence={filters.competence}
          periodPreset={filters.periodPreset}
          branches={filters.branches}
          customerSegment={filters.customerSegment}
          sellerIds={filters.sellerIds}
          canFilterPortfolios={filters.canFilterPortfolios}
          canUseTeamScope={filters.canUseTeamScope}
          filterablePortfolios={filters.filterablePortfolios}
          onDateStart={filters.setDateStart}
          onDateEnd={filters.setDateEnd}
          onCompetence={filters.setCompetence}
          onPeriodPreset={filters.setPeriodPreset}
          onBranches={filters.setBranches}
          onCustomerSegment={filters.setCustomerSegment}
          onSellerIds={filters.setSellerIds}
        />
      </CommercialPageHero>

      <SectionCard
        title="Indicadores"
        hint={CM_HELP.overview.kpis}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {dashboard.loading ? (
          <CommercialLoadingCard title="Carregando KPIs…" variant="panel" />
        ) : null}
        {dashboard.error ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={dashboard.error} role="alert" />
        ) : null}
        {!dashboard.loading ? (
          <div className="cm-home-kpi-grid cm-overview-kpi-grid" aria-label="KPIs da visão geral">
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.rol.label}
              titleHint={OVERVIEW_METRIC_BY_ID.rol.tooltip}
              value={rolKpi.value}
              valueVariant={rolKpi.valueVariant}
              goalVariant={rolKpi.valueVariant}
              contextLabel={appendBillingNatureContext(rolKpi.contextLabel, "net")}
              goalLabel={rolKpi.goalLabel}
              goalPrefix={rolKpi.goalPrefix}
              goalHint={rolKpi.goalHint}
              monthlyGoalLabel={rolKpi.monthlyGoalLabel}
              monthlyGoalPrefix={rolKpi.monthlyGoalPrefix}
              monthlyGoalHint={rolKpi.monthlyGoalHint}
              periodKindBadge={rolKpi.periodKindBadge}
              goalScopeBadge={rolKpi.goalScopeBadge}
              goalScopeHint={rolKpi.goalScopeHint}
              goalPerformanceBadge={rolKpi.goalPerformanceBadge}
              goalPerformanceBadges={rolKpi.goalPerformanceBadges}
              iddScoreLabel={rolKpi.iddScoreLabel}
              icon={<Banknote size={22} aria-hidden="true" />}
              loading={dashboard.loading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.rol_weg.label}
              titleHint={OVERVIEW_METRIC_BY_ID.rol_weg.tooltip}
              value={wegRolKpi.value}
              valueVariant={wegRolKpi.valueVariant}
              goalVariant={wegRolKpi.valueVariant}
              contextLabel={appendBillingNatureContext(wegRolKpi.contextLabel, "net")}
              goalLabel={wegRolKpi.goalLabel}
              goalPrefix={wegRolKpi.goalPrefix}
              goalHint={wegRolKpi.goalHint}
              monthlyGoalLabel={wegRolKpi.monthlyGoalLabel}
              monthlyGoalPrefix={wegRolKpi.monthlyGoalPrefix}
              monthlyGoalHint={wegRolKpi.monthlyGoalHint}
              periodKindBadge={wegRolKpi.periodKindBadge}
              goalScopeBadge={wegRolKpi.goalScopeBadge}
              goalScopeHint={wegRolKpi.goalScopeHint}
              goalPerformanceBadge={wegRolKpi.goalPerformanceBadge}
              goalPerformanceBadges={wegRolKpi.goalPerformanceBadges}
              iddScoreLabel={wegRolKpi.iddScoreLabel}
              icon={<Building2 size={22} aria-hidden="true" />}
              loading={dashboard.loading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.rol_new_business.label}
              titleHint={OVERVIEW_METRIC_BY_ID.rol_new_business.tooltip}
              value={segmentNewBusinessRolKpi.value}
              valueVariant={segmentNewBusinessRolKpi.valueVariant}
              goalVariant={segmentNewBusinessRolKpi.valueVariant}
              contextLabel={appendBillingNatureContext(segmentNewBusinessRolKpi.contextLabel, "net")}
              goalLabel={segmentNewBusinessRolKpi.goalLabel}
              goalPrefix={segmentNewBusinessRolKpi.goalPrefix}
              goalHint={segmentNewBusinessRolKpi.goalHint}
              monthlyGoalLabel={segmentNewBusinessRolKpi.monthlyGoalLabel}
              monthlyGoalPrefix={segmentNewBusinessRolKpi.monthlyGoalPrefix}
              monthlyGoalHint={segmentNewBusinessRolKpi.monthlyGoalHint}
              periodKindBadge={segmentNewBusinessRolKpi.periodKindBadge}
              goalScopeBadge={segmentNewBusinessRolKpi.goalScopeBadge}
              goalScopeHint={segmentNewBusinessRolKpi.goalScopeHint}
              goalPerformanceBadge={segmentNewBusinessRolKpi.goalPerformanceBadge}
              goalPerformanceBadges={segmentNewBusinessRolKpi.goalPerformanceBadges}
              iddScoreLabel={segmentNewBusinessRolKpi.iddScoreLabel}
              icon={<Sparkles size={22} aria-hidden="true" />}
              loading={dashboard.loading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.otd.label}
              titleHint={OVERVIEW_METRIC_BY_ID.otd.tooltip}
              value={formatDashboardMetricValue(
                dashboard.salesOrderOtd?.sales_order_otd_pct,
                dashboard.salesOrderOtd,
              )}
              {...buildKpiGoalPresentationWithBranchIdd(
                `${formatInteger(dashboard.salesOrderOtd?.on_time_lines)} no prazo / ${formatInteger(dashboard.salesOrderOtd?.total_lines)} linhas · ${contextBase}`,
                dashboard.salesOrderOtd,
                {
                  realizedValue: dashboard.salesOrderOtd?.sales_order_otd_pct,
                  activeBranch,
                  branches: dashboard.salesOrderOtdBranches,
                  dateStart: filters.dateStart,
                  dateEnd: filters.dateEnd,
                },
              )}
              periodKindBadge={periodKindBadge}
              icon={<PackageCheck size={22} aria-hidden="true" />}
              loading={dashboard.loading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.open_portfolio.label}
              titleHint={CM_HELP.overview.openPortfolio}
              value={
                dashboard.openPortfolioError
                  ? "—"
                  : dashboard.openPortfolio
                    ? formatCurrency(dashboard.openPortfolio.openValue)
                    : "—"
              }
              contextLabel={
                dashboard.openPortfolioError
                  ? dashboard.openPortfolioError
                  : appendBillingNatureContext(
                      `${formatInteger(dashboard.openPortfolio?.openLineCount)} linhas · Em aberto (agora) · ≠ PCP`,
                      "open_order_value",
                    )
              }
              icon={<ClipboardList size={22} aria-hidden="true" />}
              loading={dashboard.openPortfolioLoading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.portfolio_billing_share.label}
              titleHint={CM_HELP.overview.portfolioBillingShare}
              value={
                dashboard.portfolioBillingShare?.sharePct == null
                  ? "—"
                  : `${dashboard.portfolioBillingShare.sharePct.toLocaleString("pt-BR", {
                      minimumFractionDigits: 1,
                      maximumFractionDigits: 1,
                    })}%`
              }
              contextLabel={
                dashboard.portfolioBillingShare
                  ? `${formatCurrency(dashboard.portfolioBillingShare.portfolioRol)} / ${formatCurrency(dashboard.portfolioBillingShare.companyRol)} · ${contextBase}`
                  : contextBase
              }
              icon={<Percent size={22} aria-hidden="true" />}
              loading={dashboard.loading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.gap_to_target.label}
              titleHint={OVERVIEW_METRIC_BY_ID.gap_to_target.tooltip}
              value={
                gapToTarget == null
                  ? "—"
                  : formatCurrency(gapToTarget)
              }
              contextLabel={
                gapToTarget == null
                  ? "Sem meta SI no período"
                  : currentMonthOpen != null
                    ? `Este mês em aberto: ${formatCurrency(currentMonthOpen)} (contexto, sem soma)`
                    : "Gap = max(meta − ROL, 0) · ≠ soma com carteira"
              }
              icon={<Target size={22} aria-hidden="true" />}
              loading={dashboard.loading || dashboard.openPortfolioLoading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.closing_rate.label}
              titleHint={CM_HELP.overview.closingRate}
              value={formatDashboardMetricValue(
                dashboard.closingRate?.sales_conversion_rate_pct,
                dashboard.closingRate,
              )}
              {...buildKpiGoalPresentationWithBranchIdd(
                `${formatInteger(dashboard.closingRate?.qtd_won)} ganhas / ${formatInteger(dashboard.closingRate?.qtd_proposals)} propostas · ${contextBase}`,
                dashboard.closingRate,
                {
                  realizedValue: dashboard.closingRate?.sales_conversion_rate_pct,
                  activeBranch,
                  branches: dashboard.closingRateBranches,
                  dateStart: filters.dateStart,
                  dateEnd: filters.dateEnd,
                },
              )}
              periodKindBadge={periodKindBadge}
              icon={<Percent size={22} aria-hidden="true" />}
              loading={dashboard.loading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.new_business_pct.label}
              titleHint={OVERVIEW_METRIC_BY_ID.new_business_pct.tooltip}
              value={formatDashboardMetricValue(
                dashboard.newBusinessRol?.new_business_rol_pct,
                dashboard.newBusinessRol,
              )}
              {...buildKpiGoalPresentationWithBranchIdd(
                `${contextBase} · Novos negócios`,
                dashboard.newBusinessRol,
                {
                  realizedValue: dashboard.newBusinessRol?.new_business_rol_pct,
                  activeBranch,
                  branches: dashboard.newBusinessRolBranches,
                  dateStart: filters.dateStart,
                  dateEnd: filters.dateEnd,
                },
              )}
              periodKindBadge={periodKindBadge}
              icon={<Sparkles size={22} aria-hidden="true" />}
              loading={dashboard.loading}
            />
          </div>
        ) : null}
      </SectionCard>

      <SectionCard
        title={OVERVIEW_METRIC_BY_ID.open_portfolio_horizon.label}
        hint={CM_HELP.overview.openPortfolioHorizon}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {dashboard.openPortfolioLoading ? (
          <CommercialLoadingCard title="Carregando carteira no tempo…" variant="panel" />
        ) : null}
        {dashboard.openPortfolioError ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage={dashboard.openPortfolioError}
            role="alert"
          />
        ) : null}
        {!dashboard.openPortfolioLoading && !dashboard.openPortfolioError ? (
          <div className="cm-home-kpi-grid cm-overview-kpi-grid" aria-label="Carteira no tempo">
            {(dashboard.openPortfolioHorizon?.buckets ?? []).map((bucket) => {
              const clickable =
                bucket.id === "overdue" ||
                bucket.id === "current_month" ||
                bucket.id === "next_1_3_months" ||
                bucket.id === "later";
              return (
                <CommercialMetricCard
                  key={bucket.id}
                  label={HORIZON_BUCKET_LABELS[bucket.id] ?? bucket.id}
                  titleHint={CM_HELP.overview.openPortfolioHorizon}
                  value={formatCurrency(bucket.openValue)}
                  hint={`${formatInteger(bucket.openLineCount)} linhas`}
                  icon={<ClipboardList size={22} aria-hidden="true" />}
                  onClick={
                    clickable
                      ? () => openHorizonBucket(bucket.id as OpenOrdersHorizonBucketFocus)
                      : undefined
                  }
                />
              );
            })}
          </div>
        ) : null}
      </SectionCard>

      <div className="cm-gestao-charts-grid">
        <SectionCard
          title={OVERVIEW_METRIC_BY_ID.rol_series.label}
          hint={CM_HELP.overview.rolSeries}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <AnalyticsRolSeriesChart
            filters={{
              start_date: filters.apiParams.start_date,
              end_date: filters.apiParams.end_date,
              customer_segment: filters.apiParams.customer_segment,
              seller_id: filters.apiParams.seller_id,
              branch: filters.apiParams.branch,
            }}
            onDrillDown={(dateStart, dateEnd) => {
              filters.replaceDateFilters({
                dateStart,
                dateEnd,
                competence: "",
              });
            }}
          />
        </SectionCard>
        <SectionCard
          title={OVERVIEW_METRIC_BY_ID.funnel.label}
          hint={CM_HELP.overview.funnel}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <AnalyticsFunnelChart
            closingRate={dashboard.closingRate}
            loading={dashboard.loading}
          />
        </SectionCard>
      </div>

      <div className="cm-gestao-charts-grid cm-gestao-charts-grid--auto-span">
        <SectionCard
          title={OVERVIEW_METRIC_BY_ID.closing_rate_series.label}
          hint={CM_HELP.overview.closingRateSeries}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <AnalyticsClosingRateSeriesChart
            filters={{
              start_date: filters.apiParams.start_date,
              end_date: filters.apiParams.end_date,
              customer_segment: filters.apiParams.customer_segment,
              seller_id: filters.apiParams.seller_id,
              branch: filters.apiParams.branch,
            }}
            onDrillDown={(dateStart, dateEnd) => {
              filters.replaceDateFilters({
                dateStart,
                dateEnd,
                competence: "",
              });
            }}
          />
        </SectionCard>
      </div>
    </section>
  );
}
