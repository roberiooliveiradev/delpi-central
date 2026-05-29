import { describe, expect, it } from "vitest";

import {
  advanceRevealIndex,
  computeRevealStep,
} from "./naturalTextReveal";

describe("naturalTextReveal", () => {
  it("acelera em textos longos e desacelera no final", () => {
    expect(computeRevealStep(0, 2000, 3)).toBeGreaterThan(6);
    expect(computeRevealStep(1990, 2000, 3)).toBeLessThanOrEqual(3);
  });

  it("prefere avançar até o fim da palavra quando possível", () => {
    const text = "Consulta concluida com sucesso";
    const next = advanceRevealIndex(text, 0, 8);

    expect(text.slice(0, next)).toBe("Consulta ");
  });
});
