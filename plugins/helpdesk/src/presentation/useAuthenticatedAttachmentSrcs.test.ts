import { describe, expect, it } from "vitest";

import { persistHelpdeskAttachmentHtml } from "./useAuthenticatedAttachmentSrcs";

describe("persistHelpdeskAttachmentHtml", () => {
  it("positive: blob no DOM vira URL pública estável no rascunho", () => {
    const html =
      '<p><img src="blob:http://localhost/uuid" alt="Captura.png" data-attachment-id="1177" width="400" height="200" /></p>';
    const persisted = persistHelpdeskAttachmentHtml(html, 1122);
    expect(persisted).toContain("/apps/helpdesk-api/tickets/1122/attachments/1177");
    expect(persisted).toContain('data-attachment-id="1177"');
    expect(persisted).not.toContain("blob:");
  });

  it("irmão: carimba data-attachment-id a partir do path BFF", () => {
    const html =
      '<p><img src="/apps/helpdesk-api/tickets/1122/attachments/99" alt="x" /></p>';
    const persisted = persistHelpdeskAttachmentHtml(html, 1122);
    expect(persisted).toContain('data-attachment-id="99"');
    expect(persisted).toContain("/attachments/99");
  });

  it("negativo: img sem anexo helpdesk permanece", () => {
    const html = '<p><img src="https://cdn.example/a.png" alt="x" /></p>';
    expect(persistHelpdeskAttachmentHtml(html, 1)).toContain("https://cdn.example/a.png");
  });
});
