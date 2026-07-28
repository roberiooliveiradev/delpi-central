import { describe, expect, it } from "vitest";

import {
  measurePresentationViewportSize,
  presentationSurfaceFromViewMode,
  resolvePresentationFitMode,
} from "./presentationFitPolicy";

describe("resolvePresentationFitMode", () => {
  it("auto → contain em preview, thumbnail e kiosk (Adeus Pendrive / multi-tamanho)", () => {
    const sizes = [
      { cw: 1280, ch: 720, dw: 1920, dh: 1080 },
      { cw: 1920, ch: 1080, dw: 1920, dh: 1080 },
      { cw: 3840, ch: 2160, dw: 1920, dh: 1080 },
      { cw: 1920, ch: 1200, dw: 1920, dh: 1080 },
      { cw: 2560, ch: 1080, dw: 1920, dh: 1080 },
      { cw: 1080, ch: 1920, dw: 1080, dh: 1920 },
      { cw: 1920, ch: 1080, dw: 1080, dh: 1920 }, // orientação cruzada
    ];
    for (const surface of ["preview", "thumbnail", "kiosk"] as const) {
      for (const c of sizes) {
        expect(
          resolvePresentationFitMode({
            surface,
            designWidth: c.dw,
            designHeight: c.dh,
            containerWidth: c.cw,
            containerHeight: c.ch,
          }),
        ).toBe("contain");
      }
    }
  });

  it("kiosk auto sem medida de container → contain (não cover)", () => {
    expect(
      resolvePresentationFitMode({
        surface: "kiosk",
        designWidth: 1920,
        designHeight: 1080,
      }),
    ).toBe("contain");
  });

  it("fit explícito vence a surface", () => {
    expect(
      resolvePresentationFitMode({
        surface: "kiosk",
        designWidth: 1920,
        designHeight: 1080,
        containerWidth: 1920,
        containerHeight: 1080,
        fit: "contain",
      }),
    ).toBe("contain");
    expect(
      resolvePresentationFitMode({
        surface: "preview",
        designWidth: 1920,
        designHeight: 1080,
        fit: "cover",
      }),
    ).toBe("cover");
    expect(
      resolvePresentationFitMode({
        surface: "kiosk",
        designWidth: 1920,
        designHeight: 1080,
        containerWidth: 1920,
        containerHeight: 1200,
        fit: "cover",
      }),
    ).toBe("cover");
  });
});

describe("presentationSurfaceFromViewMode", () => {
  it("public → kiosk; preview → preview", () => {
    expect(presentationSurfaceFromViewMode("public")).toBe("kiosk");
    expect(presentationSurfaceFromViewMode("preview")).toBe("preview");
  });
});

describe("measurePresentationViewportSize", () => {
  it("usa clientWidth/Height quando bbox é zero", () => {
    const node = {
      getBoundingClientRect: () => ({ width: 0, height: 0 }),
      clientWidth: 640,
      clientHeight: 360,
    } as HTMLElement;
    expect(measurePresentationViewportSize(node)).toEqual({
      width: 640,
      height: 360,
    });
  });
});
