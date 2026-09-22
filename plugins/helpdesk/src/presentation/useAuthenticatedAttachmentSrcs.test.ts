import { describe, expect, it, vi } from "vitest";

import {
  persistHelpdeskAttachmentHtml,
  pruneAttachmentSrcs,
  resolveAttachmentDisplaySrc,
  transferPendingSrcMaps,
} from "./useAuthenticatedAttachmentSrcs";

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

  it("pending: blob vira token estável (F5 sem File em memória)", () => {
    const html =
      '<p><img src="blob:http://localhost/dead" alt="print" data-attachment-pending="abc-1" /></p>';
    const persisted = persistHelpdeskAttachmentHtml(html);
    expect(persisted).toContain('src="attachment:pending:abc-1"');
    expect(persisted).toContain('data-attachment-pending="abc-1"');
    expect(persisted).not.toContain("blob:");
  });
});

describe("transferPendingSrcMaps + resolve alias", () => {
  it("positive: após upload, pending ainda resolve o mesmo blob", () => {
    const blob = "blob:http://localhost/live";
    const transferred = transferPendingSrcMaps(
      { "pend-1": blob },
      {},
      "pend-1",
      1177,
    );
    expect(transferred.url).toBe(blob);
    expect(transferred.srcs["1177"]).toBe(blob);
    expect(transferred.srcs["pend-1"]).toBeUndefined();
    expect(
      resolveAttachmentDisplaySrc("pend-1", transferred.srcs, transferred.pendingToDocument),
    ).toBe(blob);
    expect(
      resolveAttachmentDisplaySrc("1177", transferred.srcs, transferred.pendingToDocument),
    ).toBe(blob);
  });

  it("irmão: prune não revoga blob ainda referenciado pelo document id", () => {
    const revoke = vi.fn();
    const blob = "blob:http://localhost/shared";
    const pruned = pruneAttachmentSrcs(
      { "pend-1": blob, "1177": blob },
      new Set(["1177"]),
      revoke,
    );
    expect(pruned).toEqual({ "1177": blob });
    expect(revoke).not.toHaveBeenCalled();
  });

  it("negativo: prune revoga blob órfão", () => {
    const revoke = vi.fn();
    const pruned = pruneAttachmentSrcs(
      { "pend-1": "blob:http://localhost/orphan" },
      new Set(),
      revoke,
    );
    expect(pruned).toEqual({});
    expect(revoke).toHaveBeenCalledWith("blob:http://localhost/orphan");
  });
});
