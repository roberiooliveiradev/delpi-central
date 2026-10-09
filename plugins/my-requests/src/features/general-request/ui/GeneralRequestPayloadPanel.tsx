import { MY_REQUESTS_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { MyRequestsSectionCard } from "../../../ui/mrUi";
import { parseGeneralRequestPayload } from "../domain/generalRequestPayload";

type GeneralRequestPayloadPanelProps = {
  payload: Record<string, unknown>;
};

/**
 * Chamado estilo helpdesk — o assunto é a informação principal: título em
 * destaque e a descrição logo abaixo, sem grade de campos lado a lado.
 */
export function GeneralRequestPayloadPanel({
  payload,
}: GeneralRequestPayloadPanelProps) {
  const view = parseGeneralRequestPayload(payload);
  return (
    <MyRequestsSectionCard
      title="Chamado"
      hint={MY_REQUESTS_HELP_TOOLTIPS.detail.generalRequest}
      className="my-requests-general-request"
    >
      <h3 className="my-requests-general-request__title">
        {view.title || "Chamado sem título"}
      </h3>
      {view.description ? (
        <p className="my-requests-general-request__description">
          {view.description}
        </p>
      ) : (
        <p className="my-requests-general-request__description my-requests-general-request__description--empty">
          O solicitante não preencheu a descrição.
        </p>
      )}
    </MyRequestsSectionCard>
  );
}
