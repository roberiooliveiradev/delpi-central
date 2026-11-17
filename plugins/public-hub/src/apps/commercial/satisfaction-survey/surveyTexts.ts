/**
 * Microcopy da Pesquisa de Satisfação (UI-03 §3.6) entregue ao kit.
 * O kit não tem texto fixo — toda a linguagem pública sai daqui.
 */
import type { GuidedQuestionnaireTexts } from "@delpi/plugin-ui/index";

export const SURVEY_TITLE = "Pesquisa de Satisfação de Clientes";
export const SURVEY_EYEBROW = "PESQUISA DE SATISFAÇÃO";
export const SURVEY_PURPOSE =
  "Sua avaliação ajuda a Delpi a melhorar produtos, serviços e o relacionamento com sua empresa.";
export const SURVEY_THANKS_TITLE = "Obrigado por participar!";
export const SURVEY_THANKS_MESSAGE =
  "Sua avaliação foi registrada. Ela ajuda a Delpi a melhorar produtos, serviços e o relacionamento com sua empresa.";
export const SURVEY_CLOSE_HINT = "Você já pode fechar esta página.";

export const SURVEY_TEXTS: GuidedQuestionnaireTexts = {
  back: "Voltar",
  next: "Avançar",
  review: "Revisar respostas",
  backToReview: "Voltar à revisão",
  submit: "Enviar respostas",
  submitting: "Enviando…",
  requiredLabel: "obrigatória",
  optionalLabel: "opcional",
  scaleError: "Selecione uma nota.",
  scaleErrorWithNa: 'Selecione uma nota ou "Não se aplica".',
  textError: "Escreva sua resposta.",
  stepFooterPending: (count) =>
    count === 1
      ? "Falta 1 avaliação nesta etapa."
      : `Faltam ${count} avaliações nesta etapa.`,
  stepLabel: (index, total, title) => `Etapa ${index} de ${total} — ${title}`,
  progressLabel: (done, total) => `${done} de ${total}`,
  progressAriaLabel: (done, total) =>
    `Progresso da pesquisa: ${done} de ${total} avaliações obrigatórias respondidas`,
  reviewTitle: "Revise suas respostas",
  reviewDescription:
    "Confira antes de enviar. Use “Editar” para corrigir uma etapa sem perder as demais respostas.",
  reviewNotice: "Depois de enviar, as respostas não poderão ser alteradas.",
  reviewNaValue: "Não se aplica",
  reviewEmptyValue: "Não respondida",
  submitError: "Não foi possível confirmar o envio. Tente novamente.",
  editLabel: "Editar",
  editAriaLabel: (stepTitle) => `Editar ${stepTitle}`,
  themeToggleAriaLabel: "Alternar entre tema claro e escuro",
};

const DATE_FORMATTER = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

/** «dd/mm/aaaa» no fuso do Portal, sem hora; null se a data não for válida. */
export function formatSurveyDate(value: string): string | null {
  const date = new Date(value);
  if (!value || Number.isNaN(date.getTime())) return null;
  return DATE_FORMATTER.format(date);
}

/** «dd/mm/aaaa a dd/mm/aaaa» sem hora; null se faltar alguma ponta válida. */
export function formatSurveyPeriod(
  startsAt: string,
  endsAt: string,
): string | null {
  const from = formatSurveyDate(startsAt);
  const to = formatSurveyDate(endsAt);
  return from && to ? `${from} a ${to}` : null;
}
