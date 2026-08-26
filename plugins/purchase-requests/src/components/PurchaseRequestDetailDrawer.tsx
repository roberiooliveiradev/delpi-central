import type { PurchaseRequestDetail } from "../types/purchaseRequests";
import { formatDatePtBr, formatQuantity } from "../utils/formatters";
import {
  formatBuyerLabel,
  formatRequestNumber,
  formatRequesterName,
  labelApprovalStatus,
  labelDeliveryStatus,
  labelOverallStage,
  overallStageVariant,
} from "../utils/labels";
import {
  PurchaseRequestsModal,
  PurchaseRequestsLoadingState,
  PurchaseRequestsSectionCard,
  PurchaseRequestsStateBanner,
  PurchaseRequestsStatusBadge,
  PurchaseRequestsTimeline,
} from "../ui/purchaseRequestsUi";
import { detailErrorMessage } from "../utils/pageState";

type PurchaseRequestDetailDrawerProps = {
  open: boolean;
  onClose: () => void;
  loading: boolean;
  error: string | null;
  notFound: boolean;
  detail: PurchaseRequestDetail | null;
  onRetry: () => void;
};

export function PurchaseRequestDetailDrawer({
  open,
  onClose,
  loading,
  error,
  notFound,
  detail,
  onRetry,
}: PurchaseRequestDetailDrawerProps) {
  const header = detail?.header;

  return (
    <PurchaseRequestsModal
      open={open}
      onClose={onClose}
      title={header ? formatRequestNumber(header.request_number) : "Detalhe da solicitação"}
      description={
        header
          ? `Filial ${header.branch} · ${formatRequesterName(header.requester?.name, header.requester?.code)}`
          : undefined
      }
    >
      {loading ? <PurchaseRequestsLoadingState message="Carregando detalhe…" /> : null}

      {!loading && (error || notFound) ? (
        <div className="pr-detail-error">
          <PurchaseRequestsStateBanner variant="error">
            {detailErrorMessage(error, notFound)}
          </PurchaseRequestsStateBanner>
          <button type="button" className="pr-btn pr-btn--secondary" onClick={onRetry}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {!loading && detail ? (
        <div className="pr-detail">
          <PurchaseRequestsSectionCard title="Resumo">
            <dl className="pr-detail-grid">
              <div>
                <dt>Solicitante</dt>
                <dd>{formatRequesterName(header?.requester?.name, header?.requester?.code)}</dd>
              </div>
              <div>
                <dt>Abertura</dt>
                <dd>{formatDatePtBr(header?.issue_date)}</dd>
              </div>
              <div>
                <dt>Aprovação</dt>
                <dd>{labelApprovalStatus(header?.approval_summary?.status)}</dd>
              </div>
              <div>
                <dt>Situação</dt>
                <dd>
                  <PurchaseRequestsStatusBadge
                    label={labelOverallStage(header?.overall_stage)}
                    variant={overallStageVariant(header?.overall_stage)}
                  />
                </dd>
              </div>
              <div>
                <dt>Itens autorizados</dt>
                <dd>{header?.visible_items_count ?? detail.lines.length}</dd>
              </div>
            </dl>
          </PurchaseRequestsSectionCard>

          <PurchaseRequestsSectionCard title="Itens">
            <div className="pr-detail-items">
              {detail.lines.map((line) => (
                <article key={`${line.request_item}`} className="pr-detail-item">
                  <header>
                    <strong>{line.product_code || "—"}</strong>
                    <span>{line.product_description || "—"}</span>
                  </header>
                  <dl>
                    <div>
                      <dt>CC</dt>
                      <dd>
                        {line.cost_center?.code || line.cost_center_code || "—"}
                        {line.cost_center?.description ? ` · ${line.cost_center.description}` : ""}
                      </dd>
                    </div>
                    <div>
                      <dt>Solicitado</dt>
                      <dd>{formatQuantity(line.requested_quantity)}</dd>
                    </div>
                    <div>
                      <dt>Em pedido</dt>
                      <dd>{formatQuantity(line.ordered_quantity)}</dd>
                    </div>
                    <div>
                      <dt>Saldo</dt>
                      <dd>
                        {formatQuantity(
                          (line.requested_quantity ?? 0) - (line.ordered_quantity ?? 0),
                        )}
                      </dd>
                    </div>
                    <div>
                      <dt>Necessidade</dt>
                      <dd>{formatDatePtBr(line.original_need_date)}</dd>
                    </div>
                  </dl>
                </article>
              ))}
            </div>
          </PurchaseRequestsSectionCard>

          <PurchaseRequestsSectionCard title="Pedidos de compra">
            <div className="pr-detail-items">
              {detail.lines.flatMap((line) =>
                (line.purchase_orders ?? []).map((order) => (
                  <article
                    key={`${order.order_number}-${order.order_item}-${line.request_item}`}
                    className="pr-detail-item"
                  >
                    <header>
                      <strong>PC {order.order_number || "—"}</strong>
                      <span>Item {order.order_item || "—"}</span>
                    </header>
                    <dl>
                      <div>
                        <dt>Fornecedor</dt>
                        <dd>{order.supplier_name || order.supplier_code || "—"}</dd>
                      </div>
                      <div>
                        <dt>Emissão</dt>
                        <dd>{formatDatePtBr(order.issue_date)}</dd>
                      </div>
                      <div>
                        <dt>Previsão</dt>
                        <dd>{formatDatePtBr(order.expected_delivery_date)}</dd>
                      </div>
                      <div>
                        <dt>Quantidade</dt>
                        <dd>{formatQuantity(order.ordered_quantity)}</dd>
                      </div>
                      <div>
                        <dt>Recebido</dt>
                        <dd>{formatQuantity(order.received_quantity)}</dd>
                      </div>
                      <div>
                        <dt>Saldo</dt>
                        <dd>{formatQuantity(order.open_quantity)}</dd>
                      </div>
                      <div>
                        <dt>Comprador</dt>
                        <dd>{formatBuyerLabel(order.buyer)}</dd>
                      </div>
                      <div>
                        <dt>Prazo</dt>
                        <dd>{labelDeliveryStatus(order.derived?.delivery_status)}</dd>
                      </div>
                    </dl>
                  </article>
                )),
              )}
              {detail.lines.every((line) => (line.purchase_orders?.length ?? 0) === 0) ? (
                <p className="pr-muted">Nenhum pedido de compra vinculado.</p>
              ) : null}
            </div>
          </PurchaseRequestsSectionCard>

          <PurchaseRequestsSectionCard title="Recebimentos">
            <div className="pr-detail-items">
              {detail.lines.flatMap((line) =>
                (line.purchase_orders ?? []).flatMap((order) =>
                  (order.receipts ?? []).map((receipt) => (
                    <article
                      key={`${receipt.invoice_number}-${receipt.invoice_series}-${receipt.invoice_item}`}
                      className="pr-detail-item"
                    >
                      <header>
                        <strong>
                          NF {receipt.invoice_number || "—"}
                          {receipt.invoice_series ? `/${receipt.invoice_series}` : ""}
                        </strong>
                      </header>
                      <dl>
                        <div>
                          <dt>Quantidade</dt>
                          <dd>{formatQuantity(receipt.quantity)}</dd>
                        </div>
                        <div>
                          <dt>Emissão fiscal</dt>
                          <dd>{formatDatePtBr(receipt.invoice_issue_date)}</dd>
                        </div>
                        <div>
                          <dt>Entrada TOTVS</dt>
                          <dd>{formatDatePtBr(receipt.entry_date)}</dd>
                        </div>
                      </dl>
                    </article>
                  )),
                ),
              )}
              {detail.lines.every((line) =>
                (line.purchase_orders ?? []).every((order) => (order.receipts?.length ?? 0) === 0),
              ) ? (
                <p className="pr-muted">Nenhum recebimento registrado.</p>
              ) : null}
            </div>
          </PurchaseRequestsSectionCard>

          <PurchaseRequestsSectionCard title="Timeline">
            <PurchaseRequestsTimeline
              items={(detail.timeline ?? []).map((event) => ({
                id: `${event.type}-${event.date}-${JSON.stringify(event.reference ?? {})}`,
                title: event.label || event.type,
                occurredAt: event.date || undefined,
                timeLabel: formatDatePtBr(event.date),
                detail: Object.values(event.reference ?? {})
                  .filter(Boolean)
                  .join(" · "),
              }))}
            />
          </PurchaseRequestsSectionCard>
        </div>
      ) : null}
    </PurchaseRequestsModal>
  );
}
