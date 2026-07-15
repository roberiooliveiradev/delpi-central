import { useMemo, useState } from "react";

import { AppointmentsTables } from "../components/AppointmentsTables";
import { FiltersBar, type QuickRangePreset } from "../components/FiltersBar";
import { PageHeader } from "../components/PageHeader";
import { SeriesChart } from "../components/SeriesChart";
import { EmptyState, ErrorState, LoadingState } from "../components/StateBoxes";
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
  const initialLoadingPercent = useLoadingProgress(
    showInitialLoading,
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

      {showInitialLoading ? (
        <LoadingState
          title="Carregando apontamentos…"
          message={
            initialLoadingPercent > 0
              ? `${initialLoadingPercent}%`
              : "Consultando api-delpi"
          }
        />
      ) : null}

      {dashboardError ? (
        <ErrorState
          title={permissionDenied ? "Sem permissão" : "Falha ao carregar"}
          message={dashboardError}
        />
      ) : null}

      {isEmpty ? (
        <EmptyState
          title="Sem apontamentos"
          message="Não há apontamentos de produção no período e filtros selecionados."
        />
      ) : null}

      {summary ? (
        <>
          <SummaryCards totals={summary.totals} />
          <SeriesChart points={dashboard.data.series?.points ?? []} />
          <WorkCenterSummaryTable items={summary.items} />
          <AppointmentsTables
            appointments={tables.list?.items ?? []}
            byOp={tables.byOp?.items ?? []}
            listPagination={tables.list?.pagination ?? null}
            byOpPagination={tables.byOp?.pagination ?? null}
            listPage={listPage}
            byOpPage={byOpPage}
            onListPageChange={setListPage}
            onByOpPageChange={setByOpPage}
          />
        </>
      ) : null}

      {tables.error ? (
        <ErrorState title="Falha nas tabelas" message={tables.error} />
      ) : null}
    </div>
  );
}
