import type {
  QuestionnaireAnswer,
  QuestionnaireAnswers,
  QuestionnaireQuestion,
  QuestionnaireStep,
} from "./guidedQuestionnaireTypes";

/** Fase do fluxo guiado + etapa corrente + modo edição vindo da revisão. */
export type GuidedFlow = {
  phase: "intro" | "step" | "review" | "result";
  stepIndex: number;
  editingFromReview: boolean;
};

export const initialFlow: GuidedFlow = {
  phase: "intro",
  stepIndex: 0,
  editingFromReview: false,
};

export function startFlow(): GuidedFlow {
  return { phase: "step", stepIndex: 0, editingFromReview: false };
}

export function goNext(flow: GuidedFlow, totalSteps: number): GuidedFlow {
  if (flow.phase !== "step") return flow;
  if (flow.editingFromReview || flow.stepIndex >= totalSteps - 1) {
    return { phase: "review", stepIndex: flow.stepIndex, editingFromReview: false };
  }
  return { ...flow, stepIndex: flow.stepIndex + 1 };
}

export function goBack(flow: GuidedFlow, totalSteps: number): GuidedFlow {
  if (flow.phase === "review") {
    return {
      phase: "step",
      stepIndex: Math.max(totalSteps - 1, 0),
      editingFromReview: false,
    };
  }
  if (flow.phase === "step" && !flow.editingFromReview && flow.stepIndex > 0) {
    return { ...flow, stepIndex: flow.stepIndex - 1 };
  }
  return flow;
}

/** Da revisão para a etapa `i` em modo edição (só "Voltar à revisão"). */
export function startEdit(stepIndex: number): GuidedFlow {
  return { phase: "step", stepIndex, editingFromReview: true };
}

/** Resposta válida para a pergunta (opcionais nunca bloqueiam — ver `missingInStep`). */
export function isQuestionAnswered(
  question: QuestionnaireQuestion,
  answer: QuestionnaireAnswer | undefined,
): boolean {
  if (question.kind === "scale") {
    if (question.scale.notApplicable != null) {
      return typeof answer === "number" || answer === "na";
    }
    return typeof answer === "number";
  }
  return typeof answer === "string" && answer.trim().length > 0;
}

/** Perguntas obrigatórias sem resposta na etapa. */
export function missingInStep(
  step: QuestionnaireStep,
  answers: QuestionnaireAnswers,
): QuestionnaireQuestion[] {
  return step.questions.filter(
    (q) => q.required && !isQuestionAnswered(q, answers[q.key]),
  );
}

/** Progresso: obrigatórias respondidas ÷ total de obrigatórias (todas as etapas). */
export function questionnaireProgress(
  steps: QuestionnaireStep[],
  answers: QuestionnaireAnswers,
): { done: number; total: number } {
  const required = steps.flatMap((s) => s.questions).filter((q) => q.required);
  return {
    total: required.length,
    done: required.filter((q) => isQuestionAnswered(q, answers[q.key])).length,
  };
}

/** Ao menos uma resposta presente (dispara o aviso de saída). */
export function hasAnyAnswer(answers: QuestionnaireAnswers): boolean {
  return Object.values(answers).some(
    (a) => typeof a === "number" || a === "na" || (typeof a === "string" && a.length > 0),
  );
}

/** Respostas prontas para o envio: texto vazio/só espaços é omitido. */
export function buildSubmitAnswers(
  answers: QuestionnaireAnswers,
): QuestionnaireAnswers {
  const out: QuestionnaireAnswers = {};
  for (const [key, value] of Object.entries(answers)) {
    if (typeof value === "string" && value.trim().length === 0) continue;
    out[key] = typeof value === "string" ? value.trim() : value;
  }
  return out;
}
