import { CalendarDays } from "lucide-react";

import type { CustomerSummary } from "../types/customerSummary";
import {
  resolveCustomerNextAction,
  resolveCustomerStatus,
} from "../utils/customerListPresentation";
import { formatBillingTrendPct } from "../utils/billingTrendPresentation";

type CustomerNextActionCardProps = {
  customer: CustomerSummary;
  onViewOrders: () => void;
};

function buildDescription(customer: CustomerSummary): string {
  const parts: string[] = [];
  if (customer.temAtraso) {
    parts.push("pedido vencido");
  }
  if (customer.billingTrend === "down") {
    const pct = formatBillingTrendPct(customer.billingTrendPct)
      .replace(/[+-]/g, "");
    parts.push(pct ? `redução no faturamento (${pct})` : "redução no faturamento");
  }
  if (parts.length === 0 && customer.temPedidoParcial) {
    return "Cliente com pedido parcialmente atendido — vale um acompanhamento.";
  }
  if (parts.length === 0) {
    return "Revise a carteira e registre o próximo contato comercial.";
  }
  if (parts.length === 1) {
    return `Cliente com ${parts[0]}.`;
  }
  return `Cliente com ${parts[0]} e ${parts[1]}.`;
}

export function CustomerNextActionCard({
  customer,
  onViewOrders,
}: CustomerNextActionCardProps) {
  const title = resolveCustomerNextAction(customer);
  const status = customer.status ?? resolveCustomerStatus(customer);
  const urgent = status === "atencao" || customer.temAtraso;

  return (
    <section className="pva-card pva-next-action-card" aria-label="Próxima ação">
      <div className="pva-next-action-card__icon" aria-hidden="true">
        <CalendarDays size={28} />
      </div>
      <h2 className="pva-next-action-card__eyebrow">Próxima ação</h2>
      <h3 className="pva-next-action-card__title">{title}</h3>
      <p className="pva-next-action-card__text">{buildDescription(customer)}</p>
      {urgent ? (
        <p className="pva-next-action-card__deadline">Prazo: Hoje</p>
      ) : null}
      <button
        type="button"
        className="pva-btn pva-btn--primary pva-next-action-card__cta"
        onClick={onViewOrders}
      >
        Ver pedidos em aberto
      </button>
    </section>
  );
}
