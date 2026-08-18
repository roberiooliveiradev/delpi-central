import { CommercialActionButton, CommercialSectionCard } from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import { buildCustomerDetailSearch, type CustomerDetailSection } from "../utils/customerDetailSection";

type CustomerPreMeetingChecklistProps = {
  onGoToSection: (section: CustomerDetailSection) => void;
  onGoToForecast: () => void;
};

const ITEMS: Array<{
  id: string;
  label: string;
  section?: CustomerDetailSection;
  forecast?: boolean;
  blocked?: boolean;
}> = [
  { id: "historico", label: "Histórico de faturamento", section: "historico" },
  { id: "pedidos", label: "Pedidos em aberto", section: "pedidos" },
  { id: "oportunidades", label: "Oportunidades", section: "oportunidades" },
  { id: "atividades", label: "Atividades / follow-ups", section: "atividades" },
  { id: "forecast", label: "Previsão declarada (Overview)", forecast: true },
  { id: "rent", label: "Rentabilidade (bloqueada — FIN-004)", blocked: true },
];

export function CustomerPreMeetingChecklist({
  onGoToSection,
  onGoToForecast,
}: CustomerPreMeetingChecklistProps) {
  return (
    <CommercialSectionCard
      title="Checklist pré-reunião"
      hint={CM_HELP.customerDetail.preMeetingChecklist}
    >
      <ul className="cm-customer-overview__checklist">
        {ITEMS.map((item) => (
          <li key={item.id}>
            {item.blocked ? (
              <span>{item.label}</span>
            ) : item.forecast ? (
              <CommercialActionButton variant="ghost" onClick={onGoToForecast}>
                {item.label}
              </CommercialActionButton>
            ) : item.section ? (
              <CommercialActionButton
                variant="ghost"
                onClick={() => onGoToSection(item.section!)}
              >
                {item.label}
              </CommercialActionButton>
            ) : (
              item.label
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
