import { describe, expect, it } from "vitest";

import {
  computeTourTooltipLayout,
  tourTooltipOverlapsSpotlight,
} from "./chatTourTooltipPosition";

describe("chatTourTooltipLayout", () => {
  const viewport = { width: 1280, height: 800 };

  it("posiciona acima do composer quando o alvo está no rodapé", () => {
    const spotlight = {
      top: 720,
      left: 80,
      width: 1120,
      height: 56,
    };

    const layout = computeTourTooltipLayout(spotlight, viewport.width, viewport.height, {
      estimatedHeight: 200,
    });

    expect(layout.placement).toBe("above");
    expect(layout.top + 200 + 12).toBeLessThanOrEqual(spotlight.top);
    expect(
      tourTooltipOverlapsSpotlight(layout, spotlight, 200),
    ).toBe(false);
  });

  it("posiciona abaixo de cards no topo", () => {
    const spotlight = {
      top: 180,
      left: 200,
      width: 480,
      height: 120,
    };

    const layout = computeTourTooltipLayout(spotlight, viewport.width, viewport.height, {
      estimatedHeight: 200,
    });

    expect(["below", "beside-end", "beside-start"]).toContain(layout.placement);
    expect(layout.top).toBeGreaterThanOrEqual(spotlight.top + spotlight.height + 12);
  });

  it("usa largura quase total em viewport estreita", () => {
    const spotlight = {
      top: 520,
      left: 16,
      width: 343,
      height: 52,
    };

    const layout = computeTourTooltipLayout(spotlight, 375, 667, {
      estimatedHeight: 190,
    });

    expect(layout.width).toBeGreaterThan(300);
    expect(layout.placement).toBe("above");
    expect(layout.top + 190).toBeLessThan(spotlight.top);
  });
});
