import {
  CommercialSectionCard,
  CommercialStatusBadge,
} from "../../../app/commercialUi";
import type { CustomerSummary } from "../types/customerSummary";
import { buildCustomerConversationPoints } from "../utils/customerAccountActions";

type CustomerConversationPointsProps = {
  customer: CustomerSummary;
  coveragePartial: boolean;
};

export function CustomerConversationPoints({
  customer,
  coveragePartial,
}: CustomerConversationPointsProps) {
  const points = buildCustomerConversationPoints(customer, coveragePartial);

  return (
    <CommercialSectionCard title="Pontos para conversa">
      {points.length > 0 ? (
        <div
          className="cm-customer-conversation-points"
          role="list"
          aria-label="Fatos para a próxima conversa com o cliente"
        >
          {points.map((point) => (
            <span key={point.id} role="listitem">
              <CommercialStatusBadge label={point.label} variant={point.variant} />
            </span>
          ))}
        </div>
      ) : (
        <p className="cm-customer-conversation-points__empty">
          Nenhum ponto objetivo identificado nos dados disponíveis.
        </p>
      )}
    </CommercialSectionCard>
  );
}
