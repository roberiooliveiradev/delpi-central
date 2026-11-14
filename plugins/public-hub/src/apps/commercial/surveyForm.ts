/**
 * Regras puras do formulário da Pesquisa de Satisfação (UI-03).
 * Estado vive só em memória: nenhuma persistência local; validação final é da API.
 */
import type { SurveyAnswerPayload, SurveyQuestionItem, SurveyQuestionnaire } from "./api.ts";

/** Denominador aprovado: 10 dimensões + satisfação geral + recomendação. */
export const REQUIRED_ASSESSMENTS = 12;

export const NOT_APPLICABLE = "na" as const;

export type DimensionAnswer = number | typeof NOT_APPLICABLE;

export type SurveyAnswers = {
  dimensions: Record<string, DimensionAnswer | undefined>;
  overall: number | undefined;
  recommendation: number | undefined;
  strengths: string;
  improvements: string;
  unmet_needs: string;
};

export type SurveyStep = {
  index: 1 | 2 | 3;
  title: string;
  items: SurveyQuestionItem[];
};

export const OPEN_TEXT_MAX_LENGTH = 5000;

export function createEmptyAnswers(): SurveyAnswers {
  return {
    dimensions: {},
    overall: undefined,
    recommendation: undefined,
    strengths: "",
    improvements: "",
    unmet_needs: "",
  };
}

/** Três etapas de cinco perguntas, na ordem canônica do catálogo. */
export function buildSteps(questionnaire: SurveyQuestionnaire): SurveyStep[] {
  const items = [...questionnaire.items].sort((a, b) => a.order - b.order);
  return [
    { index: 1, title: "Avaliação dos serviços — parte 1", items: items.slice(0, 5) },
    { index: 2, title: "Avaliação dos serviços — parte 2", items: items.slice(5, 10) },
    { index: 3, title: "Visão geral e comentários", items: items.slice(10, 15) },
  ];
}

/** Resposta obrigatória válida para o item? Itens abertos são sempre opcionais. */
export function isItemAnswered(item: SurveyQuestionItem, answers: SurveyAnswers): boolean {
  if (item.kind === "dimension") {
    const value = answers.dimensions[item.key];
    return value === NOT_APPLICABLE || (typeof value === "number" && value >= 1 && value <= 5);
  }
  if (item.kind === "overall") {
    return typeof answers.overall === "number" && answers.overall >= 1 && answers.overall <= 5;
  }
  if (item.kind === "recommendation") {
    return (
      typeof answers.recommendation === "number" &&
      answers.recommendation >= 0 &&
      answers.recommendation <= 10
    );
  }
  return true;
}

function isRequiredAssessment(item: SurveyQuestionItem): boolean {
  return item.kind !== "open";
}

export function countCompleted(questionnaire: SurveyQuestionnaire, answers: SurveyAnswers): number {
  return questionnaire.items.filter(
    (item) => isRequiredAssessment(item) && isItemAnswered(item, answers),
  ).length;
}

export function progressPercent(completed: number): number {
  return Math.round((100 * completed) / REQUIRED_ASSESSMENTS);
}

/** Chaves das avaliações obrigatórias ainda sem seleção em uma etapa. */
export function pendingKeys(step: SurveyStep, answers: SurveyAnswers): string[] {
  return step.items
    .filter((item) => isRequiredAssessment(item) && !isItemAnswered(item, answers))
    .map((item) => item.key);
}

export function allPendingKeys(steps: readonly SurveyStep[], answers: SurveyAnswers): string[] {
  return steps.flatMap((step) => pendingKeys(step, answers));
}

/** Primeira etapa (1–3) com pendência obrigatória; null se tudo está completo. */
export function firstIncompleteStep(
  steps: readonly SurveyStep[],
  answers: SurveyAnswers,
): SurveyStep | null {
  return steps.find((step) => pendingKeys(step, answers).length > 0) ?? null;
}

/** Há conteúdo digitado/selecionado ainda não enviado? Controla o `beforeunload`. */
export function hasUnsentAnswers(answers: SurveyAnswers): boolean {
  return (
    Object.values(answers.dimensions).some((value) => value !== undefined) ||
    answers.overall !== undefined ||
    answers.recommendation !== undefined ||
    [answers.strengths, answers.improvements, answers.unmet_needs].some(
      (text) => text.trim().length > 0,
    )
  );
}

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

/** Monta o corpo do POST; null enquanto houver avaliação obrigatória pendente. */
export function buildSubmitPayload(
  questionnaire: SurveyQuestionnaire,
  answers: SurveyAnswers,
): SurveyAnswerPayload | null {
  if (countCompleted(questionnaire, answers) !== REQUIRED_ASSESSMENTS) return null;
  const dimensions: Record<string, number | null> = {};
  for (const item of questionnaire.items) {
    if (item.kind !== "dimension") continue;
    const value = answers.dimensions[item.key];
    dimensions[item.key] = value === NOT_APPLICABLE ? null : (value as number);
  }
  return {
    overall_score: answers.overall as number,
    recommendation_score: answers.recommendation as number,
    dimensions,
    strengths: optionalText(answers.strengths),
    improvements: optionalText(answers.improvements),
    unmet_needs: optionalText(answers.unmet_needs),
  };
}

/** Texto da resposta para a revisão (sem inventar nota quando ausente). */
export function describeAnswer(
  item: SurveyQuestionItem,
  answers: SurveyAnswers,
  scaleLabels: Record<number, string>,
): string {
  if (item.kind === "dimension") {
    const value = answers.dimensions[item.key];
    if (value === NOT_APPLICABLE) return "Não se aplica";
    if (typeof value === "number") return `${value} — ${scaleLabels[value] ?? ""}`.replace(/ — $/, "");
    return "Sem resposta";
  }
  if (item.kind === "overall") {
    return typeof answers.overall === "number"
      ? `${answers.overall} — ${scaleLabels[answers.overall] ?? ""}`.replace(/ — $/, "")
      : "Sem resposta";
  }
  if (item.kind === "recommendation") {
    return typeof answers.recommendation === "number" ? String(answers.recommendation) : "Sem resposta";
  }
  const text = (
    item.key === "strengths"
      ? answers.strengths
      : item.key === "improvements"
        ? answers.improvements
        : answers.unmet_needs
  ).trim();
  return text || "Não preenchido";
}

const WINDOW_FORMATTER = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
});

function formatInstant(value: string): string | null {
  const date = new Date(value);
  if (!value || Number.isNaN(date.getTime())) return null;
  return WINDOW_FORMATTER.format(date).replace(",", "");
}

/** «dd/mm/aaaa hh:mm a dd/mm/aaaa hh:mm» no fuso do Portal; null se a API não enviou datas válidas. */
export function formatSurveyWindow(startsAt: string, endsAt: string): string | null {
  const from = formatInstant(startsAt);
  const to = formatInstant(endsAt);
  return from && to ? `${from} a ${to}` : null;
}
