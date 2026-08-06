import { AlertTriangle, ClipboardList, Clock3, Users, Wallet } from "lucide-react";

import { CM_HELP } from "../../../content/helpTooltips";
import { MetricCard } from "../../../ui/MetricCard";
import { formatCurrency } from "../../../utils/format";
import type { CustomerAggregationResult } from "../types/customerSummary";
import {
  countActivePortfolioCustomers,
  countCustomersWithoutSaleForDays,
} from "../utils/customerPortfolioKpis";

type CustomerSummaryCardsProps = {
  aggregation: CustomerAggregationResult;
  loading?: boolean;
};

const WITHOUT_SALE_DAYS = 60;

export function CustomerSummaryCards({ aggregation, loading }: CustomerSummaryCardsProps) {
  const clientesAtivos = countActivePortfolioCustomers(aggregation.customers);
  const semVenda60d = countCustomersWithoutSaleForDays(
    aggregation.customers,
    WITHOUT_SALE_DAYS,
  );

  return (
    <section className="pva-metrics pva-metrics--portfolio" aria-label="Resumo da carteira">
      <MetricCard
        label="Clientes ativos"
        titleHint={CM_HELP.customers.kpiActive}
        value={clientesAtivos.toLocaleString("pt-BR")}
        hint="Na carteira com pedidos em aberto"
        icon={<Users size={18} aria-hidden="true" />}
        loading={loading}
      />
      <MetricCard
        label="Sem venda há 60 dias"
        titleHint={CM_HELP.customers.kpiNoSale60}
        value={semVenda60d.toLocaleString("pt-BR")}
        hint="Última venda há 60 dias ou mais"
        icon={<Clock3 size={18} aria-hidden="true" />}
        loading={loading}
        tone={semVenda60d > 0 ? "danger" : "default"}
      />
      <MetricCard
        hero
        label="Valor em aberto"
        titleHint={CM_HELP.customers.kpiOpenValue}
        value={formatCurrency(aggregation.totalValorAberto)}
        hint="Soma dos pedidos com saldo em aberto"
        icon={<Wallet size={18} aria-hidden="true" />}
        loading={loading}
      />
      <MetricCard
        label="Pedidos em aberto"
        titleHint={CM_HELP.customers.kpiOpenOrders}
        value={aggregation.totalPedidosAbertos.toLocaleString("pt-BR")}
        hint="Pedidos distintos na carteira"
        icon={<ClipboardList size={18} aria-hidden="true" />}
        loading={loading}
      />
      <MetricCard
        label="Clientes com atraso"
        titleHint={CM_HELP.customers.kpiLateCustomers}
        value={aggregation.clientesComAtraso.toLocaleString("pt-BR")}
        hint="Com pedido vencido"
        icon={<AlertTriangle size={18} aria-hidden="true" />}
        loading={loading}
        tone={aggregation.clientesComAtraso > 0 ? "danger" : "default"}
      />
    </section>
  );
}
