/** PRC-CONVERSATION — contrato do adapter × envelope Engineering API. */
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("../../api/httpClient", () => ({
  ApiClientError: class ApiClientError extends Error {
    constructor(public status: number, message: string) { super(message); }
  },
  authHeaders: () => ({ Authorization: "Bearer test" }),
  getAccessToken: () => "test",
}));

import { prcConversationApi } from "./prcConversationApi";

const COMMENT = {
  commentId: "c1",
  requestId: "r1",
  authorSubject: "u1",
  authorDisplayName: "Ana",
  body: "olá",
  version: 2,
  isMine: true,
  createdAt: "2026-01-01T10:00:00Z",
  updatedAt: "2026-01-01T11:00:00Z",
  edited: true,
};

function ok(data: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify({ data }), { status }),
  );
}

describe("prcConversationApi (My Requests)", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("listComments mapeia envelope items → ConversationComment", async () => {
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(() => ok({ items: [COMMENT] }));
    const items = await prcConversationApi.listComments("r1");
    expect(spy).toHaveBeenCalledWith(
      "/apps/engineering-api/v1/product-registration/requests/r1/comments",
      expect.objectContaining({ method: "GET" }),
    );
    expect(items[0]).toMatchObject({
      id: "c1",
      authorId: "u1",
      authorName: "Ana",
      isMine: true,
      version: 2,
      edited: true,
    });
  });

  it("createComment envia Idempotency-Key e retorna comment", async () => {
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(() => ok({ comment: COMMENT }, 201));
    const created = await prcConversationApi.createComment("r1", "oi", {
      idempotencyKey: "k1",
    });
    expect(spy.mock.calls[0][1]?.headers).toMatchObject({
      "Idempotency-Key": "k1",
    });
    expect(created.id).toBe("c1");
  });

  it("updateComment envia expectedVersion (CAS)", async () => {
    const spy = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(() => ok({ comment: COMMENT }));
    await prcConversationApi.updateComment("r1", "c1", "novo", {
      expectedVersion: 2,
    });
    expect(JSON.parse(spy.mock.calls[0][1]?.body as string)).toMatchObject({
      body: "novo",
      expectedVersion: 2,
    });
  });

  it("listAttachments lê data.attachments e preserva state", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() =>
      ok({
        attachments: [
          {
            attachmentId: "a1",
            originalFileName: "f.pdf",
            mediaType: "application/pdf",
            sizeBytes: 10,
            state: "AVAILABLE",
          },
        ],
      }),
    );
    const items = await prcConversationApi.listAttachments("r1", "c1");
    expect(items[0]).toMatchObject({
      id: "a1",
      fileName: "f.pdf",
      state: "AVAILABLE",
    });
  });

  it("erro HTTP propaga status (403/404/409)", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify({ message: "negado" }), { status: 403 }),
      ),
    );
    await expect(prcConversationApi.listComments("r1")).rejects.toMatchObject({
      status: 403,
    });
  });
});
