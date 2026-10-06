import { Fragment, useEffect, useMemo, useState } from "react";
import type {
  LinkedPurchaseOrderSnapshot,
  OpenPurchaseOrderGroup,
  OpenPurchaseOrderItem,
} from "../../domain/types";
import { formatDate, formatMoney, linkedPurchaseOrderLabel } from "../format";
import { filterPurchaseOrderGroupsByProductCodes } from "./purchaseOrderProductFilter";

export type PurchaseOrderGroupSelection = {
  order_number: string;
  delivery_date: string | null;
  lines: Array<{ order_item: string }>;
};

type Props = {
  groups: OpenPurchaseOrderGroup[];
  orderCount: number;
  loading: boolean;
  error: string | null;
  canSelect: boolean;
  selectedLineKeys: Set<string>;
  onSelectedLineKeysChange: (next: Set<string>) => void;
  linked?: LinkedPurchaseOrderSnapshot[];
  emptyMessage?: string;
  /** Códigos Delpi da NF-e. Presente só quando todos os itens estão relacionados. */
  restrictToProductCodes?: string[] | null;
};

export function groupKey(
  group: Pick<OpenPurchaseOrderGroup, "order_number" | "delivery_date">,
): string {
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

export function preselectLineKeys(
  groups: OpenPurchaseOrderGroup[],
  linked: Array<Pick<LinkedPurchaseOrderSnapshot, "order_number" | "delivery_date" | "lines">>,
): Set<string> {
  const next = new Set<string>();
  for (const group of groups) {
    const match = linked.find((item) => isSameGroup(group, item as LinkedPurchaseOrderSnapshot));
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

export function selectedGroupsFromLineKeys(
  groups: OpenPurchaseOrderGroup[],
  selectedLineKeys: Set<string>,
): PurchaseOrderGroupSelection[] {
  const payload: PurchaseOrderGroupSelection[] = [];
  for (const group of groups) {
    const lines = group.items
      .filter((item) => item.order_item && selectedLineKeys.has(lineKey(group, item.order_item)))
      .map((item) => ({ order_item: item.order_item }));
    if (lines.length === 0) continue;
    payload.push({
      order_number: group.order_number,
      delivery_date: group.delivery_date,
      lines,
    });
  }
  return payload;
}

function normalizeFilterQuery(value: string): string {
  return value.trim().toLowerCase();
}

function textIncludes(haystack: unknown, query: string): boolean {
  if (!query) return true;
  return String(haystack ?? "").trim().toLowerCase().includes(query);
}

function itemMatchesFilter(item: OpenPurchaseOrderItem, query: string): boolean {
  if (!query) return true;
  return (
    textIncludes(item.product_code, query) ||
    textIncludes(item.supplier_part_number, query) ||
    textIncludes(item.product_description, query) ||
    textIncludes(item.order_item, query)
  );
}

function groupMatchesFilter(group: OpenPurchaseOrderGroup, query: string): boolean {
  if (!query) return true;
  if (textIncludes(group.order_number, query)) return true;
  return group.items.some((item) => itemMatchesFilter(item, query));
}

function visibleItemsForGroup(group: OpenPurchaseOrderGroup, query: string): OpenPurchaseOrderItem[] {
  if (!query) return group.items;
  if (textIncludes(group.order_number, query)) return group.items;
  return group.items.filter((item) => itemMatchesFilter(item, query));
}

export function PurchaseOrderSelector({
  groups,
  orderCount,
  loading,
  error,
  canSelect,
  selectedLineKeys,
  onSelectedLineKeysChange,
  linked = [],
  emptyMessage = "Nenhum pedido de compra em aberto para este fornecedor na filial.",
  restrictToProductCodes = null,
}: Props) {
  const [filterQuery, setFilterQuery] = useState("");
  const [showAllOrders, setShowAllOrders] = useState(false);
  const restrictionKey = (restrictToProductCodes ?? []).map((code) => code.trim()).filter(Boolean).join("\n");
  useEffect(() => {
    setShowAllOrders(false);
  }, [restrictionKey]);
  const productRestricted = restrictionKey.length > 0 && !showAllOrders;
  const listedGroups = useMemo(() => {
    if (!productRestricted || !restrictToProductCodes) return groups;
    return filterPurchaseOrderGroupsByProductCodes(groups, restrictToProductCodes, linked);
  }, [groups, productRestricted, restrictToProductCodes, linked]);
  const groupSignature = listedGroups.map((group) => groupKey(group)).join("\n");
  const autoExpandKey = useMemo(() => {
    if (listedGroups.length === 0) return null;
    const firstLinked = listedGroups.find((group) => linked.some((item) => isSameGroup(group, item)));
    if (firstLinked) return groupKey(firstLinked);
    return canSelect && listedGroups[0] ? groupKey(listedGroups[0]) : null;
  }, [listedGroups, linked, canSelect]);
  const [overrideKey, setOverrideKey] = useState<{ signature: string; key: string | null } | null>(null);
  const expandedKey = overrideKey?.signature === groupSignature ? overrideKey.key : autoExpandKey;
  function setExpandedKey(next: string | null) {
    setOverrideKey({ signature: groupSignature, key: next });
  }
  const normalizedFilter = useMemo(() => normalizeFilterQuery(filterQuery), [filterQuery]);
  const visibleGroups = useMemo(() => {
    if (!normalizedFilter) return listedGroups;
    return listedGroups.filter((group) => groupMatchesFilter(group, normalizedFilter));
  }, [listedGroups, normalizedFilter]);
  const displayedOrderCount = productRestricted
    ? new Set(listedGroups.map((group) => group.order_number)).size
    : orderCount;
  const displayedGroupCount = productRestricted ? listedGroups.length : groups.length;

  useEffect(() => {
    if (!normalizedFilter || visibleGroups.length === 0) return;
    const currentVisible = expandedKey && visibleGroups.some((group) => groupKey(group) === expandedKey);
    if (!currentVisible) setExpandedKey(groupKey(visibleGroups[0]));
  }, [normalizedFilter, visibleGroups, expandedKey]);

  function toggleLine(group: OpenPurchaseOrderGroup, item: OpenPurchaseOrderItem) {
    if (!item.order_item) return;
    const key = lineKey(group, item.order_item);
    const next = new Set(selectedLineKeys);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    onSelectedLineKeysChange(next);
  }

  function toggleGroup(group: OpenPurchaseOrderGroup) {
    const itemKeys = group.items.filter((item) => item.order_item).map((item) => lineKey(group, item.order_item));
    if (itemKeys.length === 0) return;
    const next = new Set(selectedLineKeys);
    const allSelected = itemKeys.every((key) => next.has(key));
    if (allSelected) {
      for (const key of itemKeys) next.delete(key);
    } else {
      for (const key of itemKeys) next.add(key);
    }
    onSelectedLineKeysChange(next);
  }

  function groupSelectionState(group: OpenPurchaseOrderGroup): { checked: boolean; indeterminate: boolean } {
    const itemKeys = group.items.filter((item) => item.order_item).map((item) => lineKey(group, item.order_item));
    if (itemKeys.length === 0) return { checked: false, indeterminate: false };
    const selectedCount = itemKeys.filter((key) => selectedLineKeys.has(key)).length;
    return {
      checked: selectedCount === itemKeys.length,
      indeterminate: selectedCount > 0 && selectedCount < itemKeys.length,
    };
  }

  if (loading) return <p data-testid="po-loading">Consultando Protheus…</p>;
  if (error) {
    return (
      <p className="lnf-error" role="alert" data-testid="po-query-error">
        {error}
      </p>
    );
  }
  if (groups.length === 0) {
    return (
      <p className="lnf-muted" data-testid="po-empty">
        {emptyMessage}
      </p>
    );
  }
  if (productRestricted && listedGroups.length === 0) {
    return (
      <div data-testid="po-product-filter-empty">
        <p className="lnf-muted">Nenhum pedido de compra em aberto contém os produtos desta NF-e.</p>
        <button type="button" className="lnf-btn lnf-btn--ghost" onClick={() => setShowAllOrders(true)}>
          Ver todos os pedidos
        </button>
      </div>
    );
  }

  return (
    <>
      {productRestricted ? (
        <p className="lnf-po-product-filter" data-testid="po-product-filter">
          <span>Só pedidos com estes produtos.</span>
          <button type="button" className="lnf-btn lnf-btn--ghost lnf-btn--compact" onClick={() => setShowAllOrders(true)}>
            Ver todos os pedidos
          </button>
        </p>
      ) : null}
      <p className="lnf-muted" data-testid="po-summary">
        {displayedOrderCount} pedido(s) · {displayedGroupCount} grupo(s)
        {normalizedFilter ? ` · ${visibleGroups.length} no filtro` : null}
        {canSelect ? ` · ${selectedLineKeys.size} item(ns)` : null}
      </p>
      <div className="lnf-field lnf-po-filter">
        <label htmlFor="lnf-po-filter-input">Filtrar</label>
        <input
          id="lnf-po-filter-input"
          type="search"
          value={filterQuery}
          onChange={(event) => setFilterQuery(event.target.value)}
          placeholder="Pedido, código Delpi ou código do fornecedor…"
          data-testid="po-filter-input"
          autoComplete="off"
        />
      </div>
      {linked.length > 0 ? (
        <p className="lnf-po-linked-banner" data-testid="po-linked-banner">
          Amarrado atualmente:{" "}
          <strong>
            {linked
              .map((item) => linkedPurchaseOrderLabel(item.order_number, item.delivery_date))
              .join(" · ")}
          </strong>
        </p>
      ) : null}
      {visibleGroups.length === 0 ? (
        <p className="lnf-muted" data-testid="po-filter-empty">
          Nenhum pedido ou item corresponde ao filtro.
        </p>
      ) : (
        <div className="lnf-table-wrap">
          <table className="lnf-table" data-testid="po-table">
            <thead>
              <tr>
                {canSelect ? <th className="lnf-po-col-select">Sel.</th> : null}
                <th>PC</th>
                <th>Produtos</th>
                <th>Emissão</th>
                <th>Entrega</th>
                <th>Valor aberto</th>
                <th>Detalhes</th>
              </tr>
            </thead>
            <tbody>
              {visibleGroups.map((group) => {
                const key = groupKey(group);
                const expanded = expandedKey === key;
                const linkedNow = linked.some((item) => isSameGroup(group, item));
                const { checked, indeterminate } = groupSelectionState(group);
                const detailItems = visibleItemsForGroup(group, normalizedFilter);
                return (
                  <Fragment key={key}>
                    <tr
                      className={linkedNow || checked || indeterminate ? "lnf-po-row--linked" : undefined}
                      data-testid={`po-group-${group.order_number}`}
                    >
                      {canSelect ? (
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
                        {linkedNow ? <div className="lnf-po-badge">Amarrado</div> : null}
                      </td>
                      <td>{group.product_count}</td>
                      <td>{formatDate(group.issue_date)}</td>
                      <td>{group.delivery_date ? formatDate(group.delivery_date) : "Sem data de entrega"}</td>
                      <td>{formatMoney(Number(group.open_value || 0))}</td>
                      <td>
                        <button
                          type="button"
                          className="lnf-btn lnf-btn--ghost lnf-btn--compact"
                          onClick={() => setExpandedKey(expanded ? null : key)}
                          data-testid={`po-details-${key}`}
                        >
                          {expanded ? "Ocultar" : "Ver detalhes"}
                        </button>
                      </td>
                    </tr>
                    {expanded ? (
                      <tr className="lnf-po-details-row">
                        <td colSpan={canSelect ? 7 : 6}>
                          <table className="lnf-table lnf-table--nested">
                            <thead>
                              <tr>
                                {canSelect ? <th className="lnf-po-col-select">Sel.</th> : null}
                                <th>Item</th>
                                <th>Produto</th>
                                <th>Saldo</th>
                                <th>Mercadoria</th>
                                <th>IPI</th>
                                <th>Total</th>
                              </tr>
                            </thead>
                            <tbody>
                              {detailItems.map((row) => {
                                const itemChecked = !!row.order_item && selectedLineKeys.has(lineKey(group, row.order_item));
                                return (
                                  <tr key={`${row.order_number}-${row.order_item}-${row.product_code}`}>
                                    {canSelect ? (
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
                                      {row.supplier_part_number ? (
                                        <span className="lnf-po-supplier-pn" title="Código do produto no fornecedor">
                                          {" "}
                                          · {row.supplier_part_number}
                                        </span>
                                      ) : null}
                                      {row.product_description ? <div className="lnf-muted">{row.product_description}</div> : null}
                                    </td>
                                    <td>{formatQty(row.open_quantity, row.unit)}</td>
                                    <td>{formatMoney(Number(row.open_merchandise_value || 0))}</td>
                                    <td>{Number(row.open_ipi_value || 0) > 0 ? formatMoney(Number(row.open_ipi_value)) : "—"}</td>
                                    <td>{formatMoney(Number(row.open_value || 0))}</td>
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
      )}
    </>
  );
}
