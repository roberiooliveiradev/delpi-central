/**
 * Página pública da Pesquisa de Satisfação (UI-03 §5.4).
 * Adaptador fino: o fluxo inteiro é o `GuidedQuestionnaire` do kit;
 * a página só converte contrato API ↔ kit. `commercial-api` segue autoridade.
 */
import { useMemo } from "react";
import {
  CalendarDays,
  ClipboardList,
  ShieldCheck,
} from "lucide-react";

import {
  FormButton,
  FormLogo,
  FormPageLayout,
  FormResultPanel,
  GuidedQuestionnaire,
  QuestionnaireThemeScope,
} from "@delpi/plugin-ui/index";
import type {
  QuestionnaireAnswers,
  QuestionnaireSubmitOutcome,
} from "@delpi/plugin-ui/index";

import type { PublicSurveyState } from "../api.ts";
import { buildSurveySteps } from "./surveyDefinition.ts";
import { stateToResultProps, submitSurveyAnswers } from "./surveyResults.ts";
import {
  SURVEY_EYEBROW,
  SURVEY_PURPOSE,
  SURVEY_TEXTS,
  SURVEY_TITLE,
  formatSurveyDate,
} from "./surveyTexts.ts";

const LOGO = { src: "/p/logoMinhaDelpi.svg", alt: "Minha DELPI" };

const resultLogo = <FormLogo src={LOGO.src} alt={LOGO.alt} prefix="ds" />;

type OpenSurvey = Extract<PublicSurveyState, { status: "open" }>;

function OpenSurveyView({ survey }: { survey: OpenSurvey }) {
  const steps = useMemo(
    () => buildSurveySteps(survey.questionnaire),
    [survey.questionnaire],
  );
  const deadline = formatSurveyDate(survey.endsAt);

  const onSubmit = async (
    answers: QuestionnaireAnswers,
  ): Promise<QuestionnaireSubmitOutcome> => {
    const next = await submitSurveyAnswers(survey, answers);
    return next.type === "result"
      ? { type: "result", result: { ...next.result, logo: resultLogo } }
      : next;
  };

  return (
    <GuidedQuestionnaire
      logo={LOGO}
      intro={{
        eyebrow: SURVEY_EYEBROW,
        title: SURVEY_TITLE,
        context: survey.companyName
          ? { label: "Respondendo em nome da empresa", value: survey.companyName }
          : undefined,
        description: SURVEY_PURPOSE,
        items: [
          {
            icon: <ClipboardList size={18} aria-hidden="true" />,
            content: "15 perguntas em 3 etapas, com revisão antes de enviar",
          },
          ...(deadline
            ? [
                {
                  icon: <CalendarDays size={18} aria-hidden="true" />,
                  content: <>Responda até <strong>{deadline}</strong></>,
                },
              ]
            : []),
          {
            icon: <ShieldCheck size={18} aria-hidden="true" />,
            content: "Não pedimos seus dados pessoais",
          },
        ],
        startLabel: "Começar",
      }}
      header={{
        title: SURVEY_TITLE,
        subtitle: survey.companyName ? (
          <>Respondendo por <strong>{survey.companyName}</strong></>
        ) : undefined,
        meta: deadline ? `Responda até ${deadline}` : undefined,
      }}
      steps={steps}
      texts={SURVEY_TEXTS}
      colorScheme="auto"
      showThemeToggle
      onSubmit={onSubmit}
    />
  );
}

/** Página `commercial.form`: estado da API → formulário guiado ou painel terminal. */
export function SatisfactionSurveyPage({ state }: { state: PublicSurveyState }) {
  if (state.status === "open") {
    return <OpenSurveyView survey={state} />;
  }
  const props = stateToResultProps(state);
  return (
    <QuestionnaireThemeScope colorScheme="auto" prefix="ds">
      <FormPageLayout band="tall" prefix="ds">
        <FormResultPanel
          {...props}
          prefix="ds"
          logo={resultLogo}
          action={
            state.status === "temporary_error" ? (
              <FormButton
                prefix="ds"
                onClick={() => window.location.reload()}
              >
                Tentar novamente
              </FormButton>
            ) : undefined
          }
        />
      </FormPageLayout>
    </QuestionnaireThemeScope>
  );
}

export type { QuestionnaireSubmitOutcome };
