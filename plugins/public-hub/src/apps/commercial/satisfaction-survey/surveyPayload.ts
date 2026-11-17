/**
 * Respostas do kit (`QuestionnaireAnswers`) → `SurveyAnswerPayload` da API.
 * N/A vira `null` em `dimensions`; abertas vazias viram `null`.
 */
import type { QuestionnaireAnswers } from "@delpi/plugin-ui/index";

import type { SurveyAnswerPayload, SurveyQuestionnaire } from "../api.ts";

function scoreOf(value: QuestionnaireAnswers[string]): number {
  return typeof value === "number" ? value : 0;
}

function textOrNull(value: QuestionnaireAnswers[string]): string | null {
  return typeof value === "string" && value.trim() !== "" ? value.trim() : null;
}

/** Monta o corpo do POST — chamado só com as obrigatórias já respondidas. */
export function buildSurveyPayload(
  questionnaire: SurveyQuestionnaire,
  answers: QuestionnaireAnswers,
): SurveyAnswerPayload {
  const dimensions: Record<string, number | null> = {};
  for (const item of questionnaire.items) {
    if (item.kind !== "dimension") continue;
    const value = answers[item.key];
    dimensions[item.key] =
      value === "na" ? null : typeof value === "number" ? value : null;
  }
  return {
    overall_score: scoreOf(answers.overall_score),
    recommendation_score: scoreOf(answers.recommendation_score),
    dimensions,
    strengths: textOrNull(answers.strengths),
    improvements: textOrNull(answers.improvements),
    unmet_needs: textOrNull(answers.unmet_needs),
  };
}
