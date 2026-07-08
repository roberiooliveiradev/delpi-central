import { describe, expect, it } from "vitest";

import { resolveDisplayScores } from "./impactEffortMatrixLayout";

describe("resolveDisplayScores", () => {
  it("desloca ponto 50×50 estratégico para dentro do quadrante superior direito", () => {
    const display = resolveDisplayScores(50, 50, "strategic", 50);
    expect(display.impacto).toBeGreaterThan(50);
    expect(display.esforco).toBeGreaterThan(50);
  });

  it("desloca quick win no limiar para cima e à esquerda", () => {
    const display = resolveDisplayScores(50, 50, "quick_win", 50);
    expect(display.impacto).toBeGreaterThan(50);
    expect(display.esforco).toBeLessThan(50);
  });

  it("mantém coordenadas quando longe do limiar", () => {
    const display = resolveDisplayScores(72, 41, "quick_win", 50);
    expect(display).toEqual({ impacto: 72, esforco: 41 });
  });
});
