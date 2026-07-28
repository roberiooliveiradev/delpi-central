import { describe, expect, it } from "vitest";

import {
  generateBrandLightning,
  lightningPathStartsNearOrigin,
} from "./brandLightning";

describe("brandLightning", () => {
  it("density low gera menos raios que high", () => {
    const origin = { x: 100, y: 100 };
    const low = generateBrandLightning({
      width: 400,
      height: 400,
      origin,
      density: "low",
    });
    const high = generateBrandLightning({
      width: 400,
      height: 400,
      origin,
      density: "high",
    });
    expect(low.length).toBeLessThanOrEqual(4);
    expect(high.length).toBeGreaterThanOrEqual(5);
    expect(lightningPathStartsNearOrigin(low[0]!, origin)).toBe(true);
  });
});
