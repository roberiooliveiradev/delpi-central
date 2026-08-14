import { FileText, Receipt, Wallet } from "lucide-react";

import { CommercialMetricCard } from "../../../../app/commercialUi";
import { CM_HELP } from "../../../../content/helpTooltips";
import { formatCurrency } from "../../../../utils/format";
import { formatDisplayDate } from "../../../../utils/dates";
import type { CustomerBillingSummary } from "../types/customerBilling";

type CustomerBillingSummaryCardsProps = {
  summary: CustomerBillingSummary | null;
  priorSummary?: CustomerBillingSummary | null;
  comparePriorYear?: boolean;
  loading?: boolean;
};

function formatYoyDelta(current: number, prior: number): string {
  if (prior === 0) {
    return current === 0 ? "0,0% vs ano ant." : "— vs ano ant.";
  }
  const pct = ((current - prior) / Math.abs(prior)) * 100;
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toLocaleString("pt-BR", {
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  })}% vs ano ant.`;
}

export function CustomerBillingSummaryCards({
  summary,
  priorSummary = null,
  comparePriorYear = false,
  loading,
}: CustomerBillingSummaryCardsProps) {
  const yoyHint =
    comparePriorYear && summary && priorSummary
      ? formatYoyDelta(summary.total_billed_value, priorSummary.total_billed_value)
      : null;

  return (
    <section className="cm-customer-metrics" aria-label="Indicadores de faturamento" aria-busy={loading || undefined}>
      <CommercialMetricCard
        hero
        label="Valor faturado no período"
        titleHint={CM_HELP.customerDetail.billingValue}
        value={summary ? formatCurrency(summary.total_billed_value) : "—"}
        hint={
          yoyHint
            ? `${yoyHint} · ant. ${formatCurrency(priorSummary?.total_billed_value)}`
            : undefined
        }
        icon={<Wallet size={18} aria-hidden="true" />}
        loading={loading && !summary}
      />
      <CommercialMetricCard
        label="Quantidade de notas"
        titleHint={CM_HELP.customerDetail.billingInvoiceCount}
        value={summary ? summary.invoice_count.toLocaleString("pt-BR") : "—"}
        hint={
          comparePriorYear && priorSummary
            ? `Ano ant.: ${priorSummary.invoice_count.toLocaleString("pt-BR")}`
            : undefined
        }
        icon={<Receipt size={18} aria-hidden="true" />}
        loading={loading && !summary}
      />
      <CommercialMetricCard
        label="Data da última nota"
        titleHint={CM_HELP.customerDetail.billingLastDate}
        value={
          summary?.last_invoice_date ? formatDisplayDate(summary.last_invoice_date) : "—"
        }
        icon={<FileText size={18} aria-hidden="true" />}
        loading={loading && !summary}
      />
      <CommercialMetricCard
        label="Valor da última nota"
        titleHint={CM_HELP.customerDetail.billingLastValue}
        value={
          summary?.last_invoice_value != null
            ? formatCurrency(summary.last_invoice_value)
            : "—"
        }
        loading={loading && !summary}
      />
    </section>
  );
}
