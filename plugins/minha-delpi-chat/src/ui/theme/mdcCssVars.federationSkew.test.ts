import { describe, expect, it, vi } from "vitest";

/**
 * Simula remote plugin-ui defasado (export ausente no Index federado).
 * Sem a guarda em resolvePaletteFamilyColors → TypeError em gráficos do chat.
 */
vi.mock("@delpi/plugin-ui/index", () => ({
  resolveColorFamily: undefined,
}));

describe("resolvePaletteFamilyColors federation skew", () => {
  it("retorna [] sem lançar quando resolveColorFamily não é função", async () => {
    const { resolvePaletteFamilyColors, resolveChartSeriesColors } = await import(
      "./mdcCssVars"
    );

    expect(resolvePaletteFamilyColors("brand")).toEqual([]);
    // Ainda cai no fallback saturado — UI de gráfico permanece utilizável.
    expect(resolveChartSeriesColors([], false, "brand")[0]).toBe("#0478b5");
  });
});
