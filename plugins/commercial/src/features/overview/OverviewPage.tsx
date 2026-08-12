import { ActionButton, DataTable, EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { Banknote, PackageCheck, Percent, RefreshCw, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { getCommercialProposals } from "../../api/analyticsApi";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialLoadingCard,
  CommercialTitleWithHelp,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/PortfolioScopeContext";
import { navigateAnalyticsOpportunityDetail, navigatePluginView } from "../../app/pluginNavigation";
import type { PluginNavigationTarget } from "../../app/pluginRoutes";
import { KpiCard } from "../../components/KpiCard";
import { ANALYTICS_CONTENT } from "../../content/analyticsContent";
import { OVERVIEW_METRIC_BY_ID } from "../../content/overviewMetricsCatalog";
import type { CommercialProposal } from "../../types/analytics";
import { formatCurrency } from "../../utils/format";
import { formatDisplayDate } from "../../utils/dates";
import { AnalyticsFilters } from "../analytics/components/AnalyticsFilters";
import { AnalyticsFunnelChart } from "../analytics/components/AnalyticsFunnelChart";
import { AnalyticsRolSeriesChart } from "../analytics/components/AnalyticsRolSeriesChart";
import { useAnalyticsDashboard } from "../analytics/hooks/useAnalyticsDashboard";
import { useAnalyticsFilters } from "../analytics/hooks/useAnalyticsFilters";
import { buildAnalyticsFilterSearchParams } from "../analytics/utils/analyticsFilterUrl";

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

type OverviewPageProps = {
  basePath: string;
};

export function OverviewPage({ basePath }: OverviewPageProps) {
  const { canUseTeamScope } = usePortfolioScope();
  const filters = useAnalyticsFilters();
  const dashboard = useAnalyticsDashboard(filters.apiParams);
  const [proposals, setProposals] = useState<CommercialProposal[]>([]);
  const [proposalsLoading, setProposalsLoading] = useState(true);
  const [proposalsError, setProposalsError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setProposalsLoading(true);
    setProposalsError(null);
    void getCommercialProposals(
      { ...filters.apiParams, page: 1, page_size: 15, sort_by: "proposal_date", sort_dir: "desc" },
      controller.signal,
    )
      .then((page) => {
        if (!controller.signal.aborted) setProposals(page.items ?? []);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setProposalsError(err instanceof Error ? err.message : "Erro ao carregar OVs.");
        setProposals([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setProposalsLoading(false);
      });
    return () => controller.abort();
  }, [
    filters.apiParams.start_date,
    filters.apiParams.end_date,
    filters.apiParams.branch,
    filters.apiParams.customer_segment,
  ]);

  const filterSearch = buildAnalyticsFilterSearchParams(filters.filterState);
  const openDrill = (view: PluginNavigationTarget) =>
    navigatePluginView(view, { basePath, search: filterSearch });

  const drills: Array<{ id: PluginNavigationTarget; label: string }> = [
    { id: "analytics_otd", label: ANALYTICS_CONTENT.overview.drillOtd },
    { id: "analytics_opportunities", label: ANALYTICS_CONTENT.overview.drillOpportunities },
    ...(canUseTeamScope
      ? [{ id: "analytics_team" as const, label: ANALYTICS_CONTENT.overview.drillTeam }]
      : []),
  ];

  const columns: DataTableColumn<CommercialProposal>[] = [
    {
      key: "proposal",
      header: "OV",
      render: (row) => (
        <button
          type="button"
          className="cm-link-button"
          onClick={() =>
            navigateAnalyticsOpportunityDetail(row.proposal_number, {
              basePath,
              search: filterSearch,
            })
          }
        >
          {row.proposal_number}
        </button>
      ),
    },
    {
      key: "customer",
      header: "Cliente",
      render: (row) => row.customer_code || "—",
    },
    {
      key: "status",
      header: "Status",
      render: (row) => row.status_label || row.status_code || "—",
    },
    {
      key: "date",
      header: "Data",
      render: (row) => formatDisplayDate(row.proposal_date),
    },
  ];

  return (
    <section className="cm-page-stack">
      <header className="cm-page-header-row">
        <CommercialTitleWithHelp
          title={ANALYTICS_CONTENT.overview.title}
          hint={ANALYTICS_CONTENT.overview.subtitle}
        />
        <ActionButton variant="ghost" onClick={dashboard.reload}>
          <RefreshCw size={16} aria-hidden="true" /> Atualizar
        </ActionButton>
      </header>

      <AnalyticsFilters
        dateStart={filters.dateStart}
        dateEnd={filters.dateEnd}
        competence={filters.competence}
        branches={filters.branches}
        customerSegment={filters.customerSegment}
        onDateStart={filters.setDateStart}
        onDateEnd={filters.setDateEnd}
        onCompetence={filters.setCompetence}
        onBranches={filters.setBranches}
        onCustomerSegment={filters.setCustomerSegment}
      />

      <nav className="cm-overview-drills" aria-label={ANALYTICS_CONTENT.overview.drillsAriaLabel}>
        {drills.map((drill) => (
          <ActionButton key={drill.id} variant="ghost" onClick={() => openDrill(drill.id)}>
            {drill.label}
          </ActionButton>
        ))}
      </nav>

      <SectionCard
        title="Indicadores"
        hint={ANALYTICS_CONTENT.overview.filters}
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
          <div className="cm-home-kpi-grid" aria-label="KPIs da visão geral">
            <KpiCard
              title={OVERVIEW_METRIC_BY_ID.rol_head_office.label}
              titleHint={OVERVIEW_METRIC_BY_ID.rol_head_office.tooltip}
              value={formatPct(dashboard.headOfficeRol?.rol_target_pct)}
              subtitle={
                dashboard.headOfficeRol
                  ? `ROL ${formatCurrency(dashboard.headOfficeRol.rol)}`
                  : undefined
              }
              icon={<Banknote size={22} />}
            />
            <KpiCard
              title={OVERVIEW_METRIC_BY_ID.rol_branch.label}
              titleHint={OVERVIEW_METRIC_BY_ID.rol_branch.tooltip}
              value={formatPct(dashboard.branchRol?.rol_target_pct)}
              subtitle={
                dashboard.branchRol ? `ROL ${formatCurrency(dashboard.branchRol.rol)}` : undefined
              }
              icon={<Banknote size={22} />}
            />
            <KpiCard
              title={OVERVIEW_METRIC_BY_ID.closing_rate.label}
              titleHint={OVERVIEW_METRIC_BY_ID.closing_rate.tooltip}
              value={formatPct(dashboard.closingRate?.sales_conversion_rate_pct)}
              subtitle={
                dashboard.closingRate
                  ? `${dashboard.closingRate.qtd_won}/${dashboard.closingRate.qtd_proposals}`
                  : undefined
              }
              icon={<Percent size={22} />}
            />
            <KpiCard
              title={OVERVIEW_METRIC_BY_ID.otd.label}
              titleHint={OVERVIEW_METRIC_BY_ID.otd.tooltip}
              value={formatPct(dashboard.salesOrderOtd?.sales_order_otd_pct)}
              icon={<PackageCheck size={22} />}
            />
            <KpiCard
              title={OVERVIEW_METRIC_BY_ID.new_business.label}
              titleHint={OVERVIEW_METRIC_BY_ID.new_business.tooltip}
              value={formatPct(dashboard.newBusinessRol?.new_business_rol_pct)}
              icon={<Sparkles size={22} />}
            />
          </div>
        ) : null}
      </SectionCard>

      <div className="cm-gestao-charts-grid">
        <SectionCard
          title={OVERVIEW_METRIC_BY_ID.rol_series.label}
          hint={OVERVIEW_METRIC_BY_ID.rol_series.tooltip}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <AnalyticsRolSeriesChart
            filters={{
              start_date: filters.apiParams.start_date,
              end_date: filters.apiParams.end_date,
              customer_segment: filters.apiParams.customer_segment,
            }}
          />
        </SectionCard>
        <SectionCard
          title={OVERVIEW_METRIC_BY_ID.funnel.label}
          hint={OVERVIEW_METRIC_BY_ID.funnel.tooltip}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <AnalyticsFunnelChart closingRate={dashboard.closingRate} />
        </SectionCard>
      </div>

      <SectionCard
        title={OVERVIEW_METRIC_BY_ID.ov_table.label}
        hint={OVERVIEW_METRIC_BY_ID.ov_table.tooltip}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {proposalsLoading ? (
          <CommercialLoadingCard title="Carregando OVs…" variant="panel" />
        ) : null}
        {proposalsError ? (
          <EmptyState classNames={cmEmptyStateClassNames} defaultMessage={proposalsError} role="alert" />
        ) : null}
        {!proposalsLoading && !proposalsError ? (
          <DataTable
            rows={proposals}
            columns={columns}
            rowKey={(row) => `${row.branch}-${row.proposal_number}-${row.revision}`}
            classNames={cmDataTableClassNames}
            labels={cmDataTableLabels}
            layout="section"
          />
        ) : null}
      </SectionCard>
    </section>
  );
}
