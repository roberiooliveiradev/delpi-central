import { describe, expect, it } from "vitest";

import {
  clipboardLooksLikeImagePaste,
  collectPasteImageFiles,
  extractClipboardHtmlImageFiles,
  shouldTryAsyncClipboardImageRead,
  uniqueClipboardImageFiles,
} from "./richTextClipboardImages";

function asDataTransfer(partial: {
  files?: File[];
  items?: Array<{ kind: string; type: string; getAsFile: () => File | null }>;
  types?: string[];
  html?: string;
  text?: string;
}): DataTransfer {
  const files = partial.files ?? [];
  const fileList = {
    length: files.length,
    item: (i: number) => files[i] ?? null,
    [Symbol.iterator]: function* () {
      yield* files;
    },
    ...Object.fromEntries(files.map((file, index) => [index, file])),
  } as unknown as FileList;
  return {
    files: fileList,
    items: (partial.items ?? []) as unknown as DataTransferItemList,
    types: partial.types ?? [],
    getData: (type: string) => {
      if (type === "text/html") return partial.html ?? "";
      if (type === "text/plain") return partial.text ?? "";
      return "";
    },
  } as unknown as DataTransfer;
}

describe("richTextClipboardImages", () => {
  it("files XOR items: uma captura", () => {
    const fromFiles = new File(["same"], "image.png", {
      type: "image/png",
      lastModified: 1,
    });
    const fromItems = new File(["same"], "image.png", {
      type: "image/png",
      lastModified: 1,
    });
    const dt = asDataTransfer({
      files: [fromFiles],
      items: [{ kind: "file", type: "image/png", getAsFile: () => fromItems }],
    });
    expect(uniqueClipboardImageFiles(dt)).toHaveLength(1);
    expect(uniqueClipboardImageFiles(dt)[0]).toBe(fromFiles);
  });

  it("coleta data: do HTML quando não há File", () => {
    const tiny =
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";
    const files = extractClipboardHtmlImageFiles(`<p><img src="${tiny}" /></p>`);
    expect(files).toHaveLength(1);
    expect(collectPasteImageFiles(asDataTransfer({ html: `<img src="${tiny}" />` }))).toHaveLength(
      1,
    );
  });

  it("Snipping Tool vazio: async hint sem prosa", () => {
    const dt = asDataTransfer({ types: ["Files"], files: [], text: "", html: "" });
    expect(clipboardLooksLikeImagePaste(dt)).toBe(true);
    expect(shouldTryAsyncClipboardImageRead(dt)).toBe(true);
  });

  it("negativo: HTML com prosa não rouba paste para async", () => {
    const dt = asDataTransfer({
      types: ["text/html", "text/plain"],
      html: "<p>olá <img src=\"file:///x.png\" /></p>",
      text: "olá",
    });
    expect(shouldTryAsyncClipboardImageRead(dt)).toBe(false);
  });
});
