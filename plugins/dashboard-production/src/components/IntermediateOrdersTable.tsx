import { useMemo } from "react";

import type { IntermediateProductionOrderRow } from "../types/production";
import { formatDisplayDate } from "../utils/dates";
import { formatDecimal, formatInteger } from "../utils/format";
import { DataTable, type DataTableColumn } from "./DataTable";
import { OtdStatusBadge } from "./OtdStatusBadge";

type IntermediateOrdersTableProps = {
  rows: IntermediateProductionOrderRow[];
  emptyMessage?: string;
  onRowClick?: (row: IntermediateProductionOrderRow) => void;
};

export function useIntermediateOrderColumns(): DataTableColumn<IntermediateProductionOrderRow>[] {
  return useMemo(
    () => [
      {
        key: "status",
        header: "Status OTD",
        sortable: true,
        render: (row) => <OtdStatusBadge status={row.otd_status} />,
      },
      {
        key: "level",
        header: "Nível",
        className: "dp-table__col--numeric",
        render: (row) => row.level,
      },
      {
        key: "branch",
        header: "Filial",
        sortable: true,
        render: (row) => row.branch || "—",
      },
      {
        key: "production_order",
        header: "OP",
        sortable: true,
        render: (row) => row.production_order || "—",
      },
      {
        key: "product_code",
        header: "Código PI",
        sortable: true,
        render: (row) => row.product_code || "—",
      },
      {
        key: "description",
        header: "Descrição",
        className: "dp-table__col--wide",
        sortable: true,
        render: (row) => row.description || "—",
      },
      {
        key: "due",
        header: "Previsto",
        sortable: true,
        render: (row) => formatDisplayDate(row.due_date),
      },
      {
        key: "finish",
        header: "Finalização",
        sortable: true,
        render: (row) => formatDisplayDate(row.finish_date),
      },
      {
        key: "days",
        header: "Dias",
        className: "dp-table__col--numeric",
        sortable: true,
        render: (row) => formatInteger(row.days_diff),
      },
      {
        key: "qty",
        header: "Qtd",
        className: "dp-table__col--numeric",
        sortable: true,
        render: (row) => formatDecimal(row.produced_qty ?? row.planned_qty),
      },
    ],
    []
  );
}

export function IntermediateOrdersTable({
  rows,
  emptyMessage = "Nenhuma OP de PI vinculada a esta ordem do PA.",
  onRowClick,
}: IntermediateOrdersTableProps) {
  const columns = useIntermediateOrderColumns();

  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={(row) => row.key}
      emptyMessage={emptyMessage}
      onRowClick={onRowClick}
    />
  );
}
