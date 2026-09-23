import { describe, expect, it } from "vitest";

import {
  DELPI_BRAND_LOGO_FRAME,
  isComunicadoBackgroundDark,
  resolveDelpiBrandLogoVariant,
  resolveStageMasterLogo,
} from "./delpiBrandLogo";
import { getDelpiBrandMode } from "./delpiBrandTheme";

describe("delpiBrandLogo", () => {
  it("fundo escuro → onDark; claro → onLight", () => {
    expect(isComunicadoBackgroundDark({ type: "color", value: "#0f172a" })).toBe(true);
    expect(resolveDelpiBrandLogoVariant({ type: "color", value: "#0f172a" })).toBe("onDark");
    expect(isComunicadoBackgroundDark({ type: "color", value: "#ffffff" })).toBe(false);
    expect(resolveDelpiBrandLogoVariant({ type: "color", value: "#ffffff" })).toBe("onLight");
  });

  it("gradiente Delpi escuro → onDark", () => {
    const dark = getDelpiBrandMode("dark");
    expect(
      isComunicadoBackgroundDark({
        type: "gradient",
        from: dark.colors.bgFrom,
        to: dark.colors.bgTo,
        angle: 180,
      }),
    ).toBe(true);
  });

  it("tema Delpi claro → brand no canto inferior direito", () => {
    const logo = resolveStageMasterLogo({
      background: { type: "color", value: "#ffffff" },
      brandThemeKey: "delpi-light",
    });
    expect(logo?.source).toBe("brand");
    expect(logo?.variant).toBe("onLight");
    expect(logo?.frame).toEqual({ ...DELPI_BRAND_LOGO_FRAME });
    expect(logo!.frame.x + logo!.frame.w).toBeLessThanOrEqual(97);
    expect(logo!.frame.y + logo!.frame.h).toBeLessThanOrEqual(97);
    expect(logo!.frame.y).toBeGreaterThan(50);
    expect(logo!.opacity).toBeLessThan(1);
    expect(logo!.url).toBeTruthy();
  });

  it("negativo: sem tema Delpi → sem logo automática", () => {
    const logo = resolveStageMasterLogo({
      background: { type: "color", value: "#ffffff" },
    });
    expect(logo).toBeNull();
  });

  it("sibling: tema Meia-noite (não Delpi) → sem logo", () => {
    const logo = resolveStageMasterLogo({
      background: { type: "color", value: "#0f172a" },
      brandThemeKey: "midnight",
    });
    expect(logo).toBeNull();
  });

  it("custom URL vence brand", () => {
    const logo = resolveStageMasterLogo({
      background: { type: "color", value: "#0f172a" },
      brandThemeKey: "delpi-dark",
      customLogo: {
        url: "https://cdn.example/logo.png",
        frame: { x: 5, y: 5, w: 20, h: 12 },
        opacity: 0.8,
      },
    });
    expect(logo?.source).toBe("custom");
    expect(logo?.url).toBe("https://cdn.example/logo.png");
    expect(logo?.frame).toEqual({ x: 5, y: 5, w: 20, h: 12 });
    expect(logo?.opacity).toBe(0.8);
  });

  it("sibling: custom sem url + tema Delpi → brand", () => {
    const logo = resolveStageMasterLogo({
      background: { type: "color", value: "#111111" },
      brandThemeKey: "delpi-dark",
      customLogo: { assetId: "a1" } as { url?: string },
    });
    expect(logo?.source).toBe("brand");
    expect(logo?.variant).toBe("onDark");
  });
});
