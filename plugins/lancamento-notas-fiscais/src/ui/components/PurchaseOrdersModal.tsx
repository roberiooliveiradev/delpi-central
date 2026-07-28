import { Fragment, useEffect, useMemo, useState } from "react";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoicePostingApi";
import type {
  LinkedPurchaseOrderSnapshot,
  OpenPurchaseOrderGroup,
  OpenPurchaseOrderItem,
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

function lineKey(
  group: Pick<OpenPurchaseOrderGroup, "order_number" | "delivery_date">,
  orderItem: string,
): string {
  return `${groupKey(group)}|${orderItem}`;
}

function formatQty(value: number, unit: string): string {
  const qty = Number.isFinite(value) ? value : 0;
  const formatted = qty.toLocaleString("pt-BR", { maximumFractionDigits: 3 });
  const um = (unit || "").trim();
  return um ? `${formatted} ${um}` : formatted;
}

function isSameGroup(
  group: OpenPurchaseOrderGroup,
  linked: LinkedPurchaseOrderSnapshot,
): boolean {
  return (
    group.order_number === linked.order_number &&
    (group.delivery_date ?? null) === (linked.delivery_date ?? null)
  );
}

function normalizeLinked(raw: unknown): LinkedPurchaseOrderSnapshot[] {
  if (Array.isArray(raw)) return raw;
  if (raw && typeof raw === "object") return [raw as LinkedPurchaseOrderSnapshot];
  return [];
}

function preselectLineKeys(
  groups: OpenPurchaseOrderGroup[],
  linked: LinkedPurchaseOrderSnapshot[],
): Set<string> {
  const next = new Set<string>();
  for (const group of groups) {
    const match = linked.find((item) => isSameGroup(group, item));
    if (!match) continue;
    const savedLines = match.lines ?? [];
    if (savedLines.length === 0) {
      for (const item of group.items) {
        if (item.order_item) next.add(lineKey(group, item.order_item));
      }
    } else {
      for (const line of savedLines) {
        if (line.order_item) next.add(lineKey(group, line.order_item));
      }
    }
  }
  return next;
}

function linkedLineKeySet(
  groups: OpenPurchaseOrderGroup[],
  linked: LinkedPurchaseOrderSnapshot[],
): Set<string> {
  return preselectLineKeys(groups, linked);
}

function setsEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false;
  for (const key of a) {
    if (!b.has(key)) return false;
  }
  return true;
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
  const [selectedLineKeys, setSelectedLineKeys] = useState<Set<string>>(new Set());
  const [expandedKey, setExpandedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setSelectedLineKeys(new Set());
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
        setSelectedLineKeys(preselectLineKeys(nextGroups, nextLinked));
        const firstLinked = nextGroups.find((g) =>
          nextLinked.some((item) => isSameGroup(g, item)),
        );
        if (firstLinked) {
          setExpandedKey(groupKey(firstLinked));
        } else if (canLink && nextGroups[0]) {
          setExpandedKey(groupKey(nextGroups[0]));
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
        setLinked([]);
        setOrderCount(0);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [open, requestId, canLink]);

  const selectedGroupsPayload = useMemo(() => {
    const payload: Array<{
      order_number: string;
      delivery_date: string | null;
      lines: Array<{ order_item: string }>;
    }> = [];
    for (const group of groups) {
      const lines = group.items
        .filter(
          (item) =>
            item.order_item && selectedLineKeys.has(lineKey(group, item.order_item)),
        )
        .map((item) => ({ order_item: item.order_item }));
      if (lines.length === 0) continue;
      payload.push({
        order_number: group.order_number,
        delivery_date: group.delivery_date,
        lines,
      });
    }
    return payload;
  }, [groups, selectedLineKeys]);

  function toggleLine(group: OpenPurchaseOrderGroup, item: OpenPurchaseOrderItem) {
    if (!item.order_item) return;
    const key = lineKey(group, item.order_item);
    setSelectedLineKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toggleGroup(group: OpenPurchaseOrderGroup) {
    const itemKeys = group.items
      .filter((item) => item.order_item)
      .map((item) => lineKey(group, item.order_item));
    if (itemKeys.length === 0) return;
    setSelectedLineKeys((prev) => {
      const next = new Set(prev);
      const allSelected = itemKeys.every((key) => next.has(key));
      if (allSelected) {
        for (const key of itemKeys) next.delete(key);
      } else {
        for (const key of itemKeys) next.add(key);
      }
      return next;
    });
  }

  function groupSelectionState(group: OpenPurchaseOrderGroup): {
    checked: boolean;
    indeterminate: boolean;
  } {
    const itemKeys = group.items
      .filter((item) => item.order_item)
      .map((item) => lineKey(group, item.order_item));
    if (itemKeys.length === 0) return { checked: false, indeterminate: false };
    const selectedCount = itemKeys.filter((key) => selectedLineKeys.has(key)).length;
    return {
      checked: selectedCount === itemKeys.length,
      indeterminate: selectedCount > 0 && selectedCount < itemKeys.length,
    };
  }

  async function handleLink() {
    if (!canLink || linking) return;
    setLinking(true);
    setError(null);
    try {
      await api.linkRequestPurchaseOrder(requestId, {
        groups: selectedGroupsPayload,
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

  const linkedKeys = linkedLineKeySet(groups, linked);
  const selectionChanged = !setsEqual(selectedLineKeys, linkedKeys);
  const selectedGroupCount = selectedGroupsPayload.length;

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
                  ? ` · ${selectedLineKeys.size} item(ns) · ${selectedGroupCount} grupo(s)`
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
                      const linkedNow = linked.some((item) => isSameGroup(group, item));
                      const { checked, indeterminate } = groupSelectionState(group);
                      return (
                        <Fragment key={key}>
                          <tr
                            className={
                              linkedNow || checked || indeterminate
                                ? "lnf-po-row--linked"
                                : undefined
                            }
                            data-testid={`po-group-${group.order_number}`}
                          >
                            {canLink ? (
                              <td>
                                <input
                                  type="checkbox"
                                  aria-label={`Selecionar PC ${group.order_number}`}
                                  checked={checked}
                                  ref={(el) => {
                                    if (el) el.indeterminate = indeterminate;
                                  }}
                                  onChange={() => toggleGroup(group)}
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
                                      {canLink ? (
                                        <th className="lnf-po-col-select">Sel.</th>
                                      ) : null}
                                      <th>Item</th>
                                      <th>Produto</th>
                                      <th>Saldo</th>
                                      <th>Mercadoria</th>
                                      <th>IPI</th>
                                      <th>Total</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {group.items.map((row) => {
                                      const itemChecked =
                                        !!row.order_item &&
                                        selectedLineKeys.has(
                                          lineKey(group, row.order_item),
                                        );
                                      return (
                                        <tr
                                          key={`${row.order_number}-${row.order_item}-${row.product_code}`}
                                        >
                                          {canLink ? (
                                            <td>
                                              <input
                                                type="checkbox"
                                                aria-label={`Selecionar item ${row.order_item} do PC ${group.order_number}`}
                                                checked={itemChecked}
                                                onChange={() => toggleLine(group, row)}
                                                data-testid={`po-line-${key}-${row.order_item}`}
                                              />
                                            </td>
                                          ) : null}
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
                                            {formatMoney(
                                              Number(row.open_merchandise_value || 0),
                                            )}
                                          </td>
                                          <td>
                                            {Number(row.open_ipi_value || 0) > 0
                                              ? formatMoney(Number(row.open_ipi_value))
                                              : "—"}
                                          </td>
                                          <td>
                                            {formatMoney(Number(row.open_value || 0))}
                                          </td>
                                        </tr>
                                      );
                                    })}
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
                : selectedLineKeys.size === 0
                  ? "Desamarrar todos"
                  : `Salvar amarração (${selectedLineKeys.size} it.)`}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
