import type { DataTableColumn } from "@delpi/plugin-ui/index";
import { type ReactNode, useId, useState } from "react";

import {
  CommercialDataRecordCard,
  CommercialDataTable,
} from "../../../app/commercialUi";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import { StatusBadge } from "../../../ui/StatusBadge";
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

function renderStatus(order: CustomerOrderSummary): ReactNode {
  return (
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
  );
}

export function CustomerOrdersTable({ orders, basePath }: CustomerOrdersTableProps) {
  const [expandedKey, setExpandedKey] = useState<string | null>(null);
  const baseId = useId();
  const toggle = (key: string) =>
    setExpandedKey((current) => (current === key ? null : key));

  const columns: DataTableColumn<CustomerOrderSummary>[] = [
    { key: "branch", header: "Filial", render: (order) => order.filial || "—" },
    { key: "order", header: "Pedido", render: (order) => order.pedido || "—" },
    {
      key: "customer-order",
      header: "Pedido do cliente",
      render: (order) => order.pedidoCliente || "—",
    },
    { key: "status", header: "Situação", render: renderStatus },
    {
      key: "lines",
      header: "Linhas",
      align: "right",
      render: (order) => order.quantidadeLinhas.toLocaleString("pt-BR"),
    },
    {
      key: "overdue",
      header: "Maior atraso",
      align: "right",
      render: (order) => formatMaxOverdue(order.maiorAtrasoDias),
    },
    {
      key: "delivery",
      header: "Próxima entrega",
      render: (order) =>
        order.proximaEntrega ? formatDisplayDate(order.proximaEntrega) : "—",
    },
    {
      key: "value",
      header: "Valor em aberto",
      align: "right",
      render: (order) => formatCurrency(order.valorTotalAberto),
    },
    {
      key: "details",
      header: "Detalhes",
      render: (order) => {
        const expanded = expandedKey === order.key;
        const panelId = `${baseId}-desktop-lines-${order.key.replace(/\|/g, "-")}`;
        return (
          <button
            type="button"
            className="pva-btn pva-btn--ghost pva-checkup-expand"
            aria-expanded={expanded}
            aria-controls={panelId}
            onClick={() => toggle(order.key)}
          >
            {expanded ? "Recolher linhas" : "Expandir linhas"}
          </button>
        );
      },
    },
  ];
  const expandedOrder = orders.find((order) => order.key === expandedKey) ?? null;

  return (
    <section className="pva-table-card" aria-label="Todos os pedidos em aberto">
      <h2 className="pva-checkup-section-title">Todos os pedidos em aberto</h2>
      <div className="pva-customer-orders__desktop">
        <CommercialDataTable
          rows={orders}
          columns={columns}
          rowKey={(order) => order.key}
          layout="section"
        />
        {expandedOrder ? (
          <div
            id={`${baseId}-desktop-lines-${expandedOrder.key.replace(/\|/g, "-")}`}
            role="region"
            aria-label={`Linhas do pedido ${expandedOrder.pedido}`}
          >
            <CustomerOrderLines
              lines={expandedOrder.lines}
              orderKey={expandedOrder.key}
              basePath={basePath}
            />
          </div>
        ) : null}
      </div>

      <div className="pva-customer-orders__mobile" aria-label="Pedidos em aberto">
        {orders.map((order) => {
          const expanded = expandedKey === order.key;
          const panelId = `${baseId}-mobile-lines-${order.key.replace(/\|/g, "-")}`;
          return (
            <div key={order.key} className="pva-customer-orders__mobile-item">
              <CommercialDataRecordCard
                title={`Pedido ${order.pedido || "não informado"}`}
                subtitle={`Filial ${order.filial || "não informada"}`}
                status={renderStatus(order)}
                fields={[
                  {
                    id: "customer-order",
                    label: "Pedido do cliente",
                    value: order.pedidoCliente || "—",
                  },
                  {
                    id: "lines",
                    label: "Linhas",
                    value: order.quantidadeLinhas.toLocaleString("pt-BR"),
                  },
                  {
                    id: "overdue",
                    label: "Maior atraso",
                    value: formatMaxOverdue(order.maiorAtrasoDias),
                  },
                  {
                    id: "delivery",
                    label: "Próxima entrega",
                    value: order.proximaEntrega
                      ? formatDisplayDate(order.proximaEntrega)
                      : "—",
                  },
                  {
                    id: "value",
                    label: "Valor em aberto",
                    value: formatCurrency(order.valorTotalAberto),
                  },
                ]}
                context={
                  <button
                    type="button"
                    className="pva-btn pva-btn--ghost pva-checkup-expand"
                    aria-expanded={expanded}
                    aria-controls={panelId}
                    onClick={() => toggle(order.key)}
                  >
                    {expanded ? "Recolher linhas" : "Expandir linhas"}
                  </button>
                }
              />
              {expanded ? (
                <div
                  id={panelId}
                  role="region"
                  aria-label={`Linhas do pedido ${order.pedido}`}
                >
                  <CustomerOrderLines
                    lines={order.lines}
                    orderKey={order.key}
                    basePath={basePath}
                  />
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
