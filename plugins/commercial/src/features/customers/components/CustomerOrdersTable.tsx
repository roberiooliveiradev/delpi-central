import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  IconButton,
  formatOperationalUnitCode,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import { ChevronDown, ChevronRight } from "lucide-react";
import { type ReactNode, useState } from "react";

import {
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialSectionCard,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import {
  currentLocationAsReturnTo,
} from "../../../app/commercialNavigationReturn";
import { navigateCustomerOrderDetail } from "../../../app/pluginNavigation";
import { CUSTOMER_ORDERS_CONTENT } from "../../../content/customerOrdersContent";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import { orderSituationLabel } from "../utils/customerOrderAggregation";
import { CustomerOrderLines } from "./CustomerOrderLines";

type CustomerOrdersTableProps = {
  orders: CustomerOrderSummary[];
  basePath: string;
  codigo: string;
  loja: string;
  canViewAnalytics: boolean;
};

function formatMaxOverdue(days: number): string {
  if (days <= 0) return "—";
  if (days === 1) return "1 dia";
  return `${days.toLocaleString("pt-BR")} dias`;
}

function renderStatus(order: CustomerOrderSummary): ReactNode {
  return (
    <CommercialStatusBadge
      variant={
        order.situacao === "atrasado"
          ? "danger"
          : order.situacao === "parcial"
            ? "warning"
            : "neutral"
      }
      label={orderSituationLabel(order.situacao)}
    />
  );
}

export function CustomerOrdersTable({
  orders,
  basePath,
  codigo,
  loja,
  canViewAnalytics,
}: CustomerOrdersTableProps) {
  const [expandedRowKey, setExpandedRowKey] = useState<string | null>(null);

  const openOrderDetail = (order: CustomerOrderSummary) => {
    if (!order.filial?.trim() || !order.pedido?.trim()) return;
    navigateCustomerOrderDetail(codigo, loja, order.filial, order.pedido, {
      basePath,
      returnNav: {
        returnTo: currentLocationAsReturnTo(),
        returnLabel: "Pedidos da conta",
      },
    });
  };

  const toggleExpand = (orderKey: string) => {
    setExpandedRowKey((current) => (current === orderKey ? null : orderKey));
  };

  const columns: DataTableColumn<CustomerOrderSummary>[] = [
    {
      key: "expand",
      header: "",
      className: "delpi-ui-table__col--compact",
      interactive: true,
      rowClick: "stop",
      render: (order) => {
        const isExpanded = expandedRowKey === order.key;
        return (
          <IconButton
            aria-label={
              isExpanded
                ? CUSTOMER_ORDERS_CONTENT.collapseLinesAriaLabel
                : CUSTOMER_ORDERS_CONTENT.expandLinesAriaLabel
            }
            aria-expanded={isExpanded}
            onClick={() => toggleExpand(order.key)}
          >
            {isExpanded ? (
              <ChevronDown size={16} aria-hidden />
            ) : (
              <ChevronRight size={16} aria-hidden />
            )}
          </IconButton>
        );
      },
    },
    {
      key: "branch",
      header: OPERATIONAL_UNIT_COLUMN_LABEL,
      render: (order) => formatOperationalUnitCode(order.filial),
    },
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
  ];

  return (
    <CommercialSectionCard title={CUSTOMER_ORDERS_CONTENT.ordersSectionTitle}>
      <div className="cm-customer-orders__desktop">
        <CommercialDataTable
          rows={orders}
          columns={columns}
          rowKey={(order) => order.key}
          layout="section"
          onRowClick={openOrderDetail}
          rowClickRole="button"
          expandedRowKey={expandedRowKey}
          onExpandedRowKeyChange={setExpandedRowKey}
          renderExpandedRow={(order) => (
            <CustomerOrderLines
              lines={order.lines}
              orderKey={order.key}
              basePath={basePath}
              canViewAnalytics={canViewAnalytics}
              returnNav={{
                returnTo: currentLocationAsReturnTo(),
                returnLabel: "Pedidos da conta",
              }}
            />
          )}
        />
      </div>

      <div
        className="cm-customer-orders__mobile"
        aria-label={CUSTOMER_ORDERS_CONTENT.mobileListAriaLabel}
      >
        {orders.map((order) => (
          <div
            key={order.key}
            className="cm-customer-orders__mobile-item cm-customer-orders__mobile-item--clickable"
            role="button"
            tabIndex={0}
            onClick={() => openOrderDetail(order)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                openOrderDetail(order);
              }
            }}
          >
            <CommercialDataRecordCard
              title={`Pedido ${order.pedido || "não informado"}`}
              subtitle={formatOperationalUnitCode(order.filial, "Unidade não informada")}
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
            />
          </div>
        ))}
      </div>
    </CommercialSectionCard>
  );
}
