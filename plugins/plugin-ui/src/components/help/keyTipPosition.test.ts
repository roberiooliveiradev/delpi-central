import { describe, expect, it } from "vitest";

import { resolveKeyTipPosition } from "./keyTipPosition";

const tip = { tipWidth: 80, tipHeight: 28 };

describe("resolveKeyTipPosition", () => {
  it("usa o lado preferido quando há espaço", () => {
    const pos = resolveKeyTipPosition({
      ...tip,
      preferred: "top",
      viewportWidth: 1200,
      viewportHeight: 800,
      anchor: { top: 200, left: 400, right: 480, bottom: 240, width: 80, height: 40 },
    });
    expect(pos.placement).toBe("top");
    expect(pos.top).toBe(200 - 28 - 10);
    expect(pos.left).toBe(400 + 40 - 40);
  });

  it("inverte para baixo quando não cabe acima (chrome superior)", () => {
    const pos = resolveKeyTipPosition({
      ...tip,
      preferred: "top",
      viewportWidth: 1200,
      viewportHeight: 800,
      anchor: { top: 4, left: 100, right: 140, bottom: 36, width: 40, height: 32 },
    });
    expect(pos.placement).toBe("bottom");
    expect(pos.top).toBe(36 + 10);
  });

  it("clampa na borda direita da viewport", () => {
    const pos = resolveKeyTipPosition({
      tipWidth: 100,
      tipHeight: 24,
      preferred: "bottom",
      viewportWidth: 200,
      viewportHeight: 400,
      anchor: { top: 50, left: 160, right: 190, bottom: 80, width: 30, height: 30 },
    });
    expect(pos.left).toBe(200 - 100 - 8);
  });

  it("aplica offsetX antes do clamp", () => {
    const pos = resolveKeyTipPosition({
      tipWidth: 60,
      tipHeight: 24,
      preferred: "bottom",
      offsetX: 20,
      viewportWidth: 1200,
      viewportHeight: 800,
      anchor: { top: 50, left: 100, right: 140, bottom: 80, width: 40, height: 30 },
    });
    expect(pos.left).toBe(100 + 20 - 30 + 20);
  });
});
