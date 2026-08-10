import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import { CustomerAttentionBanner } from "./CustomerAttentionBanner";
import { CustomerNextActionCard } from "./CustomerNextActionCard";
import { CustomerOpenOrdersPreview } from "./CustomerOpenOrdersPreview";
import { CustomerOverviewKpis } from "./CustomerOverviewKpis";

type CustomerOverviewSectionProps = {
  customer: CustomerSummary;
  orders: CustomerOrderSummary[];
  loading?: boolean;
  onGoToOrders: () => void;
};

/**
 * Visão geral do cliente — KPIs, banner, gráfico, preview de pedidos e laterais.
 */
export function CustomerOverviewSection({
  customer,
  orders,
  loading = false,
  onGoToOrders,
}: CustomerOverviewSectionProps) {
  return (
    <div className="pva-customer-overview">
      <CustomerOverviewKpis customer={customer} loading={loading} />
      <CustomerAttentionBanner customer={customer} onAnalyze={onGoToOrders} />

      <div className="pva-customer-overview__grid">
        <div className="pva-customer-overview__main">
          <CustomerOpenOrdersPreview orders={orders} onSeeAll={onGoToOrders} />
        </div>
        <aside className="pva-customer-overview__side">
          <CustomerNextActionCard customer={customer} onViewOrders={onGoToOrders} />
        </aside>
      </div>
    </div>
  );
}
