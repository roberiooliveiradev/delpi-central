import { useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";

import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS, totvsBranchFromRoute } from "../constants/branches";
import { buildOpDetailPath } from "../constants/routes";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useAppointmentsDetailQuery } from "../hooks/useAppointmentsDetailQuery";
import type { ByOpRow } from "../types/appointments";
import { buildAppointmentListColumns } from "../utils/appointmentListColumns";
import {
  formatDatePtBr,
  formatInteger,
  formatProtheusDate,
  formatQuantity,
} from "../utils/formatters";
import { exportAppointmentsExcel } from "../utils/exportTables";
import { navigateAppointments, navigateAppointmentsBack } from "../utils/navigation";
import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { DataTableSection, type DataTableColumn } from "../components/dataTableUi";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { ExportExcelButton } from "../components/ExportExcelButton";
import { FiltersBar } from "../components/FiltersBar";
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { SeriesChart } from "../components/SeriesChart";
import { SummaryCards } from "../components/SummaryCards";

type OpDetailPageProps = {
  branchRoute: BranchRouteCode;
  productionOrder: string;
};

export function OpDetailPage({ branchRoute, productionOrder }: OpDetailPageProps) {
  const totvsBranch = totvsBranchFromRoute(branchRoute);
  const query = useAppointmentsDetailQuery({
    totvsBranch,
    locked: { op: productionOrder },
  });
  const [exporting, setExporting] = useState(false);

  const opSummary = query.byOpRows[0] ?? null;

  const columns = useMemo(
    () =>
      buildAppointmentListColumns({
        includeProductionOrder: false,
        includeWorkCenter: true,
      }),
    [],
  );

  const childOpColumns = useMemo<DataTableColumn<ByOpRow>[]>(
    () => [
      {
        key: "production_order",
        header: "OP",
        headerHint: PA_HELP_TOOLTIPS.columns.productionOrder,
        sortable: true,
        sortValue: (row) => row.production_order,
        render: (row) => row.production_order,
      },
      {
        key: "product",
        header: "Produto",
        headerHint: PA_HELP_TOOLTIPS.columns.product,
        sortable: true,
        sortValue: (row) => row.product,
        className: "pa-table__col--wide",
        render: (row) =>
          `${row.product}${row.product_type ? ` (${row.product_type})` : ""}`,
      },
      {
        key: "appointment_count",
        header: "Apont.",
        headerHint: PA_HELP_TOOLTIPS.columns.appointmentCount,
        sortable: true,
        sortValue: (row) => row.appointment_count,
        className: "pa-table__col--numeric",
        render: (row) => formatInteger(row.appointment_count),
      },
      {
        key: "work_center_count",
        header: "CTs",
        headerHint: PA_HELP_TOOLTIPS.columns.workCenterCount,
        sortable: true,
        sortValue: (row) => row.work_center_count,
        className: "pa-table__col--numeric",
        render: (row) => formatInteger(row.work_center_count),
      },
      {
        key: "qty_produced",
        header: "Produzida",
        headerHint: PA_HELP_TOOLTIPS.columns.qtyProduced,
        sortable: true,
        sortValue: (row) => row.qty_produced,
        className: "pa-table__col--numeric",
        render: (row) => formatQuantity(row.qty_produced),
      },
      {
        key: "period",
        header: "Período",
        headerHint: PA_HELP_TOOLTIPS.columns.period,
        sortable: true,
        sortValue: (row) => row.first_date,
        render: (row) =>
          `${formatProtheusDate(row.first_date)} — ${formatProtheusDate(row.last_date)}`,
      },
    ],
    [],
  );

  const handleExport = async () => {
    if (!query.appliedFilters) return;
    setExporting(true);
    try {
      await exportAppointmentsExcel(query.appointments, query.appliedFilters);
    } finally {
      setExporting(false);
    }
  };

  const handleOpenChildOp = (childOp: string) => {
    navigateAppointments(buildOpDetailPath(branchRoute, childOp, query.period));
  };

  const hasData = query.appointments.length > 0;
  const hasChildOps = query.childOpRows.length > 0;
  const showContent = hasData || hasChildOps;

  return (
    <div className="dashboard-production-appointments dashboard-page pa-page pa-detail-page">
      <div className="pa-page-shell">
        <div className="pa-detail-toolbar">
          <button
            type="button"
            className="pa-btn pa-btn--secondary"
            onClick={() => navigateAppointmentsBack(branchRoute)}
          >
            <ArrowLeft size={16} aria-hidden />
            Voltar
          </button>
        </div>

        <FiltersBar
          filters={query.draftFilters}
          workCenters={query.workCenters}
          validationError={query.validationError}
          loading={query.loading}
          hiddenFields={["op"]}
          onChange={query.handleFiltersChange}
          onQuickRange={query.handleQuickRange}
        />

        <DetailCard
          title={`OP ${productionOrder}`}
          hint={`Apontamento de Produção — ${BRANCH_ROUTE_LABELS[branchRoute]} · Filial TOTVS ${totvsBranch} · ${formatDatePtBr(query.period.dateStart)} — ${formatDatePtBr(query.period.dateEnd)}`}
          headerActions={
            <ExportExcelButton
              disabled={!hasData}
              exporting={exporting}
              onExport={handleExport}
            />
          }
        >
          {query.loading ? (
            <LoadingActivityCard
              title="Carregando detalhe da OP"
              description="Consultando resumo, série, apontamentos e OPs filhas."
            />
          ) : null}

          {query.error ? <ErrorState message={query.error} /> : null}

          {!query.loading && !query.error && !showContent ? (
            <EmptyState message="Nenhum apontamento encontrado para esta OP no período." />
          ) : null}

          {!query.loading && !query.error && showContent ? (
            <>
              {hasData ? (
                <>
                  <DetailFieldGrid
                    fields={[
                      {
                        label: "Produto",
                        value: opSummary
                          ? `${opSummary.product}${opSummary.product_type ? ` (${opSummary.product_type})` : ""}`
                          : query.appointments[0]?.product || "—",
                      },
                    ]}
                  />
                  {query.totals ? (
                    <SummaryCards totals={query.totals} omitKeys={["opCount"]} />
                  ) : null}
                  <SeriesChart points={query.seriesPoints} />
                  <DataTableSection
                    columnPreferencesKey="production-appointments:OpDetailPage:apontamentos-da-op:v2"
                    title="Apontamentos da OP"
                    titleHint={PA_HELP_TOOLTIPS.tables.appointments}
                    columns={columns}
                    rows={query.appointments}
                    rowKey={(row) => String(row.appointment_id)}
                    defaultSortKey="appointment_datetime"
                    defaultSortDirection="desc"
                  />
                </>
              ) : null}
              <DataTableSection
                columnPreferencesKey="production-appointments:OpDetailPage:ops-filhas:v1"
                title="OPs filhas"
                titleHint={PA_HELP_TOOLTIPS.tables.childOps}
                columns={childOpColumns}
                rows={query.childOpRows}
                rowKey={(row) => `${row.production_order}-${row.product}`}
                defaultSortKey="production_order"
                defaultSortDirection="asc"
                onRowClick={(row) => handleOpenChildOp(row.production_order)}
                emptyMessage="Nenhuma OP filha com apontamento no período."
              />
            </>
          ) : null}
        </DetailCard>
      </div>
    </div>
  );
}
