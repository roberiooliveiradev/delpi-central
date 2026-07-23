import { describe, expect, it } from "vitest";

import { createBlock, createShapeBlock } from "./comunicadoHelpers";
import {
  isComunicadoVisualBoxBlock,
  resolveVisualBoxChrome,
  resolveVisualBoxContentLayoutStyle,
  resolveVisualBoxProfile,
  resolveVisualBoxShapeKind,
  visualBoxBlockModifierClasses,
  visualBoxEnsureRichTextBlock,
  visualBoxSupportsInlineTextEditing,
  visualBoxSupportsShapeFormatting,
  visualBoxSupportsTextFormatting,
  VISUAL_BOX_CONTENT_INSET,
} from "./comunicadoVisualBox";

describe("comunicadoVisualBox", () => {
  it("usa inset tipográfico canônico em px (editor ≡ TV)", () => {
    const heading = createBlock("heading", "Título");
    const shape = { ...createShapeBlock("rounded-rect"), content: "KPI" };
    const headingLayout = resolveVisualBoxContentLayoutStyle(heading);
    const shapeLayout = resolveVisualBoxContentLayoutStyle(shape);
    expect(headingLayout.padding).toBe(VISUAL_BOX_CONTENT_INSET);
    expect(shapeLayout.padding).toBe(VISUAL_BOX_CONTENT_INSET);
    expect(headingLayout.justifyContent).toBe("center");
    expect(shapeLayout.justifyContent).toBe("center");
  });

  it("edição inline mantém o mesmo inset da leitura (paridade de wrap)", () => {
    const heading = createBlock("heading", "PPM interno");
    const reading = resolveVisualBoxContentLayoutStyle(heading);
    const editing = resolveVisualBoxContentLayoutStyle(heading, { editorInteractive: true });
    expect(editing.padding).toBe(VISUAL_BOX_CONTENT_INSET);
    expect(editing.padding).toBe(reading.padding);
    expect(editing.pointerEvents).toBe("auto");
    expect(reading.pointerEvents).toBe("none");
  });

  it("texto preserva fill escolhido (default transparente só na inserção)", () => {
    const heading = createBlock("heading", "Título");
    expect(resolveVisualBoxChrome(heading).fill).toBe("transparent");
    const painted = {
      ...heading,
      style: { ...heading.style, fill: "#089bdb", backgroundColor: "#089bdb" },
    };
    const chrome = resolveVisualBoxChrome(painted);
    expect(chrome.fill).toBe("#089bdb");
    expect(chrome.showShapeGraphic).toBe(true);
  });

  it("identifica caixas visuais (texto e forma)", () => {
    const heading = createBlock("heading", "Título");
    const shape = createShapeBlock("rectangle");
    const image = createBlock("image");
    expect(isComunicadoVisualBoxBlock(heading)).toBe(true);
    expect(isComunicadoVisualBoxBlock(shape)).toBe(true);
    expect(isComunicadoVisualBoxBlock(image)).toBe(false);
  });

  it("texto é forma (retângulo) sem fundo — chrome gráfico ativo", () => {
    const block = createBlock("text", "Corpo");
    expect(resolveVisualBoxProfile(block)).toEqual({
      mode: "text",
      variant: "text",
      shapeKind: "rectangle",
      primitive: "area",
      textTag: "p",
      isRichTextBlock: true,
    });
    expect(resolveVisualBoxShapeKind(block)).toBe("rectangle");
    expect(resolveVisualBoxChrome(block)).toEqual({
      showShapeGraphic: true,
      fill: "transparent",
      stroke: "transparent",
      strokeWidth: 0,
      borderRadius: 0,
      shapeKind: "rectangle",
    });
    expect(visualBoxSupportsTextFormatting(block)).toBe(true);
    expect(visualBoxSupportsShapeFormatting(block)).toBe(true);
    expect(visualBoxBlockModifierClasses(block)).toContain("tdp-comunicado__visual-box--text");
    expect(visualBoxBlockModifierClasses(block)).toContain("tdp-comunicado__visual-box--shape");
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

  it("texto e forma usam overlay absoluto sobre o gráfico", () => {
    const text = createBlock("heading", "A");
    const shape = { ...createShapeBlock("rectangle"), content: "Dentro" };
    expect(resolveVisualBoxContentLayoutStyle(text).justifyContent).toBe("center");
    expect(resolveVisualBoxContentLayoutStyle(text).position).toBe("absolute");
    const shapeLayout = resolveVisualBoxContentLayoutStyle(shape);
    expect(shapeLayout.position).toBe("absolute");
    expect(shapeLayout.inset).toBe(0);
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

  it("caixa de texto aplica justifyContent do verticalAlign no content", () => {
    const block = {
      ...createBlock("text", "Texto"),
      style: { verticalAlign: "middle" as const },
    };
    expect(resolveVisualBoxContentLayoutStyle(block).justifyContent).toBe("center");
    const bottom = {
      ...createBlock("text", "Texto"),
      style: { verticalAlign: "bottom" as const },
    };
    expect(resolveVisualBoxContentLayoutStyle(bottom).justifyContent).toBe("flex-end");
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

  it("garante contentRuns na forma sem converter o tipo", () => {
    const shape = { ...createShapeBlock("rounded-rect"), content: "Olá" };
    const rich = visualBoxEnsureRichTextBlock(shape);
    expect(rich.type).toBe("shape");
    expect(rich.shape).toBe("rounded-rect");
    expect(rich.content).toBe("Olá");
    expect(rich.contentRuns).toEqual([{ text: "Olá" }]);
    expect(visualBoxSupportsInlineTextEditing(shape)).toBe(true);
  });

  it("texto com shape explícito altera o chrome", () => {
    const block = { ...createBlock("text", "X"), shape: "ellipse" as const };
    expect(resolveVisualBoxShapeKind(block)).toBe("ellipse");
    expect(resolveVisualBoxChrome(block).shapeKind).toBe("ellipse");
  });
});
