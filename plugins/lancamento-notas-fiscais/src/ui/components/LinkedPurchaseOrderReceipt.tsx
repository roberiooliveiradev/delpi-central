import { useEffect, useMemo, useState } from "react";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoicePostingApi";
import type {
  InvoicePostingRequest,
  LinkedPurchaseOrderSnapshot,
  OpenPurchaseOrderGroup,
  OpenPurchaseOrderItem,
} from "../../domain/types";
import {
  formatDate,
  formatDateTime,
  formatMoney,
  linkedPurchaseOrderLabel,
} from "../format";

type Props = {
  requestId: string;
  request: InvoicePostingRequest;
};

function formatQty(value: number, unit: string): string {
  const qty = Number.isFinite(value) ? value : 0;
  const formatted = qty.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
  const um = (unit || "").trim();
  return um ? `${formatted} ${um}` : formatted;
}

function linkedFromRequest(request: InvoicePostingRequest): LinkedPurchaseOrderSnapshot[] {
  if (Array.isArray(request.linked_purchase_orders) && request.linked_purchase_orders.length) {
    return request.linked_purchase_orders;
  }
  if (request.linked_po_number) {
    return [
      {
        order_number: request.linked_po_number,
        delivery_date: request.linked_po_delivery_date,
        issue_date: request.linked_po_issue_date,
        open_value: request.linked_po_open_value,
        product_count: request.linked_po_product_count,
        linked_at: request.linked_po_linked_at,
        linked_by_user_id: request.linked_po_linked_by_user_id,
        linked_by_name: request.linked_po_linked_by_name,
      },
    ];
  }
  return [];
}

function matchGroup(
  group: OpenPurchaseOrderGroup,
  linked: LinkedPurchaseOrderSnapshot,
): boolean {
  return (
    group.order_number === linked.order_number &&
    (group.delivery_date ?? null) === (linked.delivery_date ?? null)
  );
}

function filterLinkedItems(
  items: OpenPurchaseOrderItem[],
  linked: LinkedPurchaseOrderSnapshot,
): OpenPurchaseOrderItem[] {
  const lines = linked.lines ?? [];
  if (lines.length === 0) return items;
  const wanted = new Set(
    lines.map((line) => String(line.order_item || "").trim()).filter(Boolean),
  );
  if (wanted.size === 0) return items;
  return items.filter((item) => wanted.has(String(item.order_item || "").trim()));
}

type ReceiptBlock = {
  linked: LinkedPurchaseOrderSnapshot;
  group: OpenPurchaseOrderGroup | null;
  items: OpenPurchaseOrderItem[];
};

