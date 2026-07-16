import { useMemo, useState } from "react";
import { ArrowLeft } from "lucide-react";

import type { BranchRouteCode } from "../constants/branches";
import { BRANCH_ROUTE_LABELS, totvsBranchFromRoute } from "../constants/branches";
import { buildOpDetailPath } from "../constants/routes";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useAppointmentsDetailQuery } from "../hooks/useAppointmentsDetailQuery";
import { buildAppointmentListColumns } from "../utils/appointmentListColumns";
import {
  formatDatePtBr,
} from "../utils/formatters";
import { exportAppointmentsExcel } from "../utils/exportTables";
import { navigateAppointments, navigateAppointmentsBack } from "../utils/navigation";
import { DetailCard } from "../components/DetailCard";
import { DetailFieldGrid } from "../components/DetailFieldGrid";
import { DataTableSection } from "../components/dataTableUi";
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

  const columns = useMemo(
    () =>
      buildAppointmentListColumns({
        includeProductionOrder: true,
        includeWorkCenter: false,
      }),
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
                  {
                    label: "Inspeção final",
                    value: isInspection(ctSummary?.is_final_inspection) ? "Sim" : "Não",
                  },
                ]}
              />
              {query.totals ? (
                <SummaryCards totals={query.totals} omitKeys={["workCenterCount"]} />
              ) : null}
              <SeriesChart points={query.seriesPoints} />
              <DataTableSection
                columnPreferencesKey="production-appointments:CtDetailPage:apontamentos-do-ct:v2"
                title="Apontamentos do CT"
                titleHint={PA_HELP_TOOLTIPS.tables.ctDetailAppointments}
                columns={columns}
                rows={query.appointments}
                rowKey={(row) => String(row.appointment_id)}
                defaultSortKey="appointment_datetime"
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
