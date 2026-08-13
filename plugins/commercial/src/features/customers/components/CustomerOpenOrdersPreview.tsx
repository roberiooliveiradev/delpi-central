import type { DataTableColumn } from "@delpi/plugin-ui/index";

import {
  CommercialActionButton,
  CommercialDataRecordCard,
  CommercialDataTable,
  CommercialSectionCard,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import { currentLocationAsReturnTo } from "../../../app/commercialNavigationReturn";
import {
  navigateAnalyticsOpportunityDetail,
  navigateCustomerOrderDetail,
} from "../../../app/pluginNavigation";
import { formatCurrency } from "../../../utils/format";
import { compareDeliveryDates, formatDisplayDate } from "../../../utils/dates";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import {
  buildOrderOpportunityContextSearch,
  findOrderProposalLine,
} from "../utils/customerAccountActions";

type CustomerOpenOrdersPreviewProps = {
  orders: CustomerOrderSummary[];
  basePath: string;
  codigo: string;
  loja: string;
  canViewAnalytics: boolean;
  onSeeAll: () => void;
};

function previewStatus(order: CustomerOrderSummary): {
  label: string;
  tone: "danger" | "success" | "info";
} {
  if (order.situacao === "atrasado") return { label: "Vencido", tone: "danger" };
  if (order.situacao === "parcial") return { label: "Em produção", tone: "info" };
  return { label: "No prazo", tone: "success" };
}

function pickEmission(order: CustomerOrderSummary): string | null {
  let earliest: string | null = null;
  for (const line of order.lines) {
    const value = line.data_despacho;
    if (!value) continue;
    if (!earliest || compareDeliveryDates(value, earliest) < 0) {
      earliest = value;
    }
  }
  return earliest;
}

const PREVIEW_LIMIT = 5;

export function CustomerOpenOrdersPreview({
  orders,
  basePath,
  codigo,
  loja,
  canViewAnalytics,
  onSeeAll,
}: CustomerOpenOrdersPreviewProps) {
  const rows = orders.slice(0, PREVIEW_LIMIT);
  const openOrderDetail = (order: CustomerOrderSummary) => {
    if (!order.filial?.trim() || !order.pedido?.trim()) return;
    navigateCustomerOrderDetail(codigo, loja, order.filial, order.pedido, {
      basePath,
      returnNav: {
        returnTo: currentLocationAsReturnTo(),
        returnLabel: "Conta",
      },
    });
  };

  const opportunityAction = (order: CustomerOrderSummary) => {
    if (!canViewAnalytics) return null;
    const proposalLine = findOrderProposalLine(order.lines);
    const proposalNumber = proposalLine?.proposal_number?.trim() || null;
    if (!proposalLine || !proposalNumber) return null;
    return (
      <CommercialActionButton
        variant="link"
        onClick={() =>
          navigateAnalyticsOpportunityDetail(proposalNumber, {
            basePath,
            search: buildOrderOpportunityContextSearch(proposalLine),
          })
        }
      >
        Ver OV {proposalNumber}
      </CommercialActionButton>
    );
  };

  const columns: DataTableColumn<CustomerOrderSummary>[] = [
    { key: "order", header: "Pedido", render: (order) => order.pedido || "—" },
    {
      key: "issue",
      header: "Emissão",
      render: (order) => formatDisplayDate(pickEmission(order)),
    },
    {
      key: "forecast",
      header: "Previsão",
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
      key: "status",
      header: "Status",
      render: (order) => {
        const status = previewStatus(order);
        return <CommercialStatusBadge variant={status.tone} label={status.label} />;
      },
    },
    {
      key: "opportunity",
      header: "Oportunidade",
      interactive: true,
      rowClick: "stop",
      render: (order) => opportunityAction(order) ?? "—",
    },
  ];

  return (
    <CommercialSectionCard title="Pedidos em aberto">
      {rows.length === 0 ? (
        <p className="cm-customer-orders-preview__empty">Nenhum pedido em aberto no momento.</p>
      ) : (
        <>
          <div className="cm-customer-orders-preview__desktop">
            <CommercialDataTable
              rows={rows}
              columns={columns}
              rowKey={(order) => order.key}
              layout="section"
              onRowClick={openOrderDetail}
              rowClickRole="button"
            />
          </div>
          <div className="cm-customer-orders-preview__mobile">
            {rows.map((order) => {
              const status = previewStatus(order);
              return (
                <div
                  key={order.key}
                  className="cm-customer-orders-preview__mobile-item cm-customer-orders__mobile-item--clickable"
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
                    subtitle={`Emissão ${formatDisplayDate(pickEmission(order))}`}
                    status={
                      <CommercialStatusBadge
                        variant={status.tone}
                        label={status.label}
                      />
                    }
                    fields={[
                      {
                        id: "forecast",
                        label: "Previsão",
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
                      opportunityAction(order) ? (
                        <div
                          className="cm-customer-order-line-actions"
                          onClick={(event) => event.stopPropagation()}
                          onKeyDown={(event) => event.stopPropagation()}
                        >
                          {opportunityAction(order)}
                        </div>
                      ) : undefined
                    }
                  />
                </div>
              );
            })}
          </div>
        </>
      )}
      <div className="cm-customer-orders-preview__footer">
        <CommercialActionButton variant="ghost" onClick={onSeeAll}>
          Ver todos os pedidos
          <span aria-hidden="true"> →</span>
        </CommercialActionButton>
      </div>
    </CommercialSectionCard>
  );
}
