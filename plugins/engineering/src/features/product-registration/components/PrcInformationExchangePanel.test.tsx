import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  informationRoundConflictMessage,
  initialInfoRoleView,
  isRequesterSubject,
} from "../prcInformationExchange";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(join(here, rel), "utf8");

describe("PrcInformationExchangePanel — PRC-REF-019-FIX-01", () => {
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

  it("analista: aceitar, solicitar complemento e retomar só sem bloqueio", () => {
    expect(copy).toMatch(/acceptQuestion: "Aceitar esclarecimento"/);
    expect(copy).toMatch(/requestFollowUp: "Solicitar complemento"/);
    expect(copy).toMatch(/resume: "Retomar atendimento"/);
    expect(src).toMatch(/acceptInformationQuestion\(/);
    expect(src).toMatch(/requestInformationFollowUp\(/);
    expect(src).toMatch(/followUpQuestionIds: \[q\.id\]/);
    expect(src).toMatch(/!hasOpenBlocker/);
    expect(src).toMatch(/allowedActions\.includes\("resume"\)/);
    expect(src).toMatch(/onClick=\{onResume\}/);
    expect(copy).toMatch(/resumeBlocked:/);
    expect(copy).toMatch(/resumeConflict:/);
  });

  it("dual-role: alternância explícita sem usar canReview para ocultar resposta", () => {
    expect(src).toMatch(/dualRole/);
    expect(src).toMatch(/EngineeringSegmentToggle/);
    expect(src).toMatch(/PRC_INFO_COPY\.dualRoleRespond/);
    expect(src).toMatch(/PRC_INFO_COPY\.dualRoleReview/);
    expect(src).toMatch(/isRequesterSubject\(/);
    expect(src).not.toMatch(/isRequesterView && !canReview/);
    expect(src).not.toMatch(/currentSubject === requesterSubject/);
  });

  it("identidade ausente é fail-closed (não presume solicitante)", () => {
    expect(isRequesterSubject(null, "user-1")).toBe(false);
    expect(isRequesterSubject(undefined, "user-1")).toBe(false);
    expect(isRequesterSubject("", "user-1")).toBe(false);
    expect(isRequesterSubject("user-1", "")).toBe(false);
    expect(isRequesterSubject("user-1", "user-1")).toBe(true);
    expect(isRequesterSubject("user-1", "other")).toBe(false);
  });

  it("visão inicial dual-role prioriza solicitante enquanto aguarda resposta", () => {
    expect(
      initialInfoRoleView({
        isRequester: true,
        canRespond: true,
        canReview: true,
        activeRoundStatus: "awaiting_requester",
      }),
    ).toBe("requester");
    expect(
      initialInfoRoleView({
        isRequester: true,
        canRespond: false,
        canReview: true,
        activeRoundStatus: "awaiting_review",
      }),
    ).toBe("analyst");
    expect(
      initialInfoRoleView({
        isRequester: true,
        canRespond: true,
        canReview: false,
        activeRoundStatus: "awaiting_requester",
      }),
    ).toBe("requester");
    expect(
      initialInfoRoleView({
        isRequester: false,
        canRespond: false,
        canReview: true,
        activeRoundStatus: "awaiting_requester",
      }),
    ).toBe("analyst");
  });

  it("409 information_round_open vira mensagem funcional", () => {
    expect(
      informationRoundConflictMessage(
        "Conflito — information_round_open",
        "mensagem funcional",
      ),
    ).toBe("mensagem funcional");
    expect(
      informationRoundConflictMessage("outro erro", "fallback"),
    ).toBe("outro erro");
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
    expect(src).toMatch(/informationRoundConflictMessage/);
    expect(src).toMatch(/informationExchange/);
    expect(src).not.toMatch(/HelpCircle|HelpTooltip/);
    expect(src).not.toMatch(/my-requests|requests-api/);
  });

  it("detalhe liga o painel a informationExchange e allowedActions", () => {
    const page = read("../pages/PrcDetailPage.tsx");
    expect(page).toMatch(/informationExchange=\{detail\.informationExchange\}/);
    expect(page).toMatch(/allowedActions=\{detail\.allowedActions\}/);
    expect(page).toMatch(/getSubjectFromAccessToken\(getAccessToken\?\.\(\)\)/);
    expect(page).toMatch(/PRC_ACTION_SPECS\.resume/);
    expect(page).toMatch(/information_round_open/i);
    expect(page).not.toMatch(
      /canReview=\{detail\.allowedActions\.includes\("resume"\)\}/,
    );
  });

  it("cliente expõe informationExchange e endpoints sob information-rounds", () => {
    expect(api).toMatch(/informationExchange\?:/);
    expect(api).toMatch(/hasOpenBlocker: boolean/);
    expect(api).toMatch(/canRespond: boolean/);
    expect(api).toMatch(/canReview: boolean/);
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
  });
});
