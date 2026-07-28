import { describe, expect, it } from "vitest";

import {
  measurePresentationViewportSize,
  presentationSurfaceFromViewMode,
  resolvePresentationFitMode,
} from "./presentationFitPolicy";

describe("resolvePresentationFitMode", () => {
  it("preview e thumbnail sempre contain", () => {
    expect(
      resolvePresentationFitMode({
        surface: "preview",
        designWidth: 1920,
        designHeight: 1080,
        containerWidth: 800,
        containerHeight: 600,
      }),
    ).toBe("contain");
    expect(
      resolvePresentationFitMode({
        surface: "thumbnail",
        designWidth: 1920,
        designHeight: 1080,
        fit: "auto",
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
  });

  it("kiosk mesma orientação → cover (FitScreenAndZoom) em vários tamanhos", () => {
    const cases = [
      { cw: 1280, ch: 720, dw: 1920, dh: 1080 }, // 720p host, 1080p design
      { cw: 1920, ch: 1080, dw: 1920, dh: 1080 },
      { cw: 3840, ch: 2160, dw: 1920, dh: 1080 }, // 4k host
      { cw: 1920, ch: 1200, dw: 1920, dh: 1080 }, // mais alto que 16:9
      { cw: 2560, ch: 1080, dw: 1920, dh: 1080 }, // ultrawide
      { cw: 1080, ch: 1920, dw: 1080, dh: 1920 }, // portrait→portrait
    ];
    for (const c of cases) {
      expect(
        resolvePresentationFitMode({
          surface: "kiosk",
          designWidth: c.dw,
          designHeight: c.dh,
          containerWidth: c.cw,
          containerHeight: c.ch,
        }),
        `${c.cw}x${c.ch} vs ${c.dw}x${c.dh}`,
      ).toBe("cover");
    }
  });

  it("kiosk orientação divergente → contain (não destroi portrait na TV)", () => {
    expect(
      resolvePresentationFitMode({
        surface: "kiosk",
        designWidth: 1080,
        designHeight: 1920,
        containerWidth: 1920,
        containerHeight: 1080,
      }),
    ).toBe("contain");
    expect(
      resolvePresentationFitMode({
        surface: "kiosk",
        designWidth: 1920,
        designHeight: 1080,
        containerWidth: 1080,
        containerHeight: 1920,
      }),
    ).toBe("contain");
  });

  it("kiosk sem medida de container → cover (default wall)", () => {
    expect(
      resolvePresentationFitMode({
        surface: "kiosk",
        designWidth: 1920,
        designHeight: 1080,
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
