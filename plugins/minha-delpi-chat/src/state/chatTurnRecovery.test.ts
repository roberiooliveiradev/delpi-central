import { describe, expect, it } from "vitest";

import {
  CHAT_TURN_STALL_DRAWING_TIMEOUT_MS,
  CHAT_TURN_STALL_TIMEOUT_MS,
  isDrawingAnalysisActivityLog,
  resolveStallTimeoutMs,
} from "./chatTurnRecovery";

describe("chatTurnRecovery stall timeouts", () => {
  it("mantém timeout padrão para turnos comuns", () => {
    expect(
      resolveStallTimeoutMs([{ id: "1", message: "Consultando", state: "active" }]),
    ).toBe(CHAT_TURN_STALL_TIMEOUT_MS);
  });

  it("amplia timeout quando o fluxo é análise de desenho", () => {
    expect(
      resolveStallTimeoutMs([
        {
          id: "vision-ocr",
          phase: "document_vision",
          message: "Reconhecendo texto (Tesseract)…",
          state: "active",
        },
      ]),
    ).toBe(CHAT_TURN_STALL_DRAWING_TIMEOUT_MS);
  });

  it("detecta fluxo de desenho por fase drawing_analysis", () => {
    expect(
      isDrawingAnalysisActivityLog([
        {
          id: "drawing-analysis-query_api",
          phase: "drawing_analysis",
          message: "Consultando API DELPI…",
          state: "active",
        },
      ]),
    ).toBe(true);
  });
});
