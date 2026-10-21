import { describe, expect, it } from "vitest";

import { sourceRect } from "./imageCrop";

describe("image crop", () => {
  it("keeps the full image inside the source when zoom is 1 and the frame matches", () => {
    const rect = sourceRect({
      imageWidth: 480,
      imageHeight: 320,
      viewportWidth: 480,
      viewportHeight: 320,
      zoom: 1,
      offsetX: 0,
      offsetY: 0,
    });
    expect(rect).toEqual({ x: 0, y: 0, width: 480, height: 320 });
  });

  it("does not read outside the image when the offset is extreme", () => {
    const rect = sourceRect({
      imageWidth: 1000,
      imageHeight: 800,
      viewportWidth: 480,
      viewportHeight: 320,
      zoom: 3,
      offsetX: 4,
      offsetY: -4,
    });
    expect(rect.x).toBeGreaterThanOrEqual(0);
    expect(rect.y).toBeGreaterThanOrEqual(0);
    expect(rect.x + rect.width).toBeLessThanOrEqual(1000);
    expect(rect.y + rect.height).toBeLessThanOrEqual(800);
    expect(rect.width).toBeLessThan(1000);
  });
});
