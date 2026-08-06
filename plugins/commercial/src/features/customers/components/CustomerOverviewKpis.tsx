import { BarChart3, CalendarClock, Clock3, Wallet } from "lucide-react";

import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import { MetricCard } from "../../../ui/MetricCard";
import type { CustomerSummary } from "../types/customerSummary";
import { BillingTrendCell } from "./BillingTrendCell";

type CustomerOverviewKpisProps = {
  customer: CustomerSummary;
  loading?: boolean;
};

export function CustomerOverviewKpis({ customer, loading = false }: CustomerOverviewKpisProps) {
  const billed = customer.billed12m ?? 0;
  return (
    <section className="pva-metrics pva-metrics--overview" aria-label="Indicadores do cliente">
      <MetricCard
        label="Faturamento 12 meses"
        titleHint={CM_HELP.customerDetail.billed12m}
        value={formatCurrency(billed)}
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
      <MetricCard
        label="Valor em aberto"
        titleHint={CM_HELP.customerDetail.openValue}
        value={formatCurrency(customer.valorTotalAberto)}
        icon={<Wallet size={18} aria-hidden="true" />}
        loading={loading}
      />
      <MetricCard
        label="Pedidos em aberto"
        titleHint={CM_HELP.customerDetail.openOrders}
        value={customer.quantidadePedidosAbertos.toLocaleString("pt-BR")}
        icon={<CalendarClock size={18} aria-hidden="true" />}
        loading={loading}
      />
      <MetricCard
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
