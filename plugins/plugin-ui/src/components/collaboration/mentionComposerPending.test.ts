import { describe, expect, it } from "vitest";

import {
  isPendingImageAttachment,
  partitionPendingAttachments,
} from "./mentionComposerPending";

describe("mentionComposerPending", () => {
  it("classifica imagem por mime ou extensão", () => {
    expect(
      isPendingImageAttachment({
        fileName: "a.png",
        contentType: "image/png",
      }),
    ).toBe(true);
    expect(
      isPendingImageAttachment({
        fileName: "foto.JPG",
        contentType: "",
      }),
    ).toBe(true);
    expect(
      isPendingImageAttachment({
        fileName: "doc.pdf",
        contentType: "application/pdf",
      }),
    ).toBe(false);
  });

  it("particiona imagens vs documentos", () => {
    const { images, documents } = partitionPendingAttachments([
      { id: "1", fileName: "a.png", contentType: "image/png" },
      { id: "2", fileName: "b.pdf", contentType: "application/pdf" },
      { id: "3", fileName: "c.docx", contentType: null },
    ]);
    expect(images.map((i) => i.id)).toEqual(["1"]);
    expect(documents.map((i) => i.id)).toEqual(["2", "3"]);
  });

  it("usa File.type quando contentType falta", () => {
    const file = new File(["x"], "shot.webp", { type: "image/webp" });
    expect(isPendingImageAttachment({ fileName: "shot.webp", file })).toBe(true);
  });
});
