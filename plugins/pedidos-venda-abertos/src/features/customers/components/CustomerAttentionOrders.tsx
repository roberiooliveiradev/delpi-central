import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import { StatusBadge } from "../../../ui/StatusBadge";
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
    <section className="pva-checkup-attention" aria-label="Pedidos que exigem atenção">
      <h2 className="pva-checkup-section-title">Pedidos que exigem atenção</h2>
      {orders.length === 0 ? (
        <p className="pva-checkup-attention__empty" role="status">
          Nenhum pedido exige atenção especial no momento — carteira em dia neste recorte.
        </p>
      ) : (
        <ul className="pva-checkup-attention__list">
          {orders.map((order) => (
            <li key={order.key} className="pva-checkup-attention__item">
              <div className="pva-checkup-attention__main">
                <span className="pva-checkup-attention__pedido">
                  Pedido {order.pedido}
                  {order.filial ? ` · Filial ${order.filial}` : ""}
                </span>
                <StatusBadge tone="neutral">
                  {orderSituationLabel(order.situacao)}
                </StatusBadge>
              </div>
              <div className="pva-checkup-attention__metrics">
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
    </section>
  );
}
