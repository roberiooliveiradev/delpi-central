import { describe, expect, it } from "vitest";

import { formatTaxId } from "./formatTaxId";

describe("formatTaxId", () => {
  it("formata CNPJ e CPF", () => {
    expect(formatTaxId("12345678000199")).toBe("12.345.678/0001-99");
    expect(formatTaxId("52998224725")).toBe("529.982.247-25");
  });

  it("retorna vazio quando ausente", () => {
    expect(formatTaxId(null)).toBe("");
    expect(formatTaxId("")).toBe("");
  });
});
