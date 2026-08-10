import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import type { UseCustomerActivitiesResult } from "../hooks/useCustomerActivities";
import { useCustomerPurchaseEvolution } from "../hooks/useCustomerPurchaseEvolution";
import { CustomerActivityTimelinePanel } from "./CustomerActivityTimelinePanel";
import { CustomerConversationPoints } from "./CustomerConversationPoints";
import { CustomerOpenOrdersPreview } from "./CustomerOpenOrdersPreview";
import { CustomerOverviewKpis } from "./CustomerOverviewKpis";
import { CustomerPurchaseEvolutionChart } from "./CustomerPurchaseEvolutionChart";

type CustomerOverviewSectionProps = {
  customer: CustomerSummary;
  orders: CustomerOrderSummary[];
  loading?: boolean;
  activities: UseCustomerActivitiesResult;
  canViewActivities: boolean;
  canViewAnalytics: boolean;
  coveragePartial: boolean;
  basePath: string;
  onGoToOrders: () => void;
  onGoToActivities: () => void;
};

/**
 * Visão geral do cliente — KPIs, fatos, evolução, pedidos e atividades.
 */
export function CustomerOverviewSection({
  customer,
  orders,
  loading = false,
  activities,
  canViewActivities,
  canViewAnalytics,
  coveragePartial,
  basePath,
  onGoToOrders,
  onGoToActivities,
}: CustomerOverviewSectionProps) {
  const evolution = useCustomerPurchaseEvolution(customer.codigo, customer.loja, true);

  return (
    <div className="cm-customer-overview">
      <CustomerOverviewKpis customer={customer} loading={loading} />
      <CustomerConversationPoints
        customer={customer}
        coveragePartial={coveragePartial}
      />
      <CustomerPurchaseEvolutionChart
        points={evolution.points}
        loading={evolution.loading}
        error={evolution.error}
      />
      <CustomerOpenOrdersPreview
        orders={orders}
        basePath={basePath}
        canViewAnalytics={canViewAnalytics}
        onSeeAll={onGoToOrders}
      />
      <CustomerActivityTimelinePanel
        activities={activities}
        canViewActivities={canViewActivities}
        preview
        onViewActivities={onGoToActivities}
      />
    </div>
  );
}
