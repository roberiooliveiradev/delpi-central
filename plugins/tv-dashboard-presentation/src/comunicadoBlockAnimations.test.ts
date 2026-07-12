import { describe, expect, it } from "vitest";

import {
  assignStaggeredEntranceDelays,
  blockEntranceAnimationClass,
  clearEntranceAnimations,
  entranceAnimationFromPreset,
  entrancePresetValue,
  normalizeBlockAnimations,
  resolveEntranceAnimation,
  serializeBlockAnimations,
  syncEntranceDelaysSameInstant,
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

  it("sequencia atrasos de entrada (4E.4)", () => {
    const blocks = [{ id: "a" }, { id: "b" }, { id: "c" }];
    const map = assignStaggeredEntranceDelays(blocks, { stepMs: 300, preset: "fade" });
    expect(resolveEntranceAnimation(map.get("a"))?.delayMs).toBe(0);
    expect(resolveEntranceAnimation(map.get("b"))?.delayMs).toBe(300);
    expect(resolveEntranceAnimation(map.get("c"))?.delayMs).toBe(600);
  });

  it("sincroniza e limpa animações de entrada", () => {
    const blocks = [
      { id: "a", animations: entranceAnimationFromPreset("fade", { delayMs: 100 }) },
      { id: "b", animations: entranceAnimationFromPreset("fade", { delayMs: 400 }) },
      { id: "c" },
    ];
    const synced = syncEntranceDelaysSameInstant(blocks, 0);
    expect(resolveEntranceAnimation(synced.get("a"))?.delayMs).toBe(0);
    expect(resolveEntranceAnimation(synced.get("b"))?.delayMs).toBe(0);
    expect(synced.get("c")).toBeUndefined();

    const cleared = clearEntranceAnimations(blocks);
    expect(cleared.get("a")).toBeUndefined();
    expect(cleared.get("b")).toBeUndefined();
  });
});
