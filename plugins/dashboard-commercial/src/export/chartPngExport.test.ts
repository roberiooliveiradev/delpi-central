import { describe, expect, it } from "vitest";

import { parseViewBoxSize } from "./chartPngExport";

function mockSvg(viewBox: string | null): SVGSVGElement {
  return {
    getAttribute: (name: string) => (name === "viewBox" ? viewBox : null),
  } as SVGSVGElement;
}

describe("chartPngExport", () => {
  it("interpreta viewBox do Recharts", () => {
    expect(parseViewBoxSize(mockSvg("0 0 912 320"))).toEqual({
      width: 912,
      height: 320,
    });
  });

  it("rejeita viewBox inválido", () => {
    expect(parseViewBoxSize(mockSvg(null))).toBeNull();
    expect(parseViewBoxSize(mockSvg("0 0 0 0"))).toBeNull();
    expect(parseViewBoxSize(mockSvg("invalid"))).toBeNull();
  });
});
