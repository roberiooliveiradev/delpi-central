import { useMemo, useState } from "react";
import { HelpTooltip } from "@delpi/plugin-ui/index";

import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  AppointmentRow,
  AppointmentsQueryFilters,
  ByOpRow,
  WorkCenterSummaryRow,
} from "../types/appointments";
import {
  fetchAllAppointments,
  fetchAllAppointmentsByOp,
} from "../api/appointmentsApi";
import { buildAppointmentListColumns } from "../utils/appointmentListColumns";
import {
  formatInteger,
  formatProtheusDate,
  formatQuantity,
} from "../utils/formatters";
import {
  exportAppointmentsExcel,
  exportByOpExcel,
  exportWorkCentersExcel,
} from "../utils/exportTables";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";
import { ExportExcelButton } from "./ExportExcelButton";

export type AppointmentsTableViewMode = "work_centers" | "appointments" | "by_op";

const VIEW_MODES: ReadonlyArray<{
  id: AppointmentsTableViewMode;
  label: string;
  hint: string;
}> = [
  {
    id: "work_centers",
    label: "Por CT",
    hint: PA_HELP_TOOLTIPS.tables.byWorkCenter,
  },
  {
    id: "appointments",
    label: "Apontamentos",
    hint: PA_HELP_TOOLTIPS.tables.appointments,
  },
  {
    id: "by_op",
    label: "Por OP",
    hint: PA_HELP_TOOLTIPS.tables.byOp,
  },
];

type AppointmentsTablesProps = {
  workCenters: WorkCenterSummaryRow[];
  appointments: AppointmentRow[];
  byOp: ByOpRow[];
  filters: AppointmentsQueryFilters;
  listTotal: number;
  byOpTotal: number;
  listPage: number;
  byOpPage: number;
  listPageSize: number;
  byOpPageSize: number;
  listSearch: string;
  byOpSearch: string;
  loading?: boolean;
  workCentersLoading?: boolean;
  onListPageChange: (page: number) => void;
  onByOpPageChange: (page: number) => void;
  onListPageSizeChange: (pageSize: number) => void;
  onByOpPageSizeChange: (pageSize: number) => void;
  onListSearchChange: (value: string) => void;
  onByOpSearchChange: (value: string) => void;
  onOpenOp: (productionOrder: string) => void;
  onOpenCt: (workCenter: string) => void;
};

type SortDir = "asc" | "desc";

function isInspection(value: number | boolean | undefined): boolean {
  return value === true || value === 1;
}

function compareValues(a: unknown, b: unknown): number {
  if (typeof a === "number" && typeof b === "number") return a - b;
  return String(a ?? "").localeCompare(String(b ?? ""), "pt-BR", {
    numeric: true,
    sensitivity: "base",
  });
}

function sortRows<T>(
  rows: T[],
  columns: DataTableColumn<T>[],
  sortKey: string | null,
  sortDirection: SortDir,
): T[] {
  if (!sortKey) return rows;
  const column = columns.find((item) => item.key === sortKey);
  if (!column?.sortValue) return rows;
  const factor = sortDirection === "asc" ? 1 : -1;
  return [...rows].sort(
    (left, right) => factor * compareValues(column.sortValue!(left), column.sortValue!(right)),
  );
}

function toggleSort(
  currentKey: string | null,
  currentDir: SortDir,
  nextKey: string,
): { key: string; direction: SortDir } {
  if (currentKey === nextKey) {
    return { key: nextKey, direction: currentDir === "asc" ? "desc" : "asc" };
  }
  return { key: nextKey, direction: "asc" };
}

