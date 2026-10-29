import { describe, expect, it } from "vitest";

import { hydrateRichTextInlineImageChrome } from "./richTextInlineImage";

function editorWith(html: string): HTMLElement {
  const el = document.createElement("div");
  el.innerHTML = html;
  return el;
}

describe("hydrateRichTextInlineImageChrome", () => {
  it("wraps a restored pending img with the remove chrome (F5 parity)", () => {
    const editor = editorWith(
      '<p><img src="attachment:pending:p1" data-attachment-pending="p1" data-attachment-href="attachment:pending:p1" alt="shot.png" /></p>',
    );
    const wrapped = hydrateRichTextInlineImageChrome(editor);
    expect(wrapped).toBe(1);
    const host = editor.querySelector("span.delpi-ui-rich-text__inline-image");
    expect(host).not.toBeNull();
    expect(host?.getAttribute("contenteditable")).toBe("false");
    const img = host?.querySelector("img");
    expect(img?.getAttribute("data-attachment-pending")).toBe("p1");
    const btn = host?.querySelector("button[data-inline-image-remove]");
    expect(btn).not.toBeNull();
    expect(btn?.textContent).toBe("×");
  });

  it("wraps a restored persisted-document img (data-attachment-id)", () => {
    const editor = editorWith(
      '<p><img src="/apps/helpdesk-api/tickets/9/attachments/5" data-attachment-id="5" alt="a.png" /></p>',
    );
    expect(hydrateRichTextInlineImageChrome(editor)).toBe(1);
    expect(
      editor.querySelector(
        "span.delpi-ui-rich-text__inline-image button[data-inline-image-remove]",
      ),
    ).not.toBeNull();
  });

  it("is idempotent — an already-wrapped img is not re-wrapped", () => {
    const editor = editorWith(
      '<p><span class="delpi-ui-rich-text__inline-image" contenteditable="false">' +
        '<img src="attachment:pending:p1" data-attachment-pending="p1" alt="x" />' +
        '<button data-inline-image-remove="1">×</button></span></p>',
    );
    expect(hydrateRichTextInlineImageChrome(editor)).toBe(0);
    expect(editor.querySelectorAll("button[data-inline-image-remove]").length).toBe(1);
    // second pass stays a no-op
    hydrateRichTextInlineImageChrome(editor);
    expect(editor.querySelectorAll("span.delpi-ui-rich-text__inline-image").length).toBe(1);
  });

  it("leaves plain non-attachment images untouched", () => {
    const editor = editorWith('<p><img src="https://x/img.png" alt="ext" /></p>');
    expect(hydrateRichTextInlineImageChrome(editor)).toBe(0);
    expect(editor.querySelector("span.delpi-ui-rich-text__inline-image")).toBeNull();
  });

  it("wraps multiple restored images independently", () => {
    const editor = editorWith(
      '<p><img src="attachment:pending:a" data-attachment-pending="a" alt="a" />' +
        '<img src="attachment:pending:b" data-attachment-pending="b" alt="b" /></p>',
    );
    expect(hydrateRichTextInlineImageChrome(editor)).toBe(2);
    expect(editor.querySelectorAll("button[data-inline-image-remove]").length).toBe(2);
  });
});
