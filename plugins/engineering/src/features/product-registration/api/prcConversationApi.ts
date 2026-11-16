/** PRC-CONVERSATION — adapter da conversa oficial PRC (Issue #207).
 * Mesmo requestId/histórico do My Requests; autorização sempre no backend. */

import {
  deleteJson,
  getBlob,
  getJson,
  patchJson,
  postFormData,
  postJson,
} from "../../../api/httpClient";
import type {
  ConversationApi,
  ConversationAttachment,
  ConversationComment,
} from "@delpi/plugin-ui/index";

const BASE = "/apps/engineering-api/v1/product-registration";

type ApiComment = {
  commentId: string;
  requestId: string;
  authorSubject: string;
  authorDisplayName: string | null;
  body: string;
  version: number;
  isMine: boolean;
  createdAt: string;
  updatedAt: string | null;
  edited: boolean;
};

type ApiAttachment = {
  attachmentId: string;
  originalFileName: string;
  mediaType: string | null;
  sizeBytes: number | null;
  state: string;
};

const mapComment = (row: ApiComment): ConversationComment => ({
  id: row.commentId,
  requestId: row.requestId,
  authorId: row.authorSubject,
  authorName: row.authorDisplayName || "Usuário",
  body: row.body,
  version: row.version,
  isMine: row.isMine,
  createdAt: row.createdAt,
  updatedAt: row.updatedAt,
  edited: row.edited,
});

const mapAttachment = (row: ApiAttachment): ConversationAttachment => ({
  id: row.attachmentId,
  fileName: row.originalFileName,
  mediaType: row.mediaType,
  sizeBytes: row.sizeBytes,
  state: row.state,
});

const commentsPath = (requestId: string) =>
  `${BASE}/requests/${encodeURIComponent(requestId)}/comments`;

const attachmentsPath = (requestId: string, commentId: string) =>
  `${commentsPath(requestId)}/${encodeURIComponent(commentId)}/attachments`;

export const prcConversationApi: ConversationApi = {
  async listComments(requestId, opts) {
    const env = await getJson<{ data: { items: ApiComment[] } }>(
      commentsPath(requestId),
      opts?.signal,
    );
    return (env.data.items || []).map(mapComment);
  },

  async createComment(requestId, body, opts) {
    const env = await postJson<{ data: { comment: ApiComment } }>(
      commentsPath(requestId),
      { body },
      undefined,
      opts?.idempotencyKey
        ? { headers: { "Idempotency-Key": opts.idempotencyKey } }
        : undefined,
    );
    return mapComment(env.data.comment);
  },

  async updateComment(requestId, commentId, body, opts) {
    const env = await patchJson<{ data: { comment: ApiComment } }>(
      `${commentsPath(requestId)}/${encodeURIComponent(commentId)}`,
      { body, expectedVersion: opts?.expectedVersion ?? null },
    );
    return mapComment(env.data.comment);
  },

  async listAttachments(requestId, commentId, opts) {
    const env = await getJson<{ data: { attachments: ApiAttachment[] } }>(
      attachmentsPath(requestId, commentId),
      opts?.signal,
    );
    return (env.data.attachments || []).map(mapAttachment);
  },

  async uploadAttachment(requestId, commentId, file) {
    const form = new FormData();
    form.append("file", file);
    const env = await postFormData<{ data: { attachment: ApiAttachment } }>(
      attachmentsPath(requestId, commentId),
      form,
    );
    return mapAttachment(env.data.attachment);
  },

  downloadAttachment(requestId, commentId, attachmentId, opts) {
    return getBlob(
      `${attachmentsPath(requestId, commentId)}/${encodeURIComponent(attachmentId)}`,
      opts?.signal,
    );
  },

  async deleteAttachment(requestId, commentId, attachmentId) {
    await deleteJson(
      `${attachmentsPath(requestId, commentId)}/${encodeURIComponent(attachmentId)}`,
    );
  },
};
