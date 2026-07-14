import { describe, expect, it } from "vitest";

import { resolveDataBlockErrorText } from "./resolveDataBlockErrorText";

describe("resolveDataBlockErrorText", () => {
  it("usa error com status da API", () => {
    expect(
      resolveDataBlockErrorText({
        error: "[403] Filial não autorizada.",
        detail: "Filial não autorizada.",
        statusCode: 403,
      }),
    ).toBe("[403] Filial não autorizada.");
  });

  it("junta detail quando error é genérico legado", () => {
    expect(
      resolveDataBlockErrorText({
        error: "Dados indisponíveis no momento.",
        detail: "[503] Falha ao conectar na api-delpi",
      }),
    ).toBe("Dados indisponíveis no momento. [503] Falha ao conectar na api-delpi");
  });

  it("retorna null sem campos", () => {
    expect(resolveDataBlockErrorText({})).toBeNull();
  });
});
