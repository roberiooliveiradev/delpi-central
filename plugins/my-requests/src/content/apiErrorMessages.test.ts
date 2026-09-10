import { describe, expect, it } from "vitest";

import {
  humanizeApiErrorCode,
  isTechnicalErrorCode,
  MR_API_ERROR_MESSAGES,
} from "./apiErrorMessages";

describe("apiErrorMessages", () => {
  it("humaniza artifact_required com label de campo", () => {
    expect(humanizeApiErrorCode("artifact_required", { field: "invoice_pdf" })).toBe(
      "Anexe o PDF da nota fiscal em «Documentos gerados no atendimento» antes de concluir esta etapa.",
    );
  });

  it("reconhece códigos técnicos snake_case", () => {
    expect(isTechnicalErrorCode("artifact_required")).toBe(true);
    expect(isTechnicalErrorCode("Não foi possível")).toBe(false);
  });

  it("não devolve o próprio código como mensagem", () => {
    for (const [code, message] of Object.entries(MR_API_ERROR_MESSAGES)) {
      expect(message).not.toBe(code);
      expect(isTechnicalErrorCode(message)).toBe(false);
    }
  });
});
