import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import { useCustomerPurchaseEvolution } from "../hooks/useCustomerPurchaseEvolution";
import { CustomerAttentionBanner } from "./CustomerAttentionBanner";
import { CustomerContactsStub } from "./CustomerContactsStub";
import { CustomerNextActionCard } from "./CustomerNextActionCard";
import { CustomerOpenOrdersPreview } from "./CustomerOpenOrdersPreview";
import { CustomerOverviewKpis } from "./CustomerOverviewKpis";
import { CustomerPurchaseEvolutionChart } from "./CustomerPurchaseEvolutionChart";

type CustomerOverviewSectionProps = {
  customer: CustomerSummary;
  orders: CustomerOrderSummary[];
  loading?: boolean;
  onGoToOrders: () => void;
  onGoToContacts: () => void;
};

/**
 * Visão geral do cliente — KPIs, banner, gráfico, preview de pedidos e laterais.
 */
export function CustomerOverviewSection({
  customer,
  orders,
  loading = false,
  onGoToOrders,
  onGoToContacts,
}: CustomerOverviewSectionProps) {
  const evolution = useCustomerPurchaseEvolution(
    customer.codigo,
    customer.loja,
    true,
  );

  return (
    <div className="pva-customer-overview">
      <CustomerOverviewKpis customer={customer} loading={loading} />
      <CustomerAttentionBanner customer={customer} onAnalyze={onGoToOrders} />

      <div className="pva-customer-overview__grid">
        <div className="pva-customer-overview__main">
          <CustomerPurchaseEvolutionChart
            points={evolution.points}
            loading={evolution.loading}
            error={evolution.error}
          />
          <CustomerOpenOrdersPreview orders={orders} onSeeAll={onGoToOrders} />
        </div>
        <aside className="pva-customer-overview__side">
          <CustomerNextActionCard customer={customer} onViewOrders={onGoToOrders} />
          <CustomerContactsStub onAdd={onGoToContacts} />
        </aside>
      </div>
    </div>
  );
}
