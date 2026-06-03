import { describe, expect, it } from "vitest";

import { isIncompleteChatStreamError } from "./chatStreamConnection";

describe("isIncompleteChatStreamError", () => {
  it("detecta encerramento prematuro do SSE", () => {
    expect(
      isIncompleteChatStreamError(
        new Error(
          "A conexão de streaming foi encerrada antes da resposta ser concluída.",
        ),
      ),
    ).toBe(true);
  });

  it("detecta falha de rede do fetch", () => {
    expect(isIncompleteChatStreamError(new TypeError("Failed to fetch"))).toBe(true);
  });

  it("ignora outros erros", () => {
    expect(isIncompleteChatStreamError(new Error("Sem permissão"))).toBe(false);
  });
});
