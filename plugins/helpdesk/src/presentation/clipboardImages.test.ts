import { describe, expect, it } from "vitest";

import {
  clipboardLooksLikeImagePaste,
  collectPasteImageFiles,
  extractClipboardHtmlImageFiles,
} from "./clipboardImages";

function fileListOf(...files: File[]): FileList {
  return {
    length: files.length,
    item: (i: number) => files[i] ?? null,
    [Symbol.iterator]: function* () {
      yield* files;
    },
    ...Object.fromEntries(files.map((file, index) => [index, file])),
  } as unknown as FileList;
}

describe("clipboardImages", () => {
  it("coleta png do files e ignora pdf", () => {
    const png = new File(["x"], "shot.png", { type: "image/png" });
    const pdf = new File(["y"], "doc.pdf", { type: "application/pdf" });
    const dt = { files: fileListOf(png, pdf), items: undefined, getData: () => "" } as unknown as DataTransfer;
    expect(collectPasteImageFiles(dt).map((f) => f.name)).toEqual(["shot.png"]);
  });

  it("aceita File sem mime quando o item declara image/png (Snipping Tool)", () => {
    const raw = new File(["bytes"], "image.png", { type: "" });
    const dt = {
      files: fileListOf(),
      items: [
        {
          kind: "file",
          type: "image/png",
          getAsFile: () => raw,
        },
      ],
      getData: () => "",
    } as unknown as DataTransfer;
    const files = collectPasteImageFiles(dt);
    expect(files).toHaveLength(1);
    expect(files[0]?.type).toBe("image/png");
    expect(files[0]?.name).toBe("image.png");
  });

  it("extrai data: do HTML quando não há File no DataTransfer", () => {
    const tiny =
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
    const html = `<!--StartFragment--><img src="${tiny}" alt="print" /><!--EndFragment-->`;
    const dt = {
      files: fileListOf(),
      items: [],
      getData: (type: string) => (type === "text/html" ? html : ""),
    } as unknown as DataTransfer;
    const files = collectPasteImageFiles(dt);
    expect(files).toHaveLength(1);
    expect(files[0]?.type).toBe("image/png");
    expect(extractClipboardHtmlImageFiles(html)).toHaveLength(1);
  });

  it("detecta pista de imagem sem File (nega texto puro)", () => {
    const withImg = {
      types: ["text/html"],
      items: [],
      files: fileListOf(),
      getData: () => "<img src=\"file:///tmp/x.png\" />",
    } as unknown as DataTransfer;
    expect(clipboardLooksLikeImagePaste(withImg)).toBe(true);
    const plain = {
      types: ["text/plain"],
      items: [],
      files: fileListOf(),
      getData: () => "olá",
    } as unknown as DataTransfer;
    expect(clipboardLooksLikeImagePaste(plain)).toBe(false);
  });

  it("negativo: texto sem imagem não vira File", () => {
    const dt = {
      files: fileListOf(new File(["t"], "a.txt", { type: "text/plain" })),
      items: [],
      getData: () => "",
    } as unknown as DataTransfer;
    expect(collectPasteImageFiles(dt)).toEqual([]);
  });
});
