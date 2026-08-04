import { StatusBadge } from "../../../ui/StatusBadge";
import type { CustomerSummary } from "../types/customerSummary";
import { buildCommercialStatusLines } from "../utils/customerCommercialStatus";

type CustomerCommercialStatusProps = {
  customer: CustomerSummary;
};

export function CustomerCommercialStatus({ customer }: CustomerCommercialStatusProps) {
  const lines = buildCommercialStatusLines(customer);

  return (
    <section className="pva-checkup-panel" aria-label="Situação atual">
      <div className="pva-section__header">
        <div>
          <h2 className="pva-checkup-panel__title">Situação atual</h2>
          <p className="pva-section__hint">Leitura objetiva do status comercial do cliente.</p>
        </div>
        <div className="pva-attention-item__badges">
          {customer.temAtraso ? (
            <StatusBadge tone="danger">Com atraso</StatusBadge>
          ) : (
            <StatusBadge tone="success">Em dia</StatusBadge>
          )}
          {customer.temPedidoParcial ? (
            <StatusBadge tone="warning">Parcialmente atendido</StatusBadge>
          ) : null}
        </div>
      </div>
      <ul className="pva-checkup-status__list">
        {lines.map((line) => (
          <li key={line} className="pva-checkup-status__item">
            {line}
          </li>
        ))}
      </ul>
    </section>
  );
}
