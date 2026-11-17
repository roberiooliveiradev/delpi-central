import { describe, expect, it } from "vitest";

import {
  buildSubmitAnswers,
  goBack,
  goNext,
  hasAnyAnswer,
  initialFlow,
  isQuestionAnswered,
  missingInStep,
  questionnaireProgress,
  startEdit,
  startFlow,
} from "./guidedQuestionnaireState";
import type { QuestionnaireStep } from "./guidedQuestionnaireTypes";

const SCALE_NA: QuestionnaireStep["questions"][number] = {
  kind: "scale",
  key: "q1",
  prompt: "P1",
  required: true,
  scale: {
    min: 1,
    max: 5,
    optionLabel: (n) => `Nota ${n}`,
    endLabels: { min: "min", max: "max" },
    notApplicable: { label: "Não se aplica" },
  },
};
const SCALE_PLAIN: QuestionnaireStep["questions"][number] = {
  kind: "scale",
  key: "q2",
  prompt: "P2",
  required: true,
  scale: {
    min: 0,
    max: 10,
    optionLabel: (n) => `Nota ${n}`,
    endLabels: { min: "min", max: "max" },
  },
};
const TEXT_REQ: QuestionnaireStep["questions"][number] = {
  kind: "text",
  key: "q3",
  prompt: "P3",
  required: true,
  text: { label: "Comentário" },
};
const TEXT_OPT: QuestionnaireStep["questions"][number] = {
  kind: "text",
  key: "q4",
  prompt: "P4",
  required: false,
  text: { label: "Opcional" },
};

const STEP1: QuestionnaireStep = { id: "s1", title: "Etapa 1", questions: [SCALE_NA, SCALE_PLAIN] };
const STEP2: QuestionnaireStep = { id: "s2", title: "Etapa 2", questions: [TEXT_REQ, TEXT_OPT] };
const STEPS = [STEP1, STEP2];

describe("isQuestionAnswered", () => {
  it("escala com N/A aceita nota ou 'na'; sem N/A só nota", () => {
    expect(isQuestionAnswered(SCALE_NA, 3)).toBe(true);
    expect(isQuestionAnswered(SCALE_NA, 0)).toBe(true);
    expect(isQuestionAnswered(SCALE_NA, "na")).toBe(true);
    expect(isQuestionAnswered(SCALE_NA, undefined)).toBe(false);
    expect(isQuestionAnswered(SCALE_PLAIN, "na")).toBe(false);
    expect(isQuestionAnswered(SCALE_PLAIN, 0)).toBe(true);
  });

  it("texto obrigatório exige conteúdo após trim", () => {
    expect(isQuestionAnswered(TEXT_REQ, "  ")).toBe(false);
    expect(isQuestionAnswered(TEXT_REQ, " ok ")).toBe(true);
    expect(isQuestionAnswered(TEXT_REQ, undefined)).toBe(false);
  });
});

describe("missingInStep", () => {
  it("lista só obrigatórias pendentes; opcional vazia nunca bloqueia", () => {
    expect(missingInStep(STEP2, {}).map((q) => q.key)).toEqual(["q3"]);
    expect(missingInStep(STEP2, { q3: "x" })).toEqual([]);
    expect(missingInStep(STEP1, { q1: "na" }).map((q) => q.key)).toEqual(["q2"]);
  });
});

describe("questionnaireProgress", () => {
  it("conta só obrigatórias de todas as etapas (0, parcial, total)", () => {
    expect(questionnaireProgress(STEPS, {})).toEqual({ done: 0, total: 3 });
    expect(questionnaireProgress(STEPS, { q1: 4, q4: "ignorada" })).toEqual({ done: 1, total: 3 });
    expect(questionnaireProgress(STEPS, { q1: 4, q2: 10, q3: "ok" })).toEqual({ done: 3, total: 3 });
  });
});

describe("transições", () => {
  it("intro → step; avançar até review; voltar preserva índice; editar marca modo", () => {
    expect(initialFlow.phase).toBe("intro");
    const s0 = startFlow();
    expect(s0).toEqual({ phase: "step", stepIndex: 0, editingFromReview: false });
    const s1 = goNext(s0, 2);
    expect(s1).toEqual({ phase: "step", stepIndex: 1, editingFromReview: false });
    expect(goNext(s1, 2).phase).toBe("review");
    expect(goBack({ phase: "review", stepIndex: 1, editingFromReview: false }, 2)).toEqual({
      phase: "step", stepIndex: 1, editingFromReview: false,
    });
    expect(goBack(s1, 2)).toEqual({ phase: "step", stepIndex: 0, editingFromReview: false });
    const edit = startEdit(0);
    expect(edit).toEqual({ phase: "step", stepIndex: 0, editingFromReview: true });
    // em modo edição, avançar volta à revisão
    expect(goNext(edit, 2).phase).toBe("review");
    // em modo edição, voltar não navega
    expect(goBack(edit, 2)).toEqual(edit);
  });
});

describe("hasAnyAnswer / buildSubmitAnswers", () => {
  it("hasAnyAnswer ignora string vazia", () => {
    expect(hasAnyAnswer({})).toBe(false);
    expect(hasAnyAnswer({ q4: "" })).toBe(false);
    expect(hasAnyAnswer({ q4: "x" })).toBe(true);
    expect(hasAnyAnswer({ q1: "na" })).toBe(true);
  });

  it("buildSubmitAnswers omite texto vazio e faz trim", () => {
    expect(buildSubmitAnswers({ q1: 5, q3: "  texto  ", q4: "   " })).toEqual({
      q1: 5,
      q3: "texto",
    });
  });
});
