import { describe, expect, it } from "vitest";

import { applyComunicadoSlideTheme, COMUNICADO_SLIDE_THEMES } from "./comunicadoSlideThemes";
import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

describe("comunicadoSlideThemes Delpi", () => {
  const base: ComunicadoConfig = {
    version: 2,
    background: { type: "color", value: "#ffffff" },
    blocks: [],
  };

  it("Delpi escuro/claro ligam brandThemeKey", () => {
    const dark = COMUNICADO_SLIDE_THEMES.find((t) => t.key === "delpi-dark");
    const light = COMUNICADO_SLIDE_THEMES.find((t) => t.key === "delpi-light");
    expect(dark?.label).toMatch(/escuro/i);
    expect(light?.label).toMatch(/claro/i);
    expect(applyComunicadoSlideTheme(base, dark!).brandThemeKey).toBe("delpi-dark");
    expect(applyComunicadoSlideTheme(base, light!).brandThemeKey).toBe("delpi-light");
  });

  it("tema não-Delpi remove brandThemeKey", () => {
    const withBrand = { ...base, brandThemeKey: "delpi-dark" };
    const midnight = COMUNICADO_SLIDE_THEMES.find((t) => t.key === "midnight")!;
    expect(applyComunicadoSlideTheme(withBrand, midnight).brandThemeKey).toBeUndefined();
  });
});
