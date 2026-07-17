import { LineSeriesChart } from "@delpi/plugin-ui/index";

import { SectionError } from "./SectionError";
import type { SectionErrorState } from "../types/api";
import type {
  SafetyStockLinkedSupplier,
  SafetyStockSupplierPriceHistoryData,
} from "../types/safetyStock";
import { formatNumberPtBr, formatUnitPricePtBr } from "../utils/formatters";
import { formatIsoDatePtBr } from "../utils/safetyStockStatus";

type SafetyStockSupplierPriceHistoryPanelProps = {
  supplier: SafetyStockLinkedSupplier;
  data: SafetyStockSupplierPriceHistoryData | null;
  loading: boolean;
  error: SectionErrorState | null;
  onRetry?: () => void;
};

function supplierLabel(supplier: SafetyStockLinkedSupplier): string {
  return supplier.trade_name || supplier.legal_name || supplier.supplier_code;
}

function formatVariation(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumberPtBr(value)}%`;
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
  const points = items
    .filter((item) => item.purchase_date)
    .map((item) => ({
      label: formatIsoDatePtBr(item.purchase_date),
      value: item.unit_price,
    }));

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
        {supplier.supplier_store}.
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
            <LineSeriesChart
              points={points}
              emptyMessage="Sem pontos para o gráfico."
              options={{
                title: "Preço unitário (R$)",
                showTitle: true,
                showLegend: false,
                showAxes: true,
                showXAxisLabels: true,
                showYAxisLabels: true,
                showXAxisTitle: false,
                showYAxisTitle: false,
                showDataLabels: true,
                showGrid: true,
                showMarkers: true,
                valueFormat: "currency4",
                seriesColor: "#089bdb",
                categoryPaddingPercent: 8,
                seriesName: "Preço unitário",
              }}
            />
          </div>

          <ul className="ess-detail__price-points" aria-label="Notas do período">
            {items.map((item) => (
              <li key={`${item.invoice_number}-${item.invoice_series}-${item.purchase_date}`}>
                <span className="ess-detail__supplier-date">
                  {formatIsoDatePtBr(item.purchase_date)}
                </span>
                {" · "}
                <span className="ess-detail__supplier-price">
                  {formatUnitPricePtBr(item.unit_price)}
                </span>
                {" · NF "}
                {item.invoice_number || "—"}/{item.invoice_series || "—"}
                {" · qtd "}
                {formatNumberPtBr(item.quantity)}
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}
