import { describe, expect, it } from "vitest";

import { friendlyNoticeMessage } from "../app/MyRequestsFloatingNoticeProvider";

describe("friendlyNoticeMessage", () => {
  it("extrai message de envelope JSON cru", () => {
    const raw =
      '{"success":false,"message":"Transição não permitida para o status atual.","data":{"code":"invalid_transition"}}';
    expect(friendlyNoticeMessage(raw, "fallback")).toBe(
      "Transição não permitida para o status atual.",
    );
  });

  it("humaniza código técnico puro", () => {
    expect(friendlyNoticeMessage("artifact_required", "fallback")).toMatch(
      /Documentos gerados/,
    );
  });

  it("humaniza message=código com field no data", () => {
    const raw = JSON.stringify({
      success: false,
      message: "artifact_required",
      data: { code: "artifact_required", field: "invoice_pdf" },
    });
    expect(friendlyNoticeMessage(raw, "fallback")).toBe(
      "Anexe o PDF da nota fiscal em «Documentos gerados no atendimento» antes de concluir esta etapa.",
    );
  });

  it("mantém texto amigável simples", () => {
    expect(friendlyNoticeMessage("Falha ao carregar", "fallback")).toBe(
      "Falha ao carregar",
    );
  });
});
