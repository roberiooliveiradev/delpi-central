import { DataTable, type DataTableColumn } from "./dataTableUi";
import { SectionError } from "./SectionError";
import type { SectionErrorState } from "../types/api";
import type { SafetyStockLinkedSupplier } from "../types/safetyStock";
import { formatNumberPtBr, formatUnitPricePtBr } from "../utils/formatters";
import { formatIsoDatePtBr } from "../utils/safetyStockStatus";

const NO_PURCHASE_LABEL = "Sem compras registradas";

type SafetyStockLinkedSuppliersSectionProps = {
  items: SafetyStockLinkedSupplier[];
  loading: boolean;
  error: SectionErrorState | null;
  selectedSupplierKey?: string | null;
  onSupplierSelect?: (supplier: SafetyStockLinkedSupplier) => void;
  onRetry?: () => void;
};

function supplierDisplayName(row: SafetyStockLinkedSupplier): string {
  return row.trade_name || row.legal_name || row.supplier_code || "—";
}

function purchaseCell(row: SafetyStockLinkedSupplier, value: string): string {
  if (!row.has_last_purchase) return NO_PURCHASE_LABEL;
  return value;
}

export function supplierRowKey(row: SafetyStockLinkedSupplier): string {
  return `${row.supplier_code}-${row.supplier_store}`;
}

export function SafetyStockLinkedSuppliersSection({
  items,
  loading,
  error,
  selectedSupplierKey = null,
  onSupplierSelect,
  onRetry,
}: SafetyStockLinkedSuppliersSectionProps) {
  const columns: DataTableColumn<SafetyStockLinkedSupplier>[] = [
    {
      key: "supplier_name",
      header: "Fornecedor",
      render: (row) => (
        <span className="ess-detail__supplier-name">{supplierDisplayName(row)}</span>
      ),
    },
    {
      key: "supplier_code",
      header: "Código",
      render: (row) => row.supplier_code || "—",
    },
    {
      key: "supplier_store",
      header: "Loja",
      render: (row) => row.supplier_store || "—",
    },
    {
      key: "supplier_part_number",
      header: "Partnumber",
      render: (row) => row.supplier_part_number || "—",
    },
    {
      key: "last_purchase_date",
      header: "Última compra",
      render: (row) => (
        <span className="ess-detail__supplier-date">
          {purchaseCell(row, formatIsoDatePtBr(row.last_purchase_date))}
        </span>
      ),
    },
    {
      key: "last_unit_price",
      header: "Preço unitário",
      align: "right",
      className: "ess-table__col--numeric",
      render: (row) => (
        <span className="ess-detail__supplier-price">
          {purchaseCell(row, formatUnitPricePtBr(row.last_unit_price))}
        </span>
      ),
    },
    {
      key: "last_quantity",
      header: "Quantidade",
      align: "right",
      className: "ess-table__col--numeric",
      render: (row) =>
        purchaseCell(
          row,
          row.last_quantity === null || row.last_quantity === undefined
            ? "—"
            : formatNumberPtBr(row.last_quantity),
        ),
    },
    {
      key: "last_invoice",
      header: "NF / Série",
      render: (row) => {
        if (!row.has_last_purchase) return NO_PURCHASE_LABEL;
        const number = row.last_invoice_number || "—";
        const series = row.last_invoice_series || "—";
        return `${number} / ${series}`;
      },
    },
  ];

  return (
    <section className="ess-detail__section" aria-label="Fornecedores vinculados">
      <h3>Fornecedores vinculados</h3>
      <p className="ess-detail__hint">
        Amarrações produto × fornecedor (SA5) com a última entrada normal do produto em cada
        fornecedor (SD1). Clique em um fornecedor para ver a oscilação do preço unitário nos
        últimos 12 meses.
      </p>

      {loading ? (
        <p className="ess-detail__state" role="status">
          Consultando fornecedores vinculados…
        </p>
      ) : null}

      {!loading && error ? (
        <SectionError
          title={error.title}
          message={error.message}
          onRetry={error.retryable ? onRetry : undefined}
        />
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <p className="ess-detail__empty">Nenhum fornecedor está vinculado a este produto</p>
      ) : null}

      {!loading && !error && items.length > 0 ? (
        <DataTable
          columns={columns}
          rows={items}
          rowKey={(row: SafetyStockLinkedSupplier) => supplierRowKey(row)}
          layout="embedded"
          emptyMessage="Nenhum fornecedor está vinculado a este produto"
          onRowClick={onSupplierSelect}
          rowClickRole="button"
          getRowClassName={(row: SafetyStockLinkedSupplier) =>
            selectedSupplierKey && supplierRowKey(row) === selectedSupplierKey
              ? "is-selected"
              : undefined
          }
        />
      ) : null}
    </section>
  );
}
