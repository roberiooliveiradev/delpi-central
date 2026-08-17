import { describe, expect, it } from "vitest";

import { unwrapApiDelpiEnvelope } from "./api";

describe("unwrapApiDelpiEnvelope", () => {
  it("extrai data em sucesso", () => {
    const data = unwrapApiDelpiEnvelope<{ total_shipments: number }>({
      success: true,
      data: { total_shipments: 43 },
    });
    expect(data.total_shipments).toBe(43);
  });

  it("propaga mensagem de erro do envelope", () => {
    expect(() =>
      unwrapApiDelpiEnvelope({
        success: false,
        message: "Filial é obrigatória.",
        data: null,
      }),
    ).toThrow(/Filial é obrigatória/);
  });
});
