import { describe, expect, it } from "vitest";

import { createBlock, createShapeBlock } from "./comunicadoHelpers";
import {
  isComunicadoVisualBoxBlock,
  resolveVisualBoxChrome,
  resolveVisualBoxContentLayoutStyle,
  resolveVisualBoxProfile,
  visualBoxBlockModifierClasses,
  visualBoxSupportsInlineTextEditing,
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

  it("caixa de texto nasce sem fundo/borda e com cor Automático", () => {
    const text = createBlock("text", "Olá");
    expect(text.style?.color).toBe("auto");
    expect(text.style?.fill).toBe("transparent");
    expect(text.style?.backgroundColor).toBe("transparent");
    expect(text.style?.stroke).toBe("transparent");
    expect(text.style?.strokeWidth).toBe(0);
    expect(text.style?.borderWidth).toBe(0);
    expect(text.style?.borderColor).toBe("transparent");
    expect(resolveVisualBoxChrome(text).fill).toBe("transparent");
    expect(resolveVisualBoxChrome(text).strokeWidth).toBe(0);
  });

  it("forma nasce com fill azul, borda preta e texto Automático", () => {
    const shape = createShapeBlock("rectangle");
    expect(shape.style?.fill).toBe("#089bdb");
    expect(shape.style?.stroke).toBe("#000000");
    expect(shape.style?.color).toBe("auto");
    expect(shape.style?.fontSize).toBe(18);
    const layout = resolveVisualBoxContentLayoutStyle({ ...shape, content: "A" });
    expect(layout.color).toBe("#ffffff");
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
    expect(chrome.stroke).toBe("#000000");
    expect(chrome.strokeWidth).toBe(2);
    expect(chrome.shapeKind).toBe("ellipse");
    expect(visualBoxSupportsShapeFormatting(block)).toBe(true);
    expect(visualBoxBlockModifierClasses(block)).toContain("tdp-comunicado__visual-box--shape");
    expect(visualBoxBlockModifierClasses(block)).toContain(
      "tdp-comunicado__visual-box--primitive-area",
    );
  });

  it("propaga borderRadius no chrome da forma (cantos arredondados)", () => {
    const block = {
      ...createShapeBlock("rectangle"),
      style: { ...createShapeBlock("rectangle").style, borderRadius: 12 },
    };
    expect(resolveVisualBoxChrome(block).borderRadius).toBe(12);
  });

  it("texto usa flex coluna; forma com texto usa overlay absoluto", () => {
    const text = createBlock("heading", "A");
    const shape = { ...createShapeBlock("rectangle"), content: "Dentro" };
    expect(resolveVisualBoxContentLayoutStyle(text).justifyContent).toBe("center");
    expect(resolveVisualBoxContentLayoutStyle(text).position).toBeUndefined();
    const shapeLayout = resolveVisualBoxContentLayoutStyle(shape);
    expect(shapeLayout.position).toBe("absolute");
    expect(shapeLayout.textAlign).toBe("center");
    expect(shapeLayout.justifyContent).toBe("center");
    expect(shapeLayout.pointerEvents).toBe("none");
    const shapeEditorLayout = resolveVisualBoxContentLayoutStyle(shape, { editorInteractive: true });
    expect(shapeEditorLayout.pointerEvents).toBe("auto");
  });

  it("forma respeita textAlign e verticalAlign no layout do texto", () => {
    const base = createShapeBlock("point");
    const shape = {
      ...base,
      content: "A",
      style: { ...base.style, textAlign: "left" as const, verticalAlign: "top" as const },
    };
    const layout = resolveVisualBoxContentLayoutStyle(shape);
    expect(layout.textAlign).toBe("left");
    expect(layout.alignItems).toBe("flex-start");
    expect(layout.justifyContent).toBe("flex-start");
  });

  it("caixas visuais suportam edição inline no palco", () => {
    expect(visualBoxSupportsInlineTextEditing(createBlock("text", "A"))).toBe(true);
    expect(visualBoxSupportsInlineTextEditing(createShapeBlock("rectangle"))).toBe(true);
  });

  it("linhas usam contorno mais espesso e azul das formas por padrão", () => {
    const line = createShapeBlock("line");
    expect(resolveVisualBoxProfile(line).primitive).toBe("line");
    expect(resolveVisualBoxChrome(line).strokeWidth).toBe(4);
    expect(resolveVisualBoxChrome(line).stroke).toBe("#089bdb");
    expect(line.style?.stroke).toBe("#089bdb");
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
