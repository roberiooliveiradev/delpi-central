import { FileText, Receipt, Wallet } from "lucide-react";

import { CM_HELP } from "../../../../content/helpTooltips";
import { MetricCard } from "../../../../ui/MetricCard";
import { formatCurrency } from "../../../../utils/format";
import { formatDisplayDate } from "../../../../utils/dates";
import type { CustomerBillingSummary } from "../types/customerBilling";

type CustomerBillingSummaryCardsProps = {
  summary: CustomerBillingSummary | null;
  loading?: boolean;
};

export function CustomerBillingSummaryCards({
  summary,
  loading,
}: CustomerBillingSummaryCardsProps) {
  return (
    <section className="pva-metrics" aria-label="Indicadores de faturamento" aria-busy={loading || undefined}>
      <MetricCard
        hero
        label="Valor faturado no período"
        titleHint={CM_HELP.customerDetail.billingValue}
        value={summary ? formatCurrency(summary.total_billed_value) : "—"}
        icon={<Wallet size={18} aria-hidden="true" />}
        loading={loading && !summary}
      />
      <MetricCard
        label="Quantidade de notas"
        titleHint={CM_HELP.customerDetail.billingInvoiceCount}
        value={summary ? summary.invoice_count.toLocaleString("pt-BR") : "—"}
        icon={<Receipt size={18} aria-hidden="true" />}
        loading={loading && !summary}
      />
      <MetricCard
        label="Data da última nota"
        titleHint={CM_HELP.customerDetail.billingLastDate}
        value={
          summary?.last_invoice_date ? formatDisplayDate(summary.last_invoice_date) : "—"
        }
        icon={<FileText size={18} aria-hidden="true" />}
        loading={loading && !summary}
      />
      <MetricCard
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
