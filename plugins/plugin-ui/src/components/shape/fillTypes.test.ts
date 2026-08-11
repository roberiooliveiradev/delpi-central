import { describe, expect, it } from "vitest";

import {
  fillToCssBackground,
  normalizeFillAngle,
  normalizeGradientStops,
  solidFromFill,
  stopsFromLegacyFromTo,
} from "./fillTypes";

describe("fillTypes", () => {
  it("completa um stop para o mínimo de dois", () => {
    const stops = normalizeGradientStops([{ color: "#112233", position: 40 }]);
    expect(stops).toHaveLength(2);
    expect(stops[0]?.position).toBe(0);
    expect(stops[1]?.position).toBe(100);
  });

  it("normaliza ângulo para 0–359", () => {
    expect(normalizeFillAngle(360)).toBe(0);
    expect(normalizeFillAngle(-90)).toBe(270);
    expect(normalizeFillAngle(450)).toBe(90);
  });

  it("emite CSS linear com stops ordenados", () => {
    expect(
      fillToCssBackground({
        kind: "gradient",
        angle: 90,
        stops: [
          { color: "#fff", position: 100 },
          { color: "#000", position: 0 },
        ],
      }),
    ).toBe("linear-gradient(90deg, #000 0%, #fff 100%)");
  });

  it("solidFromFill cobre none, sólido e primeiro stop", () => {
    expect(solidFromFill({ kind: "none" })).toBe("transparent");
    expect(solidFromFill({ kind: "solid", color: "#abc" })).toBe("#abc");
    expect(
      solidFromFill({
        kind: "gradient",
        angle: 180,
        stops: stopsFromLegacyFromTo("#111", "#eee"),
      }),
    ).toBe("#111");
  });

  it("aplica opacidade do stop no CSS", () => {
    expect(
      fillToCssBackground({
        kind: "gradient",
        angle: 0,
        stops: [
          { color: "#000000", position: 0, opacity: 0.5 },
          { color: "#ffffff", position: 100 },
        ],
      }),
    ).toContain("rgba(0, 0, 0, 0.5)");
  });
});
