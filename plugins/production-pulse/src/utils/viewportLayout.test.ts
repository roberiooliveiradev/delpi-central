import { describe, expect, it } from "vitest";

import { resolveViewportBucket } from "./deviceDisplay";
import { isCompactViewport, isMobileViewport } from "./viewportLayout";

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
});
