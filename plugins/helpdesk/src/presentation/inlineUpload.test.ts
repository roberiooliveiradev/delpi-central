import { describe, expect, it } from "vitest";

import {
  appendInlineImageHtml,
  listPendingInlineIds,
  normalizeInlineAttachmentSrcs,
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

  it("normaliza blob preview para URL pública do BFF no envio", () => {
    const html = appendInlineImageHtml("<p>x</p>", {
      src: "blob:http://localhost/preview",
      documentId: 1177,
      alt: "probe",
    });
    expect(html).toContain("blob:");
    const normalized = normalizeInlineAttachmentSrcs(html, 1122);
    expect(normalized).toContain('/apps/helpdesk-api/tickets/1122/attachments/1177');
    expect(normalized).toContain('data-attachment-id="1177"');
    expect(normalized).not.toContain("blob:");
  });

  it("não altera imgs sem data-attachment-id", () => {
    const html = '<p><img src="https://cdn.example/a.png" alt="x" /></p>';
    expect(normalizeInlineAttachmentSrcs(html, 1)).toBe(html);
  });
});
