import { describe, expect, it } from "vitest";

import {
  buildInlineImageInserts,
  collectClipboardImageFiles,
  ensureInlineImageCaretAnchors,
  extractClipboardHtmlImageFiles,
  INLINE_IMAGE_ALIGN_ATTR,
  inlineImageInlineHtml,
  isComposerInlineImageFile,
  normalizeInlineImageAlign,
  parseAlignFromImageTitle,
  readInlineImageFigureAlign,
  setInlineImageFigureAlign,
  uniqueClipboardImageFiles,
} from "./mentionComposerInlineImage";
import { richTextHtmlToMarkdown } from "../rich-text/richTextMarkdown";

describe("mentionComposerInlineImage", () => {
  it("classifica imagem por mime", () => {
    expect(isComposerInlineImageFile(new File(["x"], "a.png", { type: "image/png" }))).toBe(
      true,
    );
    expect(
      isComposerInlineImageFile(new File(["x"], "a.pdf", { type: "application/pdf" })),
    ).toBe(false);
  });

  it("coleta imagens do clipboard DataTransfer-like", () => {
    const png = new File(["x"], "shot.png", { type: "image/png" });
    const pdf = new File(["y"], "doc.pdf", { type: "application/pdf" });
    const dt = {
      files: {
        length: 2,
        0: png,
        1: pdf,
        item: (i: number) => (i === 0 ? png : i === 1 ? pdf : null),
        [Symbol.iterator]: function* () {
          yield png;
          yield pdf;
        },
      } as unknown as FileList,
      items: undefined,
    } as unknown as DataTransfer;
    expect(collectClipboardImageFiles(dt).map((f) => f.name)).toEqual(["shot.png"]);
  });

  it("files XOR items: mesma captura com File distintos vira uma só", () => {
    const fromFiles = new File(["same-bytes"], "image.png", {
      type: "image/png",
      lastModified: 1_700_000_000_000,
    });
    const fromItems = new File(["same-bytes"], "image.png", {
      type: "image/png",
      lastModified: 1_700_000_000_000,
    });
    expect(fromFiles).not.toBe(fromItems);
    const dt = {
      files: {
        length: 1,
        0: fromFiles,
        item: () => fromFiles,
        [Symbol.iterator]: function* () {
          yield fromFiles;
        },
      } as unknown as FileList,
      items: [
        {
          kind: "file",
          type: "image/png",
          getAsFile: () => fromItems,
        },
      ],
    } as unknown as DataTransfer;
    expect(uniqueClipboardImageFiles(dt)).toHaveLength(1);
    expect(uniqueClipboardImageFiles(dt)[0]).toBe(fromFiles);
  });

  it("só items quando files não tem imagem", () => {
    const png = new File(["x"], "clip.png", { type: "image/png" });
    const dt = {
      files: {
        length: 0,
        item: () => null,
        [Symbol.iterator]: function* () {},
      } as unknown as FileList,
      items: [
        {
          kind: "file",
          type: "image/png",
          getAsFile: () => png,
        },
      ],
    } as unknown as DataTransfer;
    expect(uniqueClipboardImageFiles(dt).map((f) => f.name)).toEqual(["clip.png"]);
  });

  it("extrai data: do HTML uma vez e ignora http(s)", () => {
    const tiny =
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
    const html =
      `<p><img src="${tiny}" alt="a" /><img src="${tiny}" alt="dup" />` +
      `<img src="https://evil.example/x.png" /></p>`;
    const files = extractClipboardHtmlImageFiles(html);
    expect(files).toHaveLength(1);
    expect(files[0]?.type).toBe("image/png");
  });

  it("monta span inline sem âncoras p/br e turndown vira attachment:pending", () => {
    const file = new File(["x"], "foto.webp", { type: "image/webp" });
    const [insert] = buildInlineImageInserts([file]);
    expect(insert).toBeTruthy();
    const html = inlineImageInlineHtml(insert!);
    expect(html.startsWith("\u200b")).toBe(true);
    expect(html.endsWith("\u200b")).toBe(true);
    expect(html).toContain("<span class=\"delpi-ui-mention-composer__inline-image\"");
    expect(html).not.toContain("<figure");
    expect(html).not.toMatch(/<p><br><\/p>/);
    expect(html).toContain("data-attachment-pending=");
    expect(html).toContain(`attachment:pending:${insert!.pendingId}`);
    expect(html).toContain("data-inline-image-remove");
    const wrapped = `<p>antes ${html} depois</p>`;
    const md = richTextHtmlToMarkdown(wrapped);
    expect(md).toContain(`![foto.webp](attachment:pending:${insert!.pendingId})`);
    expect(md).toMatch(/antes/);
    expect(md).toMatch(/depois/);
  });

  it("normaliza e parseia align do title", () => {
    expect(normalizeInlineImageAlign("CENTER")).toBe("center");
    expect(normalizeInlineImageAlign("nope")).toBe("left");
    expect(parseAlignFromImageTitle("align=right")).toBe("right");
    expect(parseAlignFromImageTitle("align=justify")).toBe("justify");
    expect(parseAlignFromImageTitle("")).toBe("left");
  });

  it("ensureInlineImageCaretAnchors é no-op (modelo Word)", () => {
    const root = document.createElement("div");
    root.innerHTML =
      `<span class="delpi-ui-mention-composer__inline-image">` +
      `<img alt="x" data-attachment-pending="abc" />` +
      `</span>`;
    ensureInlineImageCaretAnchors(root);
    expect(root.children.length).toBe(1);
    expect(root.children[0]?.tagName).toBe("SPAN");
  });

  it("set/read data-align legado na figure", () => {
    const figure = document.createElement("figure");
    setInlineImageFigureAlign(figure, "center");
    expect(readInlineImageFigureAlign(figure)).toBe("center");
    expect(figure.getAttribute(INLINE_IMAGE_ALIGN_ATTR)).toBe("center");
  });
});
