import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";
import { type ReactNode, useState } from "react";

import {
  CommercialActionButton,
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialHostDialog,
  CommercialSectionCard,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import {
  currentLocationAsReturnTo,
} from "../../../app/commercialNavigationReturn";
import { navigateCustomerOrderDetail } from "../../../app/pluginNavigation";
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
  const [linesOrderKey, setLinesOrderKey] = useState<string | null>(null);
  const linesOrder = orders.find((order) => order.key === linesOrderKey) ?? null;

  const openOrderDetail = (order: CustomerOrderSummary) => {
    navigateCustomerOrderDetail(codigo, loja, order.filial, order.pedido, {
      basePath,
      returnNav: {
        returnTo: currentLocationAsReturnTo(),
        returnLabel: "Pedidos da conta",
      },
    });
  };

  const orderActions = (order: CustomerOrderSummary) => {
    const canOpen = Boolean(order.filial?.trim() && order.pedido?.trim());
    return (
      <div className="cm-customer-order-line-actions">
        {canOpen ? (
          <CommercialActionButton variant="ghost" onClick={() => openOrderDetail(order)}>
            Abrir pedido
          </CommercialActionButton>
        ) : null}
        <CommercialActionButton variant="ghost" onClick={() => setLinesOrderKey(order.key)}>
          Ver linhas
        </CommercialActionButton>
      </div>
    );
  };

  const columns: DataTableColumn<CustomerOrderSummary>[] = [
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
    {
      key: "details",
      header: "Ações",
      render: (order) => orderActions(order),
    },
  ];

  return (
    <CommercialSectionCard title="Todos os pedidos em aberto">
      <div className="cm-customer-orders__desktop">
        <CommercialDataTable
          rows={orders}
          columns={columns}
          rowKey={(order) => order.key}
          layout="section"
        />
      </div>

      <div className="cm-customer-orders__mobile" aria-label="Pedidos em aberto">
        {orders.map((order) => (
          <div key={order.key} className="cm-customer-orders__mobile-item">
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
              context={orderActions(order)}
            />
          </div>
        ))}
      </div>

      <CommercialHostDialog
        open={Boolean(linesOrder)}
        title={
          linesOrder
            ? `Linhas do pedido ${linesOrder.pedido || "não informado"}`
            : "Linhas do pedido"
        }
        description={
          linesOrder
            ? formatOperationalUnitCode(linesOrder.filial, "Unidade não informada")
            : undefined
        }
        onClose={() => setLinesOrderKey(null)}
        footer={
          <CommercialActionButton variant="ghost" onClick={() => setLinesOrderKey(null)}>
            Fechar
          </CommercialActionButton>
        }
      >
        {linesOrder ? (
          <CustomerOrderLines
            lines={linesOrder.lines}
            orderKey={linesOrder.key}
            basePath={basePath}
            canViewAnalytics={canViewAnalytics}
          />
        ) : null}
      </CommercialHostDialog>
    </CommercialSectionCard>
  );
}
