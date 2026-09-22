import { describe, expect, it } from "vitest";

import {
  appendInlineImageHtml,
  listPendingInlineIds,
  rewritePendingInlineImages,
  stripPendingInlineImages,
} from "./inlineUpload";

describe("inlineUpload", () => {
  it("insere imagem no HTML vazio e anexa ao existente", () => {
    expect(appendInlineImageHtml("", { src: "/apps/helpdesk-api/tickets/7/attachments/1", documentId: 1 })).toContain(
      'data-attachment-id="1"',
    );
    const next = appendInlineImageHtml("<p>oi</p>", {
      src: "blob:pending",
      pendingId: "abc",
      alt: "foto",
    });
    expect(next).toContain("<p>oi</p>");
    expect(next).toContain('data-attachment-pending="abc"');
  });

  it("reescreve pending após upload e remove pending no strip", () => {
    const html = appendInlineImageHtml("<p>texto</p>", {
      src: "blob:x",
      pendingId: "p1",
    });
    expect(listPendingInlineIds(html)).toEqual(["p1"]);
    const rewritten = rewritePendingInlineImages(html, {
      p1: { documentId: 55, ticketId: 9 },
    });
    expect(rewritten).toContain("/apps/helpdesk-api/tickets/9/attachments/55");
    expect(rewritten).toContain('data-attachment-id="55"');
    expect(rewritten).not.toContain("data-attachment-pending");
    expect(stripPendingInlineImages(html)).toContain("<p>texto</p>");
    expect(stripPendingInlineImages(html)).not.toContain("img");
  });
});
