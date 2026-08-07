import { ActionButton, DataTable, EmptyState, SectionCard, type DataTableColumn } from "@delpi/plugin-ui/index";
import { Banknote, PackageCheck, Percent, RefreshCw, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { getCommercialProposals } from "../../api/gestaoApi";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  CommercialLoadingCard,
  CommercialTitleWithHelp,
} from "../../app/commercialUi";
import { navigateAnalyticsOpportunityDetail } from "../../app/pluginNavigation";
import { KpiCard } from "../../components/KpiCard";
import { GESTAO_CONTENT } from "../../content/analyticsContent";
import type { CommercialProposal } from "../../types/gestao";
import { formatCurrency } from "../../utils/format";
import { formatDisplayDate } from "../../utils/dates";
import { GestaoFilters } from "./components/GestaoFilters";
import { GestaoFunnelChart } from "./components/GestaoFunnelChart";
import { GestaoRolSeriesChart } from "./components/GestaoRolSeriesChart";
import { useGestaoDashboard } from "./hooks/useGestaoDashboard";
import { useGestaoFilters } from "./hooks/useGestaoFilters";
import { buildGestaoFilterSearchParams } from "./utils/gestaoFilterUrl";

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  return `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
}

type GestaoPageProps = {
  basePath: string;
};

export function GestaoPage({ basePath }: GestaoPageProps) {
  const filters = useGestaoFilters();
  const dashboard = useGestaoDashboard(filters.apiParams);
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
              search: buildGestaoFilterSearchParams({
                ...filters.filterState,
              }),
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
          title={GESTAO_CONTENT.overview.title}
          hint={GESTAO_CONTENT.overview.subtitle}
        />
        <ActionButton variant="ghost" onClick={dashboard.reload}>
          <RefreshCw size={16} aria-hidden="true" /> Atualizar
        </ActionButton>
      </header>

      <GestaoFilters
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

      <SectionCard
        title="Indicadores"
        hint={GESTAO_CONTENT.overview.filters}
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
          <div className="cm-home-kpi-grid" aria-label="KPIs de gestão">
            <KpiCard
              title="ROL vs meta"
              titleHint={GESTAO_CONTENT.overview.rolKpi}
              value={formatPct(dashboard.headOfficeRol?.rol_target_pct)}
              subtitle={
                dashboard.headOfficeRol
                  ? `ROL ${formatCurrency(dashboard.headOfficeRol.rol)}`
                  : undefined
              }
              icon={<Banknote size={22} />}
            />
            <KpiCard
              title="ROL filial"
              titleHint={GESTAO_CONTENT.overview.branchRolKpi}
              value={formatPct(dashboard.branchRol?.rol_target_pct)}
              subtitle={
                dashboard.branchRol ? `ROL ${formatCurrency(dashboard.branchRol.rol)}` : undefined
              }
              icon={<Banknote size={22} />}
            />
            <KpiCard
              title="Conversão"
              titleHint={GESTAO_CONTENT.overview.closingKpi}
              value={formatPct(dashboard.closingRate?.sales_conversion_rate_pct)}
              subtitle={
                dashboard.closingRate
                  ? `${dashboard.closingRate.qtd_won}/${dashboard.closingRate.qtd_proposals}`
                  : undefined
              }
              icon={<Percent size={22} />}
            />
            <KpiCard
              title="OTD"
              titleHint={GESTAO_CONTENT.overview.otdKpi}
              value={formatPct(dashboard.salesOrderOtd?.sales_order_otd_pct)}
              icon={<PackageCheck size={22} />}
            />
            <KpiCard
              title="Novos negócios"
              titleHint={GESTAO_CONTENT.overview.newBusinessKpi}
              value={formatPct(dashboard.newBusinessRol?.new_business_rol_pct)}
              icon={<Sparkles size={22} />}
            />
          </div>
        ) : null}
      </SectionCard>

      <div className="cm-gestao-charts-grid">
        <SectionCard
          title="Evolução de ROL"
          hint={GESTAO_CONTENT.overview.rolSeries}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <GestaoRolSeriesChart
            filters={{
              start_date: filters.apiParams.start_date,
              end_date: filters.apiParams.end_date,
              customer_segment: filters.apiParams.customer_segment,
            }}
          />
        </SectionCard>
        <SectionCard
          title="Funil de conversão"
          hint={GESTAO_CONTENT.overview.funnel}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <GestaoFunnelChart closingRate={dashboard.closingRate} />
        </SectionCard>
      </div>

      <SectionCard
        title="OVs recentes"
        hint={GESTAO_CONTENT.overview.ovTable}
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
