import { ChevronRight, Circle, Lock } from "lucide-react";

import { CommercialSectionCard } from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  buildCustomerDetailSearch,
  type CustomerDetailSection,
} from "../utils/customerDetailSection";

type CustomerPreMeetingChecklistProps = {
  onGoToSection: (section: CustomerDetailSection) => void;
};

const ITEMS: Array<{
  id: string;
  label: string;
  section?: CustomerDetailSection;
  blocked?: boolean;
}> = [
  { id: "historico", label: "Histórico de faturamento", section: "historico" },
  { id: "pedidos", label: "Pedidos em aberto", section: "pedidos" },
  { id: "oportunidades", label: "Oportunidades", section: "oportunidades" },
  { id: "atividades", label: "Atividades / follow-ups", section: "atividades" },
  { id: "rent", label: "Rentabilidade (bloqueada — FIN-004)", blocked: true },
];

export function CustomerPreMeetingChecklist({
  onGoToSection,
}: CustomerPreMeetingChecklistProps) {
  return (
    <CommercialSectionCard
      title="Checklist pré-reunião"
      hint={CM_HELP.customerDetail.preMeetingChecklist}
    >
      <ul className="cm-customer-overview__checklist" aria-label="Checklist pré-reunião">
        {ITEMS.map((item) => (
          <li
            key={item.id}
            className={
              item.blocked
                ? "cm-customer-overview__checklist-item cm-customer-overview__checklist-item--blocked"
                : "cm-customer-overview__checklist-item"
            }
          >
            {item.blocked ? (
              <span className="cm-customer-overview__checklist-row">
                <Lock
                  className="cm-customer-overview__checklist-marker"
                  size={14}
                  aria-hidden
                />
                <span className="cm-customer-overview__checklist-label">
                  {item.label}
                </span>
              </span>
            ) : item.section ? (
              <button
                type="button"
                className="cm-customer-overview__checklist-row cm-customer-overview__checklist-row--action"
                onClick={() => onGoToSection(item.section!)}
              >
                <Circle
                  className="cm-customer-overview__checklist-marker"
                  size={14}
                  aria-hidden
                />
                <span className="cm-customer-overview__checklist-label">
                  {item.label}
                </span>
                <ChevronRight
                  className="cm-customer-overview__checklist-chevron"
                  size={16}
                  aria-hidden
                />
              </button>
            ) : (
              <span className="cm-customer-overview__checklist-row">
                <Circle
                  className="cm-customer-overview__checklist-marker"
                  size={14}
                  aria-hidden
                />
                <span className="cm-customer-overview__checklist-label">
                  {item.label}
                </span>
              </span>
            )}
          </li>
        ))}
      </ul>
    </CommercialSectionCard>
  );
}

export function customerDetailSectionHref(section: CustomerDetailSection): string {
  return buildCustomerDetailSearch(section);
}
