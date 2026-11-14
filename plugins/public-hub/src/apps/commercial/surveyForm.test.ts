import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { normalizeQuestionnaire } from "./api.ts";
import {
  NOT_APPLICABLE,
  REQUIRED_ASSESSMENTS,
  buildSteps,
  buildSubmitPayload,
  countCompleted,
  createEmptyAnswers,
  describeAnswer,
  firstIncompleteStep,
  formatSurveyWindow,
  hasUnsentAnswers,
  pendingKeys,
  progressPercent,
  type SurveyAnswers,
} from "./surveyForm.ts";
import { rawQuestionnaire } from "./testFixtures.ts";

const questionnaire = normalizeQuestionnaire(rawQuestionnaire());
assert.ok(questionnaire);
const steps = buildSteps(questionnaire);

function completeAnswers(): SurveyAnswers {
  const answers = createEmptyAnswers();
  for (const item of questionnaire!.items) {
    if (item.kind === "dimension") answers.dimensions[item.key] = 4;
  }
  answers.dimensions.agility = NOT_APPLICABLE;
  answers.overall = 5;
  answers.recommendation = 0;
  return answers;
}

describe("etapas e progresso (12 avaliações)", () => {
  it("divide em 3 etapas de 5 perguntas na ordem canônica", () => {
    assert.deepEqual(steps.map((s) => s.items.length), [5, 5, 5]);
    assert.deepEqual(steps[0].items.map((i) => i.order), [1, 2, 3, 4, 5]);
    assert.deepEqual(steps[2].items.map((i) => i.key), [
      "overall_score",
      "recommendation_score",
      "strengths",
      "improvements",
      "unmet_needs",
    ]);
  });

  it("nada selecionado = 0%; N/A e recomendação 0 contam como respondidas", () => {
    const answers = createEmptyAnswers();
    assert.equal(countCompleted(questionnaire!, answers), 0);
    assert.equal(progressPercent(0), 0);
    answers.dimensions.quality = NOT_APPLICABLE;
    answers.recommendation = 0;
    assert.equal(countCompleted(questionnaire!, answers), 2);
    assert.equal(progressPercent(2), 17);
  });

  it("comentários opcionais não alteram o progresso e 100% exige as 12", () => {
    const answers = completeAnswers();
    assert.equal(countCompleted(questionnaire!, answers), REQUIRED_ASSESSMENTS);
    assert.equal(progressPercent(REQUIRED_ASSESSMENTS), 100);
    answers.strengths = "ótimo";
    assert.equal(countCompleted(questionnaire!, answers), REQUIRED_ASSESSMENTS);
    const empty = createEmptyAnswers();
    empty.strengths = "texto";
    assert.equal(countCompleted(questionnaire!, empty), 0);
  });

  it("alterar/voltar recalcula a partir das escolhas atuais", () => {
    const answers = completeAnswers();
    delete answers.dimensions.quality;
    assert.equal(countCompleted(questionnaire!, answers), 11);
  });
});

describe("validação por etapa", () => {
  it("etapa 1 lista as 5 dimensões pendentes e libera quando completas", () => {
    const answers = createEmptyAnswers();
    assert.equal(pendingKeys(steps[0], answers).length, 5);
    for (const item of steps[0].items) answers.dimensions[item.key] = 3;
    assert.deepEqual(pendingKeys(steps[0], answers), []);
    assert.equal(pendingKeys(steps[1], answers).length, 5);
  });

  it("etapa 3 exige só geral e recomendação (abertas vazias não bloqueiam)", () => {
    const answers = createEmptyAnswers();
    assert.deepEqual(pendingKeys(steps[2], answers), ["overall_score", "recommendation_score"]);
    answers.overall = 1;
    answers.recommendation = 0;
    assert.deepEqual(pendingKeys(steps[2], answers), []);
  });

  it("firstIncompleteStep aponta a primeira etapa com pendência", () => {
    const answers = completeAnswers();
    assert.equal(firstIncompleteStep(steps, answers), null);
    delete answers.dimensions.partnership;
    assert.equal(firstIncompleteStep(steps, answers)?.index, 2);
  });
});

describe("payload e aviso de saída", () => {
  it("monta o payload mapeando N/A para null e abertas vazias para null", () => {
    const answers = completeAnswers();
    answers.strengths = "  bom  ";
    const payload = buildSubmitPayload(questionnaire!, answers);
    assert.ok(payload);
    assert.equal(payload.dimensions.agility, null);
    assert.equal(payload.dimensions.quality, 4);
    assert.equal(payload.recommendation_score, 0);
    assert.equal(payload.strengths, "bom");
    assert.equal(payload.improvements, null);
    assert.deepEqual(Object.keys(payload).sort(), [
      "dimensions",
      "improvements",
      "overall_score",
      "recommendation_score",
      "strengths",
      "unmet_needs",
    ]);
  });

  it("não monta payload com avaliação pendente (sem identificação pessoal no corpo)", () => {
    const answers = completeAnswers();
    delete answers.overall;
    assert.equal(buildSubmitPayload(questionnaire!, answers), null);
  });

  it("hasUnsentAnswers só é verdadeiro depois de qualquer preenchimento", () => {
    assert.equal(hasUnsentAnswers(createEmptyAnswers()), false);
    const textOnly = createEmptyAnswers();
    textOnly.improvements = "   ";
    assert.equal(hasUnsentAnswers(textOnly), false);
    const zero = createEmptyAnswers();
    zero.recommendation = 0;
    assert.equal(hasUnsentAnswers(zero), true);
  });

  it("describeAnswer não inventa nota nem resposta", () => {
    const answers = createEmptyAnswers();
    const quality = questionnaire!.items[0];
    assert.equal(describeAnswer(quality, answers, questionnaire!.scaleLabels), "Sem resposta");
    answers.dimensions.quality = NOT_APPLICABLE;
    assert.equal(describeAnswer(quality, answers, questionnaire!.scaleLabels), "Não se aplica");
    answers.dimensions.quality = 2;
    assert.equal(describeAnswer(quality, answers, questionnaire!.scaleLabels), "2 — Insatisfeito");
    const open = questionnaire!.items[12];
    assert.equal(describeAnswer(open, answers, questionnaire!.scaleLabels), "Não preenchido");
  });
});

describe("catálogo e datas", () => {
  it("rejeita catálogo parcial ou desconhecido (nunca renderiza formulário incompleto)", () => {
    const partial = rawQuestionnaire();
    (partial.items as unknown[]).pop();
    assert.equal(normalizeQuestionnaire(partial), null);
    assert.equal(normalizeQuestionnaire({}), null);
    assert.equal(normalizeQuestionnaire(null), null);
    const unknownKind = rawQuestionnaire();
    ((unknownKind.items as Array<Record<string, unknown>>)[0]).kind = "script";
    assert.equal(normalizeQuestionnaire(unknownKind), null);
  });

  it("formata o período no fuso do Portal e devolve null para datas inválidas", () => {
    assert.equal(
      formatSurveyWindow("2026-03-01T03:00:00Z", "2026-03-31T20:59:00Z"),
      "01/03/2026 00:00 a 31/03/2026 17:59",
    );
    assert.equal(formatSurveyWindow("", "x"), null);
  });
});