export function LinkedPurchaseOrderReceipt({ requestId, request }: Props) {
  const linkedSnapshots = useMemo(() => linkedFromRequest(request), [request]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [blocks, setBlocks] = useState<ReceiptBlock[]>([]);

  useEffect(() => {
    if (linkedSnapshots.length === 0) {
      setBlocks([]);
      setLoading(false);
      setError(null);
      return;
    }

    const controller = new AbortController();
    setLoading(true);
    setError(null);

    void api
      .listRequestPurchaseOrders(requestId, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const groups = data.groups ?? [];
        setBlocks(
          linkedSnapshots.map((linked) => {
            const group = groups.find((g) => matchGroup(g, linked)) ?? null;
            const items = filterLinkedItems(group?.items ?? [], linked);
            return {
              linked,
              group,
              items,
            };
          }),
        );
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError(
            err instanceof Error
              ? err.message
              : "Falha ao carregar itens do pedido de compra.",
          );
        }
        setBlocks(
          linkedSnapshots.map((linked) => ({
            linked,
            group: null,
            items: [],
          })),
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [
    requestId,
    linkedSnapshots,
    request.linked_po_linked_at,
  ]);

  if (linkedSnapshots.length === 0) return null;

  const grandTotal = blocks.reduce((acc, block) => {
    const value =
      block.group?.open_value ??
      (block.linked.open_value != null ? Number(block.linked.open_value) : 0);
    return acc + Number(value || 0);
  }, 0);

  return (
    <section
      className="lnf-card lnf-po-receipt"
      data-testid="linked-po-receipt"
      aria-label="Itens dos pedidos de compra amarrados"
    >
      <div className="lnf-po-receipt__paper">
        <header className="lnf-po-receipt__header">
          <p className="lnf-po-receipt__eyebrow">Pedidos amarrados</p>
          <h2 className="lnf-po-receipt__title">Cupom do pedido de compra</h2>
          <p className="lnf-po-receipt__subtitle">
            {linkedSnapshots.length} pedido(s) · Filial {request.branch_code} ·{" "}
            {request.supplier_name}
          </p>
        </header>

        {loading ? (
          <p className="lnf-muted" data-testid="linked-po-receipt-loading">
            Carregando itens do pedido…
          </p>
        ) : null}

        {!loading && error ? (
          <p className="lnf-error" role="alert">
            {error}
          </p>
        ) : null}

        {!loading
          ? blocks.map((block, index) => {
              const { linked, group, items } = block;
              const total =
                group?.open_value ??
                (linked.open_value != null ? Number(linked.open_value) : null);
              const productCount =
                group?.product_count ?? linked.product_count ?? items.length;
              return (
                <div
                  key={`${linked.order_number}|${linked.delivery_date ?? ""}`}
                  className="lnf-po-receipt__block"
                  data-testid={`linked-po-receipt-block-${linked.order_number}`}
                >
                  {index > 0 ? (
                    <div className="lnf-po-receipt__divider" aria-hidden="true" />
                  ) : null}
                  <div className="lnf-po-receipt__meta">
                    <div>
                      <span>Pedido</span>
                      <strong>
                        {linkedPurchaseOrderLabel(
                          linked.order_number,
                          linked.delivery_date,
                        )}
                      </strong>
                    </div>
                    {linked.issue_date ? (
                      <div>
                        <span>Emissão PC</span>
                        <strong>{formatDate(linked.issue_date)}</strong>
                      </div>
                    ) : null}
                    {linked.linked_at ? (
                      <div>
                        <span>Amarrado em</span>
                        <strong>{formatDateTime(linked.linked_at)}</strong>
                      </div>
                    ) : null}
                    {linked.linked_by_name ? (
                      <div>
                        <span>Por</span>
                        <strong>{linked.linked_by_name}</strong>
                      </div>
                    ) : null}
                  </div>

                  {items.length === 0 ? (
                    <div
                      className="lnf-po-receipt__empty"
                      data-testid="linked-po-receipt-empty"
                    >
                      <p>
                        O pedido <strong>PC {linked.order_number}</strong> está
                        amarrado, mas os itens abertos não estão disponíveis no
                        Protheus no momento.
                      </p>
                      <p className="lnf-muted">
                        {productCount != null ? `${productCount} produto(s)` : null}
                        {total != null
                          ? ` · total registrado ${formatMoney(total)}`
                          : null}
                      </p>
                    </div>
                  ) : (
                    <ul className="lnf-po-receipt__items">
                      <li className="lnf-po-receipt__item lnf-po-receipt__item--head lnf-po-receipt__item--split">
                        <span>Item</span>
                        <span className="lnf-po-receipt__qty">Qtd</span>
                        <span className="lnf-po-receipt__value">Mercadoria</span>
                        <span className="lnf-po-receipt__value lnf-po-receipt__value--ipi">
                          IPI
                        </span>
                      </li>
                      {items.map((item) => {
                        const merchandise = Number(
                          item.open_merchandise_value ??
                            Math.max(
                              0,
                              Number(item.open_value || 0) -
                                Number(item.open_ipi_value || 0),
                            ),
                        );
                        const ipi = Number(item.open_ipi_value || 0);
                        return (
                          <li
                            key={`${item.order_number}-${item.order_item}-${item.product_code}`}
                            className="lnf-po-receipt__item lnf-po-receipt__item--split"
                          >
                            <div className="lnf-po-receipt__item-main">
                              <span className="lnf-po-receipt__sku">
                                {item.product_code}
                                {item.supplier_part_number ? (
                                  <span
                                    className="lnf-po-receipt__supplier-pn"
                                    title="Código do produto no fornecedor"
                                  >
                                    {" "}
                                    · {item.supplier_part_number}
                                  </span>
                                ) : null}
                              </span>
                              <span className="lnf-po-receipt__desc">
                                {item.product_description || "Produto sem descrição"}
                              </span>
                              <span className="lnf-po-receipt__item-sub">
                                Item {item.order_item}
                                {item.warehouse ? ` · armazém ${item.warehouse}` : ""}
                              </span>
                            </div>
                            <div className="lnf-po-receipt__qty">
                              {formatQty(item.open_quantity, item.unit)}
                            </div>
                            <div className="lnf-po-receipt__value">
                              {formatMoney(merchandise)}
                            </div>
                            <div className="lnf-po-receipt__value lnf-po-receipt__value--ipi">
                              {ipi > 0 ? formatMoney(ipi) : "—"}
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  )}

                  {(() => {
                    const merchandiseTotal = items.reduce(
                      (acc, item) =>
                        acc +
                        Number(
                          item.open_merchandise_value ??
                            Math.max(
                              0,
                              Number(item.open_value || 0) -
                                Number(item.open_ipi_value || 0),
                            ),
                        ),
                      0,
                    );
                    const ipiTotal = items.reduce(
                      (acc, item) => acc + Number(item.open_ipi_value || 0),
                      0,
                    );
                    return (
                      <div className="lnf-po-receipt__footer">
                        <div className="lnf-po-receipt__footer-row">
                          <span>Mercadorias {linked.order_number}</span>
                          <strong>{formatMoney(merchandiseTotal)}</strong>
                        </div>
                        <div className="lnf-po-receipt__footer-row">
                          <span>IPI {linked.order_number}</span>
                          <strong>{formatMoney(ipiTotal)}</strong>
                        </div>
                        <div className="lnf-po-receipt__footer-row">
                          <span>Subtotal {linked.order_number}</span>
                          <strong>
                            {total != null ? formatMoney(total) : "—"}
                          </strong>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              );
            })
          : null}

        {!loading && blocks.length > 0 ? (
          <>
            <div className="lnf-po-receipt__divider" aria-hidden="true" />
            <footer className="lnf-po-receipt__footer">
              <div className="lnf-po-receipt__footer-row lnf-po-receipt__footer-row--total">
                <span>Total em aberto</span>
                <strong data-testid="linked-po-receipt-total">
                  {formatMoney(grandTotal)}
                </strong>
              </div>
            </footer>
          </>
        ) : null}

        <div className="lnf-po-receipt__barcode" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>
        <p className="lnf-po-receipt__thanks">*** pedidos vinculados à solicitação ***</p>
      </div>
      <div className="lnf-po-receipt__perforation" aria-hidden="true" />
    </section>
  );
}
