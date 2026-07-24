import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeftRight,
  ChevronRight,
  PackageCheck,
  ShieldCheck,
  Warehouse,
} from "lucide-react";
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
  SafetyStockProjectionSummary,
} from "../types/safetyStock";
import { formatNumberPtBr } from "../utils/formatters";
import { projectionSituationParts } from "../utils/projectionSituation";
import {
  branchLabel,
  dateStatusLabel,
  formatIsoDatePtBr,
  purchaseCoverageLabel,
  purchaseCoverageVariant,
} from "../utils/safetyStockStatus";
import { DataTable, type DataTableColumn } from "./dataTableUi";
import { KpiCard } from "./KpiCard";
import { SafetyStockDetailProductSearch } from "./SafetyStockDetailProductSearch";
import {
  SafetyStockLinkedSuppliersSection,
  supplierRowKey,
} from "./SafetyStockLinkedSuppliersSection";
import { SafetyStockSupplierPriceHistoryPanel } from "./SafetyStockSupplierPriceHistoryPanel";
import { ProductConsumptionChartsSection } from "./ProductConsumptionChartsSection";
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

function ProjectionSituation({ summary }: { summary: SafetyStockProjectionSummary }) {
  const parts = projectionSituationParts(summary);
  const valueClass = (value: number) =>
    value < 0 ? "ess-detail__situation-critical" : undefined;

  return (
    <p className="ess-detail__situation">
      Partindo de um saldo de{" "}
      <strong className={valueClass(summary.initial_balance)}>{parts.initialBalance}</strong>, com{" "}
      <strong className={valueClass(summary.eligible_purchase_quantity)}>
        {parts.purchaseQuantity}
      </strong>{" "}
      de entradas previstas e{" "}
      <strong className={valueClass(summary.eligible_commitment_quantity)}>
        {parts.commitmentQuantity}
      </strong>{" "}
      de consumo comprometido, o saldo final projetado é{" "}
      <strong className={valueClass(summary.final_projected_balance)}>{parts.finalBalance}</strong>.
      O menor saldo previsto no período é{" "}
      <strong className={valueClass(summary.minimum_projected_balance)}>
        {parts.minimumBalance}
      </strong>
      .{" "}
      {parts.shortageDate ? (
        <>
          A primeira ruptura está prevista para{" "}
          <strong className="ess-detail__situation-critical">{parts.shortageDate}</strong>.
        </>
      ) : (
        <>Não há ruptura projetada no período.</>
      )}
    </p>
  );
}

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
  const peerBranchStock = data?.peer_branch_stock ?? null;
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
      key: "finished_product_code",
      header: "Produto acabado",
      className: "ess-table__col--secondary",
      render: (row) => {
        const code = row.finished_product_code?.trim();
        if (!code) return "—";
        const observation = row.finished_order_observation?.trim();
        return (
          <span title={observation || undefined}>
            {code}
            {observation ? (
              <span className="ess-detail__muted"> · {observation}</span>
            ) : null}
          </span>
        );
      },
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
            <div className="ess-detail__balance-cards">
              <KpiCard
                title="Saldo disponível"
                value={formatNumberPtBr(stock.available_stock)}
                subtitle={
                  stock.last_inventory_date
                    ? `Último inventário: ${formatIsoDatePtBr(stock.last_inventory_date)}`
                    : "Sem inventário registrado"
                }
                icon={<PackageCheck size={20} />}
                wide
                className="ess-kpi-card--available-balance"
              />
              {peerBranchStock ? (
                <KpiCard
                  title={`Saldo ${branchLabel(peerBranchStock.branch)}`}
                  titleHint="Saldo disponível (01+98+99) na outra filial — útil para avaliar transferência de MP. A legenda mostra a última baixa de consumo elegível nessa filial."
                  value={formatNumberPtBr(peerBranchStock.available_stock)}
                  subtitle={
                    !peerBranchStock.found
                      ? "Produto sem cadastro/saldo nesta filial"
                      : peerBranchStock.last_consumption_date
                        ? `Último consumo: ${formatIsoDatePtBr(peerBranchStock.last_consumption_date)}`
                        : "Sem consumo registrado nesta filial"
                  }
                  icon={<ArrowLeftRight size={20} />}
                  wide
                />
              ) : null}
              <KpiCard
                title="Estoque de segurança"
                value={formatNumberPtBr(stock.safety_stock)}
                icon={<ShieldCheck size={20} />}
              />
              <KpiCard
                title="Armazém 01"
                value={formatNumberPtBr(stock.primary_stock)}
                icon={<Warehouse size={20} />}
              />
              <KpiCard
                title="Armazém 98"
                value={formatNumberPtBr(stock.warehouse_98_stock)}
                icon={<Warehouse size={20} />}
              />
              <KpiCard
                title="Armazém 99"
                value={formatNumberPtBr(stock.warehouse_99_stock)}
                icon={<Warehouse size={20} />}
              />
            </div>
          </section>

          <section className="ess-detail__section" aria-label="Projeção de saldo">
            <div className="ess-detail__section-header">
              <h3>Situação projetada</h3>
            </div>
            <ProjectionSituation summary={projectionSummary} />
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
                content="Linha do tempo consolidada: saldo atual, saídas por empenho (D4_QUANT) e entradas por pedido aberto. A data do empenho no extrato é o início previsto da OP do empenho (SC2.C2_DATPRI), não D4_DATA nem a OP do produto acabado."
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
              onClose={() => setSelectedSupplier(null)}
            />
          ) : null}

          <ProductConsumptionChartsSection
            monthlyPoints={data?.monthly_consumption?.items ?? []}
            periodConsumption={data?.monthly_consumption?.period_consumption ?? 0}
            periodStart={data?.monthly_consumption?.period_start ?? null}
            periodEnd={data?.monthly_consumption?.period_end ?? null}
            annualComparison={data?.annual_comparison}
            stockProjection={data?.stock_projection}
            loading={loading}
            resetKey={item ? `${item.branch}-${item.product_code}` : null}
          />
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
