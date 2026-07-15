import { useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";

import type { AppointmentRow } from "../types/appointments";
import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS, totvsBranchFromRoute } from "../constants/branches";
import { buildOpDetailPath } from "../constants/routes";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useAppointmentsDetailQuery } from "../hooks/useAppointmentsDetailQuery";
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

type CtDetailPageProps = {
  branchRoute: BranchRouteCode;
  workCenter: string;
};

function isInspection(value: number | boolean | undefined): boolean {
  return value === true || value === 1;
}

export function CtDetailPage({ branchRoute, workCenter }: CtDetailPageProps) {
  const totvsBranch = totvsBranchFromRoute(branchRoute);
  const query = useAppointmentsDetailQuery({
    totvsBranch,
    locked: { workCenter },
  });
  const [exporting, setExporting] = useState(false);

  const ctSummary =
    query.summaryItems.find(
      (row) => row.work_center.trim().toUpperCase() === workCenter.trim().toUpperCase(),
    ) ??
    query.summaryItems[0] ??
    null;

  const ctName =
    ctSummary?.work_center_name ||
    query.appointments[0]?.work_center_name ||
    "";

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
        render: (row) =>
          `${row.product}${row.product_type ? ` (${row.product_type})` : ""}`,
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

  const handleOpenOp = (productionOrder: string) => {
    navigateAppointments(
      buildOpDetailPath(branchRoute, productionOrder, query.period),
    );
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
          hiddenFields={["workCenter"]}
          onChange={query.handleFiltersChange}
          onQuickRange={query.handleQuickRange}
        />

        <DetailCard
          title={`CT ${workCenter}${ctName ? ` — ${ctName}` : ""}`}
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
              title="Carregando detalhe do CT"
              description="Consultando resumo, série e apontamentos do centro de trabalho."
            />
          ) : null}

          {query.error ? <ErrorState message={query.error} /> : null}

          {!query.loading && !query.error && !hasData ? (
            <EmptyState message="Nenhum apontamento encontrado para este CT no período." />
          ) : null}

          {!query.loading && !query.error && hasData ? (
            <>
              <DetailFieldGrid
                fields={[
                  { label: "CT", value: workCenter },
                  { label: "Nome", value: ctName || "—" },
                  {
                    label: "Inspeção final",
                    value: isInspection(ctSummary?.is_final_inspection) ? "Sim" : "Não",
                  },
                  {
                    label: "Apontamentos",
                    value: formatInteger(
                      ctSummary?.appointment_count ?? query.appointments.length,
                    ),
                  },
                  {
                    label: "OPs",
                    value: formatInteger(ctSummary?.op_count ?? query.byOpRows.length),
                  },
                  {
                    label: "Produzida",
                    value: formatQuantity(
                      ctSummary?.qty_produced ?? query.totals?.qty_produced,
                    ),
                  },
                  {
                    label: "Perdida",
                    value: formatQuantity(ctSummary?.qty_lost ?? query.totals?.qty_lost),
                  },
                ]}
              />
              {query.totals ? <SummaryCards totals={query.totals} /> : null}
              <SeriesChart points={query.seriesPoints} />
              <DataTableSection
                columnPreferencesKey="production-appointments:CtDetailPage:apontamentos-do-ct:v1"
                title="Apontamentos do CT"
                titleHint={PA_HELP_TOOLTIPS.tables.ctDetailAppointments}
                columns={columns}
                rows={query.appointments}
                rowKey={(row) => String(row.appointment_id)}
                defaultSortKey="appointment_date"
                defaultSortDirection="desc"
                onRowClick={(row) => handleOpenOp(row.production_order)}
              />
            </>
          ) : null}
        </DetailCard>
      </div>
    </div>
  );
}
