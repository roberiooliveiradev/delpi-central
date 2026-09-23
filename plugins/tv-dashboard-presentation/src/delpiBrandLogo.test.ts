import { describe, expect, it } from "vitest";

import {
  DELPI_BRAND_LOGO_FRAME,
  isComunicadoBackgroundDark,
  resolveDelpiBrandLogoVariant,
  resolveStageMasterLogo,
} from "./delpiBrandLogo";

describe("delpiBrandLogo", () => {
  it("fundo escuro → onDark; claro → onLight", () => {
    expect(isComunicadoBackgroundDark({ type: "color", value: "#0f172a" })).toBe(true);
    expect(resolveDelpiBrandLogoVariant({ type: "color", value: "#0f172a" })).toBe("onDark");
    expect(isComunicadoBackgroundDark({ type: "color", value: "#ffffff" })).toBe(false);
    expect(resolveDelpiBrandLogoVariant({ type: "color", value: "#ffffff" })).toBe("onLight");
  });

  it("gradiente Delpi escuro → onDark", () => {
    expect(
      isComunicadoBackgroundDark({
        type: "gradient",
        from: "#003866",
        to: "#0d2840",
        angle: 180,
      }),
    ).toBe(true);
  });

  it("sem custom → brand no canto inferior direito com margem segura", () => {
    const logo = resolveStageMasterLogo({
      background: { type: "color", value: "#ffffff" },
    });
    expect(logo.source).toBe("brand");
    expect(logo.variant).toBe("onLight");
    expect(logo.frame).toEqual({ ...DELPI_BRAND_LOGO_FRAME });
    expect(logo.frame.x + logo.frame.w).toBeLessThanOrEqual(97);
    expect(logo.frame.y + logo.frame.h).toBeLessThanOrEqual(97);
    expect(logo.frame.y).toBeGreaterThan(50);
    expect(logo.opacity).toBeLessThan(1);
    expect(logo.url).toBeTruthy();
  });

  it("custom URL vence brand", () => {
    const logo = resolveStageMasterLogo({
      background: { type: "color", value: "#0f172a" },
      customLogo: {
        url: "https://cdn.example/logo.png",
        frame: { x: 5, y: 5, w: 20, h: 12 },
        opacity: 0.8,
      },
    });
    expect(logo.source).toBe("custom");
    expect(logo.url).toBe("https://cdn.example/logo.png");
    expect(logo.frame).toEqual({ x: 5, y: 5, w: 20, h: 12 });
    expect(logo.opacity).toBe(0.8);
  });

  it("sibling: custom sem url cai no brand", () => {
    const logo = resolveStageMasterLogo({
      background: { type: "color", value: "#111111" },
      customLogo: { assetId: "a1" } as { url?: string },
    });
    expect(logo.source).toBe("brand");
    expect(logo.variant).toBe("onDark");
  });
});
