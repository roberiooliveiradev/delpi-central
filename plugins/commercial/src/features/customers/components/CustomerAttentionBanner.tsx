import { TrendingDown } from "lucide-react";

import {
  CommercialActionButton,
  CommercialStateBanner,
} from "../../../app/commercialUi";
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
    <CommercialStateBanner>
      <div className="cm-customer-attention-banner__body">
        <h2 className="cm-customer-attention-banner__title">Atenção comercial</h2>
        <ul className="cm-customer-attention-banner__list">
          {overdueCount > 0 ? (
            <li className="cm-customer-attention-banner__item cm-customer-attention-banner__item--warn">
              <span className="cm-customer-attention-banner__dot" aria-hidden="true" />
              {overdueCount === 1
                ? `1 pedido vencido${maxDays > 0 ? ` há ${maxDays} dia${maxDays === 1 ? "" : "s"}` : ""}`
                : `${overdueCount} pedidos vencidos${
                    maxDays > 0 ? ` (maior atraso: ${maxDays} dias)` : ""
                  }`}
            </li>
          ) : null}
          {billingDown ? (
            <li className="cm-customer-attention-banner__item cm-customer-attention-banner__item--down">
              <TrendingDown size={16} aria-hidden="true" />
              {pctLabel
                ? `Queda de ${pctLabel.replace(/[+-]/g, "")} no faturamento`
                : "Queda no faturamento"}
            </li>
          ) : null}
        </ul>
      </div>
      <CommercialActionButton
        variant="ghost"
        onClick={onAnalyze}
      >
        Analisar pendências
        <span aria-hidden="true"> →</span>
      </CommercialActionButton>
    </CommercialStateBanner>
  );
}
