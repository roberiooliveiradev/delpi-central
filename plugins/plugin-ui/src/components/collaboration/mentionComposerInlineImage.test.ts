import { describe, expect, it } from "vitest";

import {
  buildInlineImageInserts,
  clipboardHtmlHasProse,
  collectClipboardImageFiles,
  ensureInlineImageCaretAnchors,
  extractClipboardHtmlImageFiles,
  INLINE_IMAGE_ALIGN_ATTR,
  inlineImageInlineHtml,
  insertComposerInlineImageAtCaret,
  isComposerInlineImageFile,
  materializeClipboardHtmlInlineImages,
  normalizeInlineImageAlign,
  parseAlignFromImageTitle,
  readInlineImageFigureAlign,
  setInlineImageFigureAlign,
  stripImagesFromClipboardHtml,
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

  it("detecta prosa no HTML misto Word e ignora HTML só de screenshot", () => {
    expect(
      clipboardHtmlHasProse(
        "<p><b>antes</b></p><p><img src=\"file:///tmp/x.png\" /></p><p>depois</p>",
      ),
    ).toBe(true);
    expect(
      clipboardHtmlHasProse(
        "<!--StartFragment--><img src=\"file:///clip.png\" /><!--EndFragment-->",
      ),
    ).toBe(false);
  });

  it("materializa texto+imagem na ordem e consome File do clipboard", () => {
    const file = new File(["bytes"], "word-img.png", { type: "image/png" });
    const html =
      "<p><strong>Agsvdghagsdvgavs</strong></p>" +
      "<p><img src=\"file:///C:/Users/x/AppData/Temp/msohtmlclip1/01/clip_image001.png\" /></p>" +
      "<p>asdjhashdas</p>";
    const result = materializeClipboardHtmlInlineImages(html, [file]);
    expect(result.inserts).toHaveLength(1);
    expect(result.inserts[0]?.file.name).toBe("word-img.png");
    expect(result.remainingFiles).toHaveLength(0);
    expect(result.html).toMatch(/Agsvdghagsdvgavs/);
    expect(result.html).toMatch(/asdjhashdas/);
    expect(result.html).toContain("data-attachment-pending=");
    expect(result.html).not.toMatch(/file:\/\//);
    expect(stripImagesFromClipboardHtml(html)).not.toMatch(/<img\b/i);
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

  it("insertComposerInlineImageAtCaret mantém imagem no mesmo <p> entre textos", () => {
    const file = new File(["x"], "mid.png", { type: "image/png" });
    const [insert] = buildInlineImageInserts([file]);
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.innerHTML = "<p>antesdepois</p>";
    document.body.appendChild(editor);
    const text = editor.querySelector("p")!.firstChild as Text;
    const range = document.createRange();
    range.setStart(text, "antes".length);
    range.collapse(true);
    const selection = window.getSelection()!;
    selection.removeAllRanges();
    selection.addRange(range);

    const span = insertComposerInlineImageAtCaret(editor, insert!);
    expect(span).not.toBeNull();
    expect(editor.querySelectorAll(":scope > p")).toHaveLength(1);
    const p = editor.querySelector("p")!;
    expect(p.querySelector(".delpi-ui-mention-composer__inline-image")).toBe(span);
    const textOnly = Array.from(p.childNodes)
      .filter((n) => n.nodeType === Node.TEXT_NODE)
      .map((n) => (n.textContent ?? "").replace(/\u200b/g, ""))
      .join("");
    expect(textOnly).toBe("antesdepois");
    expect(span?.previousSibling?.textContent).toBe("\u200b");
    expect(span?.nextSibling?.textContent).toBe("\u200b");
    editor.remove();
  });

  it("set/read data-align legado na figure", () => {
    const figure = document.createElement("figure");
    setInlineImageFigureAlign(figure, "center");
    expect(readInlineImageFigureAlign(figure)).toBe("center");
    expect(figure.getAttribute(INLINE_IMAGE_ALIGN_ATTR)).toBe("center");
  });
});
