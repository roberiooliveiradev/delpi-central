import { useEffect, useMemo, useState } from "react";
import { ChevronRight } from "lucide-react";
import {
  createDashboardDetailFieldGrid,
  createDashboardStatusBadge,
  createModalShell,
  HelpTooltip,
} from "@delpi/plugin-ui/index";

import { useSafetyStockItemDetails } from "../hooks/useSafetyStockItemDetails";
import { useSafetyStockItemSuppliers } from "../hooks/useSafetyStockItemSuppliers";
import { useSafetyStockSupplierPriceHistory } from "../hooks/useSafetyStockSupplierPriceHistory";
import type {
  SafetyStockItem,
  SafetyStockLinkedSupplier,
  SafetyStockProjectionLedgerEntry,
} from "../types/safetyStock";
import { formatNumberPtBr } from "../utils/formatters";
import {
  branchLabel,
  dateStatusLabel,
  formatIsoDatePtBr,
  purchaseCoverageLabel,
  purchaseCoverageVariant,
} from "../utils/safetyStockStatus";
import { DataTable, type DataTableColumn } from "./dataTableUi";
import { SafetyStockDetailProductSearch } from "./SafetyStockDetailProductSearch";
import {
  SafetyStockLinkedSuppliersSection,
  supplierRowKey,
} from "./SafetyStockLinkedSuppliersSection";
import { SafetyStockSupplierPriceHistoryPanel } from "./SafetyStockSupplierPriceHistoryPanel";
import { SectionError } from "./SectionError";

const Modal = createModalShell({
  prefix: "ess",
  variant: "page",
  portalScopeClassName: "dashboard-estoque-seguranca",
  closeAriaLabel: "Fechar detalhes do produto",
});

const StatusBadge = createDashboardStatusBadge({ prefix: "ess" });
const DetailFields = createDashboardDetailFieldGrid({
  prefix: "ess",
  labels: {
    fieldHelpAriaLabel: (label) => `Ajuda: ${label}`,
  },
  valueFallback: "—",
});

type SafetyStockDetailModalProps = {
  item: SafetyStockItem | null;
  onClose: () => void;
  onNavigate?: (item: SafetyStockItem) => void;
};

