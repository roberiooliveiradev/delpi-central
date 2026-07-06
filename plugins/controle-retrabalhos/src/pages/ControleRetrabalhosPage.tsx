import { useMemo, useState } from "react";

import { DetalhesTable } from "../components/DetalhesTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PeriodFilters, type QuickRangePreset } from "../components/PeriodFilters";
import { RetrabalhoCharts } from "../components/RetrabalhoCharts";
import { SummaryCards } from "../components/SummaryCards";
import {
  BRANCH_ROUTE_LABELS,
  branchRouteFromPathname,
  totvsBranchFromRoute,
  type BranchRouteCode,
} from "../constants/branches";
import { useRetrabalhoDashboard } from "../hooks/useRetrabalhoDashboard";
import { useRetrabalhoDetalhes } from "../hooks/useRetrabalhoDetalhes";
import type { FilterFormState } from "../types/retrabalho";
import {
  createDefaultFilterFormState,
  filtersFromFormState,
  getDefaultLast6MonthsRange,
  getThisMonthRange,
  validatePeriodRange,
} from "../utils/dateRange";
import { formatDatePtBr } from "../utils/formatters";

type ControleRetrabalhosPageProps = {
  pathname?: string;
};

function isPermissionError(message: string | null): boolean {
  if (!message) return false;
  return /sem permissão|403|forbidden|sessão expirada/i.test(message);
}

export function ControleRetrabalhosPage({ pathname }: ControleRetrabalhosPageProps) {
  const branchRoute = branchRouteFromPathname(pathname);
  const totvsBranch = totvsBranchFromRoute(branchRoute);

  return (
    <ControleRetrabalhosContent
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

function ControleRetrabalhosContent({ branchRoute, totvsBranch }: ContentProps) {
  const defaultFilters = useMemo(() => createDefaultFilterFormState(), []);
  const [draftFilters, setDraftFilters] = useState<FilterFormState>(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState(() =>
    filtersFromFormState(totvsBranch, defaultFilters),
  );
  const [validationError, setValidationError] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  const dashboard = useRetrabalhoDashboard(appliedFilters);
  const detalhes = useRetrabalhoDetalhes(appliedFilters, page);

  const handleApplyPeriod = () => {
    const error = validatePeriodRange(draftFilters.dataInicio, draftFilters.dataFim);
    if (error) {
      setValidationError(error);
      return;
    }
    setValidationError(null);
    setExportError(null);
    setAppliedFilters(filtersFromFormState(totvsBranch, draftFilters));
    setPage(1);
  };

  const applyFilterRange = (range: FilterFormState) => {
    setDraftFilters(range);
    setValidationError(null);
    setExportError(null);
    setAppliedFilters(filtersFromFormState(totvsBranch, range));
    setPage(1);
  };

  const handleQuickRange = (preset: QuickRangePreset) => {
    const referenceDate = new Date();
    const range =
      preset === "12m"
        ? createDefaultFilterFormState(referenceDate)
        : preset === "6m"
          ? getDefaultLast6MonthsRange(referenceDate)
          : getThisMonthRange(referenceDate);
    applyFilterRange(range);
  };

  const showInitialLoading = dashboard.isLoading && !dashboard.data.resumo;
  const resumo = dashboard.data.resumo;
  const isEmpty =
    dashboard.state === "success" &&
    (resumo?.totalApontamentos ?? 0) === 0 &&
    dashboard.data.mensal.length === 0;

  const dashboardError = dashboard.state === "error" ? dashboard.error : null;
  const permissionDenied = isPermissionError(dashboardError);

  return (
    <div className="dashboard-controle-retrabalhos cr-page">
      <header className="cr-page__header">
        <div>
          <h1 className="cr-page__title">Controle de Retrabalhos</h1>
          <p className="cr-page__subtitle">
            Filial {BRANCH_ROUTE_LABELS[branchRoute]} ({totvsBranch})
            {resumo?.periodo ? (
              <> · {formatDatePtBr(resumo.periodo.dataInicio)} a {formatDatePtBr(resumo.periodo.dataFim)}</>
            ) : null}
          </p>
        </div>
      </header>

      <PeriodFilters
        filters={draftFilters}
        validationError={validationError}
        loading={dashboard.isLoading || detalhes.isLoading}
        onChange={(patch) => setDraftFilters((current) => ({ ...current, ...patch }))}
        onApply={handleApplyPeriod}
        onQuickRange={handleQuickRange}
      />

      {permissionDenied ? (
        <ErrorState message={dashboardError ?? "Sem permissão para acessar este painel."} />
      ) : null}

      {!permissionDenied && dashboardError ? (
        <ErrorState message={dashboardError} onRetry={dashboard.reload} />
      ) : null}

      {showInitialLoading ? <LoadingState message="Carregando painel…" /> : null}

      {!showInitialLoading && !dashboardError && isEmpty ? <EmptyState /> : null}

      {!showInitialLoading && !dashboardError && !isEmpty ? (
        <>
          <SummaryCards resumo={resumo} loading={dashboard.isLoading} />

          <RetrabalhoCharts
            mensal={dashboard.data.mensal}
            recursos={dashboard.data.recursos}
            colaboradores={dashboard.data.colaboradores}
          />

          {detalhes.state === "error" && !isPermissionError(detalhes.error) ? (
            <ErrorState message={detalhes.error ?? "Falha ao carregar detalhes."} onRetry={detalhes.reload} />
          ) : null}

          {exportError ? (
            <ErrorState message={exportError} onRetry={() => setExportError(null)} />
          ) : null}

          {detalhes.state !== "error" || isPermissionError(detalhes.error) ? (
            <DetalhesTable
              data={detalhes.data}
              filters={appliedFilters}
              loading={detalhes.isLoading}
              onPageChange={setPage}
              onExportError={setExportError}
            />
          ) : null}
        </>
      ) : null}
    </div>
  );
}
