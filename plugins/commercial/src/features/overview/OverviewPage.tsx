import { EmptyState, SectionCard } from "@delpi/plugin-ui/index";
import { Banknote, PackageCheck, Percent, RefreshCw, Sparkles } from "lucide-react";

import {
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialActionButton,
  CommercialLoadingCard,
  CommercialMetricCard,
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

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

type OverviewPageProps = {
  basePath: string;
};

export function OverviewPage({ basePath: _basePath }: OverviewPageProps) {
  const filters = useAnalyticsFilters();
  const dashboard = useAnalyticsDashboard(filters.apiParams);
  const copy = ANALYTICS_CONTENT.overview;

  return (
    <section className="cm-page-stack">
      <CommercialPageHero
        aria-label={copy.title}
        eyebrow="Portal Comercial"
        title={
          <CommercialSectionHintLabel label={copy.title} hint={CM_HELP.overview.page} />
        }
        description={copy.subtitle}
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
          branches={filters.branches}
          customerSegment={filters.customerSegment}
          sellerId={filters.sellerId}
          canFilterPortfolios={filters.canFilterPortfolios}
          canUseTeamScope={filters.canUseTeamScope}
          filterablePortfolios={filters.filterablePortfolios}
          onDateStart={filters.setDateStart}
          onDateEnd={filters.setDateEnd}
          onCompetence={filters.setCompetence}
          onBranches={filters.setBranches}
          onCustomerSegment={filters.setCustomerSegment}
          onSellerId={filters.setSellerId}
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
            <CommercialMetricCard
              hero
              label={OVERVIEW_METRIC_BY_ID.rol_head_office.label}
              titleHint={OVERVIEW_METRIC_BY_ID.rol_head_office.tooltip}
              value={formatPct(dashboard.headOfficeRol?.rol_target_pct)}
              hint={
                dashboard.headOfficeRol
                  ? `ROL ${formatCurrency(dashboard.headOfficeRol.rol)}`
                  : undefined
              }
              icon={<Banknote size={18} aria-hidden="true" />}
            />
            <CommercialMetricCard
              label={OVERVIEW_METRIC_BY_ID.rol_branch.label}
              titleHint={OVERVIEW_METRIC_BY_ID.rol_branch.tooltip}
              value={formatPct(dashboard.branchRol?.rol_target_pct)}
              hint={
                dashboard.branchRol ? `ROL ${formatCurrency(dashboard.branchRol.rol)}` : undefined
              }
              icon={<Banknote size={18} aria-hidden="true" />}
            />
            <CommercialMetricCard
              label={OVERVIEW_METRIC_BY_ID.closing_rate.label}
              titleHint={OVERVIEW_METRIC_BY_ID.closing_rate.tooltip}
              value={formatPct(dashboard.closingRate?.sales_conversion_rate_pct)}
              hint={
                dashboard.closingRate
                  ? `${dashboard.closingRate.qtd_won}/${dashboard.closingRate.qtd_proposals}`
                  : undefined
              }
              icon={<Percent size={18} aria-hidden="true" />}
            />
            <CommercialMetricCard
              label={OVERVIEW_METRIC_BY_ID.otd.label}
              titleHint={OVERVIEW_METRIC_BY_ID.otd.tooltip}
              value={formatPct(dashboard.salesOrderOtd?.sales_order_otd_pct)}
              icon={<PackageCheck size={18} aria-hidden="true" />}
            />
            <CommercialMetricCard
              label={OVERVIEW_METRIC_BY_ID.new_business.label}
              titleHint={OVERVIEW_METRIC_BY_ID.new_business.tooltip}
              value={formatPct(dashboard.newBusinessRol?.new_business_rol_pct)}
              icon={<Sparkles size={18} aria-hidden="true" />}
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
