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

  it("horizontalAlign end ancora à direita e faz clamp no viewport", () => {
    const next = resolveAnchoredPanelCoords({
      anchor: { left: 20, top: 200, right: 80, bottom: 240, width: 60, height: 40 },
      panelWidth: 240,
      panelHeight: 40,
      viewportWidth: 400,
      viewportHeight: 800,
      preferredPlacement: "top",
      horizontalAlign: "end",
      gap: 4,
      margin: 8,
    });
    expect(next.placement).toBe("top");
    // preferredLeft = 80 - 240 = -160 → clamp para margin 8
    expect(next.left).toBe(8);
  });
});
