import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Banknote,
  PackageCheck,
  Percent,
  TrendingUp,
} from "lucide-react";
import { ChartCard } from "../components/ChartCard";
import { ConversionFunnelChart } from "../components/ConversionFunnelChart";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { ChartToolbar } from "../components/ChartToolbar";
import type { DataTableColumn } from "../components/table";
import { DataTableSection } from "../components/table";
import { FilterBar } from "../components/FilterBar";
import { FieldLabel } from "../components/HelpTooltip";
import { KpiCard } from "../components/KpiCard";
import { ProposalStatusBadge } from "../components/ProposalStatusBadge";
import { RolEvolutionChart } from "../components/RolEvolutionChart";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { buildCommercialDetailPath } from "../constants/routes";
import { useClientTableSort } from "../hooks/useClientTableSort";
import { useCommercialDashboard } from "../hooks/useCommercialDashboard";
import { useCommercialProposals } from "../hooks/useCommercialProposals";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useCommercialFilters } from "../hooks/useCommercialFilters";
import { useCommercialRolSeries } from "../hooks/useCommercialRolSeries";
import type { ChartGranularity } from "../types/chart";
import type {
  CommercialProposal,
  CommercialProposalStatusFilter,
} from "../types/commercial";
import { downloadRolSeriesCsv } from "../utils/chartSeriesExport";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { suggestGranularity } from "../utils/periodBuckets";
import {
  COMMERCIAL_CONSOLIDATED_BRANCH_LABELS,
  COMMERCIAL_KPI_TITLES,
} from "../constants/commercialIndicators";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import { buildKpiGoalPresentation } from "../utils/goalDisplay";
import { buildRolPerUnitKpiView } from "../utils/rolPerUnitPresentation";
import {
  formatInteger,
  formatCurrency,
  formatPercent,
} from "../utils/format";
import { navigateCommercial } from "../utils/navigation";
import {
  appendCustomerSegmentToLabel,
  formatNewBusinessRolContextLine,
} from "../utils/customerSegmentLabel";

type DashboardCommercialPageProps = {
  isActive?: boolean;
};

