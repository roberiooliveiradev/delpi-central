/**
 * Definição do kit a partir do `SurveyQuestionnaire` da API (§14.6.1):
 * 15 perguntas literais, 5/5/5, N/A só nas dimensões, 0–10 acima em 6 colunas.
 */
import { describe, expect, it } from "vitest";

import type { QuestionnaireScaleQuestion } from "@delpi/plugin-ui/index";

import { normalizeQuestionnaire, type SurveyQuestionnaire } from "../api.ts";
import { rawQuestionnaire } from "../testFixtures.ts";
import { buildSurveySteps } from "./surveyDefinition.ts";

function fixture(): SurveyQuestionnaire {
  const questionnaire = normalizeQuestionnaire(rawQuestionnaire());
  if (!questionnaire) throw new Error("fixture do questionário inválida");
  return questionnaire;
}

function scales(questionnaire = fixture()): QuestionnaireScaleQuestion[] {
  return buildSurveySteps(questionnaire)
    .flatMap((step) => step.questions)
    .filter((q): q is QuestionnaireScaleQuestion => q.kind === "scale");
}

describe("buildSurveySteps", () => {
  it("monta 3 etapas de 5 perguntas na divisão canônica", () => {
    const steps = buildSurveySteps(fixture());
    expect(steps.map((step) => step.title)).toEqual([
      "Avaliação dos serviços — parte 1",
      "Avaliação dos serviços — parte 2",
      "Visão geral e comentários",
    ]);
    expect(steps.map((step) => step.questions.length)).toEqual([5, 5, 5]);
    expect(steps[0]?.questions.map((q) => q.key)).toEqual([
      "quality",
      "delivery_deadline",
      "service",
      "agility",
      "communication",
    ]);
    expect(steps[1]?.questions.map((q) => q.key)).toEqual([
      "technical_support",
      "commercial_support",
      "flexibility",
      "reliability",
      "partnership",
    ]);
    expect(steps[2]?.questions.map((q) => q.key)).toEqual([
      "overall_score",
      "recommendation_score",
      "strengths",
      "improvements",
      "unmet_needs",
    ]);
  });

  it("usa chave, título e enunciado literais da API", () => {
    const questionnaire = fixture();
    const questions = buildSurveySteps(questionnaire).flatMap(
      (step) => step.questions,
    );
    expect(questions.map((q) => q.key)).toEqual(
      questionnaire.items.map((item) => item.key),
    );
    expect(questions.map((q) => q.prompt)).toEqual(
      questionnaire.items.map((item) => item.prompt),
    );
    expect(questions.map((q) => q.eyebrow)).toEqual(
      questionnaire.items.map((item) => item.title),
    );
    expect(questions.map((q) => q.number)).toEqual(
      questionnaire.items.map((item) => item.order),
    );
  });

  it("N/A existe só nas 10 dimensões", () => {
    const withNa = scales().filter((q) => q.scale.notApplicable != null);
    expect(withNa).toHaveLength(10);
    expect(
      withNa.every((q) => q.scale.notApplicable?.label === "Não se aplica"),
    ).toBe(true);
    const overall = scales().find((q) => q.key === "overall_score");
    const recommendation = scales().find(
      (q) => q.key === "recommendation_score",
    );
    expect(overall?.scale.notApplicable).toBeUndefined();
    expect(recommendation?.scale.notApplicable).toBeUndefined();
  });

  it("dimensões e geral usam 1–5 obrigatório com rótulos da API", () => {
    const all = scales();
    const eleven = all.filter((q) => q.key !== "recommendation_score");
    expect(eleven).toHaveLength(11);
    for (const question of eleven) {
      expect(question.required).toBe(true);
      expect(question.scale.min).toBe(1);
      expect(question.scale.max).toBe(5);
      expect(question.scale.optionLabel(4)).toBe("4 — Satisfeito");
      expect(question.scale.endLabelsPosition).toBe("below");
      expect(question.scale.endLabels).toEqual({
        min: "1 · Muito insatisfeito",
        max: "5 · Muito satisfeito",
      });
      expect(question.scale.selectionCaption?.(4)).toBe(
        "Sua nota: 4 · Satisfeito",
      );
      expect(question.scale.reviewValue?.(4)).toBe("4 · Satisfeito");
      expect(question.scale.narrowColumns).toBeUndefined();
    }
  });

  it("recomendação é 0–10 com legenda acima e 6 colunas estreitas", () => {
    const recommendation = scales().find(
      (q) => q.key === "recommendation_score",
    );
    expect(recommendation?.required).toBe(true);
    expect(recommendation?.scale.min).toBe(0);
    expect(recommendation?.scale.max).toBe(10);
    expect(recommendation?.scale.endLabelsPosition).toBe("above");
    expect(recommendation?.scale.narrowColumns).toBe(6);
    expect(recommendation?.scale.endLabels).toEqual({
      min: "0 · Nada provável",
      max: "10 · Extremamente provável",
    });
    expect(recommendation?.scale.optionLabel(9)).toBe("9");
    expect(recommendation?.scale.selectionCaption?.(9)).toBe("Sua nota: 9");
    expect(recommendation?.scale.reviewValue?.(9)).toBe("9");
  });

  it("abertas são texto opcional com rótulo, exemplo e limite", () => {
    const opens = buildSurveySteps(fixture())
      .flatMap((step) => step.questions)
      .filter((q) => q.kind === "text");
    expect(opens.map((q) => q.key)).toEqual([
      "strengths",
      "improvements",
      "unmet_needs",
    ]);
    for (const question of opens) {
      expect(question.required).toBe(false);
      expect(question.text.label).toBe("Sua resposta");
      expect(question.text.placeholder).toBe("Escreva sua resposta");
      expect(question.text.maxLength).toBe(5000);
    }
  });
});

describe("questionário incompleto", () => {
  it("API rejeita catálogo incompleto — a página fica indisponível", () => {
    const raw = rawQuestionnaire();
    const items = raw.items;
    if (!Array.isArray(items)) throw new Error("fixture sem itens");
    raw.items = items.slice(0, 14);
    expect(normalizeQuestionnaire(raw)).toBeNull();
  });
});
