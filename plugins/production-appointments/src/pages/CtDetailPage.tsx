import { useEffect, useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";

import {
  fetchAllAppointments,
  fetchAppointmentsByOp,
  fetchAppointmentsSummary,
} from "../api/appointmentsApi";
import type {
  AppointmentRow,
  AppointmentsQueryFilters,
  ByOpRow,
  WorkCenterSummaryRow,
} from "../types/appointments";
import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS, totvsBranchFromRoute } from "../constants/branches";
import { buildOpDetailPath, readDetailPeriodFromUrl } from "../constants/routes";
import { createDefaultFilterFormState } from "../utils/dateRange";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
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
import { LoadingActivityCard } from "../components/LoadingActivityCard";
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
  const defaults = useMemo(() => createDefaultFilterFormState(), []);
  const period = readDetailPeriodFromUrl() ?? {
    dateStart: defaults.dateStart,
    dateEnd: defaults.dateEnd,
  };

  const filters = useMemo<AppointmentsQueryFilters>(
    () => ({
      branch: totvsBranch,
      dateStart: period.dateStart,
      dateEnd: period.dateEnd,
      workCenter,
    }),
    [totvsBranch, period.dateStart, period.dateEnd, workCenter],
  );

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [appointments, setAppointments] = useState<AppointmentRow[]>([]);
  const [byOpRows, setByOpRows] = useState<ByOpRow[]>([]);
  const [ctSummary, setCtSummary] = useState<WorkCenterSummaryRow | null>(null);
  const [totals, setTotals] = useState<Awaited<
    ReturnType<typeof fetchAppointmentsSummary>
  >["totals"] | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    async function run() {
      try {
        setLoading(true);
        setError(null);
        const [items, byOp, summary] = await Promise.all([
          fetchAllAppointments(filters, { signal: controller.signal }),
          fetchAppointmentsByOp(filters, 1, 200, { signal: controller.signal }),
          fetchAppointmentsSummary(filters, { signal: controller.signal }),
        ]);
        setAppointments(items);
        setByOpRows(byOp.items);
        const match =
          summary.items.find(
            (row) => row.work_center.trim().toUpperCase() === workCenter.trim().toUpperCase(),
          ) ??
          summary.items[0] ??
          null;
        setCtSummary(match);
        setTotals(summary.totals);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar detalhe do CT.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void run();
    return () => controller.abort();
  }, [filters, workCenter]);

  const ctName =
    ctSummary?.work_center_name ||
    appointments[0]?.work_center_name ||
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
    setExporting(true);
    try {
      await exportAppointmentsExcel(appointments, filters);
    } finally {
      setExporting(false);
    }
  };

  const handleOpenOp = (productionOrder: string) => {
    navigateAppointments(
      buildOpDetailPath(branchRoute, productionOrder, {
        dateStart: period.dateStart,
        dateEnd: period.dateEnd,
      }),
    );
  };

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

        <DetailCard
          title={`CT ${workCenter}${ctName ? ` — ${ctName}` : ""}`}
          hint={`Apontamento de Produção — ${BRANCH_ROUTE_LABELS[branchRoute]} · Filial TOTVS ${totvsBranch} · ${formatDatePtBr(period.dateStart)} — ${formatDatePtBr(period.dateEnd)}`}
          headerActions={
            <ExportExcelButton
              disabled={appointments.length === 0}
              exporting={exporting}
              onExport={handleExport}
            />
          }
        >
          {loading ? (
            <LoadingActivityCard
              title="Carregando detalhe do CT"
              description="Consultando apontamentos filtrados pelo centro de trabalho."
            />
          ) : null}

          {error ? <ErrorState message={error} /> : null}

          {!loading && !error && appointments.length === 0 ? (
            <EmptyState message="Nenhum apontamento encontrado para este CT no período." />
          ) : null}

          {!loading && !error && appointments.length > 0 ? (
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
                      ctSummary?.appointment_count ?? appointments.length,
                    ),
                  },
                  {
                    label: "OPs",
                    value: formatInteger(ctSummary?.op_count ?? byOpRows.length),
                  },
                  {
                    label: "Produzida",
                    value: formatQuantity(ctSummary?.qty_produced ?? totals?.qty_produced),
                  },
                  {
                    label: "Perdida",
                    value: formatQuantity(ctSummary?.qty_lost ?? totals?.qty_lost),
                  },
                ]}
              />
              {totals ? <SummaryCards totals={totals} /> : null}
              <DataTableSection
                columnPreferencesKey="production-appointments:CtDetailPage:apontamentos-do-ct:v1"
                title="Apontamentos do CT"
                titleHint={PA_HELP_TOOLTIPS.tables.ctDetailAppointments}
                columns={columns}
                rows={appointments}
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
