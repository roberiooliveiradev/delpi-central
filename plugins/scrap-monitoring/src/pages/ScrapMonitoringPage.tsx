import { useMemo, useState } from "react";

import { PageHeader } from "../components/PageHeader";
import { PeriodFilters, type QuickRangePreset } from "../components/PeriodFilters";
import { RankingCharts } from "../components/RankingCharts";
import { RegistrosTable } from "../components/RegistrosTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { SummaryCards } from "../components/SummaryCards";
import {
  BRANCH_ROUTE_LABELS,
  branchRouteFromPathname,
  totvsBranchFromRoute,
  type BranchRouteCode,
} from "../constants/branches";
import { useScrapDashboard } from "../hooks/useScrapDashboard";
import { useScrapFiltros } from "../hooks/useScrapFiltros";
import { useScrapRegistros } from "../hooks/useScrapRegistros";
import type { FilterFormState } from "../types/scrap";
import {
  createDefaultFilterFormState,
  filtersFromFormState,
  getDefaultLast12MonthsRange,
  getDefaultLast6MonthsRange,
  getThisMonthRange,
  validatePeriodRange,
} from "../utils/dateRange";
import { formatDatePtBr } from "../utils/formatters";
import { useLoadingProgress } from "../utils/loadingProgress";

const EMPTY_OPTIONAL_FILTERS = {
  mp: "",
  pa: "",
  op: "",
  motivo: "",
  centroTrabalho: "",
} as const;

type ScrapMonitoringPageProps = {
  pathname?: string;
};

function isPermissionError(message: string | null): boolean {
  if (!message) return false;
  return /sem permissão|403|forbidden|sessão expirada/i.test(message);
}

export function ScrapMonitoringPage({ pathname }: ScrapMonitoringPageProps) {
  const branchRoute = branchRouteFromPathname(pathname);
  const totvsBranch = totvsBranchFromRoute(branchRoute);

  return (
    <ScrapMonitoringContent
      key={totvsBranch}
      branchRoute={branchRoute}
      totvsBranch={totvsBranch}
    />
  );
}

type ContentProps = {
  branchRoute: BranchRouteCode;
  totvsBranch: string;
};

function ScrapMonitoringContent({ branchRoute, totvsBranch }: ContentProps) {
  const defaultFilters = useMemo(() => createDefaultFilterFormState(), []);
  const [draftFilters, setDraftFilters] = useState<FilterFormState>(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState(() =>
    filtersFromFormState(totvsBranch, defaultFilters),
  );
  const [validationError, setValidationError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const dashboard = useScrapDashboard(appliedFilters);
  const registros = useScrapRegistros(appliedFilters, page);
  const filtrosOptions = useScrapFiltros(appliedFilters);

  const handleApplyPeriod = () => {
    const error = validatePeriodRange(draftFilters.dataInicio, draftFilters.dataFim);
    if (error) {
      setValidationError(error);
      return;
    }
    setValidationError(null);
    setAppliedFilters(filtersFromFormState(totvsBranch, draftFilters));
    setPage(1);
  };

  const applyFilterRange = (range: Pick<FilterFormState, "dataInicio" | "dataFim">) => {
    setDraftFilters((current) => {
      const next = { ...current, ...range };
      setAppliedFilters(filtersFromFormState(totvsBranch, next));
      return next;
    });
    setValidationError(null);
    setPage(1);
  };

  const handleQuickRange = (preset: QuickRangePreset) => {
    const referenceDate = new Date();
    const range =
      preset === "12m"
        ? getDefaultLast12MonthsRange(referenceDate)
        : preset === "6m"
          ? getDefaultLast6MonthsRange(referenceDate)
          : getThisMonthRange(referenceDate);
    applyFilterRange(range);
  };

  const handleClearOptional = () => {
    setDraftFilters((current) => {
      const next = { ...current, ...EMPTY_OPTIONAL_FILTERS };
      setAppliedFilters(filtersFromFormState(totvsBranch, next));
      return next;
    });
    setValidationError(null);
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
    : `${formatDatePtBr(appliedFilters.dataInicio)} — ${formatDatePtBr(appliedFilters.dataFim)}`;

  return (
    <div className="dashboard-scrap-monitoring dashboard-page sm-page">
      <PageHeader
        title={`Acompanhamento de Refugos — ${branchLabel}`}
        subtitle={`Filial TOTVS ${totvsBranch} · ${periodoLabel}`}
      />

      <PeriodFilters
        filters={draftFilters}
        options={filtrosOptions.data}
        optionsLoading={filtrosOptions.loading}
        validationError={validationError}
        loading={dashboard.loading || dashboard.refreshing}
        onChange={(patch) => setDraftFilters((current) => ({ ...current, ...patch }))}
        onApply={handleApplyPeriod}
        onQuickRange={handleQuickRange}
        onClearOptional={handleClearOptional}
      />

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
          ) : (
            <RegistrosTable
              items={registros.data?.items ?? []}
              loading={registros.loading}
              page={registros.data?.page ?? page}
              pageSize={registros.data?.pageSize ?? 50}
              totalPages={registros.data?.totalPages ?? 1}
              total={registros.data?.total ?? 0}
              onPageChange={setPage}
            />
          )}
        </>
      ) : null}
    </div>
  );
}
