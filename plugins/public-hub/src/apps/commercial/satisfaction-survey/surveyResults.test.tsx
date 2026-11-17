/**
 * Desfechos da API → telas do kit (§14.6.3/§14.6.4):
 * sucesso só com `submitted`; terminais sem nome da campanha; período sem hora.
 */
import { describe, expect, it } from "vitest";

import type { PublicSurveyState, SubmitOutcome } from "../api.ts";
import {
  outcomeToSubmitOutcome,
  stateToResultProps,
  toPublicSurveyState,
} from "./surveyResults.ts";
import { formatSurveyDate, formatSurveyPeriod } from "./surveyTexts.ts";

const WINDOW = {
  campaignName: "CAMPANHA-INTERNA-SEGREDO",
  startsAt: "2026-03-02T12:00:00Z",
  endsAt: "2026-03-20T12:00:00Z",
};

describe("outcomeToSubmitOutcome", () => {
  it("submitted → resultado de sucesso com agradecimento e dica de fechamento", () => {
    const outcome = outcomeToSubmitOutcome({ outcome: "submitted" });
    expect(outcome.type).toBe("result");
    if (outcome.type !== "result") return;
    expect(outcome.result.tone).toBe("success");
    expect(outcome.result.title).toBe("Obrigado por participar!");
    expect(outcome.result.message).toBe(
      "Sua avaliação foi registrada. Ela ajuda a Delpi a melhorar produtos, serviços e o relacionamento com sua empresa.",
    );
    expect(outcome.result.hint).toBe("Você já pode fechar esta página.");
  });

  it("rejected e temporary_error viram nova tentativa com a mensagem", () => {
    for (const kind of ["rejected", "temporary_error"] as const) {
      const outcome = outcomeToSubmitOutcome({
        outcome: kind,
        message: "Falha controlada",
      });
      expect(outcome).toEqual({ type: "retry", message: "Falha controlada" });
    }
  });

  it("nova tentativa usa mensagem de fallback quando a API não informa", () => {
    const outcome = outcomeToSubmitOutcome({
      outcome: "temporary_error",
      message: "",
    });
    expect(outcome.type).toBe("retry");
  });

  it("outcomes terminais do POST viram painel com os textos vigentes", () => {
    const cases: Array<[SubmitOutcome, string]> = [
      [
        { outcome: "already_submitted", message: "x" },
        "Resposta já registrada",
      ],
      [{ outcome: "not_open", message: "x" }, "A pesquisa ainda não está aberta"],
      [{ outcome: "closed", message: "x" }, "A pesquisa foi encerrada"],
      [{ outcome: "invalid", message: "x" }, "Link inválido ou indisponível"],
    ];
    for (const [input, title] of cases) {
      const outcome = outcomeToSubmitOutcome(input);
      expect(outcome.type).toBe("result");
      if (outcome.type === "result") expect(outcome.result.title).toBe(title);
    }
  });
});

describe("stateToResultProps", () => {
  function props(status: Exclude<PublicSurveyState["status"], "open">) {
    if (status === "invalid" || status === "temporary_error") {
      return stateToResultProps({ status });
    }
    return stateToResultProps({ status, ...WINDOW });
  }

  it("not_open mostra painel info com o período sem hora", () => {
    const result = props("not_open");
    expect(result.tone).toBe("info");
    expect(result.title).toBe("A pesquisa ainda não está aberta");
    expect(result.hint).toBe(
      "Período da pesquisa: 02/03/2026 a 20/03/2026",
    );
  });

  it("closed mostra painel info com o período sem hora", () => {
    const result = props("closed");
    expect(result.title).toBe("A pesquisa foi encerrada");
    expect(result.hint).toBe("Período da pesquisa: 02/03/2026 a 20/03/2026");
  });

  it("already_submitted e invalid não exibem período", () => {
    expect(props("already_submitted").hint).toBeUndefined();
    expect(props("invalid").hint).toBeUndefined();
    expect(props("invalid").tone).toBe("error");
  });

  it("temporary_error mostra painel de erro sem período", () => {
    const result = props("temporary_error");
    expect(result.tone).toBe("error");
    expect(result.title).toBe("Pesquisa temporariamente indisponível");
    expect(result.hint).toBeUndefined();
  });

  it("nunca expõe o nome interno da campanha", () => {
    for (const status of ["not_open", "closed", "already_submitted"] as const) {
      expect(JSON.stringify(props(status))).not.toContain(
        "CAMPANHA-INTERNA-SEGREDO",
      );
    }
  });
});

describe("toPublicSurveyState", () => {
  it("devolve estados conhecidos como vieram", () => {
    const open: PublicSurveyState = {
      status: "open",
      token: "t",
      companyName: null,
      questionnaire: { version: "v", scaleLabels: {}, items: [] },
      ...WINDOW,
    };
    expect(toPublicSurveyState(open)).toBe(open);
    expect(toPublicSurveyState({ status: "invalid" })).toEqual({
      status: "invalid",
    });
  });

  it("qualquer desvio vira indisponibilidade temporária", () => {
    expect(toPublicSurveyState(null)).toEqual({ status: "temporary_error" });
    expect(toPublicSurveyState("open")).toEqual({ status: "temporary_error" });
    expect(toPublicSurveyState({ status: "estranho" })).toEqual({
      status: "temporary_error",
    });
    expect(toPublicSurveyState({ status: "open" })).toEqual({
      status: "temporary_error",
    });
  });
});

describe("formatadores de data (sem hora, fuso do Portal)", () => {
  it("formata dd/mm/aaaa sem componente de hora", () => {
    expect(formatSurveyDate("2026-03-02T23:59:00-03:00")).toBe("02/03/2026");
    expect(formatSurveyDate("2026-12-31T12:00:00Z")).toBe("31/12/2026");
  });

  it("retorna null para data vazia ou inválida", () => {
    expect(formatSurveyDate("")).toBeNull();
    expect(formatSurveyDate("não-é-data")).toBeNull();
  });

  it("período une as duas pontas; null se faltar alguma", () => {
    expect(
      formatSurveyPeriod("2026-03-02T12:00:00Z", "2026-03-20T12:00:00Z"),
    ).toBe("02/03/2026 a 20/03/2026");
    expect(formatSurveyPeriod("", "2026-03-20T12:00:00Z")).toBeNull();
  });
});
