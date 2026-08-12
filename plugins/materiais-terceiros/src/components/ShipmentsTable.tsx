import { ExcelExportButton } from "@delpi/plugin-ui/index";

import { HELP_TOOLTIPS } from "../content/helpTooltips";
import type { Shipment } from "../types/thirdPartyMaterials";
import { formatDatePtBr, formatQuantity, formatStatus } from "../utils/formatters";
import { DataTableSection, type DataTableColumn } from "./dataTableUi";

type ShipmentsTableProps = {
  rows: Shipment[];
  loading?: boolean;
  refreshing?: boolean;
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
  onSelect: (row: Shipment) => void;
  canExport?: boolean;
  exporting?: boolean;
  onExportCsv?: () => void;
  onExportXlsx?: () => void;
};

const columns: DataTableColumn<Shipment>[] = [
  {
    key: "receipt",
    header: "NF recebimento",
    render: (row) => row.receipt_invoice.number || "—",
    sortValue: (row) => row.receipt_invoice.number,
  },
  {
    key: "issued",
    header: "Emissão",
    render: (row) => formatDatePtBr(row.receipt_invoice.issued_on),
    sortValue: (row) => row.receipt_invoice.issued_on,
  },
  {
    key: "product",
    header: "Produto",
    render: (row) => (
      <span>
        <strong>{row.product.code}</strong>
        {row.product.description ? ` — ${row.product.description}` : ""}
      </span>
    ),
    sortValue: (row) => row.product.code,
  },
  {
    key: "customerReference",
    header: "Ref. cliente",
    headerHint: HELP_TOOLTIPS.filters.customerReference,
    render: (row) => row.product.customer_reference || "—",
    sortValue: (row) => row.product.customer_reference,
  },
  {
    key: "partner",
    header: "Cliente",
    render: (row) => row.partner.name || row.partner.code || "—",
    sortValue: (row) => row.partner.name || row.partner.code,
  },
  {
    key: "received",
    header: "Qtd. recebida",
    align: "right",
    render: (row) => formatQuantity(row.received_quantity, row.product.unit),
    sortValue: (row) => row.received_quantity,
  },
  {
    key: "returned",
    header: "Qtd. devolvida",
    align: "right",
    render: (row) => formatQuantity(row.returned_quantity, row.product.unit),
    sortValue: (row) => row.returned_quantity,
  },
  {
    key: "balance",
    header: "Saldo",
    headerHint: HELP_TOOLTIPS.table.balance,
    align: "right",
    render: (row) => formatQuantity(row.pending_balance, row.product.unit),
    sortValue: (row) => row.pending_balance,
  },
  {
    key: "status",
    header: "Status",
    render: (row) => formatStatus(String(row.status)),
    sortValue: (row) => row.status,
  },
  {
    key: "returns",
    header: "Retornos",
    align: "right",
    render: (row) => String(row.returns?.length ?? 0),
    sortValue: (row) => row.returns?.length ?? 0,
  },
];

export function ShipmentsTable({
  rows,
  loading,
  refreshing,
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
  onSelect,
  canExport = false,
  exporting = false,
  onExportCsv,
  onExportXlsx,
}: ShipmentsTableProps) {
  return (
    <DataTableSection
      title="Remessas"
      hint={HELP_TOOLTIPS.table.shipment}
      columns={columns}
      rows={rows}
      rowKey={(row) => String(row.shipment_recno)}
      loading={loading}
      refreshing={refreshing}
      onRowClick={onSelect}
      interactive
      serverPagination={{
        page,
        pageSize,
        total,
        onPageChange,
        onPageSizeChange,
      }}
      headerActions={
        canExport ? (
          <div className="mt-export-actions">
            <ExcelExportButton
              label="CSV"
              exportingLabel="Exportando…"
              exporting={exporting}
              onExport={() => void onExportCsv?.()}
            />
            <ExcelExportButton
              label="Excel"
              exportingLabel="Exportando…"
              exporting={exporting}
              onExport={() => void onExportXlsx?.()}
            />
          </div>
        ) : null
      }
    />
  );
}
