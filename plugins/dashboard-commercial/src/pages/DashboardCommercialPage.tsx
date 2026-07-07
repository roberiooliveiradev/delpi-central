import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import {
  Banknote,
  Building2,
  PackageCheck,
  Percent,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import {
  getCommercialProposalsForExport,
  resolveProposalSortApiKey,
} from "../api/commercialApi";
import { ChartCard } from "../components/ChartCard";
import { ConversionFunnelChart } from "../components/ConversionFunnelChart";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { ChartToolbar } from "../components/ChartToolbar";
import type { DataTableColumn } from "../components/dataTableUi";
import { DataTableSection } from "../components/dataTableUi";
import { FilterBar } from "../components/FilterBar";
import { FieldLabel } from "@delpi/plugin-ui";
import { KpiCard } from "../components/KpiCard";
import { ProposalStatusBadge } from "../components/ProposalStatusBadge";
import { RolEvolutionChart } from "../components/RolEvolutionChart";
import { TotvsSourceBanner } from "../components/TotvsSourceBanner";
import { buildCommercialDetailPath } from "../constants/routes";
import { useCommercialDashboard } from "../hooks/useCommercialDashboard";
import { useCommercialProposals } from "../hooks/useCommercialProposals";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useLoadingProgress } from "../hooks/useSimulatedLoadingProgress";
import { useCommercialFilters } from "../hooks/useCommercialFilters";
import { useCommercialRolSeries } from "../hooks/useCommercialRolSeries";
import { useServerTable } from "../hooks/useServerTable";
import type { ChartGranularity } from "../types/chart";
import type {
  CommercialProposal,
  CommercialProposalStatusFilter,
} from "../types/commercial";
import {
  buildDashboardKpisPayload,
  buildFunnelPayload,
  buildProposalsPayload,
  buildRolSeriesPayload,
  CommercialExportButtons,
  type DashboardExportContext,
} from "../export";
import { formatDisplayDate, formatPeriodLabel } from "../utils/dates";
import { suggestGranularity } from "../utils/periodBuckets";
import {
  COMMERCIAL_CONSOLIDATED_BRANCH_LABELS,
  COMMERCIAL_KPI_TITLES,
} from "../constants/commercialIndicators";
import { COMMERCIAL_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  buildKpiGoalPresentationWithBranchIdd,
  formatDashboardMetricValue,
} from "../utils/goalDisplay";
import { buildRolPerUnitKpiView } from "../utils/rolPerUnitPresentation";
import {
  formatInteger,
  formatCurrency,
  formatPercent,
} from "../utils/format";
import { navigateCommercial } from "../utils/navigation";
import {
  formatCommercialBranchFilterLabel,
  resolveCommercialApiBranch,
} from "../utils/commercialClientFilters";
import { OPERATIONAL_UNIT_COLUMN_LABEL, formatOperationalUnitCode, normalizeOperationalUnitCode } from "../utils/operationalUnitLabels";
import {
  appendCustomerSegmentToLabel,
  formatNewBusinessRolContextLine,
} from "../utils/customerSegmentLabel";

type DashboardCommercialPageProps = {
  isActive?: boolean;
};

const PROPOSALS_PAGE_SIZE = 20;
const PROPOSAL_SEARCH_DEBOUNCE_MS = 350;

