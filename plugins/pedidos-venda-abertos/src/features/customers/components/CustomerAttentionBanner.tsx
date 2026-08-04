import { TrendingDown } from "lucide-react";

import { formatBillingTrendPct } from "../utils/billingTrendPresentation";
import type { CustomerSummary } from "../types/customerSummary";

type CustomerAttentionBannerProps = {
  customer: CustomerSummary;
  onAnalyze: () => void;
};

/**
 * Banner “Atenção comercial” — atraso e/ou queda de faturamento.
 */
export function CustomerAttentionBanner({
  customer,
  onAnalyze,
}: CustomerAttentionBannerProps) {
  const overdueCount = customer.quantidadePedidosAtrasados;
  const maxDays = customer.maiorAtrasoDias;
  const billingDown = customer.billingTrend === "down";
  const pctLabel = formatBillingTrendPct(customer.billingTrendPct);

  if (overdueCount <= 0 && !billingDown) return null;

  return (
    <aside className="pva-attention-banner" role="status" aria-label="Atenção comercial">
      <div className="pva-attention-banner__body">
        <h2 className="pva-attention-banner__title">Atenção comercial</h2>
        <ul className="pva-attention-banner__list">
          {overdueCount > 0 ? (
            <li className="pva-attention-banner__item pva-attention-banner__item--warn">
              <span className="pva-attention-banner__dot" aria-hidden="true" />
              {overdueCount === 1
                ? `1 pedido vencido${maxDays > 0 ? ` há ${maxDays} dia${maxDays === 1 ? "" : "s"}` : ""}`
                : `${overdueCount} pedidos vencidos${
                    maxDays > 0 ? ` (maior atraso: ${maxDays} dias)` : ""
                  }`}
            </li>
          ) : null}
          {billingDown ? (
            <li className="pva-attention-banner__item pva-attention-banner__item--down">
              <TrendingDown size={16} aria-hidden="true" />
              {pctLabel
                ? `Queda de ${pctLabel.replace(/[+-]/g, "")} no faturamento`
                : "Queda no faturamento"}
            </li>
          ) : null}
        </ul>
      </div>
      <button
        type="button"
        className="pva-attention-banner__link"
        onClick={onAnalyze}
      >
        Analisar pendências
        <span aria-hidden="true"> →</span>
      </button>
    </aside>
  );
}
