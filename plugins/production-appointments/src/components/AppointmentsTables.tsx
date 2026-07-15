import { useMemo, useState } from "react";

import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  AppointmentRow,
  AppointmentsQueryFilters,
  ByOpRow,
} from "../types/appointments";
import {
  fetchAllAppointments,
  fetchAllAppointmentsByOp,
} from "../api/appointmentsApi";
import {
  formatInteger,
  formatProtheusDate,
  formatQuantity,
} from "../utils/formatters";
import {
  exportAppointmentsExcel,
  exportByOpExcel,
} from "../utils/exportTables";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";
import { ExportExcelButton } from "./ExportExcelButton";

type AppointmentsTablesProps = {
  appointments: AppointmentRow[];
  byOp: ByOpRow[];
  filters: AppointmentsQueryFilters;
  listTotal: number;
  byOpTotal: number;
  listPage: number;
  byOpPage: number;
  listPageSize: number;
  byOpPageSize: number;
  loading?: boolean;
  onListPageChange: (page: number) => void;
  onByOpPageChange: (page: number) => void;
  onListPageSizeChange: (pageSize: number) => void;
  onByOpPageSizeChange: (pageSize: number) => void;
  onOpenOp: (productionOrder: string) => void;
};

type SortDir = "asc" | "desc";

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
  appointments,
  byOp,
  filters,
  listTotal,
  byOpTotal,
  listPage,
  byOpPage,
  listPageSize,
  byOpPageSize,
  loading = false,
  onListPageChange,
  onByOpPageChange,
  onListPageSizeChange,
  onByOpPageSizeChange,
  onOpenOp,
}: AppointmentsTablesProps) {
  const [exportingList, setExportingList] = useState(false);
  const [exportingByOp, setExportingByOp] = useState(false);
  const [listSortKey, setListSortKey] = useState<string | null>("appointment_date");
  const [listSortDir, setListSortDir] = useState<SortDir>("desc");
  const [byOpSortKey, setByOpSortKey] = useState<string | null>("qty_produced");
  const [byOpSortDir, setByOpSortDir] = useState<SortDir>("desc");

  const appointmentColumns = useMemo<DataTableColumn<AppointmentRow>[]>(
    () => [
      {
        key: "appointment_date",
        header: "Data",
        sortable: true,
        sortValue: (row) => row.appointment_date,
        render: (row) => formatProtheusDate(row.appointment_date),
      },
      {
        key: "production_order",
        header: "OP",
        sortable: true,
        sortValue: (row) => row.production_order,
        render: (row) => row.production_order,
      },
      {
        key: "product",
        header: "Produto",
        sortable: true,
        sortValue: (row) => row.product,
        className: "pa-table__col--wide",
        render: (row) =>
          `${row.product}${row.product_type ? ` (${row.product_type})` : ""}`,
      },
      {
        key: "work_center",
        header: "CT",
        sortable: true,
        sortValue: (row) => row.work_center,
        className: "pa-table__col--wide",
        render: (row) =>
          `${row.work_center}${row.work_center_name ? ` — ${row.work_center_name}` : ""}`,
      },
      {
        key: "qty_produced",
        header: "Produzida",
        sortable: true,
        sortValue: (row) => row.qty_produced,
        className: "pa-table__col--numeric",
        render: (row) => formatQuantity(row.qty_produced),
      },
      {
        key: "qty_lost",
        header: "Perdida",
        sortable: true,
        sortValue: (row) => row.qty_lost,
        className: "pa-table__col--numeric",
        render: (row) => formatQuantity(row.qty_lost),
      },
    ],
    [],
  );

  const byOpColumns = useMemo<DataTableColumn<ByOpRow>[]>(
    () => [
      {
        key: "production_order",
        header: "OP",
        sortable: true,
        sortValue: (row) => row.production_order,
        render: (row) => row.production_order,
      },
      {
        key: "product",
        header: "Produto",
        sortable: true,
        sortValue: (row) => row.product,
        className: "pa-table__col--wide",
        render: (row) =>
          `${row.product}${row.product_type ? ` (${row.product_type})` : ""}`,
      },
      {
        key: "appointment_count",
        header: "Apont.",
        sortable: true,
        sortValue: (row) => row.appointment_count,
        className: "pa-table__col--numeric",
        render: (row) => formatInteger(row.appointment_count),
      },
      {
        key: "work_center_count",
        header: "CTs",
        sortable: true,
        sortValue: (row) => row.work_center_count,
        className: "pa-table__col--numeric",
        render: (row) => formatInteger(row.work_center_count),
      },
      {
        key: "qty_produced",
        header: "Produzida",
        sortable: true,
        sortValue: (row) => row.qty_produced,
        className: "pa-table__col--numeric",
        render: (row) => formatQuantity(row.qty_produced),
      },
      {
        key: "period",
        header: "Período",
        sortable: true,
        sortValue: (row) => row.first_date,
        render: (row) =>
          `${formatProtheusDate(row.first_date)} — ${formatProtheusDate(row.last_date)}`,
      },
    ],
    [],
  );

  const sortedAppointments = useMemo(
    () => sortRows(appointments, appointmentColumns, listSortKey, listSortDir),
    [appointments, appointmentColumns, listSortKey, listSortDir],
  );
  const sortedByOp = useMemo(
    () => sortRows(byOp, byOpColumns, byOpSortKey, byOpSortDir),
    [byOp, byOpColumns, byOpSortKey, byOpSortDir],
  );

  const handleExportList = async () => {
    setExportingList(true);
    try {
      const items = await fetchAllAppointments(filters);
      await exportAppointmentsExcel(items, filters);
    } finally {
      setExportingList(false);
    }
  };

  const handleExportByOp = async () => {
    setExportingByOp(true);
    try {
      const items = await fetchAllAppointmentsByOp(filters);
      await exportByOpExcel(items, filters);
    } finally {
      setExportingByOp(false);
    }
  };

  return (
    <div className="pa-tables-stack">
      <DataTableSection
        title="Apontamentos"
        titleHint={PA_HELP_TOOLTIPS.tables.appointments}
        columns={appointmentColumns}
        rows={sortedAppointments}
        rowKey={(row) => String(row.appointment_id)}
        loading={loading}
        onRowClick={(row) => onOpenOp(row.production_order)}
        headerActions={
          <ExportExcelButton
            disabled={listTotal === 0}
            exporting={exportingList}
            onExport={handleExportList}
          />
        }
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

      <DataTableSection
        title="Por ordem de produção"
        titleHint={PA_HELP_TOOLTIPS.tables.byOp}
        columns={byOpColumns}
        rows={sortedByOp}
        rowKey={(row) => `${row.production_order}-${row.product}`}
        loading={loading}
        onRowClick={(row) => onOpenOp(row.production_order)}
        headerActions={
          <ExportExcelButton
            disabled={byOpTotal === 0}
            exporting={exportingByOp}
            onExport={handleExportByOp}
          />
        }
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
    </div>
  );
}
