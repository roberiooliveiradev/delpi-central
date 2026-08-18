import { useState } from "react";

import type { CustomerSummary } from "../types/customerSummary";
import type { CustomerOrderSummary } from "../types/customerOrderSummary";
import type { UseCustomerActivitiesResult } from "../hooks/useCustomerActivities";
import {
  useCustomerPurchaseEvolution,
  type PurchaseEvolutionWindowMonths,
} from "../hooks/useCustomerPurchaseEvolution";
import { CustomerActivityTimelinePanel } from "./CustomerActivityTimelinePanel";
import { CustomerConversationPoints } from "./CustomerConversationPoints";
import { CustomerPreMeetingChecklist } from "./CustomerPreMeetingChecklist";
import { CustomerOpenOrdersPreview } from "./CustomerOpenOrdersPreview";
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
  onGoToSection: (section: "historico" | "pedidos" | "oportunidades" | "atividades") => void;
};

/**
 * Visão geral do cliente — fatos, evolução, pedidos e atividades.
 */
export function CustomerOverviewSection({
  customer,
  orders,
  activities,
  canViewActivities,
  canViewAnalytics,
  coveragePartial,
  basePath,
  onGoToOrders,
  onGoToActivities,
  onGoToSection,
}: CustomerOverviewSectionProps) {
  const [windowMonths, setWindowMonths] =
    useState<PurchaseEvolutionWindowMonths>(12);
  const evolution = useCustomerPurchaseEvolution(
    customer.codigo,
    customer.loja,
    true,
    windowMonths,
  );

  return (
    <div className="cm-customer-overview">
      <CustomerPreMeetingChecklist onGoToSection={onGoToSection} />
      <CustomerConversationPoints
        customer={customer}
        coveragePartial={coveragePartial}
      />
      <CustomerPurchaseEvolutionChart
        points={evolution.points}
        loading={evolution.loading}
        error={evolution.error}
        windowMonths={windowMonths}
        onWindowMonthsChange={setWindowMonths}
      />
      <CustomerOpenOrdersPreview
        orders={orders}
        basePath={basePath}
        codigo={customer.codigo}
        loja={customer.loja}
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
