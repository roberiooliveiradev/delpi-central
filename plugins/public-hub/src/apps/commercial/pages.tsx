import type { AppPublicPages } from "../../shell/types";
import { fetchPublicSurvey } from "./api.ts";
import { SatisfactionSurveyPage } from "./satisfaction-survey/SatisfactionSurveyPage.tsx";
import { toPublicSurveyState } from "./satisfaction-survey/surveyResults.ts";

export const commercialPages: AppPublicPages = {
  form: {
    documentTitle: "Pesquisa de Satisfação de Clientes",
    // Sem decoração do shell: o formulário do kit controla tema e layout
    // (chrome "bare" também garante o contrato do rodapé fixo — §14.4e).
    chrome: "bare",
    // O estado inválido/indisponível é apresentado pela própria página (não o 404 genérico).
    load: ({ token }) => fetchPublicSurvey(token),
    render: (data) => <SatisfactionSurveyPage state={toPublicSurveyState(data)} />,
  },
};
