import { describe, expect, it } from "vitest";

import { resolveShortcutTipPosition } from "./shortcutTipPosition";

const tip = { tipWidth: 80, tipHeight: 28 };

describe("resolveShortcutTipPosition", () => {
  it("usa o lado preferido quando há espaço", () => {
    const pos = resolveShortcutTipPosition({
      ...tip,
      preferred: "top",
      viewportWidth: 1200,
      viewportHeight: 800,
      anchor: { top: 200, left: 400, right: 480, bottom: 240, width: 80, height: 40 },
    });
    expect(pos.placement).toBe("top");
    expect(pos.top).toBe(200 - 28 - 8);
    expect(pos.left).toBe(400 + 40 - 40); // centro − metade do tip
  });

  it("inverte para baixo quando não cabe acima (chrome superior)", () => {
    const pos = resolveShortcutTipPosition({
      ...tip,
      preferred: "top",
      viewportWidth: 1200,
      viewportHeight: 800,
      anchor: { top: 4, left: 100, right: 140, bottom: 36, width: 40, height: 32 },
    });
    expect(pos.placement).toBe("bottom");
    expect(pos.top).toBe(36 + 8);
  });

  it("clampa na borda direita da viewport", () => {
    const pos = resolveShortcutTipPosition({
      tipWidth: 100,
      tipHeight: 24,
      preferred: "bottom",
      viewportWidth: 200,
      viewportHeight: 400,
      anchor: { top: 50, left: 160, right: 190, bottom: 80, width: 30, height: 30 },
    });
    expect(pos.left).toBe(200 - 100 - 8);
  });
});
