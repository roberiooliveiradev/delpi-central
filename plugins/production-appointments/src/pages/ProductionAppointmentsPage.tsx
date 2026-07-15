import { useEffect, useMemo, useState } from "react";

import { AppointmentsTables } from "../components/AppointmentsTables";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { FiltersBar, type QuickRangePreset } from "../components/FiltersBar";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { PageHeader } from "../components/PageHeader";
import { SeriesChart } from "../components/SeriesChart";
import { SummaryCards } from "../components/SummaryCards";
import {
  BRANCH_ROUTE_LABELS,
  type BranchRouteCode,
} from "../constants/branches";
import { buildCtDetailPath, buildOpDetailPath } from "../constants/routes";
import { useAppointmentsDashboard } from "../hooks/useAppointmentsDashboard";
import { useAppointmentsTables } from "../hooks/useAppointmentsTables";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
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
import { navigateAppointments } from "../utils/navigation";

type ProductionAppointmentsPageProps = {
  branchRoute: BranchRouteCode;
  totvsBranch: string;
  isActive?: boolean;
};

function isPermissionError(message: string | null): boolean {
  if (!message) return false;
  return /sem permissão|403|forbidden|sessão expirada/i.test(message);
}

export function ProductionAppointmentsPage({
  branchRoute,
  totvsBranch,
  isActive = true,
}: ProductionAppointmentsPageProps) {
  return (
    <ProductionAppointmentsContent
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

function ProductionAppointmentsContent({
  branchRoute,
  totvsBranch,
  isActive,
}: ContentProps) {
  const defaultFilters = useMemo(() => createDefaultFilterFormState(), []);
  const [draftFilters, setDraftFilters] = useState<FilterFormState>(defaultFilters);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [listPage, setListPage] = useState(1);
  const [byOpPage, setByOpPage] = useState(1);
  const [listPageSize, setListPageSize] = useState(20);
  const [byOpPageSize, setByOpPageSize] = useState(20);

  const debouncedOp = useDebouncedValue(draftFilters.op, 350);
  const debouncedProduct = useDebouncedValue(draftFilters.product, 350);

  const autoFilters = useMemo(
    () => ({
      ...draftFilters,
      op: debouncedOp,
      product: debouncedProduct,
    }),
    [draftFilters, debouncedOp, debouncedProduct],
  );

  const appliedFilters = useMemo(() => {
    const error = validatePeriodRange(autoFilters.dateStart, autoFilters.dateEnd);
    if (error) return null;
    return filtersFromFormState(totvsBranch, autoFilters);
  }, [autoFilters, totvsBranch]);

  useEffect(() => {
    setValidationError(validatePeriodRange(draftFilters.dateStart, draftFilters.dateEnd));
  }, [draftFilters.dateStart, draftFilters.dateEnd]);

  useEffect(() => {
    setListPage(1);
    setByOpPage(1);
  }, [
    appliedFilters?.dateStart,
    appliedFilters?.dateEnd,
    appliedFilters?.workCenter,
    appliedFilters?.op,
    appliedFilters?.product,
    totvsBranch,
  ]);

  const dashboard = useAppointmentsDashboard(isActive ? appliedFilters : null);
  const tables = useAppointmentsTables(
    isActive ? appliedFilters : null,
    listPage,
    byOpPage,
    listPageSize,
    byOpPageSize,
  );

  const handleFiltersChange = (patch: Partial<FilterFormState>) => {
    setDraftFilters((current) => ({ ...current, ...patch }));
  };

  const handleQuickRange = (preset: QuickRangePreset) => {
    const referenceDate = new Date();
    const range =
      preset === "6m"
        ? getDefaultLast6MonthsRange(referenceDate)
        : preset === "30d"
          ? getDefaultLast30DaysRange(referenceDate)
          : getThisMonthRange(referenceDate);
    setDraftFilters((current) => ({ ...current, ...range }));
  };

  const handleOpenOp = (productionOrder: string) => {
    if (!appliedFilters) return;
    navigateAppointments(
      buildOpDetailPath(branchRoute, productionOrder, {
        dateStart: appliedFilters.dateStart,
        dateEnd: appliedFilters.dateEnd,
      }),
    );
  };

  const handleOpenCt = (workCenter: string) => {
    if (!appliedFilters) return;
    navigateAppointments(
      buildCtDetailPath(branchRoute, workCenter, {
        dateStart: appliedFilters.dateStart,
        dateEnd: appliedFilters.dateEnd,
      }),
    );
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
  const periodoLabel = appliedFilters
    ? `${formatDatePtBr(appliedFilters.dateStart)} — ${formatDatePtBr(appliedFilters.dateEnd)}`
    : "";

  return (
    <div
      className="dashboard-production-appointments dashboard-page pa-page"
      hidden={!isActive}
      aria-hidden={!isActive}
    >
      <div className="pa-page-shell">
      <PageHeader
        title={`Apontamento de Produção — ${branchLabel}`}
        subtitle={
          periodoLabel
            ? `Filial TOTVS ${totvsBranch} · Período ${periodoLabel}`
            : `Filial TOTVS ${totvsBranch}`
        }
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
        onChange={handleFiltersChange}
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

      {!showInitialLoading && !dashboardError && !isEmpty && summary && appliedFilters ? (
        <>
          <SummaryCards totals={summary.totals} loading={dashboard.loading} />
          <SeriesChart points={dashboard.data.series?.points ?? []} />
          <AppointmentsTables
            workCenters={summary.items}
            appointments={tables.list?.items ?? []}
            byOp={tables.byOp?.items ?? []}
            filters={appliedFilters}
            listTotal={tables.list?.pagination.total ?? 0}
            byOpTotal={tables.byOp?.pagination.total ?? 0}
            listPage={listPage}
            byOpPage={byOpPage}
            listPageSize={listPageSize}
            byOpPageSize={byOpPageSize}
            loading={tables.loading}
            workCentersLoading={dashboard.loading}
            onListPageChange={setListPage}
            onByOpPageChange={setByOpPage}
            onListPageSizeChange={setListPageSize}
            onByOpPageSizeChange={setByOpPageSize}
            onOpenOp={handleOpenOp}
            onOpenCt={handleOpenCt}
          />
        </>
      ) : null}

      {!permissionDenied && tables.error ? (
        <ErrorState message={tables.error} onRetry={tables.reload} />
      ) : null}
      </div>
    </div>
  );
}
