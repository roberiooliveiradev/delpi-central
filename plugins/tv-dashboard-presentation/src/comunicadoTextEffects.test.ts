import { describe, expect, it } from "vitest";

import {
  applyComunicadoTextEffectsToCss,
  resolveTextShadowPresetId,
} from "./comunicadoTextEffects";

describe("comunicadoTextEffects", () => {
  it("aplica textShadow e stroke no CSS", () => {
    const css: Record<string, unknown> = {};
    applyComunicadoTextEffectsToCss(
      { textShadow: "1px 1px 0 #000", textStrokeColor: "#fff", textStrokeWidth: 1.5 },
      css,
    );
    expect(css.textShadow).toBe("1px 1px 0 #000");
    expect(css.WebkitTextStroke).toBe("1.5px #fff");
  });

  it("resolve preset id", () => {
    expect(resolveTextShadowPresetId(undefined)).toBe("none");
    expect(resolveTextShadowPresetId("0 1px 2px rgba(0,0,0,0.35)")).toBe("soft");
    expect(resolveTextShadowPresetId("1px 1px 0 red")).toBe("custom");
  });
});