export function AppointmentsTables({
  workCenters,
  appointments,
  byOp,
  filters,
  listTotal,
  byOpTotal,
  listPage,
  byOpPage,
  listPageSize,
  byOpPageSize,
  listSearch,
  byOpSearch,
  loading = false,
  workCentersLoading = false,
  onListPageChange,
  onByOpPageChange,
  onListPageSizeChange,
  onByOpPageSizeChange,
  onListSearchChange,
  onByOpSearchChange,
  onOpenOp,
  onOpenCt,
}: AppointmentsTablesProps) {
  const [viewMode, setViewMode] = useState<AppointmentsTableViewMode>("appointments");
  const [exporting, setExporting] = useState(false);

  const [listSortKey, setListSortKey] = useState<string | null>("appointment_datetime");
  const [listSortDir, setListSortDir] = useState<SortDir>("desc");
  const [byOpSortKey, setByOpSortKey] = useState<string | null>("qty_produced");
  const [byOpSortDir, setByOpSortDir] = useState<SortDir>("desc");
  const [ctSortKey, setCtSortKey] = useState<string | null>("qty_produced");
  const [ctSortDir, setCtSortDir] = useState<SortDir>("desc");

  const workCenterColumns = useMemo<DataTableColumn<WorkCenterSummaryRow>[]>(
    () => [
      {
        key: "work_center",
        header: "CT",
        headerHint: PA_HELP_TOOLTIPS.columns.workCenter,
        sortable: true,
        sortValue: (row) => row.work_center,
        render: (row) => (
          <>
            {row.work_center}
            {isInspection(row.is_final_inspection) ? (
              <span className="pa-badge">Inspeção final</span>
            ) : null}
          </>
        ),
      },
      {
        key: "work_center_name",
        header: "Nome",
        headerHint: PA_HELP_TOOLTIPS.columns.workCenterName,
        sortable: true,
        sortValue: (row) => row.work_center_name || "",
        className: "pa-table__col--wide",
        render: (row) => row.work_center_name,
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
      {
        key: "op_count",
        header: "OPs",
        headerHint: PA_HELP_TOOLTIPS.columns.opCount,
        sortable: true,
        sortValue: (row) => row.op_count,
        className: "pa-table__col--numeric",
        render: (row) => formatInteger(row.op_count),
      },
    ],
    [],
  );

  const appointmentColumns = useMemo(
    () =>
      buildAppointmentListColumns({
        includeProductionOrder: true,
        includeWorkCenter: true,
      }),
    [],
  );

  const byOpColumns = useMemo<DataTableColumn<ByOpRow>[]>(
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

  const sortedWorkCenters = useMemo(
    () => sortRows(workCenters, workCenterColumns, ctSortKey, ctSortDir),
    [workCenters, workCenterColumns, ctSortKey, ctSortDir],
  );
  const sortedAppointments = useMemo(
    () => sortRows(appointments, appointmentColumns, listSortKey, listSortDir),
    [appointments, appointmentColumns, listSortKey, listSortDir],
  );
  const sortedByOp = useMemo(
    () => sortRows(byOp, byOpColumns, byOpSortKey, byOpSortDir),
    [byOp, byOpColumns, byOpSortKey, byOpSortDir],
  );

  const activeMode = VIEW_MODES.find((mode) => mode.id === viewMode) ?? VIEW_MODES[1];

  const handleExport = async () => {
    setExporting(true);
    try {
      if (viewMode === "work_centers") {
        await exportWorkCentersExcel(workCenters, filters);
        return;
      }
      if (viewMode === "by_op") {
        const items = await fetchAllAppointmentsByOp(filters, { search: byOpSearch });
        await exportByOpExcel(items, filters);
        return;
      }
      const items = await fetchAllAppointments(filters, { search: listSearch });
      await exportAppointmentsExcel(items, filters);
    } finally {
      setExporting(false);
    }
  };

  const exportDisabled =
    viewMode === "work_centers"
      ? workCenters.length === 0
      : viewMode === "by_op"
        ? byOpTotal === 0
        : listTotal === 0;

  const viewSwitcher = (
    <div className="pa-table-view-modes" role="tablist" aria-label="Modo de visualização da tabela">
      {VIEW_MODES.map((mode) => (
        <button
          key={mode.id}
          type="button"
          role="tab"
          aria-selected={viewMode === mode.id}
          className={`pa-table-view-modes__btn${
            viewMode === mode.id ? " pa-table-view-modes__btn--active" : ""
          }`}
          onClick={() => setViewMode(mode.id)}
        >
          {mode.label}
          <HelpTooltip
            content={mode.hint}
            ariaLabel={`Ajuda: ${mode.label}`}
            className="pa-table-view-modes__help"
          />
        </button>
      ))}
    </div>
  );

  const exportAction = (
    <ExportExcelButton
      disabled={exportDisabled}
      exporting={exporting}
      onExport={handleExport}
    />
  );

  return (
    <section className="pa-tables-panel" aria-label="Tabelas de apontamento">
      {viewSwitcher}

      {viewMode === "work_centers" ? (
        <DataTableSection
          columnPreferencesKey="production-appointments:AppointmentsTables:resumo-por-centro-de-trabalho:v1"
          title="Resumo por centro de trabalho"
          titleHint={activeMode.hint}
          columns={workCenterColumns}
          rows={sortedWorkCenters}
          rowKey={(row) => row.work_center}
          loading={workCentersLoading}
          defaultSortKey={ctSortKey ?? "qty_produced"}
          defaultSortDirection={ctSortDir}
          headerActions={exportAction}
          onRowClick={(row) => onOpenCt(row.work_center)}
          searchPlaceholder="Buscar CT ou nome…"
          searchHint={PA_HELP_TOOLTIPS.tables.byWorkCenterSearch}
          getSearchText={(row) =>
            `${row.work_center} ${row.work_center_name || ""}`.toLowerCase()
          }
          serverSort={{
            sortKey: ctSortKey,
            sortDirection: ctSortDir,
            onSortChange: (columnKey) => {
              const next = toggleSort(ctSortKey, ctSortDir, columnKey);
              setCtSortKey(next.key);
              setCtSortDir(next.direction);
            },
          }}
        />
      ) : null}

      {viewMode === "appointments" ? (
        <DataTableSection
          columnPreferencesKey="production-appointments:AppointmentsTables:apontamentos-1:v2"
          title="Apontamentos"
          titleHint={activeMode.hint}
          columns={appointmentColumns}
          rows={sortedAppointments}
          rowKey={(row) => String(row.appointment_id)}
          loading={loading}
          onRowClick={(row) => onOpenOp(row.production_order)}
          headerActions={exportAction}
          searchPlaceholder="Buscar operador, OP, produto, CT…"
          searchHint={PA_HELP_TOOLTIPS.tables.appointmentsSearch}
          serverSearch={{
            value: listSearch,
            onChange: onListSearchChange,
          }}
          serverSort={{
            sortKey: listSortKey,
            sortDirection: listSortDir,
            onSortChange: (columnKey) => {
              const next = toggleSort(listSortKey, listSortDir, columnKey);
              setListSortKey(next.key);
              setListSortDir(next.direction);
            },
          }}
          serverPagination={{
            page: listPage,
            pageSize: listPageSize,
            total: listTotal,
            onPageChange: onListPageChange,
            onPageSizeChange: (size) => {
              onListPageSizeChange(size);
              onListPageChange(1);
            },
          }}
        />
      ) : null}

      {viewMode === "by_op" ? (
        <DataTableSection
          columnPreferencesKey="production-appointments:AppointmentsTables:por-ordem-de-produ-o-2:v1"
          title="Por ordem de produção"
          titleHint={activeMode.hint}
          columns={byOpColumns}
          rows={sortedByOp}
          rowKey={(row) => `${row.production_order}-${row.product}`}
          loading={loading}
          onRowClick={(row) => onOpenOp(row.production_order)}
          headerActions={exportAction}
          searchPlaceholder="Buscar OP ou produto…"
          searchHint={PA_HELP_TOOLTIPS.tables.byOpSearch}
          serverSearch={{
            value: byOpSearch,
            onChange: onByOpSearchChange,
          }}
          serverSort={{
            sortKey: byOpSortKey,
            sortDirection: byOpSortDir,
            onSortChange: (columnKey) => {
              const next = toggleSort(byOpSortKey, byOpSortDir, columnKey);
              setByOpSortKey(next.key);
              setByOpSortDir(next.direction);
            },
          }}
          serverPagination={{
            page: byOpPage,
            pageSize: byOpPageSize,
            total: byOpTotal,
            onPageChange: onByOpPageChange,
            onPageSizeChange: (size) => {
              onByOpPageSizeChange(size);
              onByOpPageChange(1);
            },
          }}
        />
      ) : null}
    </section>
  );
}
