import { describe, expect, it } from "vitest";

import { resolveAnchoredPanelCoords } from "./anchoredPanelCoords";

describe("resolveAnchoredPanelCoords", () => {
  const anchor = { left: 100, top: 80, right: 140, bottom: 120, width: 40, height: 40 };

  it("preferred right usa o lado quando há espaço", () => {
    const next = resolveAnchoredPanelCoords({
      anchor,
      panelWidth: 220,
      panelHeight: 280,
      viewportWidth: 1200,
      viewportHeight: 800,
      preferredPlacement: "right",
      gap: 4,
    });
    expect(next.placement).toBe("right");
    expect(next.left).toBe(144);
    expect(next.top).toBe(80);
  });

  it("preferred right cai para left se a direita não couber", () => {
    const next = resolveAnchoredPanelCoords({
      anchor: { left: 900, top: 80, right: 940, bottom: 120, width: 40, height: 40 },
      panelWidth: 220,
      panelHeight: 200,
      viewportWidth: 1000,
      viewportHeight: 800,
      preferredPlacement: "right",
    });
    expect(next.placement).toBe("left");
    expect(next.left).toBe(900 - 220 - 4);
  });

  it("preferred right cai para bottom se nenhum lado couber", () => {
    const next = resolveAnchoredPanelCoords({
      anchor: { left: 40, top: 80, right: 80, bottom: 120, width: 40, height: 40 },
      panelWidth: 400,
      panelHeight: 120,
      viewportWidth: 420,
      viewportHeight: 800,
      preferredPlacement: "right",
    });
    expect(next.placement).toBe("bottom");
    expect(next.top).toBe(124);
  });

  it("default bottom mantém comportamento clássico", () => {
    const next = resolveAnchoredPanelCoords({
      anchor,
      panelWidth: 200,
      panelHeight: 100,
      viewportWidth: 1200,
      viewportHeight: 800,
    });
    expect(next.placement).toBe("bottom");
    expect(next.top).toBe(124);
    expect(next.left).toBe(100);
  });

  it("allowFlip false mantém bottom mesmo sem espaço (clamp)", () => {
    const next = resolveAnchoredPanelCoords({
      anchor: { left: 40, top: 700, right: 80, bottom: 740, width: 40, height: 40 },
      panelWidth: 200,
      panelHeight: 200,
      viewportWidth: 800,
      viewportHeight: 800,
      preferredPlacement: "bottom",
      allowFlip: false,
      gap: 4,
      margin: 8,
    });
    expect(next.placement).toBe("bottom");
    expect(next.top).toBe(800 - 200 - 8);
  });
});
