import { useEffect, useMemo, useState } from "react";

import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { PageHeader } from "../components/PageHeader";
import { PeriodFilters, type QuickRangePreset } from "../components/PeriodFilters";
import { RankingCharts } from "../components/RankingCharts";
import { RegistrosTable } from "../components/RegistrosTable";
import { SummaryCards } from "../components/SummaryCards";
import {
  BRANCH_ROUTE_LABELS,
  type BranchRouteCode,
  totvsBranchFromRoute,
} from "../constants/branches";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useScrapDashboard } from "../hooks/useScrapDashboard";
import { useScrapFiltros } from "../hooks/useScrapFiltros";
import { useScrapRegistros } from "../hooks/useScrapRegistros";
import type { FilterFormState, ScrapRegistroItem } from "../types/scrap";
import {
  createDefaultFilterFormState,
  filtersFromFormState,
  getDefaultLast12MonthsRange,
  getDefaultLast6MonthsRange,
  getThisMonthRange,
  getThisWeekRange,
  getTodayRange,
  validatePeriodRange,
} from "../utils/dateRange";
import { formatDatePtBr } from "../utils/formatters";
import { useLoadingProgress } from "../utils/loadingProgress";
import { navigateScrap } from "../utils/navigation";
import { buildRegistroDetailPath } from "../utils/routes";

const EMPTY_OPTIONAL_FILTERS = {
  mp: "",
  pa: "",
  op: "",
  motivo: "",
  centroTrabalho: "",
} as const;

const DEFAULT_PAGE_SIZE = 25;

type ScrapMonitoringPageProps = {
  branchRoute: BranchRouteCode;
  isActive?: boolean;
};

function isPermissionError(message: string | null): boolean {
  if (!message) return false;
  return /sem permissão|403|forbidden|sessão expirada/i.test(message);
}

export function ScrapMonitoringPage({
  branchRoute,
  isActive = true,
}: ScrapMonitoringPageProps) {
  const totvsBranch = totvsBranchFromRoute(branchRoute);

  return (
    <ScrapMonitoringContent
      key={totvsBranch}
      branchRoute={branchRoute}
      totvsBranch={totvsBranch}
      isActive={isActive}
    />
  );
}

type ContentProps = {
  branchRoute: BranchRouteCode;
  totvsBranch: string;
  isActive: boolean;
};

