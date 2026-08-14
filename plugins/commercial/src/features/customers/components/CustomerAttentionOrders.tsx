import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
} from "@delpi/plugin-ui/index";
import {
  CommercialEntityLink,
  CommercialSectionCard,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import { currentLocationAsReturnTo } from "../../../app/commercialNavigationReturn";
import {
  buildCustomerOrderDetailHref,
  navigateCustomerOrderDetail,
} from "../../../app/pluginNavigation";
import { orderLinkTitle } from "../../../content/entityLinkHints";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import { orderSituationLabel } from "../utils/customerOrderAggregation";

type CustomerAttentionOrdersProps = {
  orders: CustomerOrderSummary[];
  basePath: string;
  codigo: string;
  loja: string;
};

function formatMaxOverdue(days: number): string {
  if (days <= 0) return "—";
  if (days === 1) return "1 dia";
  return `${days.toLocaleString("pt-BR")} dias`;
}

export function CustomerAttentionOrders({
  orders,
  basePath,
  codigo,
  loja,
}: CustomerAttentionOrdersProps) {
  const orderReturnNav = {
    returnTo: currentLocationAsReturnTo(),
    returnLabel: "Pedidos da conta",
  };

  const openOrderDetail = (order: CustomerOrderSummary) => {
    if (!order.filial?.trim() || !order.pedido?.trim()) return;
    navigateCustomerOrderDetail(codigo, loja, order.filial, order.pedido, {
      basePath,
      returnNav: orderReturnNav,
    });
  };

  return (
    <CommercialSectionCard title="Pedidos que exigem atenção">
      {orders.length === 0 ? (
        <p className="cm-customer-attention-orders__empty" role="status">
          Nenhum pedido exige atenção especial no momento — carteira em dia neste recorte.
        </p>
      ) : (
        <ul className="cm-customer-attention-orders__list">
          {orders.map((order) => {
            const href = buildCustomerOrderDetailHref(
              codigo,
              loja,
              order.filial,
              order.pedido,
              { basePath, returnNav: orderReturnNav },
            );
            const orderLabel = `Pedido ${order.pedido}${
              order.filial
                ? ` · ${OPERATIONAL_UNIT_COLUMN_LABEL} ${formatOperationalUnitCode(order.filial)}`
                : ""
            }`;
            return (
              <li key={order.key} className="cm-customer-attention-orders__item">
                <div
                  className="cm-customer-attention-orders__hit"
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
                  <div className="cm-customer-attention-orders__main">
                    {href ? (
                      <CommercialEntityLink
                        href={href}
                        title={orderLinkTitle(order.pedido)}
                        className="cm-link-button cm-customer-attention-orders__order"
                        onNavigate={() => openOrderDetail(order)}
                      >
                        {orderLabel}
                      </CommercialEntityLink>
                    ) : (
                      <span className="cm-customer-attention-orders__order">
                        {orderLabel}
                      </span>
                    )}
                    <CommercialStatusBadge
                      variant="neutral"
                      label={orderSituationLabel(order.situacao)}
                    />
                  </div>
                  <div className="cm-customer-attention-orders__metrics">
                    {order.temAtraso ? (
                      <span>Maior atraso: {formatMaxOverdue(order.maiorAtrasoDias)}</span>
                    ) : null}
                    <span>Valor: {formatCurrency(order.valorTotalAberto)}</span>
                    {order.proximaEntrega ? (
                      <span>Próxima entrega: {formatDisplayDate(order.proximaEntrega)}</span>
                    ) : null}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </CommercialSectionCard>
  );
}
