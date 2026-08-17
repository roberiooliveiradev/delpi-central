import { describe, expect, it } from "vitest";

import {
  applyColorPaintToCss,
  applyCssShapePaints,
  applyFillPaintBackground,
  cssAngleToSvgGradientLine,
  resolveStyleFillCss,
  resolveStyleStrokeCss,
  resolveSvgPaintRef,
} from "./comunicadoFillPaint";

const gradient = {
  kind: "gradient" as const,
  angle: 180,
  stops: [
    { color: "#0f172a", position: 0 },
    { color: "#1e3a5f", position: 100 },
  ],
};

describe("comunicadoFillPaint", () => {
  it("mapeia ângulo CSS 180 para linha SVG de cima para baixo", () => {
    const line = cssAngleToSvgGradientLine(180);
    expect(line.x1).toBeCloseTo(0.5);
    expect(line.y1).toBeCloseTo(0);
    expect(line.x2).toBeCloseTo(0.5);
    expect(line.y2).toBeCloseTo(1);
  });

  it("fillPaint manda no CSS; strokePaint gradient vira url(#id) no SVG", () => {
    expect(resolveStyleFillCss({ fill: "#fff", fillPaint: gradient })).toContain("linear-gradient");
    expect(resolveStyleStrokeCss({ stroke: "#000", strokePaint: gradient })).toBe("#0f172a");
    expect(resolveSvgPaintRef(gradient, "#fff", "g1")).toBe("url(#g1)");
  });

  it("caixa CSS usa duas camadas quando o contorno é gradiente", () => {
    const box: Record<string, unknown> = {};
    applyCssShapePaints(box, {
      fillHex: "#89b4e8",
      strokeHex: "#166534",
      strokeWidth: 4,
      strokePaint: {
        kind: "gradient",
        angle: 135,
        stops: [
          { color: "#166534", position: 0 },
          { color: "#7c3aed", position: 100 },
        ],
      },
    });
    expect(String(box.backgroundImage)).toContain("linear-gradient");
    expect(String(box.backgroundImage)).toContain("#7c3aed");
    expect(box.backgroundClip).toBe("padding-box, border-box");
    expect(box.border).toBe("4px solid transparent");
  });

  it("aplica clip de texto e fundo CSS sem backgroundColor no gradiente", () => {
    const text: Record<string, unknown> = {};
    expect(applyColorPaintToCss(text, gradient)).toBe(true);
    expect(text.backgroundClip).toBe("text");
    expect(text.color).toBe("transparent");

    const box: Record<string, unknown> = {};
    applyFillPaintBackground(box, gradient, "#fff");
    expect(box.backgroundImage).toEqual(expect.stringContaining("linear-gradient"));
    expect(box.backgroundColor).toBe("transparent");
  });
});
