import { describe, expect, it } from "vitest";

import { resolveXLabelStep, shouldRotateXLabels } from "./layout";

describe("seriesChart layout", () => {
  it("aumenta o passo de rótulos X quando há muitos pontos", () => {
    const labels = Array.from({ length: 24 }, (_, index) => `2026-${String(index + 1).padStart(2, "0")}`);
    const step = resolveXLabelStep(24, 336, labels);
    expect(step).toBeGreaterThan(1);
  });

  it("rotaciona rótulos X quando a largura estimada excede a área", () => {
    const labels = Array.from({ length: 12 }, (_, index) => `jan/${String(index + 1).padStart(2, "0")}`);
    expect(shouldRotateXLabels(12, 1, 336, labels)).toBe(true);
  });
});
