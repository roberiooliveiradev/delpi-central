import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import type { UseCustomerActivitiesResult } from "../hooks/useCustomerActivities";
import { useCustomerPurchaseEvolution } from "../hooks/useCustomerPurchaseEvolution";
import { CustomerActivityTimelinePanel } from "./CustomerActivityTimelinePanel";
import { CustomerAttentionBanner } from "./CustomerAttentionBanner";
import { CustomerNextActionCard } from "./CustomerNextActionCard";
import { CustomerOpenOrdersPreview } from "./CustomerOpenOrdersPreview";
import { CustomerOverviewKpis } from "./CustomerOverviewKpis";
import { CustomerPurchaseEvolutionChart } from "./CustomerPurchaseEvolutionChart";

type CustomerOverviewSectionProps = {
  customer: CustomerSummary;
  orders: CustomerOrderSummary[];
  loading?: boolean;
  activities: UseCustomerActivitiesResult;
  canViewActivities: boolean;
  onGoToOrders: () => void;
  onGoToActivities: () => void;
};

/**
 * Visão geral do cliente — KPIs, banner, gráfico, preview de pedidos e laterais.
 */
export function CustomerOverviewSection({
  customer,
  orders,
  loading = false,
  activities,
  canViewActivities,
  onGoToOrders,
  onGoToActivities,
}: CustomerOverviewSectionProps) {
  const evolution = useCustomerPurchaseEvolution(customer.codigo, customer.loja, true);

  return (
    <div className="cm-customer-overview">
      <CustomerOverviewKpis customer={customer} loading={loading} />
      <CustomerAttentionBanner customer={customer} onAnalyze={onGoToOrders} />

      <div className="cm-customer-overview__grid">
        <div className="cm-customer-overview__main">
          <CustomerPurchaseEvolutionChart
            points={evolution.points}
            loading={evolution.loading}
            error={evolution.error}
          />
          <CustomerOpenOrdersPreview orders={orders} onSeeAll={onGoToOrders} />
          <CustomerActivityTimelinePanel
            activities={activities}
            canViewActivities={canViewActivities}
            preview
            onViewActivities={onGoToActivities}
          />
        </div>
        <aside className="cm-customer-overview__side">
          <CustomerNextActionCard customer={customer} onViewOrders={onGoToOrders} />
        </aside>
      </div>
    </div>
  );
}
