import { describe, expect, it } from "vitest";

import {
  attachmentIdsInMarkdown,
  messageBodyHtmlFromMarkdown,
  messageBodyHtmlIsPlainParagraph,
} from "./messageThreadMarkdown";

describe("attachmentIdsInMarkdown", () => {
  it("lista uuids e ignora pending", () => {
    const md =
      "![a](attachment:pending:x) ![b](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)";
    expect(attachmentIdsInMarkdown(md)).toEqual([
      "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    ]);
  });
});

describe("messageBodyHtmlFromMarkdown attachment src", () => {
  it("aplica resolveAttachmentImageSrc", () => {
    const html = messageBodyHtmlFromMarkdown(
      "![x](attachment:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)",
      null,
      "chip",
      {
        resolveAttachmentImageSrc: (id) =>
          id === "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" ? "blob:preview" : null,
      },
    );
    expect(html).toContain('src="blob:preview"');
    expect(html).toContain("data-attachment-id=");
    expect(messageBodyHtmlIsPlainParagraph(html)).toBe(false);
  });
});
