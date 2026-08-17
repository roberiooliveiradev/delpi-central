import { describe, expect, it } from "vitest";

import { shouldAcceptMeasuredSize } from "./stableChartSize";

describe("shouldAcceptMeasuredSize", () => {
  it("aceita o primeiro tamanho válido", () => {
    expect(shouldAcceptMeasuredSize(null, { w: 320, h: 240 })).toBe(true);
  });

  it("rejeita host ainda medindo", () => {
    expect(shouldAcceptMeasuredSize(null, { w: 0, h: 240 })).toBe(false);
    expect(shouldAcceptMeasuredSize(null, { w: 320, h: 4 })).toBe(false);
  });

  it("rejeita ruído subpixel / 1px (anti React #185)", () => {
    const prev = { w: 800, h: 280 };
    expect(shouldAcceptMeasuredSize(prev, { w: 800, h: 280 })).toBe(false);
    expect(shouldAcceptMeasuredSize(prev, { w: 800.4, h: 280 })).toBe(false);
    expect(shouldAcceptMeasuredSize(prev, { w: 801, h: 280 }, 2)).toBe(false);
  });

  it("aceita resize real da sidebar (±300px no main-area)", () => {
    const prev = { w: 800, h: 280 };
    expect(shouldAcceptMeasuredSize(prev, { w: 1100, h: 280 })).toBe(true);
    expect(shouldAcceptMeasuredSize(prev, { w: 500, h: 280 })).toBe(true);
  });

  it("não oscila em jitter de scrollbar típico quando epsilon > 15", () => {
    const prev = { w: 1000, h: 280 };
    expect(shouldAcceptMeasuredSize(prev, { w: 985, h: 280 }, 16)).toBe(false);
    expect(shouldAcceptMeasuredSize(prev, { w: 980, h: 280 }, 16)).toBe(true);
  });
});
