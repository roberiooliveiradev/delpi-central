import { describe, expect, it } from "vitest";

import {
  applyRichTextImageWidth,
  clampRichTextImageWidth,
  fitRichTextImageToContainer,
  resolveRichTextImageNaturalSize,
  resolveRichTextImageResizeHandlePosition,
} from "./richTextImageResize";

describe("richTextImageResize", () => {
  it("limita largura ao teto do container e ao mínimo", () => {
    expect(clampRichTextImageWidth(10)).toBe(48);
    expect(clampRichTextImageWidth(900, { containerWidth: 400 })).toBe(400);
    expect(clampRichTextImageWidth(200, { min: 80, max: 180 })).toBe(180);
  });

  it("aplica width/height HTML preservando proporção", () => {
    const img = document.createElement("img");
    Object.defineProperty(img, "naturalWidth", { value: 800 });
    Object.defineProperty(img, "naturalHeight", { value: 400 });
    const size = applyRichTextImageWidth(img, 200);
    expect(size).toEqual({ width: 200, height: 100 });
    expect(img.getAttribute("width")).toBe("200");
    expect(img.getAttribute("height")).toBe("100");
  });

  it("resolve tamanho natural com fallback", () => {
    const img = document.createElement("img");
    expect(resolveRichTextImageNaturalSize(img).width).toBeGreaterThan(0);
  });

  it("encaixa imagem grande sem width no container", () => {
    const img = document.createElement("img");
    Object.defineProperty(img, "naturalWidth", { value: 1600 });
    Object.defineProperty(img, "naturalHeight", { value: 900 });
    const size = fitRichTextImageToContainer(img, 400);
    expect(size?.width).toBeLessThanOrEqual(400);
    expect(img.getAttribute("width")).toBeTruthy();
  });

  it("não sobrescreve width já escolhido", () => {
    const img = document.createElement("img");
    img.setAttribute("width", "220");
    Object.defineProperty(img, "naturalWidth", { value: 1600 });
    Object.defineProperty(img, "naturalHeight", { value: 900 });
    expect(fitRichTextImageToContainer(img, 400)).toBeNull();
    expect(img.getAttribute("width")).toBe("220");
  });

  it("handle SE fica na interseção visível imagem∩editor", () => {
    const root = document.createElement("div");
    const editor = document.createElement("div");
    const img = document.createElement("img");
    document.body.append(root, editor, img);
    root.getBoundingClientRect = () =>
      ({ top: 0, left: 0, right: 500, bottom: 400, width: 500, height: 400 }) as DOMRect;
    editor.getBoundingClientRect = () =>
      ({ top: 40, left: 10, right: 410, bottom: 240, width: 400, height: 200 }) as DOMRect;
    img.getBoundingClientRect = () =>
      ({ top: 50, left: 20, right: 820, bottom: 650, width: 800, height: 600 }) as DOMRect;
    const pos = resolveRichTextImageResizeHandlePosition({ img, root, editor, handleSize: 12 });
    expect(pos.left).toBeCloseTo(410 - 0 - 6, 0);
    expect(pos.top).toBeCloseTo(240 - 0 - 6, 0);
    root.remove();
    editor.remove();
    img.remove();
  });
});
