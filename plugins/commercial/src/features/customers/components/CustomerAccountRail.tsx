import { ActionButton } from "@delpi/plugin-ui/index";

import {
  CommercialDetailCard,
  CommercialDetailFieldGrid,
  CommercialSectionCard,
} from "../../../app/commercialUi";
import { navigatePluginView } from "../../../app/pluginNavigation";
import { CM_HELP } from "../../../content/helpTooltips";
import { formatCurrency } from "../../../utils/format";
import { formatDisplayDate } from "../../../utils/dates";
import type { CustomerSummary } from "../types/customerSummary";
import { statusLabel, resolveCustomerStatus } from "../utils/customerListPresentation";

type CustomerAccountRailProps = {
  customer: CustomerSummary;
  basePath: string;
  canViewProposals: boolean;
  onViewOrders: () => void;
};

export function CustomerAccountRail({
  customer,
  basePath,
  canViewProposals,
  onViewOrders,
}: CustomerAccountRailProps) {
  const fields = [
    { label: "Última venda", value: formatDisplayDate(customer.lastPurchaseDate) },
    {
      label: "Faturamento 12 meses",
      value: customer.billed12m == null ? null : formatCurrency(customer.billed12m),
    },
    {
      label: "Situação",
      value: statusLabel(customer.status ?? resolveCustomerStatus(customer)),
    },
    { label: "Próxima entrega", value: formatDisplayDate(customer.proximaEntrega) },
    { label: "Próxima ação", value: customer.nextAction || null },
  ];

  const content = () => (
    <>
      <CommercialDetailFieldGrid fields={fields} valueFallback="Dado indisponível" wrapLabels />
      <div className="cm-nav-row">
        {customer.quantidadePedidosAbertos > 0 ? (
          <ActionButton variant="ghost" onClick={onViewOrders}>
            Ver pedidos
          </ActionButton>
        ) : null}
        {canViewProposals ? (
          <ActionButton
            variant="ghost"
            onClick={() => navigatePluginView("proposals", { basePath })}
          >
            Propostas gerais
          </ActionButton>
        ) : null}
      </div>
    </>
  );

  return (
    <>
      <div className="pva-customer-account-rail__desktop">
        <CommercialDetailCard
          title="Dados da conta"
          hint={CM_HELP.customerDetail.accountData}
          className="pva-customer-account-rail"
        >
          {content()}
        </CommercialDetailCard>
      </div>
      <div className="pva-customer-account-rail__mobile">
        <CommercialSectionCard
          title="Dados da conta"
          hint={CM_HELP.customerDetail.accountData}
          collapsible
          defaultOpen={false}
        >
          {content()}
        </CommercialSectionCard>
      </div>
    </>
  );
}
