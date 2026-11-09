import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  informationRoundConflictMessage,
  isRequesterSubject,
  resolveInfoPresentation,
} from "../prcInformationExchange";

const here = dirname(fileURLToPath(import.meta.url));
const read = (rel: string) => readFileSync(join(here, rel), "utf8");

describe("PrcInformationExchangePanel — PRC-REF-019-FIX-02", () => {
  const src = read("PrcInformationExchangePanel.tsx");
  const copy = read("../prcCopy.ts");
  const api = read("../api/productRegistrationApi.ts");
  const page = read("../pages/PrcDetailPage.tsx");

  it("não usa SegmentToggle nem estado de papel manual", () => {
    expect(src).not.toMatch(/EngineeringSegmentToggle/);
    expect(src).not.toMatch(/dualRole|roleView|InfoRoleView|initialInfoRoleView/);
    expect(src).not.toMatch(/Responder como solicitante|Analisar como Engenharia/);
    expect(copy).not.toMatch(/dualRoleRespond|dualRoleReview|dualRoleHint/);
  });

  it("fluxo contínuo: formulário / análise / resolvido por estado", () => {
    expect(src).toMatch(/resolveInfoPresentation/);
    expect(src).toMatch(/awaiting_requester_form/);
    expect(src).toMatch(/awaiting_review_analyst/);
    expect(src).toMatch(/resolved_ready/);
    expect(src).toMatch(/RequesterAnswerForm/);
    expect(src).toMatch(/AnalystReview/);
  });

  it("solicitante: rascunho e envio; analista: aceitar e complemento", () => {
    expect(src).toMatch(/draftInformationAnswers\(/);
    expect(src).toMatch(/submitInformationAnswers\(/);
    expect(src).toMatch(/acceptInformationQuestion\(/);
    expect(src).toMatch(/requestInformationFollowUp\(/);
    expect(copy).toMatch(/saveDraft: "Salvar rascunho"/);
    expect(copy).toMatch(/submitAnswers: "Enviar respostas"/);
  });

  it("retomada não é duplicada no painel — cabeçalho é a ação principal", () => {
    expect(src).not.toMatch(/onResume/);
    expect(src).not.toMatch(/onClick=\{onResume\}/);
    expect(copy).toMatch(/resumeReadyHint:/);
    expect(page).toMatch(/action !== "resume" && action !== "start"/);
    expect(page).toMatch(/PRC_ACTION_SPECS\.resume|primaryAction/);
  });

  it("identidade ausente é fail-closed", () => {
    expect(isRequesterSubject(null, "user-1")).toBe(false);
    expect(isRequesterSubject("", "user-1")).toBe(false);
    expect(isRequesterSubject("user-1", "user-1")).toBe(true);
  });

  it("resolveInfoPresentation: dual-role vê formulário e depois análise", () => {
    expect(
      resolveInfoPresentation({
        loadState: "ok",
        hasRounds: true,
        activeStatus: "awaiting_requester",
        canRespond: true,
        canReview: true,
        canResume: false,
      }),
    ).toBe("awaiting_requester_form");
    expect(
      resolveInfoPresentation({
        loadState: "ok",
        hasRounds: true,
        activeStatus: "awaiting_requester",
        canRespond: false,
        canReview: true,
        canResume: false,
      }),
    ).toBe("awaiting_requester_watch");
    expect(
      resolveInfoPresentation({
        loadState: "ok",
        hasRounds: true,
        activeStatus: "awaiting_review",
        canRespond: false,
        canReview: true,
        canResume: false,
      }),
    ).toBe("awaiting_review_analyst");
    expect(
      resolveInfoPresentation({
        loadState: "ok",
        hasRounds: true,
        activeStatus: "awaiting_review",
        canRespond: true,
        canReview: false,
        canResume: false,
      }),
    ).toBe("awaiting_review_watch");
    expect(
      resolveInfoPresentation({
        loadState: "ok",
        hasRounds: true,
        activeStatus: null,
        canRespond: false,
        canReview: true,
        canResume: true,
      }),
    ).toBe("resolved_ready");
  });

  it("409 information_round_open vira mensagem funcional", () => {
    expect(
      informationRoundConflictMessage(
        "Conflito — information_round_open",
        "mensagem funcional",
      ),
    ).toBe("mensagem funcional");
  });

  it("detalhe liga informationExchange e filtra resume da ActionBar", () => {
    expect(page).toMatch(/informationExchange=\{detail\.informationExchange\}/);
    expect(page).toMatch(/allowedActions=\{detail\.allowedActions\}/);
    expect(page).not.toMatch(/onResume=/);
    expect(page).not.toMatch(
      /canReview=\{detail\.allowedActions\.includes\("resume"\)\}/,
    );
  });

  it("cliente expõe informationExchange e endpoints de rodadas", () => {
    expect(api).toMatch(/informationExchange\?:/);
    expect(api).toMatch(/canRespond: boolean/);
    expect(api).toMatch(/listInformationRounds/);
    expect(api).toMatch(/submitInformationAnswers/);
  });
});
