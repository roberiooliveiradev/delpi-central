import { useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";

import type { AppointmentRow } from "../types/appointments";
import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS, totvsBranchFromRoute } from "../constants/branches";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useAppointmentsDetailQuery } from "../hooks/useAppointmentsDetailQuery";
import {
  formatDatePtBr,
  formatInteger,
  formatProtheusDate,
  formatQuantity,
} from "../utils/formatters";
import { exportAppointmentsExcel } from "../utils/exportTables";
import { navigateAppointmentsBack } from "../utils/navigation";
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

  const columns = useMemo<DataTableColumn<AppointmentRow>[]>(
    () => [
      {
        key: "appointment_date",
        header: "Data",
        headerHint: PA_HELP_TOOLTIPS.columns.appointmentDate,
        sortable: true,
        sortValue: (row) => row.appointment_date,
        render: (row) => formatProtheusDate(row.appointment_date),
      },
      {
        key: "product",
        header: "Produto",
        headerHint: PA_HELP_TOOLTIPS.columns.product,
        sortable: true,
        sortValue: (row) => row.product,
        render: (row) =>
          `${row.product}${row.product_type ? ` (${row.product_type})` : ""}`,
      },
      {
        key: "work_center",
        header: "CT",
        headerHint: PA_HELP_TOOLTIPS.columns.workCenter,
        sortable: true,
        sortValue: (row) => row.work_center,
        render: (row) =>
          `${row.work_center}${row.work_center_name ? ` — ${row.work_center_name}` : ""}`,
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
        key: "qty_lost",
        header: "Perdida",
        headerHint: PA_HELP_TOOLTIPS.columns.qtyLost,
        sortable: true,
        sortValue: (row) => row.qty_lost,
        className: "pa-table__col--numeric",
        render: (row) => formatQuantity(row.qty_lost),
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

  const hasData = query.appointments.length > 0;

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
              description="Consultando resumo, série e apontamentos da ordem de produção."
            />
          ) : null}

          {query.error ? <ErrorState message={query.error} /> : null}

          {!query.loading && !query.error && !hasData ? (
            <EmptyState message="Nenhum apontamento encontrado para esta OP no período." />
          ) : null}

          {!query.loading && !query.error && hasData ? (
            <>
              <DetailFieldGrid
                fields={[
                  { label: "OP", value: productionOrder },
                  {
                    label: "Produto",
                    value: opSummary
                      ? `${opSummary.product}${opSummary.product_type ? ` (${opSummary.product_type})` : ""}`
                      : query.appointments[0]?.product || "—",
                  },
                  {
                    label: "Apontamentos",
                    value: formatInteger(
                      opSummary?.appointment_count ?? query.appointments.length,
                    ),
                  },
                  {
                    label: "CTs",
                    value: formatInteger(opSummary?.work_center_count ?? 0),
                  },
                  {
                    label: "Produzida",
                    value: formatQuantity(
                      opSummary?.qty_produced ?? query.totals?.qty_produced,
                    ),
                  },
                  {
                    label: "Perdida",
                    value: formatQuantity(opSummary?.qty_lost ?? query.totals?.qty_lost),
                  },
                ]}
              />
              {query.totals ? <SummaryCards totals={query.totals} /> : null}
              <SeriesChart points={query.seriesPoints} />
              <DataTableSection
                columnPreferencesKey="production-appointments:OpDetailPage:apontamentos-da-op:v1"
                title="Apontamentos da OP"
                columns={columns}
                rows={query.appointments}
                rowKey={(row) => String(row.appointment_id)}
                defaultSortKey="appointment_date"
                defaultSortDirection="desc"
              />
            </>
          ) : null}
        </DetailCard>
      </div>
    </div>
  );
}
