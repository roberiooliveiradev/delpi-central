import { BarChart3, CalendarClock, Clock3, Wallet } from "lucide-react";

import { CommercialMetricCard } from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import type { CustomerSummary } from "../types/customerSummary";
import { BillingTrendCell } from "./BillingTrendCell";

type CustomerOverviewKpisProps = {
  customer: CustomerSummary;
  loading?: boolean;
};

export function CustomerOverviewKpis({ customer, loading = false }: CustomerOverviewKpisProps) {
  return (
    <section className="cm-customer-metrics cm-customer-metrics--overview" aria-label="Indicadores do cliente">
      <CommercialMetricCard
        label="Faturamento 12 meses"
        titleHint={CM_HELP.customerDetail.billed12m}
        value={customer.billed12m == null ? "—" : formatCurrency(customer.billed12m)}
        icon={<BarChart3 size={18} aria-hidden="true" />}
        loading={loading}
        hint={
          loading ? undefined : (
            <BillingTrendCell
              trend={customer.billingTrend}
              pct={customer.billingTrendPct}
            />
          )
        }
      />
      <CommercialMetricCard
        label="Valor em aberto"
        titleHint={CM_HELP.customerDetail.openValue}
        value={formatCurrency(customer.valorTotalAberto)}
        icon={<Wallet size={18} aria-hidden="true" />}
        loading={loading}
      />
      <CommercialMetricCard
        label="Pedidos em aberto"
        titleHint={CM_HELP.customerDetail.openOrders}
        value={customer.quantidadePedidosAbertos.toLocaleString("pt-BR")}
        icon={<CalendarClock size={18} aria-hidden="true" />}
        loading={loading}
      />
      <CommercialMetricCard
        label="Última venda"
        titleHint={CM_HELP.customerDetail.lastSale}
        value={
          customer.lastPurchaseDate
            ? formatDisplayDate(customer.lastPurchaseDate)
            : "—"
        }
        icon={<Clock3 size={18} aria-hidden="true" />}
        loading={loading}
      />
    </section>
  );
}
