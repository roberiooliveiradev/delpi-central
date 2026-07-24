import { describe, expect, it } from "vitest";

import { resolveContextMenuSubFlyout } from "./resolveContextMenuSubFlyout";

describe("resolveContextMenuSubFlyout", () => {
  const trigger = {
    left: 100,
    top: 200,
    right: 280,
    bottom: 236,
    width: 180,
    height: 36,
  };

  it("abre à direita quando há espaço", () => {
    const next = resolveContextMenuSubFlyout({
      trigger,
      panelWidth: 220,
      panelHeight: 160,
      viewportWidth: 1200,
      viewportHeight: 800,
    });
    expect(next.side).toBe("right");
    expect(next.left).toBe(trigger.right + 2);
    expect(next.top).toBe(trigger.top);
  });

  it("flip à esquerda quando não cabe à direita", () => {
    const next = resolveContextMenuSubFlyout({
      trigger: { ...trigger, left: 900, right: 1080 },
      panelWidth: 220,
      panelHeight: 160,
      viewportWidth: 1100,
      viewportHeight: 800,
    });
    expect(next.side).toBe("left");
    expect(next.left).toBeLessThan(900);
  });

  it("clampa no fundo do viewport quando o flyout ultrapassaria a tela", () => {
    const next = resolveContextMenuSubFlyout({
      trigger: { ...trigger, top: 700, bottom: 736 },
      panelWidth: 220,
      panelHeight: 280,
      viewportWidth: 1200,
      viewportHeight: 800,
      margin: 8,
    });
    expect(next.top + 280).toBeLessThanOrEqual(800 - 8);
    expect(next.top).toBeGreaterThanOrEqual(8);
  });
});
