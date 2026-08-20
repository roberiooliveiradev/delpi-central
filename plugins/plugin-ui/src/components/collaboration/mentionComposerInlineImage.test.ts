import { describe, expect, it } from "vitest";

import {
  buildInlineImageInserts,
  collectClipboardImageFiles,
  inlineImageBlockHtml,
  isComposerInlineImageFile,
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

  it("monta html com data-attachment-pending e turndown vira attachment:pending", () => {
    const file = new File(["x"], "foto.webp", { type: "image/webp" });
    const [insert] = buildInlineImageInserts([file]);
    expect(insert).toBeTruthy();
    const html = inlineImageBlockHtml(insert!);
    expect(html).toContain("data-attachment-pending=");
    expect(html).toContain(`attachment:pending:${insert!.pendingId}`);
    expect(html).toContain("data-inline-image-remove");
    expect(html).not.toMatch(/<p><\/p>/);
    const md = richTextHtmlToMarkdown(html);
    expect(md).toContain(`![foto.webp](attachment:pending:${insert!.pendingId})`);
  });
});
