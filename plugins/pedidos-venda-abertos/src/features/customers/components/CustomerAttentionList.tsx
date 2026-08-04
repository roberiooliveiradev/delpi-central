import { formatCurrency } from "../../../utils/format";
import { formatEntityCodeStore } from "../../../utils/entityCodeStore";
import { navigateCustomerDetail } from "../../../app/pluginNavigation";
import { StatusBadge } from "../../../ui/StatusBadge";
import type { CustomerSummary } from "../types/customerSummary";

type CustomerAttentionListProps = {
  customers: CustomerSummary[];
  totalWithOverdue: number;
  basePath: string;
};

function formatMaxOverdue(days: number): string {
  if (days <= 0) return "—";
  if (days === 1) return "1 dia";
  return `${days.toLocaleString("pt-BR")} dias`;
}

export function CustomerAttentionList({
  customers,
  totalWithOverdue,
  basePath,
}: CustomerAttentionListProps) {
  return (
    <section className="pva-attention" aria-label="Clientes que exigem atenção">
      <header className="pva-attention__header">
        <div>
          <h2 className="pva-attention__title">Clientes que exigem atenção</h2>
          <p className="pva-attention__hint">
            Prioridade por atraso, maior atraso, pedidos atrasados e valor em aberto.
          </p>
        </div>
      </header>

      {totalWithOverdue === 0 ? (
        <p className="pva-attention__empty" role="status">
          Nenhum cliente com pedidos atrasados no momento.
        </p>
      ) : (
        <ul className="pva-attention__list">
          {customers.map((customer) => {
            const codeStore =
              formatEntityCodeStore(customer.codigo, customer.loja) ??
              `${customer.codigo}-${customer.loja}`;
            const openLabel = `Abrir cliente ${customer.nome || codeStore}`;
            return (
              <li key={customer.key} className="pva-attention-item">
                <div className="pva-attention-item__identity">
                  <p className="pva-attention-item__name">{customer.nome || "—"}</p>
                  <p className="pva-attention-item__meta">
                    {customer.codigo} · Loja {customer.loja}
                  </p>
                  <div className="pva-attention-item__badges">
                    <StatusBadge tone="danger">Com atraso</StatusBadge>
                    {customer.temPedidoParcial ? (
                      <StatusBadge tone="warning">Parcialmente atendido</StatusBadge>
                    ) : null}
                  </div>
                </div>
                <div className="pva-attention-item__metrics">
                  <div className="pva-attention-item__metric">
                    <p className="pva-attention-item__metric-label">Atrasados</p>
                    <p className="pva-attention-item__metric-value pva-attention-item__metric-value--danger">
                      {customer.quantidadePedidosAtrasados.toLocaleString("pt-BR")}
                    </p>
                  </div>
                  <div className="pva-attention-item__metric">
                    <p className="pva-attention-item__metric-label">Maior atraso</p>
                    <p className="pva-attention-item__metric-value">
                      {formatMaxOverdue(customer.maiorAtrasoDias)}
                    </p>
                  </div>
                  <div className="pva-attention-item__metric">
                    <p className="pva-attention-item__metric-label">Valor em aberto</p>
                    <p className="pva-attention-item__metric-value">
                      {formatCurrency(customer.valorTotalAberto)}
                    </p>
                  </div>
                </div>
                <div className="pva-attention-item__actions">
                  <button
                    type="button"
                    className="pva-btn pva-btn--primary"
                    aria-label={openLabel}
                    onClick={() =>
                      navigateCustomerDetail(customer.codigo, customer.loja, { basePath })
                    }
                  >
                    Abrir cliente
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
