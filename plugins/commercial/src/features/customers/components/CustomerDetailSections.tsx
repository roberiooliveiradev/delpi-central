import type { CustomerDetailSection } from "../utils/customerDetailSection";
import {
  CUSTOMER_DETAIL_SECTION_ORDER,
  customerDetailPanelId,
  customerDetailTabId,
} from "../utils/customerDetailSection";
import { CommercialUnderlineNav } from "../../../app/commercialUi";

type CustomerDetailSectionsProps = {
  section: CustomerDetailSection;
  onChange: (section: CustomerDetailSection) => void;
  openOrdersCount?: number;
};

const LABELS: Record<CustomerDetailSection, string> = {
  resumo: "Visão geral",
  pedidos: "Pedidos em aberto",
  historico: "Histórico de vendas",
  oportunidades: "Oportunidades",
  contatos: "Contatos",
  atividades: "Atividades",
};

export function CustomerDetailSections({
  section,
  onChange,
  openOrdersCount = 0,
}: CustomerDetailSectionsProps) {
  return (
    <CommercialUnderlineNav
      mode="tabs"
      activeId={section}
      aria-label="Seções do cliente"
      items={CUSTOMER_DETAIL_SECTION_ORDER.map((id) => ({
        id,
        label: LABELS[id],
        count: id === "pedidos" ? openOrdersCount : undefined,
        tabId: customerDetailTabId(id),
        controlId: customerDetailPanelId(id),
        onSelect: () => onChange(id),
      }))}
    />
  );
}