export function SafetyStockDetailModal({ item, onClose, onNavigate }: SafetyStockDetailModalProps) {
  const open = Boolean(item);
  const [selectedSupplier, setSelectedSupplier] = useState<SafetyStockLinkedSupplier | null>(
    null,
  );
  const { data, loading, error, reload } = useSafetyStockItemDetails(
    item?.branch ?? null,
    item?.product_code ?? null,
  );
  const {
    data: suppliersData,
    loading: suppliersLoading,
    error: suppliersError,
    reload: reloadSuppliers,
  } = useSafetyStockItemSuppliers(item?.branch ?? null, item?.product_code ?? null);

  const priceHistorySelection = useMemo(
    () =>
      selectedSupplier
        ? {
            supplierCode: selectedSupplier.supplier_code,
            supplierStore: selectedSupplier.supplier_store,
          }
        : null,
    [selectedSupplier],
  );
  const {
    data: priceHistoryData,
    loading: priceHistoryLoading,
    error: priceHistoryError,
    reload: reloadPriceHistory,
  } = useSafetyStockSupplierPriceHistory(
    item?.branch ?? null,
    item?.product_code ?? null,
    priceHistorySelection,
  );

  useEffect(() => {
    setSelectedSupplier(null);
  }, [item?.branch, item?.product_code]);

  const product = data?.product;
  const stock = data?.stock;
  const coverage = data?.purchase_coverage;
  const projection = data?.stock_projection;
  const projectionSummary = projection?.summary;
  const ledger = projection?.items ?? [];
  const linkedSuppliers = suppliersData?.items ?? [];
  const selectedSupplierKey = selectedSupplier ? supplierRowKey(selectedSupplier) : null;

  const title = item
    ? `${item.product_code} · ${item.product_description || "Matéria-prima"}`
    : "Detalhes do produto";

  const ledgerColumns: DataTableColumn<SafetyStockProjectionLedgerEntry>[] = [
    {
      key: "event_date",
      header: "Data",
      render: (row) => (
        <span>
          {formatIsoDatePtBr(row.event_date)}
          <span className="ess-detail__muted"> · {dateStatusLabel(row.date_status)}</span>
        </span>
      ),
    },
    {
      key: "origin",
      header: "Origem",
      render: (row) => row.origin_label,
    },
    {
      key: "reference",
      header: "Referência",
      render: (row) => row.reference || "",
    },
    {
      key: "inflow",
      header: "Entrada",
      align: "right",
      className: "ess-table__col--numeric",
      render: (row) =>
        row.inflow ? (
          <span className="ess-detail__flow--positive">{`+${formatNumberPtBr(row.inflow)}`}</span>
        ) : (
          ""
        ),
    },
    {
      key: "outflow",
      header: "Saída",
      align: "right",
      className: "ess-table__col--numeric",
      render: (row) =>
        row.outflow ? (
          <span className="ess-detail__flow--negative">{`−${formatNumberPtBr(row.outflow)}`}</span>
        ) : (
          ""
        ),
    },
    {
      key: "running_balance",
      header: "Saldo",
      align: "right",
      className: "ess-table__col--numeric",
      render: (row) => (
        <span
          className={
            row.running_balance < 0
              ? "ess-detail__balance--negative"
              : "ess-detail__balance--positive"
          }
        >
          {formatNumberPtBr(row.running_balance)}
        </span>
      ),
    },
  ];

  return (
    <Modal
      open={open}
      title={title}
      description={item ? branchLabel(item.branch) : undefined}
      onClose={onClose}
      headerActions={
        item && onNavigate ? (
          <SafetyStockDetailProductSearch branch={item.branch} onNavigate={onNavigate} />
        ) : undefined
      }
      footer={
        <button type="button" className="ess-btn ess-btn--primary" onClick={onClose}>
          Fechar
        </button>
      }
    >
      {loading ? (
        <div className="ess-detail__state" role="status">
          Carregando detalhe, empenhos e pedidos de compra…
        </div>
      ) : null}

      {!loading && error ? (
        <SectionError
          title={error.title}
          message={error.message}
          onRetry={error.retryable ? reload : undefined}
        />
      ) : null}

      {!loading && !error && product && stock && coverage && projectionSummary ? (
        <div className="ess-detail">
          <section className="ess-detail__section" aria-label="Saldos">
            <h3>Saldos e estoque de segurança</h3>
            <DetailFields
              fields={[
                { label: "Estoque de segurança", value: formatNumberPtBr(stock.safety_stock) },
                { label: "Saldo disponível", value: formatNumberPtBr(stock.available_stock) },
                {
                  label: "Déficit físico",
                  value:
                    stock.deficit_quantity > 0 ? (
                      <span className="ess-detail__balance--negative">
                        {formatNumberPtBr(stock.deficit_quantity)}
                      </span>
                    ) : (
                      formatNumberPtBr(stock.deficit_quantity)
                    ),
                },
                { label: "Armazém 01", value: formatNumberPtBr(stock.primary_stock) },
                { label: "Armazém 98", value: formatNumberPtBr(stock.warehouse_98_stock) },
                { label: "Armazém 99", value: formatNumberPtBr(stock.warehouse_99_stock) },
              ]}
            />
          </section>

          <section className="ess-detail__section" aria-label="Projeção de saldo">
            <div className="ess-detail__section-header">
              <h3>Projeção (físico + compras − empenhos)</h3>
            </div>
            <DetailFields
              fields={[
                {
                  label: "Saldo final projetado",
                  value: formatNumberPtBr(projectionSummary.final_projected_balance),
                },
                {
                  label: "Menor saldo no período",
                  value: formatNumberPtBr(projectionSummary.minimum_projected_balance),
                },
                {
                  label: "Empenhos elegíveis",
                  value: formatNumberPtBr(projectionSummary.eligible_commitment_quantity),
                },
                {
                  label: "Pedidos elegíveis",
                  value: formatNumberPtBr(projectionSummary.eligible_purchase_quantity),
                },
                {
                  label: "Primeira ruptura",
                  value: formatIsoDatePtBr(projectionSummary.first_shortage_date),
                },
              ]}
            />
            {projectionSummary.warnings.map((warning) => (
              <p key={warning} className="ess-detail__warning">
                {warning}
              </p>
            ))}
          </section>

          <section className="ess-detail__section" aria-label="Cobertura de compras">
            <div className="ess-detail__section-header">
              <h3>Cobertura por pedidos de compra</h3>
              <StatusBadge
                label={purchaseCoverageLabel(coverage.status)}
                variant={purchaseCoverageVariant(coverage.status)}
              />
            </div>
            <DetailFields
              fields={[
                {
                  label: "Qtd. em pedidos elegíveis",
                  value: formatNumberPtBr(coverage.eligible_open_quantity),
                },
                {
                  label: "Ainda comprar (déficit físico)",
                  value: formatNumberPtBr(coverage.remaining_to_buy),
                },
                {
                  label: "Próxima entrega",
                  value: formatIsoDatePtBr(coverage.next_expected_delivery_date),
                },
                {
                  label: "Pedidos elegíveis",
                  value: String(coverage.eligible_order_count),
                },
              ]}
            />
            {coverage.warnings.map((warning) => (
              <p key={warning} className="ess-detail__warning">
                {warning}
              </p>
            ))}
          </section>

          <section className="ess-detail__section" aria-label="Extrato projetado">
            <div className="ess-detail__section-header ess-detail__section-header--help">
              <h3>Extrato projetado de saldo</h3>
              <HelpTooltip
                ariaLabel="Como funciona o extrato projetado"
                content="Linha do tempo consolidada: saldo atual, saídas por empenho (D4_QUANT) e entradas por pedido aberto. A data do empenho é a data do empenho no Protheus, não a garantia de consumo fabril."
                placement="bottom"
              />
            </div>
            {ledger.length === 0 ? (
              <p className="ess-detail__empty">Nenhum movimento projetado.</p>
            ) : (
              <DataTable
                columns={ledgerColumns}
                rows={ledger}
                rowKey={(row: SafetyStockProjectionLedgerEntry) => String(row.sequence)}
                layout="embedded"
                emptyMessage="Nenhum movimento projetado."
              />
            )}
          </section>

          <SafetyStockLinkedSuppliersSection
            items={linkedSuppliers}
            loading={suppliersLoading}
            error={suppliersError}
            selectedSupplierKey={selectedSupplierKey}
            onSupplierSelect={setSelectedSupplier}
            onRetry={reloadSuppliers}
          />

          {selectedSupplier ? (
            <SafetyStockSupplierPriceHistoryPanel
              supplier={selectedSupplier}
              data={priceHistoryData}
              loading={priceHistoryLoading}
              error={priceHistoryError}
              onRetry={reloadPriceHistory}
            />
          ) : null}
        </div>
      ) : null}
    </Modal>
  );
}

export function SafetyStockDetailsActionHint() {
  return (
    <span className="ess-table__action" aria-hidden="true">
      <ChevronRight size={16} />
    </span>
  );
}
