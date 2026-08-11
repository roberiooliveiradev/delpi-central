import { describe, expect, it } from "vitest";

import {
  measurePresentationViewportSize,
  presentationStageEntranceClass,
  presentationSurfaceFromViewMode,
  resolvePresentationFitMode,
  resolvePresentationScaleMethod,
} from "./presentationFitPolicy";

describe("resolvePresentationFitMode", () => {
  it("auto → contain em preview, thumbnail e kiosk", () => {
    for (const surface of ["preview", "thumbnail", "kiosk"] as const) {
      expect(
        resolvePresentationFitMode({
          surface,
          designWidth: 1920,
          designHeight: 1080,
          containerWidth: 1920,
          containerHeight: 1200,
        }),
      ).toBe("contain");
    }
  });

  it("fit explícito vence a surface", () => {
    expect(
      resolvePresentationFitMode({
        surface: "kiosk",
        designWidth: 1920,
        designHeight: 1080,
        fit: "cover",
      }),
    ).toBe("cover");
  });
});

describe("resolvePresentationScaleMethod", () => {
  it("kiosk usa zoom para Adeus Pendrive (scrollWidth = visual)", () => {
    expect(resolvePresentationScaleMethod("kiosk")).toBe("zoom");
  });

  it("preview/thumbnail usam transform", () => {
    expect(resolvePresentationScaleMethod("preview")).toBe("transform");
    expect(resolvePresentationScaleMethod("thumbnail")).toBe("transform");
  });
});

describe("presentationSurfaceFromViewMode", () => {
  it("public → kiosk; preview → preview", () => {
    expect(presentationSurfaceFromViewMode("public")).toBe("kiosk");
    expect(presentationSurfaceFromViewMode("preview")).toBe("preview");
  });
});

describe("presentationStageEntranceClass", () => {
  it("liga entradas só em preview e kiosk", () => {
    expect(presentationStageEntranceClass("preview")).toBe("tdp-stage--animate-entrances");
    expect(presentationStageEntranceClass("kiosk")).toBe("tdp-stage--animate-entrances");
    expect(presentationStageEntranceClass("thumbnail")).toBeNull();
    expect(presentationStageEntranceClass("editor")).toBeNull();
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
