/** PRC-CONVERSATION — contrato do adapter × envelope Engineering API. */
import { describe, expect, it, vi, beforeEach } from "vitest";

const getJson = vi.fn();
const postJson = vi.fn();
const patchJson = vi.fn();
const deleteJson = vi.fn();
const getBlob = vi.fn();
const postFormData = vi.fn();

vi.mock("../../../api/httpClient", () => ({
  getJson: (...a: unknown[]) => getJson(...a),
  postJson: (...a: unknown[]) => postJson(...a),
  patchJson: (...a: unknown[]) => patchJson(...a),
  deleteJson: (...a: unknown[]) => deleteJson(...a),
  getBlob: (...a: unknown[]) => getBlob(...a),
  postFormData: (...a: unknown[]) => postFormData(...a),
}));

import { prcConversationApi } from "./prcConversationApi";

const COMMENT = {
  commentId: "c1",
  requestId: "r1",
  authorSubject: "u1",
  authorDisplayName: "Ana",
  body: "olá",
  version: 1,
  isMine: false,
  createdAt: "2026-01-01T10:00:00Z",
  updatedAt: null,
  edited: false,
};

describe("prcConversationApi (Engineering)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("listComments usa mesmo requestId da Engineering API", async () => {
    getJson.mockResolvedValue({ data: { items: [COMMENT] } });
    const items = await prcConversationApi.listComments("r1");
    expect(getJson).toHaveBeenCalledWith(
      "/apps/engineering-api/v1/product-registration/requests/r1/comments",
      undefined,
    );
    expect(items[0]).toMatchObject({ id: "c1", isMine: false });
  });

  it("createComment propaga Idempotency-Key via options.headers", async () => {
    postJson.mockResolvedValue({ data: { comment: COMMENT } });
    await prcConversationApi.createComment("r1", "oi", {
      idempotencyKey: "k9",
    });
    expect(postJson).toHaveBeenCalledWith(
      expect.stringContaining("/comments"),
      { body: "oi" },
      undefined,
      { headers: { "Idempotency-Key": "k9" } },
    );
  });

  it("updateComment envia expectedVersion para CAS", async () => {
    patchJson.mockResolvedValue({ data: { comment: COMMENT } });
    await prcConversationApi.updateComment("r1", "c1", "x", {
      expectedVersion: 7,
    });
    expect(patchJson).toHaveBeenCalledWith(
      expect.stringContaining("/comments/c1"),
      { body: "x", expectedVersion: 7 },
    );
  });

  it("deleteAttachment chama DELETE no path do anexo", async () => {
    deleteJson.mockResolvedValue({});
    await prcConversationApi.deleteAttachment("r1", "c1", "a1");
    expect(deleteJson).toHaveBeenCalledWith(
      "/apps/engineering-api/v1/product-registration/requests/r1/comments/c1/attachments/a1",
    );
  });
});
