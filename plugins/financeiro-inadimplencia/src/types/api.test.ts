import { describe, expect, it } from "vitest";
import { unwrapApiDelpiEnvelope } from "./api";

describe("unwrapApiDelpiEnvelope", () => {
  it("extrai data em sucesso", () => {
    const data = unwrapApiDelpiEnvelope<{ titulos: number }>({
      success: true,
      data: { titulos: 10 },
    });
    expect(data.titulos).toBe(10);
  });

  it("propaga mensagem de erro HTTP amigável", () => {
    expect(() =>
      unwrapApiDelpiEnvelope({
        success: false,
        message: "O período máximo permitido é de 60 meses.",
        data: null,
      }),
    ).toThrow(/60 meses/);
  });
});