export function DashboardCommercialPage({
  isActive = true,
}: DashboardCommercialPageProps) {
  const {
    dateStart,
    dateEnd,
    branch,
    customerSegment,
    setDateStart,
    setDateEnd,
    setBranch,
    setCustomerSegment,
    apiParams,
    filterState,
  } = useCommercialFilters();

  const [granularity, setGranularity] = useState<ChartGranularity>("month");
  const [proposalStatusFilter, setProposalStatusFilter] =
    useState<CommercialProposalStatusFilter>("all");

  const {
    headOfficeRol,
    branchRol,
    closingRate,
    salesOrderOtd,
    newBusinessRol,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  } = useCommercialDashboard(apiParams);

  const rolSeries = useCommercialRolSeries({
    filters: {
      start_date: apiParams.start_date,
      end_date: apiParams.end_date,
      customer_segment: apiParams.customer_segment,
    },
    granularity,
  });

  const {
    items: proposals,
    total: proposalsTotal,
    loading: proposalsLoading,
    refreshing: proposalsRefreshing,
    error: proposalsError,
    reload: reloadProposals,
  } = useCommercialProposals(apiParams, proposalStatusFilter);

  const tableSort = useClientTableSort({
    defaultSortKey: "proposal_date",
    defaultSortDirection: "desc",
  });

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const branchLabel = branch ? `Filial ${branch}` : null;

  const rolContextLabel = appendCustomerSegmentToLabel(
    branch
      ? `Filial ${branch} · ${periodLabel}`
      : `${COMMERCIAL_CONSOLIDATED_BRANCH_LABELS.sum} · ${periodLabel}`,
    customerSegment
  );

  const consolidatedOtherKpisLabel = appendCustomerSegmentToLabel(
    COMMERCIAL_CONSOLIDATED_BRANCH_LABELS.allBranches,
    customerSegment
  );

  const rolKpi = useMemo(
    () =>
      buildRolPerUnitKpiView(
        headOfficeRol,
        branchRol,
        rolContextLabel,
        formatCurrency,
        branch,
      ),
    [branch, branchRol, headOfficeRol, rolContextLabel],
  );

  const isBusy = loading || refreshing;
  const hasData = headOfficeRol !== null || branchRol !== null;
  const isChartBusy = rolSeries.loading;
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);

  const hasChartValues = rolSeries.points.some(
    (point) => point.rolMatrix > 0 || point.rolBranch > 0
  );

  const printDisabled = loading && !hasData;

  const handleChartDrillDown = useCallback(
    (nextStart: string, nextEnd: string) => {
      setDateStart(nextStart);
      setDateEnd(nextEnd);
    },
    [setDateStart, setDateEnd]
  );

  const handleExportChartCsv = useCallback(() => {
    downloadRolSeriesCsv("rol-evolucao.csv", rolSeries.points);
  }, [rolSeries.points]);

  const handleProposalRowClick = useCallback(
    (row: CommercialProposal) => {
      if (!isActive) return;
      navigateCommercial(
        buildCommercialDetailPath(row.proposal_number, {
          dateStart,
          dateEnd,
          branch,
          customerSegment,
          proposalBranch: row.branch,
          revision: row.revision,
        })
      );
    },
    [branch, customerSegment, dateEnd, dateStart, isActive]
  );

  const proposalColumns = useMemo<DataTableColumn<CommercialProposal>[]>(
    () => [
      {
        key: "branch",
        header: "Filial",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.branch,
        render: (row) => row.branch || "—",
        sortable: true,
        sortValue: (row) => row.branch,
      },
      {
        key: "proposal",
        header: "Nº proposta",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.proposal,
        render: (row) => row.proposal_number,
        sortable: true,
        sortValue: (row) => row.proposal_number,
      },
      {
        key: "revision",
        header: "Rev.",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.revision,
        className: "dc-table__col--numeric",
        render: (row) => row.revision || "—",
        sortable: true,
        sortValue: (row) => row.revision,
      },
      {
        key: "description",
        header: "Descrição",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.description,
        className: "dc-table__col--wide",
        render: (row) => row.description ?? "—",
        sortable: true,
        sortValue: (row) => row.description,
      },
      {
        key: "proposal_date",
        header: "Data",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.proposalDate,
        className: "dc-table__col--numeric",
        render: (row) => formatDisplayDate(row.proposal_date),
        sortable: true,
        sortValue: (row) => row.proposal_date,
      },
      {
        key: "end_date",
        header: "Fim",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.endDate,
        className: "dc-table__col--numeric",
        render: (row) => formatDisplayDate(row.end_date),
        sortable: true,
        sortValue: (row) => row.end_date,
      },
      {
        key: "status",
        header: "Status",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.status,
        render: (row): ReactNode => (
          <ProposalStatusBadge
            label={row.status_label ?? row.status_code ?? "—"}
            category={row.status_category}
            code={row.status_code}
          />
        ),
        sortable: true,
        sortValue: (row) => row.status_label ?? row.status_code,
      },
      {
        key: "customer",
        header: "Cliente",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.customerCode,
        className: "dc-table__col--numeric",
        render: (row) => row.customer_code ?? "—",
        sortable: true,
        sortValue: (row) => row.customer_code,
      },
      {
        key: "customer_store",
        header: "Loja",
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.customerStore,
        className: "dc-table__col--numeric",
        render: (row) => row.customer_store ?? "—",
        sortable: true,
        sortValue: (row) => row.customer_store,
      },
    ],
    []
  );

  const proposalStatusHint =
    proposalStatusFilter === "won"
      ? "Somente propostas ganhas (status 9) com aceite (AD1_DTASSI) no período."
      : proposalStatusFilter === "open"
        ? "Propostas sem fechamento ganho."
        : "Última revisão por proposta no período (data AD1_DATA).";

  const chartSubtitle =
    "Clique em um ponto para filtrar o período ao intervalo. Séries por filial 01 e 02.";

  return (
    <div className="dashboard-commercial dashboard-page dc-print-root">
      <FilterBar
        filterState={filterState}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branch={branch}
        customerSegment={customerSegment}
        printDisabled={printDisabled}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchChange={setBranch}
        onCustomerSegmentChange={setCustomerSegment}
        onRefresh={() => {
          reload();
          reloadProposals();
        }}
        refreshing={refreshing}
      />

      <TotvsSourceBanner />

      {error ? (
        <div className="dc-state dc-state--error" role="alert">
          <p>{error}</p>
          <button className="dc-primary-btn" type="button" onClick={reload}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {Object.keys(sectionErrors).length > 0 ? (
        <div className="dc-state dc-state--warning" role="status">
          <p>
            Alguns indicadores não carregaram. Os demais permanecem disponíveis.
          </p>
        </div>
      ) : null}

      {refreshing && hasData ? (
        <LoadingActivityCard
          title="Atualizando indicadores comerciais"
          description="Recalculando ROL, conversão e OTD com os filtros selecionados."
          variant="compact"
          sticky
          progressPercent={refreshLoadingProgress}
        />
      ) : null}

      {loading && !hasData ? (
        <LoadingActivityCard
          title="Carregando indicadores comerciais"
          description="Buscando ROL, taxa de conversão, OTD e novos negócios no TOTVS."
          progressPercent={initialLoadingProgress}
        />
      ) : null}

      <section className="dc-kpi-grid" aria-busy={isBusy}>
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.rol}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.rol}
          value={rolKpi.value}
          valueVariant={rolKpi.valueVariant}
          goalVariant={rolKpi.valueVariant}
          contextLabel={rolKpi.contextLabel}
          goalLabel={rolKpi.goalLabel}
          goalScopeBadge={rolKpi.goalScopeBadge}
          goalScopeHint={rolKpi.goalScopeHint}
          goalPerformanceBadge={rolKpi.goalPerformanceBadge}
          goalPerformanceBadges={rolKpi.goalPerformanceBadges}
          icon={<Banknote size={22} />}
          loading={isBusy && !headOfficeRol && !branchRol}
        />
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.salesOrderOtd}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.salesOrderOtd}
          value={formatPercent(salesOrderOtd?.sales_order_otd_pct)}
          {...buildKpiGoalPresentation(
            `${formatInteger(salesOrderOtd?.on_time_lines)} no prazo / ${formatInteger(salesOrderOtd?.total_lines)} linhas · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
            salesOrderOtd,
            formatPercent,
            { realizedValue: salesOrderOtd?.sales_order_otd_pct },
          )}
          icon={<PackageCheck size={22} />}
          loading={isBusy && !salesOrderOtd}
        />
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.closingRate}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.closingRate}
          value={formatPercent(closingRate?.sales_conversion_rate_pct)}
          {...buildKpiGoalPresentation(
            `${formatInteger(closingRate?.qtd_won)} ganhas / ${formatInteger(closingRate?.qtd_proposals)} propostas · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
            closingRate,
            formatPercent,
            { realizedValue: closingRate?.sales_conversion_rate_pct },
          )}
          icon={<Percent size={22} />}
          loading={isBusy && !closingRate}
        />
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.newBusinessRol}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.newBusinessRol}
          value={formatPercent(newBusinessRol?.new_business_rol_pct)}
          {...buildKpiGoalPresentation(
            `${formatNewBusinessRolContextLine(newBusinessRol, customerSegment, formatCurrency)} · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
            newBusinessRol,
            formatPercent,
            { realizedValue: newBusinessRol?.new_business_rol_pct },
          )}
          icon={<TrendingUp size={22} />}
          loading={isBusy && !newBusinessRol}
        />
      </section>

      <section className="dc-chart-section dc-no-print" aria-busy={isChartBusy}>
        <ChartCard
          title="Evolução do ROL (R$)"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.charts.rolEvolution}
          hint={chartSubtitle}
        >
          <ChartToolbar
            idPrefix="rol"
            granularity={granularity}
            onGranularityChange={setGranularity}
            onExportCsv={handleExportChartCsv}
            exportDisabled={rolSeries.points.length === 0}
          />

          {rolSeries.error ? (
            <div className="dc-state dc-state--error" role="alert">
              <p>{rolSeries.error}</p>
            </div>
          ) : null}

          {!rolSeries.error &&
          (rolSeries.points.length > 0 || rolSeries.loading) ? (
            <RolEvolutionChart
              data={rolSeries.points}
              loading={rolSeries.loading}
              onDrillDown={handleChartDrillDown}
            />
          ) : null}

          {!rolSeries.error &&
          rolSeries.points.length === 0 &&
          !rolSeries.loading ? (
            <div className="dc-state-box">Sem dados para o gráfico no período.</div>
          ) : null}

          {rolSeries.truncated ? (
            <p className="dc-chart-card__hint dc-chart-card__hint--below">
              Período limitado aos primeiros 60 intervalos para desempenho.
            </p>
          ) : null}

          {!rolSeries.error &&
          rolSeries.points.length > 0 &&
          !hasChartValues &&
          !rolSeries.loading ? (
            <p className="dc-chart-card__hint dc-chart-card__hint--below">
              Todos os intervalos retornaram ROL zero no período filtrado.
            </p>
          ) : null}
        </ChartCard>
      </section>

      <section className="dc-chart-section dc-no-print">
        <ChartCard
          title="Funil de conversão"
          titleHint={COMMERCIAL_HELP_TOOLTIPS.charts.conversionFunnel}
          hint="Volume de propostas, ganhas e perdas no período — alinhado ao KPI de conversão."
          className="dc-chart-card--funnel"
        >
          <ConversionFunnelChart
            data={closingRate}
            loading={isBusy && !closingRate}
          />
        </ChartCard>
      </section>

      <section className="dc-proposals-section dc-no-print">
        <div className="dc-proposals-toolbar">
          <label className="dc-proposals-filter dc-field">
            <FieldLabel
              label="Status da proposta"
              hint={COMMERCIAL_HELP_TOOLTIPS.filters.proposalStatus}
            />
            <select
              value={proposalStatusFilter}
              onChange={(event) =>
                setProposalStatusFilter(
                  event.target.value as CommercialProposalStatusFilter
                )
              }
            >
              <option value="all">Todas</option>
              <option value="won">Ganhas</option>
              <option value="open">Em aberto</option>
            </select>
          </label>
        </div>

        {proposalsError ? (
          <div className="dc-state dc-state--error" role="alert">
            <p>{proposalsError}</p>
            <button
              className="dc-primary-btn"
              type="button"
              onClick={reloadProposals}
            >
              Tentar novamente
            </button>
          </div>
        ) : (
          <DataTableSection
            title="Propostas do período"
            titleHint={COMMERCIAL_HELP_TOOLTIPS.table.section}
            hint={`${proposalStatusHint} ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}${
              proposalsTotal > proposals.length
                ? ` · exibindo ${proposals.length} de ${proposalsTotal}`
                : ""
            }`}
            columns={proposalColumns}
            rows={proposals}
            rowKey={(row) =>
              `${row.branch}-${row.proposal_number}-${row.revision}`
            }
            onRowClick={handleProposalRowClick}
            loading={proposalsLoading}
            refreshing={proposalsRefreshing}
            clientSort={{
              sortKey: tableSort.sortKey,
              sortDirection: tableSort.sortDirection,
              onSortChange: tableSort.handleSortChange,
            }}
            emptyMessage="Nenhuma proposta encontrada para os filtros selecionados."
            searchPlaceholder="Buscar proposta, descrição, status, cliente…"
            searchHint={COMMERCIAL_HELP_TOOLTIPS.table.search}
            getSearchText={(row) =>
              [
                row.branch,
                row.proposal_number,
                row.revision,
                row.description,
                row.status_label,
                row.status_code,
                row.customer_code,
                row.customer_store,
                row.stage,
              ]
                .filter(Boolean)
                .join(" ")
            }
          />
        )}
      </section>
    </div>
  );
}