function ScrapMonitoringContent({
  branchRoute,
  totvsBranch,
  isActive,
}: ContentProps) {
  const defaultFilters = useMemo(() => createDefaultFilterFormState(), []);
  const [filters, setFilters] = useState<FilterFormState>(defaultFilters);
  const debouncedFilters = useDebouncedValue(filters, 350);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [exportError, setExportError] = useState<string | null>(null);

  const periodError = validatePeriodRange(
    debouncedFilters.dataInicio,
    debouncedFilters.dataFim,
  );
  const appliedFilters = useMemo(() => {
    if (periodError) return null;
    return filtersFromFormState(totvsBranch, debouncedFilters);
  }, [debouncedFilters, periodError, totvsBranch]);

  const appliedFiltersKey = appliedFilters
    ? [
        appliedFilters.filial,
        appliedFilters.dataInicio,
        appliedFilters.dataFim,
        appliedFilters.mp ?? "",
        appliedFilters.pa ?? "",
        appliedFilters.op ?? "",
        appliedFilters.motivo ?? "",
        appliedFilters.centroTrabalho ?? "",
      ].join("|")
    : "";

  useEffect(() => {
    setPage(1);
  }, [appliedFiltersKey]);

  const dashboard = useScrapDashboard(isActive ? appliedFilters : null);
  const registros = useScrapRegistros(
    isActive ? appliedFilters : null,
    page,
    pageSize,
  );
  const filtrosOptions = useScrapFiltros(isActive ? appliedFilters : null);

  const handleChange = (patch: Partial<FilterFormState>) => {
    setFilters((current) => ({ ...current, ...patch }));
  };

  const handleQuickRange = (preset: QuickRangePreset) => {
    const referenceDate = new Date();
    const range =
      preset === "today"
        ? getTodayRange(referenceDate)
        : preset === "thisWeek"
          ? getThisWeekRange(referenceDate)
          : preset === "12m"
            ? getDefaultLast12MonthsRange(referenceDate)
            : preset === "6m"
              ? getDefaultLast6MonthsRange(referenceDate)
              : getThisMonthRange(referenceDate);
    setFilters((current) => ({ ...current, ...range }));
  };

  const handleClearOptional = () => {
    setFilters((current) => ({ ...current, ...EMPTY_OPTIONAL_FILTERS }));
  };

  const handleRowClick = (item: ScrapRegistroItem) => {
    navigateScrap(buildRegistroDetailPath(branchRoute, item));
  };

  const handlePageSizeChange = (nextPageSize: number) => {
    setPageSize(nextPageSize);
    setPage(1);
  };

  const resumo = dashboard.data.resumo;
  const hasDashboardData = resumo !== null;
  const showInitialLoading = dashboard.loading && !hasDashboardData;
  const initialLoadingProgress = useLoadingProgress(
    showInitialLoading,
    dashboard.requestProgress,
  );

  const isEmpty =
    dashboard.state === "success" &&
    (resumo?.ocorrencias ?? 0) === 0 &&
    dashboard.data.motivos.length === 0;

  const dashboardError = dashboard.state === "error" ? dashboard.error : null;
  const permissionDenied = isPermissionError(dashboardError);
  const branchLabel = BRANCH_ROUTE_LABELS[branchRoute];
  const periodoLabel = resumo?.periodo
    ? `${formatDatePtBr(resumo.periodo.dataInicio)} — ${formatDatePtBr(resumo.periodo.dataFim)}`
    : `${formatDatePtBr(debouncedFilters.dataInicio)} — ${formatDatePtBr(debouncedFilters.dataFim)}`;

  return (
    <div className="dashboard-scrap-monitoring dashboard-page sm-page">
      <div className="sm-app-shell">
        <PageHeader
          title={`Acompanhamento de Refugos — ${branchLabel}`}
          subtitle={`Filial TOTVS ${totvsBranch} · ${periodoLabel}`}
        />

        <PeriodFilters
          filters={filters}
          options={filtrosOptions.data}
          optionsLoading={filtrosOptions.loading}
          validationError={periodError}
          loading={dashboard.loading || dashboard.refreshing}
          onChange={handleChange}
          onQuickRange={handleQuickRange}
          onClearOptional={handleClearOptional}
        />

        {exportError ? (
          <ErrorState
            title="Falha na exportação"
            message={exportError}
            actionLabel="Fechar"
            onAction={() => setExportError(null)}
          />
        ) : null}

        {permissionDenied ? (
          <ErrorState
            title="Sem permissão"
            message={dashboardError ?? "Sem permissão para esta filial."}
          />
        ) : null}

        {!permissionDenied && dashboardError ? (
          <ErrorState
            title="Falha ao carregar"
            message={dashboardError}
            actionLabel="Tentar novamente"
            onAction={dashboard.reload}
          />
        ) : null}

        {!permissionDenied && showInitialLoading ? (
          <LoadingActivityCard
            title="Carregando painel…"
            description={
              initialLoadingProgress > 0
                ? `${initialLoadingProgress}%`
                : "Consultando API de refugos"
            }
            variant="panel"
            progressPercent={initialLoadingProgress}
          />
        ) : null}

        {!permissionDenied && !showInitialLoading && isEmpty ? (
          <EmptyState
            title="Sem refugos no período"
            message="Não há registros de refugo (BC_TIPO = R) para os filtros selecionados."
          />
        ) : null}

        {!permissionDenied && !showInitialLoading && !isEmpty && hasDashboardData ? (
          <>
            <SummaryCards resumo={resumo} loading={dashboard.refreshing} />
            <RankingCharts
              motivos={dashboard.data.motivos}
              serie={dashboard.data.serie}
              serieGranularity={dashboard.data.serieGranularity}
              materiais={dashboard.data.materiais}
              produtos={dashboard.data.produtos}
              centros={dashboard.data.centros}
              colaboradores={dashboard.data.colaboradores}
            />
            {registros.error ? (
              <ErrorState
                title="Falha ao carregar registros"
                message={registros.error}
                actionLabel="Tentar novamente"
                onAction={registros.reload}
              />
            ) : appliedFilters ? (
              <RegistrosTable
                items={registros.data?.items ?? []}
                filters={appliedFilters}
                loading={registros.loading}
                refreshing={registros.loading && Boolean(registros.data)}
                page={registros.data?.page ?? page}
                pageSize={registros.data?.pageSize ?? pageSize}
                total={registros.data?.total ?? 0}
                onPageChange={setPage}
                onPageSizeChange={handlePageSizeChange}
                onRowClick={handleRowClick}
                onExportError={setExportError}
              />
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}
