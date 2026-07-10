import { describe, expect, it } from "vitest";

import {
  blockEntranceAnimationClass,
  entranceAnimationFromPreset,
  entrancePresetValue,
  normalizeBlockAnimations,
  resolveEntranceAnimation,
  serializeBlockAnimations,
} from "./comunicadoBlockAnimations";

describe("comunicadoBlockAnimations", () => {
  it("normaliza e serializa animação de entrada", () => {
    const animations = normalizeBlockAnimations([
      { phase: "entrance", kind: "slide-in", direction: "left", delayMs: 200, durationMs: 800 },
    ]);
    expect(animations?.[0]?.kind).toBe("slide-in");
    expect(animations?.[0]?.direction).toBe("left");
    const serialized = serializeBlockAnimations(animations);
    expect(serialized?.[0]).toMatchObject({ phase: "entrance", kind: "slide-in", direction: "left" });
  });

  it("resolve classe CSS por tipo", () => {
    expect(
      blockEntranceAnimationClass([
        { phase: "entrance", kind: "fade" },
      ]),
    ).toBe("tdp-comunicado__block--anim-fade");
    expect(
      blockEntranceAnimationClass([
        { phase: "entrance", kind: "slide-in", direction: "up" },
      ]),
    ).toContain("tdp-comunicado__block--anim-slide-in-up");
  });

  it("converte preset do editor", () => {
    const fade = entranceAnimationFromPreset("fade", { delayMs: 100 });
    expect(resolveEntranceAnimation(fade)?.kind).toBe("fade");
    expect(entrancePresetValue(fade?.[0])).toBe("fade");

    const slide = entranceAnimationFromPreset("slide-in:right");
    expect(resolveEntranceAnimation(slide)?.direction).toBe("right");
    expect(entrancePresetValue(slide?.[0])).toBe("slide-in:right");

    expect(entranceAnimationFromPreset("none")).toBeUndefined();
  });
});
