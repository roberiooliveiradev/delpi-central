/**
 * Desfechos da API → telas do kit (§14.4c).
 * `submitted` é o único sucesso; `rejected`/`temporary_error` viram nova
 * tentativa na revisão; os demais são terminais com os textos vigentes.
 * O nome interno da campanha nunca aparece.
 */
import type {
  FormResultPanelProps,
  QuestionnaireAnswers,
  QuestionnaireSubmitOutcome,
} from "@delpi/plugin-ui/index";

import {
  submitPublicSurvey,
  type PublicSurveyState,
  type SubmitOutcome,
} from "../api.ts";
import { buildSurveyPayload } from "./surveyPayload.ts";
import {
  SURVEY_CLOSE_HINT,
  SURVEY_THANKS_MESSAGE,
  SURVEY_THANKS_TITLE,
  formatSurveyPeriod,
} from "./surveyTexts.ts";

export type SurveyTerminalStatus = Exclude<PublicSurveyState["status"], "open">;

const TERMINAL: Record<
  SurveyTerminalStatus,
  Pick<FormResultPanelProps, "tone" | "title" | "message">
> = {
  not_open: {
    tone: "info",
    title: "A pesquisa ainda não está aberta",
    message:
      "Este link será liberado no início do período da pesquisa. Volte a acessá-lo nessa data.",
  },
  closed: {
    tone: "info",
    title: "A pesquisa foi encerrada",
    message: "O período de respostas terminou. Agradecemos o seu interesse.",
  },
  already_submitted: {
    tone: "info",
    title: "Resposta já registrada",
    message:
      "Já recebemos a resposta da sua empresa nesta pesquisa. Ela não pode ser enviada novamente.",
  },
  invalid: {
    tone: "error",
    title: "Link inválido ou indisponível",
    message:
      "Não foi possível localizar esta pesquisa. Confira o link recebido ou solicite um novo convite.",
  },
  temporary_error: {
    tone: "error",
    title: "Pesquisa temporariamente indisponível",
    message:
      "Não foi possível carregar a pesquisa agora. Tente novamente em alguns instantes.",
  },
};

const SUBMIT_RETRY_FALLBACK =
  "Não foi possível confirmar o envio. Tente novamente.";

/** `SubmitOutcome` do POST → desfecho declarado ao `GuidedQuestionnaire`. */
export function outcomeToSubmitOutcome(
  outcome: SubmitOutcome,
): QuestionnaireSubmitOutcome {
  if (outcome.outcome === "submitted") {
    return {
      type: "result",
      result: {
        tone: "success",
        title: SURVEY_THANKS_TITLE,
        message: SURVEY_THANKS_MESSAGE,
        hint: SURVEY_CLOSE_HINT,
      },
    };
  }
  if (outcome.outcome === "rejected" || outcome.outcome === "temporary_error") {
    return {
      type: "retry",
      message: outcome.message || SUBMIT_RETRY_FALLBACK,
    };
  }
  const copy = TERMINAL[outcome.outcome];
  return { type: "result", result: { ...copy } };
}

type OpenSurvey = Extract<PublicSurveyState, { status: "open" }>;

const KNOWN_STATUSES: readonly string[] = [
  "open",
  "not_open",
  "closed",
  "already_submitted",
  "invalid",
  "temporary_error",
];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/**
 * Estreita `data` do `render` do shell (unknown) para o estado da API.
 * `load` já devolve `PublicSurveyState` normalizado; qualquer desvio vira
 * indisponibilidade temporária em vez de quebrar a página.
 */
function isPublicSurveyState(data: unknown): data is PublicSurveyState {
  return (
    isRecord(data) &&
    typeof data.status === "string" &&
    KNOWN_STATUSES.includes(data.status) &&
    (data.status !== "open" || isRecord(data.questionnaire))
  );
}

export function toPublicSurveyState(data: unknown): PublicSurveyState {
  return isPublicSurveyState(data) ? data : { status: "temporary_error" };
}

/** `onSubmit` da página: respostas do kit → POST → desfecho declarado. */
export async function submitSurveyAnswers(
  survey: OpenSurvey,
  answers: QuestionnaireAnswers,
): Promise<QuestionnaireSubmitOutcome> {
  const outcome = await submitPublicSurvey(
    survey.token,
    buildSurveyPayload(survey.questionnaire, answers),
  );
  return outcomeToSubmitOutcome(outcome);
}

/** Estado do GET que não é `open` → painel terminal (sem nome de campanha). */
export function stateToResultProps(
  state: Exclude<PublicSurveyState, { status: "open" }>,
): FormResultPanelProps {
  const copy = TERMINAL[state.status];
  const props: FormResultPanelProps = { ...copy };
  if (
    (state.status === "not_open" || state.status === "closed") &&
    state.startsAt &&
    state.endsAt
  ) {
    const period = formatSurveyPeriod(state.startsAt, state.endsAt);
    if (period) props.hint = `Período da pesquisa: ${period}`;
  }
  return props;
}
