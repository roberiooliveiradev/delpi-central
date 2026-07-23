import { describe, expect, it } from "vitest";

import { resolveHttpErrorMessage } from "./httpClient";

describe("resolveHttpErrorMessage", () => {
  it("prioriza message do envelope TV", () => {
    expect(resolveHttpErrorMessage({ message: "Playlist não encontrada" }, 404)).toBe(
      "Playlist não encontrada",
    );
  });

  it("traduz detail Unauthorized do JWT para PT-BR", () => {
    expect(resolveHttpErrorMessage({ detail: "Unauthorized" }, 401)).toBe(
      "Não autorizado. Faça login novamente.",
    );
  });

  it("fallback para status HTTP", () => {
    expect(resolveHttpErrorMessage(null, 502)).toBe("Erro HTTP 502");
    expect(resolveHttpErrorMessage(null, 401)).toBe("Não autorizado. Faça login novamente.");
  });
});
