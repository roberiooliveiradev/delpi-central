import { useMemo, useState } from "react";

import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import type {
  AppointmentsQueryFilters,
  WorkCenterSummaryRow,
} from "../types/appointments";
import { formatInteger, formatQuantity } from "../utils/formatters";
import { exportWorkCentersExcel } from "../utils/exportTables";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";
import { ExportExcelButton } from "./ExportExcelButton";

type WorkCenterSummaryTableProps = {
  items: WorkCenterSummaryRow[];
  filters: AppointmentsQueryFilters;
  loading?: boolean;
};

function isInspection(value: number | boolean | undefined): boolean {
  return value === true || value === 1;
}

export function WorkCenterSummaryTable({
  items,
  filters,
  loading = false,
}: WorkCenterSummaryTableProps) {
  const [exporting, setExporting] = useState(false);

  const columns = useMemo<DataTableColumn<WorkCenterSummaryRow>[]>(
    () => [
      {
        key: "work_center",
        header: "CT",
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
        sortable: true,
        sortValue: (row) => row.work_center_name || "",
        className: "pa-table__col--wide",
        render: (row) => row.work_center_name,
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
      {
        key: "op_count",
        header: "OPs",
        sortable: true,
        sortValue: (row) => row.op_count,
        className: "pa-table__col--numeric",
        render: (row) => formatInteger(row.op_count),
      },
    ],
    [],
  );

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportWorkCentersExcel(items, filters);
    } finally {
      setExporting(false);
    }
  };

  return (
    <DataTableSection
      title="Resumo por centro de trabalho"
      titleHint={PA_HELP_TOOLTIPS.tables.byWorkCenter}
      columns={columns}
      rows={items}
      rowKey={(row) => row.work_center}
      loading={loading}
      defaultSortKey="qty_produced"
      defaultSortDirection="desc"
      headerActions={
        <ExportExcelButton
          disabled={items.length === 0}
          exporting={exporting}
          onExport={handleExport}
        />
      }
    />
  );
}
