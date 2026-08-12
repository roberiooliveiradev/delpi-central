import {
  OPERATIONAL_UNIT_COLUMN_LABEL,
  formatOperationalUnitCode,
} from "@delpi/plugin-ui/index";
import {
  CommercialSectionCard,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import { orderSituationLabel } from "../utils/customerOrderAggregation";

type CustomerAttentionOrdersProps = {
  orders: CustomerOrderSummary[];
};

function formatMaxOverdue(days: number): string {
  if (days <= 0) return "—";
  if (days === 1) return "1 dia";
  return `${days.toLocaleString("pt-BR")} dias`;
}

export function CustomerAttentionOrders({ orders }: CustomerAttentionOrdersProps) {
  return (
    <CommercialSectionCard title="Pedidos que exigem atenção">
      {orders.length === 0 ? (
        <p className="cm-customer-attention-orders__empty" role="status">
          Nenhum pedido exige atenção especial no momento — carteira em dia neste recorte.
        </p>
      ) : (
        <ul className="cm-customer-attention-orders__list">
          {orders.map((order) => (
            <li key={order.key} className="cm-customer-attention-orders__item">
              <div className="cm-customer-attention-orders__main">
                <span className="cm-customer-attention-orders__order">
                  Pedido {order.pedido}
                  {order.filial
                    ? ` · ${OPERATIONAL_UNIT_COLUMN_LABEL} ${formatOperationalUnitCode(order.filial)}`
                    : ""}
                </span>
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
            </li>
          ))}
        </ul>
      )}
    </CommercialSectionCard>
  );
}
