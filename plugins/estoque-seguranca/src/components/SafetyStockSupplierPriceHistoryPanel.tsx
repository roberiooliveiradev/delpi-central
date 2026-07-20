import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { createDashboardDetailFieldGrid } from "@delpi/plugin-ui/index";

import { SectionError } from "./SectionError";
import { DataTable, type DataTableColumn } from "./dataTableUi";
import { EssModernLineChart } from "./EssModernLineChart";
import type { SectionErrorState } from "../types/api";
import type {
  SafetyStockLinkedSupplier,
  SafetyStockSupplierPriceHistoryData,
  SafetyStockSupplierPriceHistoryPoint,
} from "../types/safetyStock";
import { formatCurrencyPtBr, formatNumberPtBr, formatUnitPricePtBr } from "../utils/formatters";
import { formatIsoDatePtBr } from "../utils/safetyStockStatus";

type SafetyStockSupplierPriceHistoryPanelProps = {
  supplier: SafetyStockLinkedSupplier;
  data: SafetyStockSupplierPriceHistoryData | null;
  loading: boolean;
  error: SectionErrorState | null;
  onRetry?: () => void;
};

const DetailFields = createDashboardDetailFieldGrid({
  prefix: "ess",
  labels: {
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
});

function supplierLabel(supplier: SafetyStockLinkedSupplier): string {
  return supplier.trade_name || supplier.legal_name || supplier.supplier_code;
}

function formatVariation(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumberPtBr(value)}%`;
}

function averageUnitPrice(points: { value: number }[]): number | null {
  if (points.length === 0) return null;
  return points.reduce((total, point) => total + point.value, 0) / points.length;
}

function invoiceRowKey(item: SafetyStockSupplierPriceHistoryPoint): string {
  return [
    item.invoice_number || "",
    item.invoice_series || "",
    item.purchase_date || "",
    String(item.unit_price),
    String(item.quantity),
  ].join("|");
}

function invoiceLabel(item: SafetyStockSupplierPriceHistoryPoint): string {
  const number = item.invoice_number?.trim() || "—";
  const series = item.invoice_series?.trim() || "—";
  return `${number}/${series}`;
}

export function SafetyStockSupplierPriceHistoryPanel({
  supplier,
  data,
  loading,
  error,
  onRetry,
}: SafetyStockSupplierPriceHistoryPanelProps) {
  const items = data?.items ?? [];
  const summary = data?.summary;
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  useEffect(() => {
    setExpandedKey(null);
  }, [supplier.supplier_code, supplier.supplier_store, data?.date_start, data?.date_end_exclusive]);

  const points = items
    .filter((item) => item.purchase_date)
    .map((item) => ({
      label: formatIsoDatePtBr(item.purchase_date),
      value: item.unit_price,
    }));

  const expandedItem = useMemo(
    () => items.find((item) => invoiceRowKey(item) === expandedKey) ?? null,
    [expandedKey, items],
  );

  const columns = useMemo<DataTableColumn<SafetyStockSupplierPriceHistoryPoint>[]>(
    () => [
      {
        key: "purchase_date",
        header: "Data",
        render: (row) => formatIsoDatePtBr(row.purchase_date),
      },
      {
        key: "invoice",
        header: "NF",
        render: (row) => invoiceLabel(row),
      },
      {
        key: "unit_price",
        header: "Preço unitário",
        className: "ess-table__col--numeric",
        align: "right",
        render: (row) => formatUnitPricePtBr(row.unit_price),
      },
      {
        key: "quantity",
        header: "Quantidade",
        className: "ess-table__col--numeric",
        align: "right",
        render: (row) => formatNumberPtBr(row.quantity),
      },
      {
        key: "total_value",
        header: "Valor total",
        className: "ess-table__col--numeric",
        align: "right",
        render: (row) => formatCurrencyPtBr(row.total_value),
      },
      {
        key: "expand",
        header: "Detalhes",
        className: "ess-table__col--action",
        interactive: true,
        render: (row) => {
          const key = invoiceRowKey(row);
          const open = expandedKey === key;
          return (
            <span className="ess-table__action" aria-hidden="true">
              {open ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </span>
          );
        },
      },
    ],
    [expandedKey],
  );

  return (
    <section
      className="ess-detail__section ess-detail__price-history"
      aria-label="Histórico de preço do fornecedor"
    >
      <div className="ess-detail__section-header">
        <h3>Oscilação de preço — {supplierLabel(supplier)}</h3>
      </div>
      <p className="ess-detail__hint">
        Compras do produto com este fornecedor nos últimos 12 meses (um ponto por NF, preço
        unitário D1_VUNIT, data D1_DTDIGIT). Código {supplier.supplier_code} · loja{" "}
        {supplier.supplier_store}. Clique em uma linha para ver os detalhes da nota.
      </p>

      {loading ? (
        <p className="ess-detail__state" role="status">
          Consultando histórico de preço…
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
        <p className="ess-detail__empty">
          Nenhuma compra registrada com este fornecedor nos últimos 12 meses.
        </p>
      ) : null}

      {!loading && !error && items.length > 0 && summary ? (
        <>
          <div className="ess-detail__price-summary" aria-label="Resumo do período">
            <span>
              <strong>Compras:</strong> {summary.total_purchases}
            </span>
            <span>
              <strong>Mínimo:</strong> {formatUnitPricePtBr(summary.min_unit_price)}
            </span>
            <span>
              <strong>Máximo:</strong> {formatUnitPricePtBr(summary.max_unit_price)}
            </span>
            <span>
              <strong>Primeiro:</strong> {formatUnitPricePtBr(summary.first_unit_price)}
            </span>
            <span>
              <strong>Último:</strong> {formatUnitPricePtBr(summary.last_unit_price)}
            </span>
            <span>
              <strong>Variação:</strong> {formatVariation(summary.variation_percent)}
            </span>
          </div>

          <div className="ess-detail__price-chart">
            <p className="ess-detail__chart-title">Preço unitário (R$)</p>
            <EssModernLineChart
              points={points}
              seriesLabel="Preço unitário"
              formatValue={formatUnitPricePtBr}
              averageValue={averageUnitPrice(points)}
              averageLabel="Preço médio do período"
              emptyMessage="Sem pontos para o gráfico."
            />
          </div>

          <div className="ess-detail__price-table">
            <DataTable
              columns={columns}
              rows={items}
              rowKey={invoiceRowKey}
              layout="embedded"
              emptyMessage="Sem notas no período."
              onRowClick={(row: SafetyStockSupplierPriceHistoryPoint) => {
                const key = invoiceRowKey(row);
                setExpandedKey((current) => (current === key ? null : key));
              }}
            />
          </div>

          {expandedItem ? (
            <article
              className="ess-detail__nf-card"
              aria-label={`Detalhes da NF ${invoiceLabel(expandedItem)}`}
            >
              <div className="ess-detail__nf-card-header">
                <h4>Detalhes da NF {invoiceLabel(expandedItem)}</h4>
                <button
                  type="button"
                  className="ess-btn ess-btn--secondary ess-detail__nf-card-close"
                  onClick={() => setExpandedKey(null)}
                >
                  Fechar
                </button>
              </div>
              <DetailFields
                fields={[
                  {
                    label: "Data da compra",
                    value: formatIsoDatePtBr(expandedItem.purchase_date),
                  },
                  {
                    label: "Data de emissão",
                    value: formatIsoDatePtBr(expandedItem.issue_date),
                  },
                  {
                    label: "Número / série",
                    value: invoiceLabel(expandedItem),
                  },
                  {
                    label: "Fornecedor",
                    value: expandedItem.supplier_name || supplierLabel(supplier),
                  },
                  {
                    label: "Código / loja",
                    value: `${expandedItem.supplier_code} · ${expandedItem.supplier_store}`,
                  },
                  {
                    label: "Preço unitário",
                    value: formatUnitPricePtBr(expandedItem.unit_price),
                  },
                  {
                    label: "Quantidade",
                    value: formatNumberPtBr(expandedItem.quantity),
                  },
                  {
                    label: "Valor total",
                    value: formatCurrencyPtBr(expandedItem.total_value),
                  },
                ]}
              />
            </article>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
