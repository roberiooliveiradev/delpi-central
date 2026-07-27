import { Fragment, useEffect, useMemo, useState } from "react";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoicePostingApi";
import type {
  LinkedPurchaseOrderSnapshot,
  OpenPurchaseOrderGroup,
} from "../../domain/types";
import { formatDate, formatMoney, linkedPurchaseOrderLabel } from "../format";

type Props = {
  open: boolean;
  requestId: string;
  supplierName: string;
  branchCode: string;
  canLink: boolean;
  onClose: () => void;
  onLinked?: () => void;
};

function groupKey(group: Pick<OpenPurchaseOrderGroup, "order_number" | "delivery_date">): string {
  return `${group.order_number}|${group.delivery_date ?? ""}`;
}

function formatQty(value: number, unit: string): string {
  const qty = Number.isFinite(value) ? value : 0;
  const formatted = qty.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
  const um = (unit || "").trim();
  return um ? `${formatted} ${um}` : formatted;
}

function isSameLink(
  group: OpenPurchaseOrderGroup,
  linked: LinkedPurchaseOrderSnapshot | null,
): boolean {
  if (!linked) return false;
  return (
    group.order_number === linked.order_number &&
    (group.delivery_date ?? null) === (linked.delivery_date ?? null)
  );
}

export function PurchaseOrdersModal({
  open,
  requestId,
  supplierName,
  branchCode,
  canLink,
  onClose,
  onLinked,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [linking, setLinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [groups, setGroups] = useState<OpenPurchaseOrderGroup[]>([]);
  const [linked, setLinked] = useState<LinkedPurchaseOrderSnapshot | null>(null);
  const [orderCount, setOrderCount] = useState(0);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setSelectedKey(null);
    setExpandedKey(null);
    void api
      .listRequestPurchaseOrders(requestId, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const nextGroups = data.groups ?? [];
        setGroups(nextGroups);
        setLinked(data.linked ?? null);
        setOrderCount(data.order_count ?? 0);
        if (data.linked) {
          const match = nextGroups.find((g) => isSameLink(g, data.linked));
          if (match) setSelectedKey(groupKey(match));
        }
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError(
            err instanceof Error
              ? err.message
              : "Falha ao consultar pedidos de compra no Protheus.",
          );
        }
        setGroups([]);
        setLinked(null);
        setOrderCount(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [open, requestId]);

  const selectedGroup = useMemo(
    () => groups.find((g) => groupKey(g) === selectedKey) ?? null,
    [groups, selectedKey],
  );

  async function handleLink() {
    if (!selectedGroup || !canLink || linking) return;
    setLinking(true);
    setError(null);
    try {
      await api.linkRequestPurchaseOrder(requestId, {
        order_number: selectedGroup.order_number,
        delivery_date: selectedGroup.delivery_date,
      });
      onLinked?.();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          err instanceof Error ? err.message : "Falha ao amarrar pedido de compra.",
        );
      }
    } finally {
      setLinking(false);
    }
  }

  if (!open) return null;

  return (
    <div className="lnf-modal-backdrop" role="presentation">
      <div
        className="lnf-modal lnf-modal--wide"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lnf-po-title"
      >
        <h2 id="lnf-po-title">Pedidos de compra</h2>
        <p className="lnf-muted">
          Em aberto no Protheus · Filial {branchCode} · {supplierName}
        </p>

        {loading ? <p data-testid="po-loading">Consultando Protheus…</p> : null}
        {error ? (
          <p className="lnf-error" role="alert">
            {error}
          </p>
        ) : null}

        {!loading && !error ? (
          groups.length === 0 ? (
            <p className="lnf-muted" data-testid="po-empty">
              Nenhum pedido de compra em aberto para este fornecedor na filial.
            </p>
          ) : (
            <>
              <p className="lnf-muted" data-testid="po-summary">
                {orderCount} pedido(s) · {groups.length} grupo(s)
              </p>
              {linked ? (
                <p className="lnf-po-linked-banner" data-testid="po-linked-banner">
                  Amarrado atualmente:{" "}
                  <strong>
                    {linkedPurchaseOrderLabel(
                      linked.order_number,
                      linked.delivery_date,
                    )}
                  </strong>
                </p>
              ) : null}
              <div className="lnf-table-wrap">
                <table className="lnf-table" data-testid="po-table">
                  <thead>
                    <tr>
                      {canLink ? <th className="lnf-po-col-select">Sel.</th> : null}
                      <th>PC</th>
                      <th>Produtos</th>
                      <th>Emissão</th>
                      <th>Entrega</th>
                      <th>Valor aberto</th>
                      <th>Detalhes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {groups.map((group) => {
                      const key = groupKey(group);
                      const expanded = expandedKey === key;
                      const linkedNow = isSameLink(group, linked);
                      return (
                        <Fragment key={key}>
                          <tr
                            className={
                              linkedNow ? "lnf-po-row--linked" : undefined
                            }
                            data-testid={`po-group-${group.order_number}`}
                          >
                            {canLink ? (
                              <td>
                                <input
                                  type="radio"
                                  name="lnf-po-select"
                                  aria-label={`Selecionar PC ${group.order_number}`}
                                  checked={selectedKey === key}
                                  onChange={() => setSelectedKey(key)}
                                  data-testid={`po-select-${key}`}
                                />
                              </td>
                            ) : null}
                            <td>
                              <strong>{group.order_number || "—"}</strong>
                              {linkedNow ? (
                                <div className="lnf-po-badge">Amarrado</div>
                              ) : null}
                            </td>
                            <td>{group.product_count}</td>
                            <td>{formatDate(group.issue_date)}</td>
                            <td>
                              {group.delivery_date
                                ? formatDate(group.delivery_date)
                                : "Sem data de entrega"}
                            </td>
                            <td>{formatMoney(Number(group.open_value || 0))}</td>
                            <td>
                              <button
                                type="button"
                                className="lnf-btn lnf-btn--ghost lnf-btn--compact"
                                onClick={() =>
                                  setExpandedKey(expanded ? null : key)
                                }
                                data-testid={`po-details-${key}`}
                              >
                                {expanded ? "Ocultar" : "Ver detalhes"}
                              </button>
                            </td>
                          </tr>
                          {expanded ? (
                            <tr className="lnf-po-details-row">
                              <td colSpan={canLink ? 7 : 6}>
                                <table className="lnf-table lnf-table--nested">
                                  <thead>
                                    <tr>
                                      <th>Item</th>
                                      <th>Produto</th>
                                      <th>Saldo</th>
                                      <th>Valor aberto</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {group.items.map((row) => (
                                      <tr
                                        key={`${row.order_number}-${row.order_item}-${row.product_code}`}
                                      >
                                        <td>{row.order_item || "—"}</td>
                                        <td>
                                          <strong>{row.product_code || "—"}</strong>
                                          {row.product_description ? (
                                            <div className="lnf-muted">
                                              {row.product_description}
                                            </div>
                                          ) : null}
                                        </td>
                                        <td>
                                          {formatQty(row.open_quantity, row.unit)}
                                        </td>
                                        <td>
                                          {formatMoney(Number(row.open_value || 0))}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </td>
                            </tr>
                          ) : null}
                        </Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )
        ) : null}

        <div className="lnf-modal__actions">
          <button
            type="button"
            className="lnf-btn lnf-btn--ghost"
            onClick={onClose}
            disabled={linking}
          >
            Fechar
          </button>
          {canLink ? (
            <button
              type="button"
              className="lnf-btn lnf-btn--primary"
              disabled={!selectedGroup || linking || loading}
              onClick={() => void handleLink()}
              data-testid="po-link-btn"
            >
              {linking ? "Amarrando…" : "Amarrar à solicitação"}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
