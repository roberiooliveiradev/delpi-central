/**
 * Respostas do kit → `SurveyAnswerPayload` da API (§14.6.2):
 * N/A → null, abertas vazias → null, notas preservadas (inclui 0).
 */
import { describe, expect, it } from "vitest";

import type { QuestionnaireAnswers } from "@delpi/plugin-ui/index";

import { normalizeQuestionnaire, type SurveyQuestionnaire } from "../api.ts";
import { rawQuestionnaire } from "../testFixtures.ts";
import { buildSurveyPayload } from "./surveyPayload.ts";

const DIMENSION_KEYS = [
  "quality",
  "delivery_deadline",
  "service",
  "agility",
  "communication",
  "technical_support",
  "commercial_support",
  "flexibility",
  "reliability",
  "partnership",
];

function fixture(): SurveyQuestionnaire {
  const questionnaire = normalizeQuestionnaire(rawQuestionnaire());
  if (!questionnaire) throw new Error("fixture do questionário inválida");
  return questionnaire;
}

function baseAnswers(): QuestionnaireAnswers {
  const answers: QuestionnaireAnswers = {};
  for (const key of DIMENSION_KEYS) answers[key] = 4;
  answers.overall_score = 5;
  answers.recommendation_score = 9;
  return answers;
}

describe("buildSurveyPayload", () => {
  it("mapeia todas as respostas para o contrato da API", () => {
    const answers = baseAnswers();
    answers.strengths = "Atendimento ágil";
    answers.improvements = "Prazos";
    answers.unmet_needs = "Integrações";
    expect(buildSurveyPayload(fixture(), answers)).toEqual({
      overall_score: 5,
      recommendation_score: 9,
      dimensions: Object.fromEntries(DIMENSION_KEYS.map((key) => [key, 4])),
      strengths: "Atendimento ágil",
      improvements: "Prazos",
      unmet_needs: "Integrações",
    });
  });

  it('"na" vira null na dimensão correspondente', () => {
    const answers = baseAnswers();
    answers.service = "na";
    const payload = buildSurveyPayload(fixture(), answers);
    expect(payload.dimensions.service).toBeNull();
    expect(payload.dimensions.quality).toBe(4);
  });

  it("abertas vazias, em branco ou ausentes viram null; preenchida vai aparada", () => {
    const answers = baseAnswers();
    answers.strengths = "   ";
    answers.improvements = "  melhorar prazos  ";
    const payload = buildSurveyPayload(fixture(), answers);
    expect(payload.strengths).toBeNull();
    expect(payload.improvements).toBe("melhorar prazos");
    expect(payload.unmet_needs).toBeNull();
  });

  it("preserva nota 0 na recomendação", () => {
    const answers = baseAnswers();
    answers.recommendation_score = 0;
    expect(buildSurveyPayload(fixture(), answers).recommendation_score).toBe(0);
  });

  it("preserva a chave de cada dimensão declarada pela API", () => {
    const payload = buildSurveyPayload(fixture(), baseAnswers());
    expect(Object.keys(payload.dimensions).sort()).toEqual(
      [...DIMENSION_KEYS].sort(),
    );
  });
});
