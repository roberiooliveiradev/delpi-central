import { useEffect, useMemo, useState } from "react";
import { NativeCheckboxControl } from "@delpi/plugin-ui/index";
import { II_HELP } from "../../content/helpTooltips";
import { ApiError } from "../../data/api/httpClient";
import * as api from "../../data/api/invoiceIssuanceApi";
import {
  salesOrderLineKey,
  toIssuanceItemFromOpenLine,
} from "../../domain/openSalesOrders";
import type { IssuanceItem, OpenSalesOrderGroup, OpenSalesOrderLine } from "../../domain/types";
import { formatMoney, formatQuantity } from "../format";
import { QuantityInput } from "./QuantityInput";

type Props = {
  branch: string;
  partyCode: string;
  partyStore: string;
  stockWriteOff?: boolean;
  onApply: (items: IssuanceItem[]) => void;
};

type QtyMap = Record<string, number>;

export function OpenSalesOrderPicker({
  branch,
  partyCode,
  partyStore,
  stockWriteOff = true,
  onApply,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orders, setOrders] = useState<OpenSalesOrderGroup[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [quantities, setQuantities] = useState<QtyMap>({});

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setSelected(new Set());
    setQuantities({});
    setExpanded(null);
    void api
      .listOpenSalesOrders(branch, partyCode, partyStore, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const next = data.orders ?? [];
        setOrders(next);
        const defaults: QtyMap = {};
        for (const order of next) {
          for (const line of order.lines) {
            defaults[salesOrderLineKey(line)] = line.quantity_open;
          }
        }
        setQuantities(defaults);
        if (next[0]) setExpanded(next[0].sales_order);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setOrders([]);
        setError(
          err instanceof ApiError
            ? err.message
            : "Falha ao consultar pedidos de venda em aberto.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [branch, partyCode, partyStore]);

  const lineByKey = useMemo(() => {
    const map = new Map<string, OpenSalesOrderLine>();
    for (const order of orders) {
      for (const line of order.lines) {
        map.set(salesOrderLineKey(line), line);
      }
    }
    return map;
  }, [orders]);

  function toggleLine(line: OpenSalesOrderLine) {
    const key = salesOrderLineKey(line);
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function toggleOrder(order: OpenSalesOrderGroup) {
    const keys = order.lines.map((line) => salesOrderLineKey(line));
    setSelected((current) => {
      const next = new Set(current);
      const allSelected = keys.every((key) => next.has(key));
      if (allSelected) {
        for (const key of keys) next.delete(key);
      } else {
        for (const key of keys) next.add(key);
      }
      return next;
    });
  }

  function applySelected() {
    const items = [...selected]
      .map((key) => {
        const line = lineByKey.get(key);
        if (!line) return null;
        return toIssuanceItemFromOpenLine(
          line,
          quantities[key] ?? line.quantity_open,
          stockWriteOff,
        );
      })
      .filter((item): item is IssuanceItem => Boolean(item && item.quantity > 0));
    onApply(items);
  }

  return (
    <div className="ii-stack" data-testid="open-sales-order-picker">
      <p className="ii-muted">{II_HELP.openSalesOrders}</p>
      {loading ? <p className="ii-muted">Buscando pedidos em aberto…</p> : null}
      {error ? (
        <p className="ii-alert ii-error" role="alert">
          {error}
        </p>
      ) : null}
      {!loading && !error && orders.length === 0 ? (
        <p className="ii-alert" data-testid="open-sales-orders-empty">
          {II_HELP.openSalesOrdersEmpty}
        </p>
      ) : null}
      {orders.map((order) => {
        const open = expanded === order.sales_order;
        const keys = order.lines.map((line) => salesOrderLineKey(line));
        const selectedCount = keys.filter((key) => selected.has(key)).length;
        return (
          <div
            key={order.sales_order}
            className={open ? "ii-order ii-order--open" : "ii-order"}
          >
            <div className="ii-order__head">
              <NativeCheckboxControl
                checked={selectedCount > 0 && selectedCount === keys.length}
                onChange={() => toggleOrder(order)}
                label=""
              />
              <button
                type="button"
                className="ii-order__toggle"
                onClick={() =>
                  setExpanded((current) =>
                    current === order.sales_order ? null : order.sales_order,
                  )
                }
              >
                <strong>PV {order.sales_order}</strong>
                {order.customer_order_number ? (
                  <span className="ii-muted"> · Pedido cliente {order.customer_order_number}</span>
                ) : null}
                <span className="ii-muted">
                  {" "}
                  · {order.lines_count} linha(s) · saldo {formatQuantity(order.open_quantity)} ·{" "}
                  {formatMoney(order.open_amount)}
                </span>
              </button>
            </div>
            {open ? (
              <div className="ii-order__body">
                <table className="ii-table">
                  <thead>
                    <tr>
                      <th />
                      <th>Item</th>
                      <th>Produto</th>
                      <th>Saldo</th>
                      <th>Qtd a faturar</th>
                      <th>Preço</th>
                    </tr>
                  </thead>
                  <tbody>
                    {order.lines.map((line) => {
                      const key = salesOrderLineKey(line);
                      return (
                        <tr key={key}>
                          <td>
                            <NativeCheckboxControl
                              checked={selected.has(key)}
                              onChange={() => toggleLine(line)}
                              label={`Linha ${line.sales_order_item}`}
                            />
                          </td>
                          <td>{line.sales_order_item}</td>
                          <td>
                            {line.product_code}
                            <span className="ii-muted"> {line.product_description}</span>
                          </td>
                          <td>{formatQuantity(line.quantity_open)}</td>
                          <td>
                            <QuantityInput
                              ariaLabel={`Quantidade a faturar ${line.product_code}`}
                              value={quantities[key] ?? line.quantity_open}
                              max={line.quantity_open}
                              min={0}
                              onChange={(next) =>
                                setQuantities((current) => ({ ...current, [key]: next }))
                              }
                            />
                          </td>
                          <td>{formatMoney(line.unit_price)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        );
      })}
      <button
        type="button"
        className="ii-btn ii-btn--primary"
        disabled={selected.size === 0}
        onClick={applySelected}
      >
        Usar itens marcados
      </button>
    </div>
  );
}
