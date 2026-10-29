import { describe, expect, it } from "vitest";

import {
  ATTACHMENT_AUTHOR_NOTICE_TEXT,
  attachmentAuthorDegraded,
  consumeAttachmentAuthorNotice,
  consumeTicketNotice,
  stageAttachmentAuthorNotice,
  stageTicketNotice,
} from "./attachmentAuthorNotice";

describe("attachmentAuthorNotice", () => {
  it("flags only explicitly degraded authorship — never a false negative on success", () => {
    expect(attachmentAuthorDegraded({ author_verified: false })).toBe(true);
    expect(attachmentAuthorDegraded({ author_verified: true })).toBe(false);
    expect(attachmentAuthorDegraded({})).toBe(false);
    expect(attachmentAuthorDegraded(null)).toBe(false);
  });

  it("stage/consume round-trips the notice exactly once", () => {
    const store = new Map<string, string>();
    (globalThis as { sessionStorage?: unknown }).sessionStorage = {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
    };
    try {
      expect(consumeAttachmentAuthorNotice()).toBeNull();
      stageAttachmentAuthorNotice();
      expect(consumeAttachmentAuthorNotice()).toBe(ATTACHMENT_AUTHOR_NOTICE_TEXT);
      expect(consumeAttachmentAuthorNotice()).toBeNull();
    } finally {
      delete (globalThis as { sessionStorage?: unknown }).sessionStorage;
    }
  });

  it("survives environments without sessionStorage (SSR/test)", () => {
    expect(consumeAttachmentAuthorNotice()).toBeNull();
    expect(() => stageAttachmentAuthorNotice()).not.toThrow();
  });

  it("staged ticket notice (partial links) round-trips the text once", () => {
    const store = new Map<string, string>();
    (globalThis as { sessionStorage?: unknown }).sessionStorage = {
      getItem: (k: string) => store.get(k) ?? null,
      setItem: (k: string, v: string) => void store.set(k, v),
      removeItem: (k: string) => void store.delete(k),
    };
    try {
      expect(consumeTicketNotice()).toBeNull();
      stageTicketNotice("  vínculo parcial  ");
      expect(consumeTicketNotice()).toBe("vínculo parcial");
      expect(consumeTicketNotice()).toBeNull();
      stageTicketNotice("   ");
      expect(consumeTicketNotice()).toBeNull();
    } finally {
      delete (globalThis as { sessionStorage?: unknown }).sessionStorage;
    }
  });
});
