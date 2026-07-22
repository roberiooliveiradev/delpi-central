import { describe, expect, it } from "vitest";

import { resolveHttpErrorMessage } from "./httpClient";

describe("resolveHttpErrorMessage", () => {
  it("prioriza message do envelope TV", () => {
    expect(resolveHttpErrorMessage({ message: "Playlist não encontrada" }, 404)).toBe(
      "Playlist não encontrada",
    );
  });

  it("usa detail do FastAPI quando não há message", () => {
    expect(resolveHttpErrorMessage({ detail: "Unauthorized" }, 401)).toBe("Unauthorized");
  });

  it("fallback para status HTTP", () => {
    expect(resolveHttpErrorMessage(null, 502)).toBe("Erro HTTP 502");
  });
});
