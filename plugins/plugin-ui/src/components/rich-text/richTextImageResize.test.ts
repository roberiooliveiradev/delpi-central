import { describe, expect, it } from "vitest";

import {
  RICH_TEXT_IMAGE_MAX_WIDTH,
  applyRichTextImageWidth,
  clampRichTextImageWidth,
  fitRichTextImageToContainer,
  isRichTextImagePlaceholderSrc,
  resolveRichTextImageNaturalSize,
  resolveRichTextImageResizeHandlePosition,
} from "./richTextImageResize";
import {
  ATTACHMENT_SRC_PLACEHOLDER,
  applyAttachmentImageSources,
  isNonDisplayAttachmentSrc,
  patchLiveAttachmentImageSources,
} from "./richTextMarkdown";

describe("richTextImageResize", () => {
  it("limita largura ao teto BFF e ao mínimo", () => {
    expect(clampRichTextImageWidth(10)).toBe(48);
    expect(clampRichTextImageWidth(9000)).toBe(RICH_TEXT_IMAGE_MAX_WIDTH);
    expect(clampRichTextImageWidth(200, { min: 80, max: 180 })).toBe(180);
  });

  it("não prende o teto à largura do container (ampliar além do editor)", () => {
    expect(clampRichTextImageWidth(900, { containerWidth: 400 })).toBe(900);
  });

  it("aplica width/height HTML preservando proporção (fit → max-width 100%)", () => {
    const img = document.createElement("img");
    Object.defineProperty(img, "naturalWidth", { value: 800 });
    Object.defineProperty(img, "naturalHeight", { value: 400 });
    const size = applyRichTextImageWidth(img, 200);
    expect(size).toEqual({ width: 200, height: 100 });
    expect(img.getAttribute("width")).toBe("200");
    expect(img.getAttribute("height")).toBe("100");
    expect(img.style.maxWidth).toBe("100%");
    expect(img.style.height).toBe("auto");
  });

  it("irmão: enlarge com lockHeight permite ultrapassar a coluna", () => {
    const img = document.createElement("img");
    Object.defineProperty(img, "naturalWidth", { value: 800 });
    Object.defineProperty(img, "naturalHeight", { value: 400 });
    applyRichTextImageWidth(img, 900, { lockHeight: true });
    expect(img.style.maxWidth).toBe("none");
    expect(img.style.height).toBe("450px");
  });

  it("resolve tamanho natural com fallback", () => {
    const img = document.createElement("img");
    expect(resolveRichTextImageNaturalSize(img).width).toBeGreaterThan(0);
  });

  it("positive: cola encaixando na coluna do editor", () => {
    const img = document.createElement("img");
    Object.defineProperty(img, "naturalWidth", { value: 1600 });
    Object.defineProperty(img, "naturalHeight", { value: 900 });
    const size = fitRichTextImageToContainer(img, 400);
    expect(size?.width).toBe(Math.floor(400 * 0.92));
    expect(img.getAttribute("width")).toBe(String(Math.floor(400 * 0.92)));
  });

  it("irmão: imagem menor que a coluna permanece no tamanho natural", () => {
    const img = document.createElement("img");
    Object.defineProperty(img, "naturalWidth", { value: 200 });
    Object.defineProperty(img, "naturalHeight", { value: 100 });
    const size = fitRichTextImageToContainer(img, 400);
    expect(size?.width).toBe(200);
  });

  it("negativo: não sobrescreve width já escolhido", () => {
    const img = document.createElement("img");
    img.setAttribute("width", "220");
    Object.defineProperty(img, "naturalWidth", { value: 1600 });
    Object.defineProperty(img, "naturalHeight", { value: 900 });
    expect(fitRichTextImageToContainer(img, 400)).toBeNull();
    expect(img.getAttribute("width")).toBe("220");
  });

  it("negativo: placeholder 1×1 nunca trava largura minúscula", () => {
    const img = document.createElement("img");
    img.src = ATTACHMENT_SRC_PLACEHOLDER;
    Object.defineProperty(img, "naturalWidth", { value: 1 });
    Object.defineProperty(img, "naturalHeight", { value: 1 });
    expect(isRichTextImagePlaceholderSrc(img.src)).toBe(true);
    expect(fitRichTextImageToContainer(img, 400)).toBeNull();
    expect(img.getAttribute("width")).toBeNull();
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

describe("applyAttachmentImageSources (compose)", () => {
  it("positive: resolve blob quando há seed", () => {
    const html =
      '<p><img src="attachment:pending:abc" data-attachment-pending="abc" alt="x" /></p>';
    const next = applyAttachmentImageSources(html, (id) =>
      id === "abc" ? "blob:preview" : null,
    );
    expect(next).toContain('src="blob:preview"');
  });

  it("irmão: sem resolve, attachment:pending vira placeholder (não URL quebrada)", () => {
    expect(isNonDisplayAttachmentSrc("attachment:pending:abc")).toBe(true);
    const html =
      '<p><img src="attachment:pending:abc" data-attachment-pending="abc" alt="x" width="800" height="600" /></p>';
    const next = applyAttachmentImageSources(html);
    expect(next).toContain(ATTACHMENT_SRC_PLACEHOLDER);
    expect(next).toContain('data-attachment-placeholder="1"');
    expect(next).not.toContain("attachment:pending");
    expect(next).not.toContain('width="800"');
    expect(next).not.toContain('height="600"');
  });

  it("negativo: blob real não é tocado quando resolve falta", () => {
    const html =
      '<p><img src="blob:keep-me" data-attachment-pending="abc" alt="x" /></p>';
    const next = applyAttachmentImageSources(html);
    expect(next).toContain('src="blob:keep-me"');
  });

  it("patch live: blob após placeholder limpa width para refit", () => {
    const root = document.createElement("div");
    root.innerHTML =
      `<p><img src="${ATTACHMENT_SRC_PLACEHOLDER}" data-attachment-pending="p1" data-attachment-placeholder="1" width="48" height="48" /></p>`;
    const img = root.querySelector("img")!;
    img.style.width = "48px";
    const changed = patchLiveAttachmentImageSources(root, (id) =>
      id === "p1" ? "blob:real" : null,
    );
    expect(changed).toBe(true);
    expect(img.getAttribute("src")).toBe("blob:real");
    expect(img.getAttribute("width")).toBeNull();
    expect(img.getAttribute("data-attachment-placeholder")).toBeNull();
    expect(img.style.width).toBe("");
  });

  it("negativo: placeholder com width grande não vira caixa branca", () => {
    const root = document.createElement("div");
    root.innerHTML =
      '<p><img src="attachment:pending:p2" data-attachment-pending="p2" width="900" height="700" /></p>';
    const img = root.querySelector("img")!;
    patchLiveAttachmentImageSources(root, () => null);
    expect(img.getAttribute("src")).toBe(ATTACHMENT_SRC_PLACEHOLDER);
    expect(img.getAttribute("data-attachment-placeholder")).toBe("1");
    expect(img.getAttribute("width")).toBeNull();
    expect(img.getAttribute("height")).toBeNull();
  });
});
