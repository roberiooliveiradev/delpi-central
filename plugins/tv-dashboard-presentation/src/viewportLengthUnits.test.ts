import { describe, expect, it } from "vitest";

import {
  clampDesignPx,
  cssPxToMm,
  formatViewportDimensionFromPx,
  parseViewportDimensionToPx,
  pxFromUnit,
  unitFromPx,
  VIEWPORT_DESIGN_PX_MAX,
  VIEWPORT_DESIGN_PX_MIN,
} from "./viewportLengthUnits";
import {
  isCustomViewportProfile,
  listViewportProfileSelectOptions,
  resolveViewportPixelSize,
  VIEWPORT_CUSTOM_PROFILE,
} from "./viewportPixelSize";

describe("resolveViewportPixelSize", () => {
  it("resolve perfis conhecidos", () => {
    expect(resolveViewportPixelSize("1080p")).toEqual({ width: 1920, height: 1080 });
    expect(resolveViewportPixelSize("720p")).toEqual({ width: 1280, height: 720 });
    expect(resolveViewportPixelSize("4k")).toEqual({ width: 3840, height: 2160 });
    expect(resolveViewportPixelSize("1080p_portrait")).toEqual({ width: 1080, height: 1920 });
    expect(resolveViewportPixelSize("1366x768")).toEqual({ width: 1366, height: 768 });
    expect(resolveViewportPixelSize("2560x1440")).toEqual({ width: 2560, height: 1440 });
  });

  it("custom usa width/height clampados", () => {
    expect(resolveViewportPixelSize("custom", { width: 100, height: 70 })).toEqual({
      width: 100,
      height: 70,
    });
    expect(resolveViewportPixelSize(VIEWPORT_CUSTOM_PROFILE, { width: 10, height: 9000 })).toEqual({
      width: VIEWPORT_DESIGN_PX_MIN,
      height: VIEWPORT_DESIGN_PX_MAX,
    });
  });

  it("custom sem dims cai em 1080p", () => {
    expect(resolveViewportPixelSize("custom")).toEqual({ width: 1920, height: 1080 });
    expect(resolveViewportPixelSize("custom", { width: null, height: null })).toEqual({
      width: 1920,
      height: 1080,
    });
  });

  it("cai em 1080p para perfil ausente ou inválido", () => {
    expect(resolveViewportPixelSize(undefined)).toEqual({ width: 1920, height: 1080 });
    expect(resolveViewportPixelSize("nope")).toEqual({ width: 1920, height: 1080 });
  });

  it("lista select inclui Personalizado", () => {
    const options = listViewportProfileSelectOptions();
    expect(options.some((item) => item.value === "1080p")).toBe(true);
    expect(options.at(-1)).toEqual({ value: "custom", label: "Personalizado…" });
    expect(isCustomViewportProfile("custom")).toBe(true);
  });
});

describe("viewportLengthUnits", () => {
  it("converte CSS 96dpi px↔in↔pt↔cm", () => {
    expect(pxFromUnit(1, "in")).toBe(96);
    expect(pxFromUnit(72, "pt")).toBe(96);
    expect(pxFromUnit(2.54, "cm")).toBeCloseTo(96, 5);
    expect(unitFromPx(96, "in")).toBe(1);
    expect(unitFromPx(96, "pt")).toBe(72);
  });

  it("parse 10 cm → px e 100×70 px", () => {
    expect(parseViewportDimensionToPx(10, "cm")).toBe(clampDesignPx(pxFromUnit(10, "cm")));
    expect(parseViewportDimensionToPx("100", "px")).toBe(100);
    expect(parseViewportDimensionToPx("70", "px")).toBe(70);
    expect(parseViewportDimensionToPx("0", "px")).toBeNull();
  });

  it("format e round-trip px↔cm", () => {
    const px = 1920;
    const cm = unitFromPx(px, "cm");
    expect(parseViewportDimensionToPx(formatViewportDimensionFromPx(px, "cm"), "cm")).toBe(
      clampDesignPx(pxFromUnit(cm, "cm")),
    );
  });

  it("cssPxToMm alinha com 96dpi", () => {
    expect(cssPxToMm(96)).toBeCloseTo(25.4, 5);
  });
});
