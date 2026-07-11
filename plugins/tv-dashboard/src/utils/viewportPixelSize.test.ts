import { describe, expect, it } from "vitest";

import { resolveViewportPixelSize } from "./viewportPixelSize";

describe("resolveViewportPixelSize", () => {
  it("mapeia perfis conhecidos", () => {
    expect(resolveViewportPixelSize("1080p")).toEqual({ width: 1920, height: 1080 });
    expect(resolveViewportPixelSize("720p")).toEqual({ width: 1280, height: 720 });
    expect(resolveViewportPixelSize("4k")).toEqual({ width: 3840, height: 2160 });
    expect(resolveViewportPixelSize("1080p_portrait")).toEqual({ width: 1080, height: 1920 });
  });

  it("fallback 1080p", () => {
    expect(resolveViewportPixelSize(undefined)).toEqual({ width: 1920, height: 1080 });
    expect(resolveViewportPixelSize("nope")).toEqual({ width: 1920, height: 1080 });
  });
});
