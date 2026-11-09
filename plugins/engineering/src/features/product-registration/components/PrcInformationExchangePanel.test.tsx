import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(join(here, rel), "utf8");

describe("PrcInformationExchangePanel — PRC-REF-019", () => {
  const src = read("PrcInformationExchangePanel.tsx");
  const copy = read("../prcCopy.ts");
  const api = read("../api/productRegistrationApi.ts");

  it("solicitante: rascunho e envio de respostas", () => {
    expect(copy).toMatch(/saveDraft: "Salvar rascunho"/);
    expect(copy).toMatch(/submitAnswers: "Enviar respostas"/);
    expect(src).toMatch(/draftInformationAnswers\(/);
    expect(src).toMatch(/submitInformationAnswers\(/);
    expect(src).toMatch(/validateInfoAnswersForSubmit/);
    expect(src).toMatch(/expectedRoundVersion: round\.version/);
  });

  it("analista: aceitar, solicitar complemento e retomar", () => {
    expect(copy).toMatch(/acceptQuestion: "Aceitar esclarecimento"/);
    expect(copy).toMatch(/requestFollowUp: "Solicitar complemento"/);
    expect(copy).toMatch(/resume: "Retomar atendimento"/);
    expect(src).toMatch(/acceptInformationQuestion\(/);
    expect(src).toMatch(/requestInformationFollowUp\(/);
    expect(src).toMatch(/followUpQuestionIds: \[q\.id\]/);
    expect(src).toMatch(/!hasOpenBlocker/);
    expect(src).toMatch(/allInformationQuestionsAccepted/);
    expect(src).toMatch(/onClick=\{onResume\}/);
  });

  it("carrega rodadas, recolhe histórico e só exibe quando há contexto", () => {
    expect(src).toMatch(/listInformationRounds\(requestId\)/);
    expect(src).toMatch(/<details className="engineering-prc__info-history">/);
    expect(src).toMatch(
      /rounds\.length > 0 \|\| requestStatus === "needs_information"/,
    );
  });

  it("papel é só apresentação: backend decide (409 recarrega, sem bypass)", () => {
    expect(src).toMatch(/err\.status === 409/);
    expect(src).toMatch(/currentSubject === requesterSubject/);
    expect(src).not.toMatch(/HelpCircle|HelpTooltip/);
    expect(src).not.toMatch(/my-requests|requests-api/);
  });

  it("detalhe liga o painel a allowedActions e resume", () => {
    const page = read("../pages/PrcDetailPage.tsx");
    expect(page).toMatch(/canReview=\{detail\.allowedActions\.includes\("resume"\)\}/);
    expect(page).toMatch(/getSubjectFromAccessToken\(getAccessToken\?\.\(\)\)/);
    expect(page).toMatch(/PRC_ACTION_SPECS\.resume/);
  });

  it("cliente expõe os endpoints sob information-rounds com Idempotency-Key", () => {
    for (const fn of [
      "listInformationRounds",
      "getInformationRound",
      "draftInformationAnswers",
      "submitInformationAnswers",
      "acceptInformationQuestion",
      "requestInformationFollowUp",
    ]) {
      expect(api).toMatch(new RegExp(`export async function ${fn}\\(`));
    }
    expect(api).toMatch(/requests\/\$\{requestId\}\/information-rounds`/);
    expect(api).toMatch(/information-rounds\/\$\{roundId\}\/answers`/);
    expect(api).toMatch(/actions\/submit-answers`/);
    expect(api).toMatch(/questions\/\$\{questionId\}\/actions\/accept`/);
    expect(api).toMatch(/actions\/request-follow-up`/);
    expect(api).toMatch(/"Idempotency-Key": idempotencyKey/);
    expect(api).toMatch(/export type PrcRequestInformationBody/);
  });
});