export function DashboardCommercialPage({
  isActive = true,
}: DashboardCommercialPageProps) {
  const {
    dateStart,
    dateEnd,
    competence,
    branches,
    customerSegment,
    setDateStart,
    setDateEnd,
    setCompetence,
    setBranches,
    setCustomerSegment,
    apiParams,
    filterState,
  } = useCommercialFilters();

  const [granularity, setGranularity] = useState<ChartGranularity>("month");
  const [proposalStatusFilter, setProposalStatusFilter] =
    useState<CommercialProposalStatusFilter>("all");
  const [proposalSearch, setProposalSearch] = useState("");
  const debouncedProposalSearch = useDebouncedValue(
    proposalSearch,
    PROPOSAL_SEARCH_DEBOUNCE_MS
  );
  const proposalsServerTable = useServerTable({
    pageSize: PROPOSALS_PAGE_SIZE,
    defaultSortKey: "proposal_date",
    defaultSortDirection: "desc",
  });

  const {
    headOfficeRol,
    branchRol,
    headOfficeWegRol,
    branchWegRol,
    headOfficeNewBusinessRol,
    branchNewBusinessRol,
    closingRate,
    salesOrderOtd,
    newBusinessRol,
    closingRateBranches,
    salesOrderOtdBranches,
    newBusinessRolBranches,
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
    page: proposalsPage,
    pageSize: proposalsPageSize,
    loading: proposalsLoading,
    refreshing: proposalsRefreshing,
    error: proposalsError,
    reload: reloadProposals,
  } = useCommercialProposals({
    filters: apiParams,
    statusFilter: proposalStatusFilter,
    search: debouncedProposalSearch,
    tableQuery: proposalsServerTable.query,
  });

  useEffect(() => {
    proposalsServerTable.resetPage();
  }, [
    apiParams.branch,
    apiParams.customer_segment,
    apiParams.end_date,
    apiParams.start_date,
    proposalStatusFilter,
    debouncedProposalSearch,
    proposalsServerTable.resetPage,
  ]);

  useEffect(() => {
    setGranularity(suggestGranularity(dateStart, dateEnd));
  }, [dateStart, dateEnd]);

  const periodLabel = useMemo(
    () => formatPeriodLabel(dateStart, dateEnd),
    [dateStart, dateEnd]
  );

  const activeApiBranch = resolveCommercialApiBranch(branches);

  const branchLabel = formatCommercialBranchFilterLabel(branches);

  const rolContextLabel = appendCustomerSegmentToLabel(
    activeApiBranch
      ? `${formatOperationalUnitCode(activeApiBranch, activeApiBranch)} · ${periodLabel}`
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
        activeApiBranch,
      ),
    [activeApiBranch, branchRol, headOfficeRol, rolContextLabel],
  );

  const wegRolContextLabel = appendCustomerSegmentToLabel(
    activeApiBranch
      ? `${formatOperationalUnitCode(activeApiBranch, activeApiBranch)} · ${periodLabel}`
      : `${COMMERCIAL_CONSOLIDATED_BRANCH_LABELS.sum} · ${periodLabel}`,
    "weg",
  );

  const newBusinessRolContextLabel = appendCustomerSegmentToLabel(
    activeApiBranch
      ? `${formatOperationalUnitCode(activeApiBranch, activeApiBranch)} · ${periodLabel}`
      : `${COMMERCIAL_CONSOLIDATED_BRANCH_LABELS.sum} · ${periodLabel}`,
    "new_business",
  );

  const wegRolKpi = useMemo(
    () =>
      buildRolPerUnitKpiView(
        headOfficeWegRol,
        branchWegRol,
        wegRolContextLabel,
        formatCurrency,
        activeApiBranch,
      ),
    [
      activeApiBranch,
      branchWegRol,
      headOfficeWegRol,
      wegRolContextLabel,
    ],
  );

  const segmentNewBusinessRolKpi = useMemo(
    () =>
      buildRolPerUnitKpiView(
        headOfficeNewBusinessRol,
        branchNewBusinessRol,
        newBusinessRolContextLabel,
        formatCurrency,
        activeApiBranch,
      ),
    [
      activeApiBranch,
      branchNewBusinessRol,
      headOfficeNewBusinessRol,
      newBusinessRolContextLabel,
    ],
  );

  const isBusy = loading || refreshing;
  const hasData =
    headOfficeRol !== null ||
    branchRol !== null ||
    headOfficeWegRol !== null ||
    branchWegRol !== null ||
    headOfficeNewBusinessRol !== null ||
    branchNewBusinessRol !== null;
  const isChartBusy = rolSeries.loading;
  const initialLoadingProgress = useLoadingProgress(loading && !hasData, requestProgress);
  const refreshLoadingProgress = useLoadingProgress(refreshing && hasData, requestProgress);

  const hasChartValues = rolSeries.points.some(
    (point) => point.rolMatrix > 0 || point.rolBranch > 0
  );

  const handleChartDrillDown = useCallback(
    (nextStart: string, nextEnd: string) => {
      setDateStart(nextStart);
      setDateEnd(nextEnd);
    },
    [setDateStart, setDateEnd]
  );


  const kpiExportRows = useMemo(
    () => [
      {
        indicador: COMMERCIAL_KPI_TITLES.rol,
        valor: rolKpi.value,
        contexto: [rolKpi.contextLabel, rolKpi.goalLabel].filter(Boolean).join(" · "),
      },
      {
        indicador: COMMERCIAL_KPI_TITLES.rolWeg,
        valor: wegRolKpi.value,
        contexto: [wegRolKpi.contextLabel, wegRolKpi.goalLabel]
          .filter(Boolean)
          .join(" · "),
      },
      {
        indicador: COMMERCIAL_KPI_TITLES.rolNewBusiness,
        valor: segmentNewBusinessRolKpi.value,
        contexto: [
          segmentNewBusinessRolKpi.contextLabel,
          segmentNewBusinessRolKpi.goalLabel,
        ]
          .filter(Boolean)
          .join(" · "),
      },
      {
        indicador: COMMERCIAL_KPI_TITLES.salesOrderOtd,
        valor: formatPercent(salesOrderOtd?.sales_order_otd_pct),
        contexto: `${formatInteger(salesOrderOtd?.on_time_lines)} no prazo / ${formatInteger(salesOrderOtd?.total_lines)} linhas · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
      },
      {
        indicador: COMMERCIAL_KPI_TITLES.closingRate,
        valor: formatPercent(closingRate?.sales_conversion_rate_pct),
        contexto: `${formatInteger(closingRate?.qtd_won)} ganhas / ${formatInteger(closingRate?.qtd_proposals)} propostas · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
      },
      {
        indicador: COMMERCIAL_KPI_TITLES.newBusinessRol,
        valor: formatPercent(newBusinessRol?.new_business_rol_pct),
        contexto: `${formatNewBusinessRolContextLine(newBusinessRol, customerSegment, formatCurrency)} · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
      },
    ],
    [
      branchLabel,
      closingRate,
      consolidatedOtherKpisLabel,
      customerSegment,
      newBusinessRol,
      periodLabel,
      rolKpi.contextLabel,
      rolKpi.goalLabel,
      rolKpi.value,
      segmentNewBusinessRolKpi.contextLabel,
      segmentNewBusinessRolKpi.goalLabel,
      segmentNewBusinessRolKpi.value,
      salesOrderOtd,
      wegRolKpi.contextLabel,
      wegRolKpi.goalLabel,
      wegRolKpi.value,
    ],
  );

  const dashboardExportContext = useMemo<DashboardExportContext>(
    () => ({
      documentTitle: "dashboard-comercial",
      periodLabel,
      scopeLabel: branchLabel ?? consolidatedOtherKpisLabel,
      kpiRows: kpiExportRows,
      rolPoints: rolSeries.points,
      funnel: closingRate,
      proposals,
    }),
    [
      branchLabel,
      closingRate,
      consolidatedOtherKpisLabel,
      kpiExportRows,
      periodLabel,
      proposals,
      rolSeries.points,
    ],
  );

  const proposalsExportPayload = useMemo(
    () => buildProposalsPayload(proposals),
    [proposals],
  );

  const proposalsExportParams = useMemo(
    () => ({
      ...apiParams,
      status: proposalStatusFilter === "all" ? undefined : proposalStatusFilter,
      total: proposalsTotal,
      sort_by: resolveProposalSortApiKey(proposalsServerTable.query.sortKey),
      sort_dir: proposalsServerTable.query.sortDirection,
      search: debouncedProposalSearch.trim() || undefined,
    }),
    [
      apiParams,
      debouncedProposalSearch,
      proposalStatusFilter,
      proposalsServerTable.query.sortDirection,
      proposalsServerTable.query.sortKey,
      proposalsTotal,
    ],
  );

  const resolveProposalsExportPayload = useCallback(async () => {
    const result = await getCommercialProposalsForExport(proposalsExportParams);
    return buildProposalsPayload(result.items);
  }, [proposalsExportParams]);

  const resolveDashboardExportContext = useCallback(async () => {
    const proposalsResult =
      proposalsTotal > 0
        ? await getCommercialProposalsForExport(proposalsExportParams)
        : { items: [] as CommercialProposal[] };

    return {
      documentTitle: "dashboard-comercial",
      periodLabel,
      scopeLabel: branchLabel ?? consolidatedOtherKpisLabel,
      kpiRows: kpiExportRows,
      rolPoints: rolSeries.points,
      funnel: closingRate,
      proposals: proposalsResult.items,
    };
  }, [
    branchLabel,
    closingRate,
    consolidatedOtherKpisLabel,
    kpiExportRows,
    periodLabel,
    proposalsExportParams,
    proposalsTotal,
    rolSeries.points,
  ]);

  const rolSeriesExportPayload = useMemo(
    () => buildRolSeriesPayload(rolSeries.points),
    [rolSeries.points],
  );

  const kpiExportPayload = useMemo(
    () => buildDashboardKpisPayload(kpiExportRows),
    [kpiExportRows],
  );

  const funnelExportPayload = useMemo(
    () => buildFunnelPayload(closingRate),
    [closingRate],
  );

  const handleProposalRowClick = useCallback(
    (row: CommercialProposal) => {
      if (!isActive) return;
      navigateCommercial(
        buildCommercialDetailPath(row.proposal_number, {
          dateStart,
          dateEnd,
          competence,
          branches,
          customerSegment,
          proposalBranch: normalizeOperationalUnitCode(row.branch),
          revision: row.revision,
        })
      );
    },
    [branches, competence, customerSegment, dateEnd, dateStart, isActive]
  );

  const proposalColumns = useMemo<DataTableColumn<CommercialProposal>[]>(
    () => [
      {
        key: "branch",
        header: OPERATIONAL_UNIT_COLUMN_LABEL,
        headerHint: COMMERCIAL_HELP_TOOLTIPS.table.branch,
        render: (row) => formatOperationalUnitCode(row.branch),
        sortable: true,
        sortValue: (row) => formatOperationalUnitCode(row.branch, ""),
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
    "Clique em um ponto para filtrar o período ao intervalo. Séries por Santa Catarina e Espírito Santo.";

  return (
    <div className="dashboard-commercial dashboard-page dc-print-root">
      <FilterBar
        filterState={filterState}
        competence={competence}
        dateStart={dateStart}
        dateEnd={dateEnd}
        branches={branches}
        customerSegment={customerSegment}
        exportActions={
          <CommercialExportButtons
            variant="dashboard"
            context={dashboardExportContext}
            resolveContext={resolveDashboardExportContext}
            disabled={loading && !hasData}
          />
        }
        onCompetenceChange={setCompetence}
        onDateStartChange={setDateStart}
        onDateEndChange={setDateEnd}
        onBranchesChange={setBranches}
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
        <div className="dc-kpi-grid__export dc-no-print">
          <CommercialExportButtons
            variant="table"
            payload={kpiExportPayload}
            disabled={isBusy && !hasData}
            className="dc-export-actions dc-export-actions--compact"
          />
        </div>
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
          iddScoreLabel={rolKpi.iddScoreLabel}
          icon={<Banknote size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.rolWeg}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.rolWeg}
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
          icon={<Building2 size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.rolNewBusiness}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.rolNewBusiness}
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
          icon={<Sparkles size={22} />}
          loading={
            isBusy && !headOfficeNewBusinessRol && !branchNewBusinessRol
          }
        />
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.salesOrderOtd}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.salesOrderOtd}
          value={formatDashboardMetricValue(
            salesOrderOtd?.sales_order_otd_pct,
            salesOrderOtd,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `${formatInteger(salesOrderOtd?.on_time_lines)} no prazo / ${formatInteger(salesOrderOtd?.total_lines)} linhas · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
            salesOrderOtd,
            {
              realizedValue: salesOrderOtd?.sales_order_otd_pct,
              activeBranch: activeApiBranch,
              branches: salesOrderOtdBranches,
            },
          )}
          icon={<PackageCheck size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.closingRate}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.closingRate}
          value={formatDashboardMetricValue(
            closingRate?.sales_conversion_rate_pct,
            closingRate,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `${formatInteger(closingRate?.qtd_won)} ganhas / ${formatInteger(closingRate?.qtd_proposals)} propostas · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
            closingRate,
            {
              realizedValue: closingRate?.sales_conversion_rate_pct,
              activeBranch: activeApiBranch,
              branches: closingRateBranches,
            },
          )}
          icon={<Percent size={22} />}
          loading={isBusy}
        />
        <KpiCard
          title={COMMERCIAL_KPI_TITLES.newBusinessRol}
          titleHint={COMMERCIAL_HELP_TOOLTIPS.kpis.newBusinessRol}
          value={formatDashboardMetricValue(
            newBusinessRol?.new_business_rol_pct,
            newBusinessRol,
          )}
          {...buildKpiGoalPresentationWithBranchIdd(
            `${formatNewBusinessRolContextLine(newBusinessRol, customerSegment, formatCurrency)} · ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`,
            newBusinessRol,
            {
              realizedValue: newBusinessRol?.new_business_rol_pct,
              activeBranch: activeApiBranch,
              branches: newBusinessRolBranches,
            },
          )}
          icon={<TrendingUp size={22} />}
          loading={isBusy}
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
            exportActions={
              <CommercialExportButtons
                variant="table"
                payload={rolSeriesExportPayload}
                disabled={rolSeries.points.length === 0}
                className="dc-export-actions dc-export-actions--compact"
                buttonClassName="dc-ghost-btn dc-chart-toolbar__export"
              />
            }
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
          headerActions={
            <CommercialExportButtons
              variant="table"
              payload={funnelExportPayload}
              disabled={!closingRate || (closingRate.qtd_proposals ?? 0) === 0}
              className="dc-export-actions dc-export-actions--compact"
              buttonClassName="dc-ghost-btn dc-chart-toolbar__export"
            />
          }
        >
          <ConversionFunnelChart
            data={closingRate}
            loading={isBusy}
          />
        </ChartCard>
      </section>

      <section className="dc-proposals-section dc-no-print">
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
            hint={`${proposalStatusHint} ${branchLabel ?? consolidatedOtherKpisLabel} · ${periodLabel}`}
            columns={proposalColumns}
            rows={proposals}
            rowKey={(row) =>
              `${row.branch}-${row.proposal_number}-${row.revision}`
            }
            onRowClick={handleProposalRowClick}
            loading={proposalsLoading}
            refreshing={proposalsRefreshing}
            pageSize={PROPOSALS_PAGE_SIZE}
            serverPagination={{
              page: proposalsPage,
              pageSize: proposalsPageSize,
              total: proposalsTotal,
              onPageChange: proposalsServerTable.setPage,
              onPageSizeChange: proposalsServerTable.setPageSize,
            }}
            serverSort={{
              sortKey: proposalsServerTable.query.sortKey,
              sortDirection: proposalsServerTable.query.sortDirection,
              onSortChange: proposalsServerTable.handleSortChange,
            }}
            serverSearch={{
              value: proposalSearch,
              onChange: setProposalSearch,
            }}
            toolbarExtra={
              <label className="dc-proposals-filter dc-field">
                <FieldLabel
                  label="Status da proposta"
                  hint={COMMERCIAL_HELP_TOOLTIPS.filters.proposalStatus}
                  className="dc-field__label"
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
            }
            emptyMessage="Nenhuma proposta encontrada para os filtros selecionados."
            searchPlaceholder="Buscar proposta, descrição, status, cliente…"
            searchHint={COMMERCIAL_HELP_TOOLTIPS.table.search}
            headerActions={
              <CommercialExportButtons
                variant="table"
                payload={proposalsExportPayload}
                resolvePayload={resolveProposalsExportPayload}
                disabled={proposalsTotal === 0}
                className="dc-export-actions dc-export-actions--compact"
              />
            }
          />
        )}
      </section>
    </div>
  );
}
