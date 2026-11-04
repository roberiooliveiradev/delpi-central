import { describe, expect, it } from "vitest";

import {
  applyColorPaintToCss,
  applyCssShapePaints,
  applyFillPaintBackground,
  cssAngleToSvgGradientLine,
  resolveContrastFillHex,
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

  it("colorPaint solid explícito pinta o texto e vence style.color divergente", () => {
    const text: Record<string, unknown> = { color: "#ffffff" };
    expect(
      applyColorPaintToCss(text, { kind: "solid", color: "#000000" }),
    ).toBe(true);
    expect(text.color).toBe("#000000");
    expect(text.backgroundClip).toBeUndefined();
  });

  it("colorPaint solid branco explícito não é tratado como ausência", () => {
    const text: Record<string, unknown> = { color: "#000000" };
    expect(
      applyColorPaintToCss(text, { kind: "solid", color: "#ffffff" }),
    ).toBe(true);
    expect(text.color).toBe("#ffffff");
  });

  it("Case B residual: fillPaint/strokePaint solid vencem hex legado divergente", () => {
    expect(
      resolveStyleFillCss({
        fill: "#ffffff",
        fillPaint: { kind: "solid", color: "#000000" },
      }),
    ).toBe("#000000");
    expect(
      resolveStyleStrokeCss({
        stroke: "#00ff00",
        strokePaint: { kind: "solid", color: "#ff0000" },
      }),
    ).toBe("#ff0000");
    const box: Record<string, unknown> = {};
    applyFillPaintBackground(
      box,
      { kind: "solid", color: "#111111" },
      "#ffffff",
    );
    expect(box.backgroundColor).toBe("#111111");
  });

  it("resolveContrastFillHex usa fillPaint residual; gradient → primeiro stop", () => {
    expect(
      resolveContrastFillHex({
        fill: "#ffffff",
        fillPaint: { kind: "solid", color: "#0f172a" },
      }),
    ).toBe("#0f172a");
    expect(resolveContrastFillHex({ fill: "#089bdb" })).toBe("#089bdb");
    expect(
      resolveContrastFillHex({
        fill: "#ffffff",
        fillPaint: gradient,
      }),
    ).toBe("#0f172a");
    expect(resolveContrastFillHex({ fillPaint: { kind: "none" } }, "#ccc")).toBe(
      "transparent",
    );
  });

  it("colorPaint auto/none/ausente não aplica — caller usa style.color", () => {
    const autoCss: Record<string, unknown> = { color: "#ffffff" };
    expect(applyColorPaintToCss(autoCss, { kind: "solid", color: "auto" })).toBe(
      false,
    );
    expect(autoCss.color).toBe("#ffffff");

    const noneCss: Record<string, unknown> = { color: "#089bdb" };
    expect(applyColorPaintToCss(noneCss, { kind: "none" })).toBe(false);
    expect(noneCss.color).toBe("#089bdb");

    const missing: Record<string, unknown> = { color: "#089bdb" };
    expect(applyColorPaintToCss(missing, undefined)).toBe(false);
    expect(missing.color).toBe("#089bdb");
  });
});
