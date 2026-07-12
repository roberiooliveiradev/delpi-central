import { describe, expect, it } from "vitest";

import { applyTextEffectStyleToCss } from "./textEffectStyle";

describe("textEffectStyle", () => {
  it("ignora stroke sem largura", () => {
    const css: Record<string, unknown> = {};
    applyTextEffectStyleToCss({ textStrokeColor: "#000", textStrokeWidth: 0 }, css);
    expect(css.WebkitTextStroke).toBeUndefined();
  });

  it("aplica reflexo tipográfico", () => {
    const css: Record<string, unknown> = {};
    applyTextEffectStyleToCss({ textReflection: true }, css);
    expect(String(css.WebkitBoxReflect)).toContain("below");
  });
});
