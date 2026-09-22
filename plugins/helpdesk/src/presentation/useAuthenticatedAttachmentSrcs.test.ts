import { describe, expect, it, vi } from "vitest";

import { HelpdeskApiError } from "../api/helpdeskApi";
import {
  attachmentKeysSignature,
  attachmentSrcMapsEqual,
  collectAttachmentCacheKeys,
  isHardAttachmentFetchFailure,
  persistHelpdeskAttachmentHtml,
  pruneAttachmentSrcs,
  resolveAttachmentDisplaySrc,
  shouldFetchAttachmentBlob,
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

describe("attachment fetch storm gates", () => {
  it("positive: keys signature estável quando só o texto ao redor muda", () => {
    const extra = [10];
    const aliases = {};
    const withImage =
      '<p>a</p><p><img data-attachment-id="1201" src="/apps/helpdesk-api/tickets/1/attachments/1201" /></p>';
    const typedMore =
      '<p>ajhgdghas ajhsdhsadas</p><p><img data-attachment-id="1201" src="/apps/helpdesk-api/tickets/1/attachments/1201" /></p>';
    const a = collectAttachmentCacheKeys(withImage, extra, aliases);
    const b = collectAttachmentCacheKeys(typedMore, extra, aliases);
    expect(attachmentKeysSignature(a)).toBe(attachmentKeysSignature(b));
    expect(a).toEqual(["10", "1201"]);
  });

  it("irmão: 404 hard-fail não refetcha; seed presente também não", () => {
    const failed = new Set(["1201"]);
    const inFlight = new Set<string>();
    expect(
      shouldFetchAttachmentBlob("1201", {}, failed, inFlight),
    ).toBe(false);
    expect(
      shouldFetchAttachmentBlob("1201", { "1201": "blob:x" }, new Set(), inFlight),
    ).toBe(false);
    expect(
      shouldFetchAttachmentBlob("1202", {}, failed, inFlight),
    ).toBe(true);
  });

  it("negativo: erro de rede não é hard-fail (pode retentar depois)", () => {
    expect(isHardAttachmentFetchFailure(new Error("network"))).toBe(false);
    expect(isHardAttachmentFetchFailure(new HelpdeskApiError("not_found", 404))).toBe(true);
    expect(isHardAttachmentFetchFailure(new HelpdeskApiError("forbidden", 403))).toBe(true);
    expect(isHardAttachmentFetchFailure(new HelpdeskApiError("request_failed", 500))).toBe(
      false,
    );
  });

  it("prune igual não deve forçar novo mapa", () => {
    const map = { "1201": "blob:a" };
    expect(attachmentSrcMapsEqual(map, { "1201": "blob:a" })).toBe(true);
    expect(attachmentSrcMapsEqual(map, { "1201": "blob:b" })).toBe(false);
  });
});
