import { describe, expect, it } from "vitest";

import {
  COMUNICADO_TEXT_SHADOW_PRESETS,
  applyComunicadoTextEffectsToCss,
  resolveTextShadowPresetId,
} from "./comunicadoTextEffects";

describe("comunicadoTextEffects", () => {
  it("aplica textShadow e stroke no CSS", () => {
    const css: Record<string, unknown> = {};
    applyComunicadoTextEffectsToCss(
      {
        textShadow: "1px 1px 0 #000",
        textStrokeColor: "#fff",
        textStrokeWidth: 1.5,
        textReflection: true,
      },
      css,
    );
    expect(css.textShadow).toBe("1px 1px 0 #000");
    expect(css.WebkitTextStroke).toBe("1.5px #fff");
    expect(String(css.WebkitBoxReflect)).toContain("below");
  });

  it("resolve preset id alinhado à forma", () => {
    expect(resolveTextShadowPresetId(undefined)).toBe("none");
    expect(resolveTextShadowPresetId("0 4px 14px rgba(0, 0, 0, 0.28)")).toBe("soft");
    expect(resolveTextShadowPresetId("0 8px 24px rgba(0, 0, 0, 0.35)")).toBe("medium");
    expect(resolveTextShadowPresetId("0 2px 10px rgba(0, 0, 0, 0.55)")).toBe("hard");
    expect(
      resolveTextShadowPresetId(
        "0 1px 3px rgba(0, 0, 0, 0.2), 0 12px 28px rgba(0, 0, 0, 0.12)",
      ),
    ).toBe("elevated");
  });

  it("legado offset/glow/strong → custom", () => {
    expect(resolveTextShadowPresetId("2px 2px 0 rgba(0,0,0,0.45)")).toBe("custom");
    expect(resolveTextShadowPresetId("0 0 8px rgba(8,155,219,0.85)")).toBe("custom");
    expect(resolveTextShadowPresetId("0 2px 6px rgba(0,0,0,0.55)")).toBe("custom");
    expect(resolveTextShadowPresetId("1px 1px 0 red")).toBe("custom");
  });

  it("expõe presets none/soft/medium/hard/elevated", () => {
    expect(COMUNICADO_TEXT_SHADOW_PRESETS.map((preset) => preset.id)).toEqual([
      "none",
      "soft",
      "medium",
      "hard",
      "elevated",
    ]);
  });
});
