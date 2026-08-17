import { describe, expect, it } from "vitest";

import { designSizeToPdfFormatMm } from "./exportSlidePng";
import { resolvePlaylistDesignSize } from "./exportPlaylistPdf";

describe("designSizeToPdfFormatMm", () => {
  it("converte px → mm na base CSS 96 dpi", () => {
    const inch = designSizeToPdfFormatMm({ width: 96, height: 96 });
    expect(inch[0]).toBeCloseTo(25.4, 5);
    expect(inch[1]).toBeCloseTo(25.4, 5);
    const [w, h] = designSizeToPdfFormatMm({ width: 1920, height: 1080 });
    expect(w).toBeCloseTo((1920 * 25.4) / 96, 5);
    expect(h).toBeCloseTo((1080 * 25.4) / 96, 5);
  });

  it("preserva aspecto retrato e custom 100×70", () => {
    const portrait = designSizeToPdfFormatMm({ width: 1080, height: 1920 });
    expect(portrait[1]).toBeGreaterThan(portrait[0]);
    const custom = designSizeToPdfFormatMm({ width: 100, height: 70 });
    expect(custom[0]).toBeCloseTo((100 * 25.4) / 96, 5);
    expect(custom[1]).toBeCloseTo((70 * 25.4) / 96, 5);
  });
});

describe("resolvePlaylistDesignSize", () => {
  it("usa dims custom da playlist", () => {
    expect(
      resolvePlaylistDesignSize({
        viewportProfile: "custom",
        viewportWidth: 100,
        viewportHeight: 70,
      }),
    ).toEqual({ width: 100, height: 70 });
  });

  it("resolve preset 1080p", () => {
    expect(resolvePlaylistDesignSize({ viewportProfile: "1080p" })).toEqual({
      width: 1920,
      height: 1080,
    });
  });
});
