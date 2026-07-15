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
} from "../types/appointments";
import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS, totvsBranchFromRoute } from "../constants/branches";
import { readDetailPeriodFromUrl } from "../constants/routes";
import { createDefaultFilterFormState } from "../utils/dateRange";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
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
import { LoadingActivityCard } from "../components/LoadingActivityCard";
import { SummaryCards } from "../components/SummaryCards";

type OpDetailPageProps = {
  branchRoute: BranchRouteCode;
  productionOrder: string;
};

export function OpDetailPage({ branchRoute, productionOrder }: OpDetailPageProps) {
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
      op: productionOrder,
    }),
    [totvsBranch, period.dateStart, period.dateEnd, productionOrder],
  );

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [appointments, setAppointments] = useState<AppointmentRow[]>([]);
  const [opSummary, setOpSummary] = useState<ByOpRow | null>(null);
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
          fetchAppointmentsByOp(filters, 1, 20, { signal: controller.signal }),
          fetchAppointmentsSummary(filters, { signal: controller.signal }),
        ]);
        setAppointments(items);
        setOpSummary(byOp.items[0] ?? null);
        setTotals(summary.totals);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Falha ao carregar detalhe da OP.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void run();
    return () => controller.abort();
  }, [filters]);

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
    setExporting(true);
    try {
      await exportAppointmentsExcel(appointments, filters);
    } finally {
      setExporting(false);
    }
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
        title={`OP ${productionOrder}`}
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
            title="Carregando detalhe da OP"
            description="Consultando apontamentos filtrados pela ordem de produção."
          />
        ) : null}

        {error ? <ErrorState message={error} /> : null}

        {!loading && !error && appointments.length === 0 ? (
          <EmptyState message="Nenhum apontamento encontrado para esta OP no período." />
        ) : null}

        {!loading && !error && appointments.length > 0 ? (
          <>
            <DetailFieldGrid
              fields={[
                { label: "OP", value: productionOrder },
                {
                  label: "Produto",
                  value: opSummary
                    ? `${opSummary.product}${opSummary.product_type ? ` (${opSummary.product_type})` : ""}`
                    : appointments[0]?.product || "—",
                },
                {
                  label: "Apontamentos",
                  value: formatInteger(opSummary?.appointment_count ?? appointments.length),
                },
                {
                  label: "CTs",
                  value: formatInteger(opSummary?.work_center_count ?? 0),
                },
                {
                  label: "Produzida",
                  value: formatQuantity(opSummary?.qty_produced ?? totals?.qty_produced),
                },
                {
                  label: "Perdida",
                  value: formatQuantity(opSummary?.qty_lost ?? totals?.qty_lost),
                },
              ]}
            />
            {totals ? <SummaryCards totals={totals} /> : null}
            <DataTableSection
              title="Apontamentos da OP"
              columns={columns}
              rows={appointments}
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
