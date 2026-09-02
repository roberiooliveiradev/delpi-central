import { describe, expect, it } from "vitest";

import { resolveViewportBucket } from "./deviceDisplay";
import { isCompactViewport, isMobileViewport, isShortViewportHeight } from "./viewportLayout";

describe("viewportLayout", () => {
  it("classifica compact até 1100px", () => {
    expect(isCompactViewport(resolveViewportBucket(640))).toBe(true);
    expect(isCompactViewport(resolveViewportBucket(900))).toBe(true);
    expect(isCompactViewport(resolveViewportBucket(1280))).toBe(false);
  });

  it("classifica mobile até 768px", () => {
    expect(isMobileViewport(resolveViewportBucket(640))).toBe(true);
    expect(isMobileViewport(resolveViewportBucket(900))).toBe(false);
  });

  it("detecta viewport baixo para layout operador sem scroll", () => {
    expect(isShortViewportHeight(375)).toBe(true);
    expect(isShortViewportHeight(520)).toBe(true);
    expect(isShortViewportHeight(667)).toBe(true);
    expect(isShortViewportHeight(700)).toBe(true);
    expect(isShortViewportHeight(701)).toBe(false);
  });
});
