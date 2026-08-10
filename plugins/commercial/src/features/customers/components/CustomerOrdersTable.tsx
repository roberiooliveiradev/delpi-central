import { Fragment, useId, useState } from "react";

import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import { StatusBadge } from "../../../ui/StatusBadge";
import { PVA_TABLE } from "../../../ui/tableChrome";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import { orderSituationLabel } from "../utils/customerOrderAggregation";
import { CustomerOrderLines } from "./CustomerOrderLines";

type CustomerOrdersTableProps = {
  orders: CustomerOrderSummary[];
  basePath: string;
};

function formatMaxOverdue(days: number): string {
  if (days <= 0) return "—";
  if (days === 1) return "1 dia";
  return `${days.toLocaleString("pt-BR")} dias`;
}

export function CustomerOrdersTable({ orders, basePath }: CustomerOrdersTableProps) {
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const baseId = useId();

  const toggle = (key: string) => {
    setExpandedKey((current) => (current === key ? null : key));
  };

  return (
    <section className="pva-table-card" aria-label="Todos os pedidos em aberto">
      <h2 className="pva-checkup-section-title">Todos os pedidos em aberto</h2>
      <div className={PVA_TABLE.wrap}>
        <table className={PVA_TABLE.sortableTable}>
          <thead>
            <tr>
              <th scope="col">Filial</th>
              <th scope="col">Pedido</th>
              <th scope="col">Pedido do cliente</th>
              <th scope="col">Situação</th>
              <th scope="col" className={PVA_TABLE.colNumeric}>
                Linhas
              </th>
              <th scope="col" className={PVA_TABLE.colNumeric}>
                Maior atraso
              </th>
              <th scope="col">Próxima entrega</th>
              <th scope="col" className={PVA_TABLE.colNumeric}>
                Valor em aberto
              </th>
              <th scope="col">Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => {
              const expanded = expandedKey === order.key;
              const safeKey = order.key.replace(/\|/g, "-");
              const panelId = `${baseId}-lines-${safeKey}`;
              const controlId = `${baseId}-toggle-${safeKey}`;
              return (
                <Fragment key={order.key}>
                  <tr>
                    <td data-label="Filial">{order.filial || "—"}</td>
                    <td data-label="Pedido">{order.pedido || "—"}</td>
                    <td data-label="Pedido do cliente">{order.pedidoCliente || "—"}</td>
                    <td data-label="Situação">
                      <StatusBadge
                        tone={
                          order.situacao === "atrasado"
                            ? "danger"
                            : order.situacao === "parcial"
                              ? "warning"
                              : "neutral"
                        }
                      >
                        {orderSituationLabel(order.situacao)}
                      </StatusBadge>
                    </td>
                    <td data-label="Linhas" className={PVA_TABLE.colNumeric}>
                      {order.quantidadeLinhas.toLocaleString("pt-BR")}
                    </td>
                    <td data-label="Maior atraso" className={PVA_TABLE.colNumeric}>
                      {formatMaxOverdue(order.maiorAtrasoDias)}
                    </td>
                    <td data-label="Próxima entrega">
                      {order.proximaEntrega ? formatDisplayDate(order.proximaEntrega) : "—"}
                    </td>
                    <td data-label="Valor em aberto" className={PVA_TABLE.colNumeric}>
                      {formatCurrency(order.valorTotalAberto)}
                    </td>
                    <td data-label="Detalhes">
                      <button
                        type="button"
                        id={controlId}
                        className="pva-btn pva-btn--ghost pva-checkup-expand"
                        aria-expanded={expanded}
                        aria-controls={panelId}
                        onClick={() => toggle(order.key)}
                      >
                        {expanded ? "Recolher linhas" : "Expandir linhas"}
                      </button>
                    </td>
                  </tr>
                  {expanded ? (
                    <tr className="pva-checkup-detail-row">
                      <td colSpan={9}>
                        <div id={panelId} role="region" aria-labelledby={controlId}>
                          <CustomerOrderLines
                            lines={order.lines}
                            orderKey={order.key}
                            basePath={basePath}
                          />
                        </div>
                      </td>
                    </tr>
                  ) : null}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
