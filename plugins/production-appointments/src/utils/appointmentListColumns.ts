import type { DataTableColumn } from "@delpi/plugin-ui/index";
import { PA_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { AppointmentRow } from "../types/appointments";
import {
  appointmentDateTimeSortKey,
  formatAppointmentDateTime,
  formatOperatorLabel,
  formatQuantity,
  formatResourceLabel,
} from "./formatters";

export type AppointmentListColumnOptions = {
  /** Inclui coluna OP (útil no detalhe do CT / lista geral). */
  includeProductionOrder?: boolean;
  /** Inclui coluna CT (útil no detalhe da OP / lista geral). */
  includeWorkCenter?: boolean;
};

/** Colunas canônicas da lista de apontamentos individuais. */
export function buildAppointmentListColumns(
  options: AppointmentListColumnOptions = {},
): DataTableColumn<AppointmentRow>[] {
  const { includeProductionOrder = true, includeWorkCenter = true } = options;
  const columns: DataTableColumn<AppointmentRow>[] = [
    {
      key: "appointment_datetime",
      header: "Data/Hora",
      headerHint: PA_HELP_TOOLTIPS.columns.appointmentDateTime,
      sortable: true,
      sortValue: (row) => appointmentDateTimeSortKey(row),
      className: "pa-table__col--wide",
      render: (row) => formatAppointmentDateTime(row),
    },
    {
      key: "operator",
      header: "Operador",
      headerHint: PA_HELP_TOOLTIPS.columns.operator,
      sortable: true,
      sortValue: (row) => formatOperatorLabel(row),
      className: "pa-table__col--wide",
      render: (row) => formatOperatorLabel(row),
    },
    {
      key: "operation",
      header: "Operação",
      headerHint: PA_HELP_TOOLTIPS.columns.operation,
      sortable: true,
      sortValue: (row) => row.operation ?? "",
      render: (row) => row.operation?.trim() || "—",
    },
    {
      key: "resource",
      header: "Recurso",
      headerHint: PA_HELP_TOOLTIPS.columns.resource,
      sortable: true,
      sortValue: (row) => formatResourceLabel(row),
      className: "pa-table__col--wide",
      render: (row) => formatResourceLabel(row),
    },
  ];

  if (includeProductionOrder) {
    columns.push({
      key: "production_order",
      header: "OP",
      headerHint: PA_HELP_TOOLTIPS.columns.productionOrder,
      sortable: true,
      sortValue: (row) => row.production_order,
      render: (row) => row.production_order,
    });
  }

  columns.push({
    key: "product",
    header: "Produto",
    headerHint: PA_HELP_TOOLTIPS.columns.product,
    sortable: true,
    sortValue: (row) => row.product,
    className: "pa-table__col--wide",
    render: (row) =>
      `${row.product}${row.product_type ? ` (${row.product_type})` : ""}`,
  });

  if (includeWorkCenter) {
    columns.push({
      key: "work_center",
      header: "CT",
      headerHint: PA_HELP_TOOLTIPS.columns.workCenter,
      sortable: true,
      sortValue: (row) => row.work_center,
      className: "pa-table__col--wide",
      render: (row) =>
        `${row.work_center}${row.work_center_name ? ` — ${row.work_center_name}` : ""}`,
    });
  }

  columns.push(
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
  );

  return columns;
}
