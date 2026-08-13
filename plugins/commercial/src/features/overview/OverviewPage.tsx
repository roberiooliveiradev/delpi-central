import { EmptyState, SectionCard, formatOperationalUnitCode } from "@delpi/plugin-ui/index";
import {
  Banknote,
  Building2,
  ClipboardList,
  PackageCheck,
  Percent,
  RefreshCw,
  Sparkles,
} from "lucide-react";
import { useMemo } from "react";

import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialDashboardKpiCard,
  CommercialLoadingCard,
  CommercialPageHero,
  CommercialSectionHintLabel,
} from "../../app/commercialUi";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { CM_HELP } from "../../content/helpTooltips";
import { OVERVIEW_METRIC_BY_ID } from "../../content/overviewMetricsCatalog";
import { formatCurrency } from "../../utils/format";
import { AnalyticsFilters } from "../analytics/components/AnalyticsFilters";
import { AnalyticsFunnelChart } from "../analytics/components/AnalyticsFunnelChart";
import { AnalyticsRolSeriesChart } from "../analytics/components/AnalyticsRolSeriesChart";
import { useAnalyticsDashboard } from "../analytics/hooks/useAnalyticsDashboard";
import { useAnalyticsFilters } from "../analytics/hooks/useAnalyticsFilters";
import { DepartmentIddBadge } from "./DepartmentIddBadge";
import {
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
} from "./goalDisplay";
import { buildRolPerUnitKpiView } from "./rolPerUnitPresentation";

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

export function OverviewPage({ basePath: _basePath }: OverviewPageProps) {
  const filters = useAnalyticsFilters();
  const dashboard = useAnalyticsDashboard(filters.apiParams);
  const copy = ANALYTICS_CONTENT.overview;
  const activeBranch = filters.apiParams.branch;
  const periodLabel = formatPeriodLabel(filters.dateStart, filters.dateEnd);
  const branchLabel = activeBranch
    ? formatOperationalUnitCode(activeBranch, activeBranch)
    : "Consolidado (todas as unidades)";
  const contextBase = `${branchLabel} · ${periodLabel}`;

  const rolKpi = useMemo(
    () =>
      buildRolPerUnitKpiView(
        dashboard.headOfficeRol,
        dashboard.branchRol,
        contextBase,
        formatCurrency,
        activeBranch,
      ),
    [activeBranch, contextBase, dashboard.branchRol, dashboard.headOfficeRol],
  );

  const wegRolKpi = useMemo(
    () =>
      buildRolPerUnitKpiView(
        dashboard.headOfficeWegRol,
        dashboard.branchWegRol,
        `${contextBase} · WEG`,
        formatCurrency,
        activeBranch,
      ),
    [
      activeBranch,
      contextBase,
      dashboard.branchWegRol,
      dashboard.headOfficeWegRol,
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
      ),
    [
      activeBranch,
      contextBase,
      dashboard.branchNewBusinessRol,
      dashboard.headOfficeNewBusinessRol,
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
              contextLabel={rolKpi.contextLabel}
              goalLabel={rolKpi.goalLabel}
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
              contextLabel={wegRolKpi.contextLabel}
              goalLabel={wegRolKpi.goalLabel}
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
              contextLabel={segmentNewBusinessRolKpi.contextLabel}
              goalLabel={segmentNewBusinessRolKpi.goalLabel}
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
                },
              )}
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
                  : `${formatInteger(dashboard.openPortfolio?.openLineCount)} linhas · Em aberto (agora)`
              }
              icon={<ClipboardList size={22} aria-hidden="true" />}
              loading={dashboard.openPortfolioLoading}
            />
            <CommercialDashboardKpiCard
              title={OVERVIEW_METRIC_BY_ID.closing_rate.label}
              titleHint={OVERVIEW_METRIC_BY_ID.closing_rate.tooltip}
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
                },
              )}
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
                },
              )}
              icon={<Sparkles size={22} aria-hidden="true" />}
              loading={dashboard.loading}
            />
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
    </section>
  );
}
