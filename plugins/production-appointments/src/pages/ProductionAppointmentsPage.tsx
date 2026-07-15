import { useMemo, useState } from "react";

import { AppointmentsTables } from "../components/AppointmentsTables";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { FiltersBar, type QuickRangePreset } from "../components/FiltersBar";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { PageHeader } from "../components/PageHeader";
import { SeriesChart } from "../components/SeriesChart";
import { SummaryCards } from "../components/SummaryCards";
import { WorkCenterSummaryTable } from "../components/WorkCenterSummaryTable";
import {
  BRANCH_ROUTE_LABELS,
  branchRouteFromPathname,
  totvsBranchFromRoute,
  type BranchRouteCode,
} from "../constants/branches";
import { useAppointmentsDashboard } from "../hooks/useAppointmentsDashboard";
import { useAppointmentsTables } from "../hooks/useAppointmentsTables";
import type { FilterFormState } from "../types/appointments";
import {
  createDefaultFilterFormState,
  filtersFromFormState,
  getDefaultLast30DaysRange,
  getDefaultLast6MonthsRange,
  getThisMonthRange,
  validatePeriodRange,
} from "../utils/dateRange";
import { formatDatePtBr } from "../utils/formatters";
import { useLoadingProgress } from "../utils/loadingProgress";

type ProductionAppointmentsPageProps = {
  pathname?: string;
};

function isPermissionError(message: string | null): boolean {
  if (!message) return false;
  return /sem permissão|403|forbidden|sessão expirada/i.test(message);
}

export function ProductionAppointmentsPage({ pathname }: ProductionAppointmentsPageProps) {
  const branchRoute = branchRouteFromPathname(pathname);
  const totvsBranch = totvsBranchFromRoute(branchRoute);

  return (
    <ProductionAppointmentsContent
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

function ProductionAppointmentsContent({ branchRoute, totvsBranch }: ContentProps) {
  const defaultFilters = useMemo(() => createDefaultFilterFormState(), []);
  const [draftFilters, setDraftFilters] = useState<FilterFormState>(defaultFilters);
  const [appliedFilters, setAppliedFilters] = useState(() =>
    filtersFromFormState(totvsBranch, defaultFilters),
  );
  const [validationError, setValidationError] = useState<string | null>(null);
  const [listPage, setListPage] = useState(1);
  const [byOpPage, setByOpPage] = useState(1);

  const dashboard = useAppointmentsDashboard(appliedFilters);
  const tables = useAppointmentsTables(appliedFilters, listPage, byOpPage);

  const handleApply = () => {
    const error = validatePeriodRange(draftFilters.dateStart, draftFilters.dateEnd);
    if (error) {
      setValidationError(error);
      return;
    }
    setValidationError(null);
    setAppliedFilters(filtersFromFormState(totvsBranch, draftFilters));
    setListPage(1);
    setByOpPage(1);
  };

  const applyFilterRange = (range: Pick<FilterFormState, "dateStart" | "dateEnd">) => {
    const next = { ...draftFilters, ...range };
    setDraftFilters(next);
    setValidationError(null);
    setAppliedFilters(filtersFromFormState(totvsBranch, next));
    setListPage(1);
    setByOpPage(1);
  };

  const handleQuickRange = (preset: QuickRangePreset) => {
    const referenceDate = new Date();
    const range =
      preset === "6m"
        ? getDefaultLast6MonthsRange(referenceDate)
        : preset === "30d"
          ? getDefaultLast30DaysRange(referenceDate)
          : getThisMonthRange(referenceDate);
    applyFilterRange(range);
  };

  const summary = dashboard.data.summary;
  const hasDashboardData = summary !== null;
  const showInitialLoading = dashboard.loading && !hasDashboardData;
  const showRefreshLoading = dashboard.refreshing && hasDashboardData;
  const initialLoadingPercent = useLoadingProgress(
    showInitialLoading,
    dashboard.requestProgress,
  );
  const refreshLoadingPercent = useLoadingProgress(
    showRefreshLoading,
    dashboard.requestProgress,
  );

  const isEmpty =
    dashboard.state === "success" && (summary?.totals.appointment_count ?? 0) === 0;

  const dashboardError = dashboard.state === "error" ? dashboard.error : null;
  const permissionDenied = isPermissionError(dashboardError);
  const branchLabel = BRANCH_ROUTE_LABELS[branchRoute];
  const periodoLabel = `${formatDatePtBr(appliedFilters.dateStart)} — ${formatDatePtBr(appliedFilters.dateEnd)}`;

  return (
    <div className="dashboard-production-appointments dashboard-page pa-page">
      <PageHeader
        title={`Apontamento de Produção — ${branchLabel}`}
        subtitle={`Filial TOTVS ${totvsBranch} · Período ${periodoLabel}`}
        refreshing={dashboard.refreshing}
        onRefresh={() => {
          dashboard.reload();
          tables.reload();
        }}
      />

      <FiltersBar
        filters={draftFilters}
        workCenters={dashboard.data.workCenters}
        validationError={validationError}
        loading={dashboard.loading || dashboard.refreshing}
        onChange={(patch) => setDraftFilters((current) => ({ ...current, ...patch }))}
        onApply={handleApply}
        onQuickRange={handleQuickRange}
      />

      {permissionDenied ? (
        <ErrorState message={dashboardError ?? "Sem permissão para acessar este painel."} />
      ) : null}

      {!permissionDenied && dashboardError ? (
        <ErrorState
          message={dashboardError}
          onRetry={() => {
            dashboard.reload();
            tables.reload();
          }}
        />
      ) : null}

      {showRefreshLoading ? (
        <LoadingActivityCard
          title="Atualizando apontamentos"
          description="Recalculando resumo, série e rankings com o período selecionado."
          variant="compact"
          sticky
          progressPercent={refreshLoadingPercent}
        />
      ) : null}

      {showInitialLoading ? (
        <LoadingActivityCard
          title="Carregando apontamentos"
          description="Consultando resumo, centros de trabalho e série temporal na api-delpi."
          progressPercent={initialLoadingPercent}
        />
      ) : null}

      {!showInitialLoading && !dashboardError && isEmpty ? <EmptyState /> : null}

      {!showInitialLoading && !dashboardError && !isEmpty && summary ? (
        <>
          <SummaryCards totals={summary.totals} loading={dashboard.loading} />
          <SeriesChart points={dashboard.data.series?.points ?? []} />
          <WorkCenterSummaryTable items={summary.items} />
          <AppointmentsTables
            appointments={tables.list?.items ?? []}
            byOp={tables.byOp?.items ?? []}
            listPagination={tables.list?.pagination ?? null}
            byOpPagination={tables.byOp?.pagination ?? null}
            listPage={listPage}
            byOpPage={byOpPage}
            pageSize={tables.pageSize}
            onListPageChange={setListPage}
            onByOpPageChange={setByOpPage}
          />
        </>
      ) : null}

      {!permissionDenied && tables.error ? (
        <ErrorState message={tables.error} onRetry={tables.reload} />
      ) : null}
    </div>
  );
}
