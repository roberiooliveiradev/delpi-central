import { describe, expect, it } from "vitest";

import { CANAL_DENUNCIA_PUBLIC_PATH, resolveCanalDenunciaPublicUrl } from "./publicLink";

describe("resolveCanalDenunciaPublicUrl", () => {
  it("monta o path canônico na origem informada", () => {
    expect(resolveCanalDenunciaPublicUrl("https://portal.delpi.com.br")).toBe(
      `https://portal.delpi.com.br${CANAL_DENUNCIA_PUBLIC_PATH}`,
    );
  });
});
