/**
 * Questionário da API (`SurveyQuestionnaire`) → definição declarativa do kit.
 * As 15 perguntas são literais da API (§14.4a); nenhuma pergunta é inventada.
 */
import type {
  QuestionnaireQuestion,
  QuestionnaireStep,
} from "@delpi/plugin-ui/index";

import type { SurveyQuestionItem, SurveyQuestionnaire } from "../api.ts";
import { OPEN_TEXT_MAX_LENGTH, buildSteps } from "../surveyForm.ts";

const NOT_APPLICABLE_LABEL = "Não se aplica";
const OPEN_TEXT_LABEL = "Sua resposta";
const OPEN_TEXT_PLACEHOLDER = "Escreva sua resposta";

type ScaleLabels = Record<number, string>;

function scaleLabel(labels: ScaleLabels, n: number): string {
  return labels[n] ?? "";
}

function scaleQuestion(
  item: SurveyQuestionItem,
  labels: ScaleLabels,
): QuestionnaireQuestion {
  const isRecommendation = item.kind === "recommendation";
  const min = item.scaleMin ?? 1;
  const max = item.scaleMax ?? 5;
  const caption = (n: number) =>
    isRecommendation
      ? `Sua nota: ${n}`
      : `Sua nota: ${n} · ${scaleLabel(labels, n)}`;
  const reviewValue = (n: number) =>
    isRecommendation ? `${n}` : `${n} · ${scaleLabel(labels, n)}`;
  return {
    kind: "scale",
    key: item.key,
    number: item.order,
    eyebrow: item.title,
    prompt: item.prompt,
    required: true,
    scale: {
      min,
      max,
      optionLabel: (n) =>
        isRecommendation ? `${n}` : `${n} — ${scaleLabel(labels, n)}`,
      endLabels: isRecommendation
        ? { min: "0 · Nada provável", max: "10 · Extremamente provável" }
        : {
            min: `${min} · ${scaleLabel(labels, min)}`,
            max: `${max} · ${scaleLabel(labels, max)}`,
          },
      endLabelsPosition: isRecommendation ? "above" : "below",
      narrowColumns: isRecommendation ? 6 : undefined,
      selectionCaption: caption,
      notApplicable: item.allowsNotApplicable
        ? { label: NOT_APPLICABLE_LABEL }
        : undefined,
      reviewValue,
    },
  };
}

function openQuestion(item: SurveyQuestionItem): QuestionnaireQuestion {
  return {
    kind: "text",
    key: item.key,
    number: item.order,
    eyebrow: item.title,
    prompt: item.prompt,
    required: false,
    text: {
      label: OPEN_TEXT_LABEL,
      placeholder: OPEN_TEXT_PLACEHOLDER,
      maxLength: OPEN_TEXT_MAX_LENGTH,
    },
  };
}

/** Três etapas de cinco perguntas na ordem canônica (reuso de `buildSteps`). */
export function buildSurveySteps(
  questionnaire: SurveyQuestionnaire,
): QuestionnaireStep[] {
  const labels = questionnaire.scaleLabels;
  return buildSteps(questionnaire).map((step) => ({
    id: `step-${step.index}`,
    title: step.title,
    questions: step.items.map((item) =>
      item.kind === "open"
        ? openQuestion(item)
        : scaleQuestion(item, labels),
    ),
  }));
}
