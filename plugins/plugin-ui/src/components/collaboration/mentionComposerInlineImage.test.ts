import { describe, expect, it } from "vitest";

import {
  buildInlineImageInserts,
  collectClipboardImageFiles,
  ensureInlineImageCaretAnchors,
  INLINE_IMAGE_ALIGN_ATTR,
  inlineImageBlockHtml,
  isComposerInlineImageFile,
  normalizeInlineImageAlign,
  parseAlignFromImageTitle,
  readInlineImageFigureAlign,
  setInlineImageFigureAlign,
} from "./mentionComposerInlineImage";
import {
  enhanceAttachmentImagesInHtml,
  markdownToRichTextHtml,
  richTextHtmlToMarkdown,
} from "../rich-text/richTextMarkdown";

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

  it("monta html com âncoras caret, data-align left e turndown vira attachment:pending", () => {
    const file = new File(["x"], "foto.webp", { type: "image/webp" });
    const [insert] = buildInlineImageInserts([file]);
    expect(insert).toBeTruthy();
    const html = inlineImageBlockHtml(insert!);
    expect(html).toContain("data-attachment-pending=");
    expect(html).toContain(`attachment:pending:${insert!.pendingId}`);
    expect(html).toContain("data-inline-image-remove");
    expect(html).toContain(`${INLINE_IMAGE_ALIGN_ATTR}="left"`);
    expect(html).toMatch(/<p><br><\/p>/);
    const md = richTextHtmlToMarkdown(html);
    expect(md).toContain(`![foto.webp](attachment:pending:${insert!.pendingId})`);
    expect(md).not.toMatch(/align=/);
  });

  it("normaliza e parseia align do title", () => {
    expect(normalizeInlineImageAlign("CENTER")).toBe("center");
    expect(normalizeInlineImageAlign("nope")).toBe("left");
    expect(parseAlignFromImageTitle('align=right')).toBe("right");
    expect(parseAlignFromImageTitle("align=justify")).toBe("justify");
    expect(parseAlignFromImageTitle("")).toBe("left");
  });

  it("ensureInlineImageCaretAnchors insere p/br antes e depois da figure", () => {
    const root = document.createElement("div");
    root.innerHTML =
      `<figure class="delpi-ui-mention-composer__inline-image" ${INLINE_IMAGE_ALIGN_ATTR}="left">` +
      `<img alt="x" data-attachment-pending="abc" />` +
      `</figure>`;
    ensureInlineImageCaretAnchors(root);
    expect(root.children.length).toBe(3);
    expect(root.children[0]?.tagName).toBe("P");
    expect(root.children[1]?.tagName).toBe("FIGURE");
    expect(root.children[2]?.tagName).toBe("P");
  });

  it("set/read data-align na figure", () => {
    const figure = document.createElement("figure");
    setInlineImageFigureAlign(figure, "center");
    expect(readInlineImageFigureAlign(figure)).toBe("center");
  });

  it("round-trip align no title do markdown attachment", () => {
    const md = '![shot](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee "align=center")';
    const html = markdownToRichTextHtml(md);
    expect(html).toContain(`${INLINE_IMAGE_ALIGN_ATTR}="center"`);
    expect(html).toContain("data-inline-image-remove");
    const back = richTextHtmlToMarkdown(html);
    expect(back).toMatch(/attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee\s+"align=center"/);
  });

  it("enhance restaura align e botão remove para uuid remoto", () => {
    const html = enhanceAttachmentImagesInHtml(
      '<p><img src="attachment:uuid-1" alt="a.png" title="align=right"></p>',
    );
    expect(html).toContain(`${INLINE_IMAGE_ALIGN_ATTR}="right"`);
    expect(html).toContain("data-attachment-id");
    expect(html).toContain("data-inline-image-remove");
    expect(html).toMatch(/<p><br><\/p>/);
  });
});
