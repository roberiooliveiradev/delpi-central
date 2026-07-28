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

function isLinkedGroup(
  group: OpenPurchaseOrderGroup,
  linked: LinkedPurchaseOrderSnapshot[],
): boolean {
  return linked.some(
    (item) =>
      group.order_number === item.order_number &&
      (group.delivery_date ?? null) === (item.delivery_date ?? null),
  );
}

function normalizeLinked(raw: unknown): LinkedPurchaseOrderSnapshot[] {
  if (Array.isArray(raw)) return raw;
  if (raw && typeof raw === "object") return [raw as LinkedPurchaseOrderSnapshot];
  return [];
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
  const [linked, setLinked] = useState<LinkedPurchaseOrderSnapshot[]>([]);
  const [orderCount, setOrderCount] = useState(0);
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setSelectedKeys(new Set());
    setExpandedKey(null);
    void api
      .listRequestPurchaseOrders(requestId, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const nextGroups = data.groups ?? [];
        const nextLinked = normalizeLinked(data.linked);
        setGroups(nextGroups);
        setLinked(nextLinked);
        setOrderCount(data.order_count ?? 0);
        const preselected = new Set<string>();
        for (const group of nextGroups) {
          if (isLinkedGroup(group, nextLinked)) {
            preselected.add(groupKey(group));
          }
        }
        setSelectedKeys(preselected);
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
        setLinked([]);
        setOrderCount(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [open, requestId]);

  const selectedGroups = useMemo(
    () => groups.filter((g) => selectedKeys.has(groupKey(g))),
    [groups, selectedKeys],
  );

  function toggleKey(key: string) {
    setSelectedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function handleLink() {
    if (!canLink || linking) return;
    setLinking(true);
    setError(null);
    try {
      await api.linkRequestPurchaseOrder(requestId, {
        groups: selectedGroups.map((group) => ({
          order_number: group.order_number,
          delivery_date: group.delivery_date,
        })),
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

  const selectionChanged =
    selectedGroups.length !== linked.length ||
    selectedGroups.some((g) => !isLinkedGroup(g, linked)) ||
    linked.some(
      (item) =>
        !selectedGroups.some(
          (g) =>
            g.order_number === item.order_number &&
            (g.delivery_date ?? null) === (item.delivery_date ?? null),
        ),
    );

  return (
    <div className="lnf-modal-backdrop" role="presentation">
      <div
        className="lnf-modal lnf-modal--wide"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lnf-po-title"
      >
        <div className="lnf-modal__header">
          <h2 id="lnf-po-title">Pedidos de compra</h2>
          <button
            type="button"
            className="lnf-modal__close"
            onClick={onClose}
            disabled={linking}
            aria-label="Fechar"
            data-testid="po-close-btn"
          >
            ×
          </button>
        </div>
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
                {canLink
                  ? ` · ${selectedKeys.size} selecionado(s)`
                  : null}
              </p>
              {linked.length > 0 ? (
                <p className="lnf-po-linked-banner" data-testid="po-linked-banner">
                  Amarrado atualmente:{" "}
                  <strong>
                    {linked
                      .map((item) =>
                        linkedPurchaseOrderLabel(
                          item.order_number,
                          item.delivery_date,
                        ),
                      )
                      .join(" · ")}
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
                      const linkedNow = isLinkedGroup(group, linked);
                      const checked = selectedKeys.has(key);
                      return (
                        <Fragment key={key}>
                          <tr
                            className={
                              linkedNow || checked ? "lnf-po-row--linked" : undefined
                            }
                            data-testid={`po-group-${group.order_number}`}
                          >
                            {canLink ? (
                              <td>
                                <input
                                  type="checkbox"
                                  aria-label={`Selecionar PC ${group.order_number}`}
                                  checked={checked}
                                  onChange={() => toggleKey(key)}
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
              disabled={linking || loading || !selectionChanged}
              onClick={() => void handleLink()}
              data-testid="po-link-btn"
            >
              {linking
                ? "Salvando…"
                : selectedKeys.size === 0
                  ? "Desamarrar todos"
                  : `Salvar amarração (${selectedKeys.size})`}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
