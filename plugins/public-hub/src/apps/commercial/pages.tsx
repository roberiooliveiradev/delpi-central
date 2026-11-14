import type { AppPublicPages } from "../../shell/types";
import { fetchPublicSurvey, type PublicSurveyState } from "./api.ts";
import { SurveyFormView } from "./FormPage";
import { SurveyStateView } from "./SurveyStateView";

function renderState(state: PublicSurveyState) {
  if (state.status === "open") return <SurveyFormView survey={state} />;
  if (state.status === "invalid" || state.status === "temporary_error") {
    return <SurveyStateView status={state.status} />;
  }
  return (
    <SurveyStateView
      status={state.status}
      campaignName={state.campaignName}
      startsAt={state.startsAt}
      endsAt={state.endsAt}
    />
  );
}

export const commercialPages: AppPublicPages = {
  form: {
    documentTitle: "Pesquisa de Satisfação — DELPI",
    chrome: "fullpage",
    // O estado inválido/indisponível é apresentado pela própria view (não o 404 genérico).
    load: ({ token }) => fetchPublicSurvey(token),
    render: (data) => renderState(data as PublicSurveyState),
  },
};
