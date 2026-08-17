import { describe, expect, it } from "vitest";

import {
  listViewportProfileSelectOptions,
  parseViewportDimensionToPx,
  resolveViewportPixelSize,
} from "./viewportPixelSize";

describe("resolveViewportPixelSize", () => {
  it("mapeia perfis conhecidos", () => {
    expect(resolveViewportPixelSize("1080p")).toEqual({ width: 1920, height: 1080 });
    expect(resolveViewportPixelSize("720p")).toEqual({ width: 1280, height: 720 });
    expect(resolveViewportPixelSize("4k")).toEqual({ width: 3840, height: 2160 });
    expect(resolveViewportPixelSize("1080p_portrait")).toEqual({ width: 1080, height: 1920 });
  });

  it("custom e fallback 1080p", () => {
    expect(resolveViewportPixelSize("custom", { width: 100, height: 70 })).toEqual({
      width: 100,
      height: 70,
    });
    expect(resolveViewportPixelSize(undefined)).toEqual({ width: 1920, height: 1080 });
    expect(resolveViewportPixelSize("nope")).toEqual({ width: 1920, height: 1080 });
  });

  it("select inclui Personalizado e parse cm", () => {
    expect(listViewportProfileSelectOptions().some((o) => o.value === "custom")).toBe(true);
    expect(parseViewportDimensionToPx(2.54, "cm")).toBe(96);
  });
});
