import { describe, expect, it } from "vitest";

import { formatPercentDisplay } from "./formatPercentDisplay";

describe("formatPercentDisplay", () => {
  it("limita a no máximo 2 casas decimais em pt-BR", () => {
    expect(formatPercentDisplay("-28.654321")).toBe("-28,65%");
    expect(formatPercentDisplay("12.345")).toBe("12,35%");
    expect(formatPercentDisplay("100")).toBe("100%");
    expect(formatPercentDisplay(0)).toBe("0%");
  });

  it("trata vazio e inválido", () => {
    expect(formatPercentDisplay(null)).toBe("—");
    expect(formatPercentDisplay("")).toBe("—");
    expect(formatPercentDisplay("abc")).toBe("—");
  });
});
