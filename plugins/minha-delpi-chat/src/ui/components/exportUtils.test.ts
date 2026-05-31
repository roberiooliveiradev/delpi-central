import { describe, expect, it } from "vitest";

import { sanitizeSheetName } from "./exportUtils";

describe("sanitizeSheetName", () => {
  it("remove caracteres inválidos do Excel (ex.: barra no título de estoque)", () => {
    expect(sanitizeSheetName("Estoque por filial/armazém")).toBe(
      "Estoque por filial armazém",
    );
  });

  it("limita a 31 caracteres", () => {
    const long = "A".repeat(40);
    expect(sanitizeSheetName(long).length).toBeLessThanOrEqual(31);
  });

  it("retorna fallback quando vazio", () => {
    expect(sanitizeSheetName("   ///   ")).toBe("Dados");
  });
});
