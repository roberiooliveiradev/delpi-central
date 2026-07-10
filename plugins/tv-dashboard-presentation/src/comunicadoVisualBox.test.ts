import { describe, expect, it } from "vitest";

import { createBlock, createShapeBlock } from "./comunicadoHelpers";
import {
  isComunicadoVisualBoxBlock,
  resolveVisualBoxChrome,
  resolveVisualBoxContentLayoutStyle,
  resolveVisualBoxProfile,
  visualBoxBlockModifierClasses,
  visualBoxSupportsShapeFormatting,
  visualBoxSupportsTextFormatting,
} from "./comunicadoVisualBox";

describe("comunicadoVisualBox", () => {
  it("identifica caixas visuais (texto e forma)", () => {
    const heading = createBlock("heading", "Título");
    const shape = createShapeBlock("rectangle");
    const image = createBlock("image");
    expect(isComunicadoVisualBoxBlock(heading)).toBe(true);
    expect(isComunicadoVisualBoxBlock(shape)).toBe(true);
    expect(isComunicadoVisualBoxBlock(image)).toBe(false);
  });

  it("deriva perfil texto sem chrome gráfico", () => {
    const block = createBlock("text", "Corpo");
    expect(resolveVisualBoxProfile(block)).toEqual({
      mode: "text",
      variant: "text",
      textTag: "p",
      isRichTextBlock: true,
    });
    expect(resolveVisualBoxChrome(block)).toEqual({
      showShapeGraphic: false,
      fill: "transparent",
      stroke: "transparent",
      strokeWidth: 0,
    });
    expect(visualBoxSupportsTextFormatting(block)).toBe(true);
    expect(visualBoxSupportsShapeFormatting(block)).toBe(false);
    expect(visualBoxBlockModifierClasses(block)).toContain("tdp-comunicado__visual-box--text");
  });

  it("deriva perfil forma com preenchimento e contorno", () => {
    const block = createShapeBlock("ellipse");
    const profile = resolveVisualBoxProfile(block);
    expect(profile.mode).toBe("shape");
    expect(profile.variant).toBe("ellipse");
    expect(profile.primitive).toBe("area");
    const chrome = resolveVisualBoxChrome(block);
    expect(chrome.showShapeGraphic).toBe(true);
    expect(chrome.fill).toBe("#089bdb");
    expect(chrome.stroke).toBe("#ffffff");
    expect(chrome.strokeWidth).toBe(2);
    expect(chrome.shapeKind).toBe("ellipse");
    expect(visualBoxSupportsShapeFormatting(block)).toBe(true);
    expect(visualBoxBlockModifierClasses(block)).toContain("tdp-comunicado__visual-box--shape");
    expect(visualBoxBlockModifierClasses(block)).toContain(
      "tdp-comunicado__visual-box--primitive-area",
    );
  });

  it("texto usa flex coluna; forma com texto usa overlay absoluto", () => {
    const text = createBlock("heading", "A");
    const shape = { ...createShapeBlock("rectangle"), content: "Dentro" };
    expect(resolveVisualBoxContentLayoutStyle(text).justifyContent).toBe("center");
    expect(resolveVisualBoxContentLayoutStyle(text).position).toBeUndefined();
    const shapeLayout = resolveVisualBoxContentLayoutStyle(shape);
    expect(shapeLayout.position).toBe("absolute");
    expect(shapeLayout.textAlign).toBe("center");
  });

  it("linhas usam contorno mais espesso por padrão", () => {
    const line = createShapeBlock("line");
    expect(resolveVisualBoxProfile(line).primitive).toBe("line");
    expect(resolveVisualBoxChrome(line).strokeWidth).toBe(4);
    expect(visualBoxBlockModifierClasses(line)).toContain(
      "tdp-comunicado__visual-box--primitive-line",
    );
  });

  it("ponto usa primitivo point, posição sem dimensão", () => {
    const point = createShapeBlock("point");
    expect(resolveVisualBoxProfile(point).primitive).toBe("point");
    expect(resolveVisualBoxChrome(point).strokeWidth).toBe(0);
    expect(point.frame).toEqual({ x: 45, y: 45, w: 0, h: 0 });
    expect(visualBoxBlockModifierClasses(point)).toContain(
      "tdp-comunicado__visual-box--primitive-point",
    );
  });
});
