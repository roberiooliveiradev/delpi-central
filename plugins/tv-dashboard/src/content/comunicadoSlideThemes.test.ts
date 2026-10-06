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

  it("slide com heading/text/shape recebe cores do tema em um único candidato", () => {
    // Cobertura do caso que habilita a corrida de persistência (TV-THEME-PERSISTENCE-RACE-001):
    // blocks: [] não exercitava restyle de blocos.
    const populated: ComunicadoConfig = {
      version: 2,
      background: { type: "color", value: "#ffffff" },
      brandThemeKey: "delpi-light",
      blocks: [
        {
          id: "h1",
          type: "heading",
          content: "Título",
          style: { color: "#111111" },
        },
        {
          id: "t1",
          type: "text",
          content: "Corpo",
          style: { color: "#222222" },
        },
        {
          id: "s1",
          type: "shape",
          shape: "rectangle",
          style: { fill: "#e5e7eb", stroke: "#9ca3af", color: "#333333" },
        },
        { id: "img1", type: "image", style: {} },
      ] as unknown as ComunicadoConfig["blocks"],
    };
    const dark = COMUNICADO_SLIDE_THEMES.find((t) => t.key === "delpi-dark")!;
    const next = applyComunicadoSlideTheme(populated, dark);

    expect(next.background).toEqual(dark.background);
    expect(next.brandThemeKey).toBe("delpi-dark");
    const byId = new Map((next.blocks ?? []).map((b) => [b.id, b]));
    expect(byId.get("h1")?.style?.color).toBe(dark.textColor);
    expect(byId.get("t1")?.style?.color).toBe(dark.textColor);
    expect(byId.get("s1")?.style?.fill).toBe(dark.accent);
    expect(byId.get("s1")?.style?.stroke).toBe(dark.shapeStroke);
    // Blocos fora do vocabulário do tema ficam intocados (mesma referência).
    const beforeImg = (populated.blocks ?? []).find((b) => b.id === "img1");
    expect(byId.get("img1")).toBe(beforeImg);
  });
});
