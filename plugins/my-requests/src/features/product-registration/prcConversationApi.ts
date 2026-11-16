/** PRC-CONVERSATION — adapter da conversa oficial PRC (Issue #207).
 *
 * My Requests consome a mesma Engineering API do Portal Engenharia —
 * mesmo requestId, mesmo histórico, nenhum espelho no requests-api.
 * Autorização e escopo são decididos no backend; aqui só contrato.
 */

import {
  ApiClientError,
  authHeaders,
  getAccessToken,
} from "../../api/httpClient";
import type { Envelope } from "../../types/requests";
import type {
  ConversationApi,
  ConversationAttachment,
  ConversationComment,
} from "@delpi/plugin-ui/index";

const PRC_BASE = "/apps/engineering-api/v1/product-registration";

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

function mapComment(row: ApiComment): ConversationComment {
  return {
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
  };
}

function mapAttachment(row: ApiAttachment): ConversationAttachment {
  return {
    id: row.attachmentId,
    fileName: row.originalFileName,
    mediaType: row.mediaType,
    sizeBytes: row.sizeBytes,
    state: row.state,
  };
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  headers?: Record<string, string>,
): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: { ...authHeaders(), ...(body ? { "Content-Type": "application/json" } : {}), ...headers },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let message = `Falha na operação (${response.status}).`;
    try {
      const parsed = await response.json();
      message = parsed?.message || parsed?.detail || message;
    } catch {
      /* resposta não-JSON */
    }
    throw new ApiClientError(response.status, message);
  }
  const parsed = (await response.json()) as Envelope<T>;
  return parsed.data;
}

const commentsPath = (requestId: string) =>
  `${PRC_BASE}/requests/${encodeURIComponent(requestId)}/comments`;

const attachmentsPath = (requestId: string, commentId: string) =>
  `${commentsPath(requestId)}/${encodeURIComponent(commentId)}/attachments`;

export const prcConversationApi: ConversationApi = {
  async listComments(requestId, opts) {
    const data = await request<{ items: ApiComment[] }>(
      "GET",
      commentsPath(requestId),
    );
    void opts;
    return (data.items || []).map(mapComment);
  },

  async createComment(requestId, body, opts) {
    const data = await request<{ comment: ApiComment }>(
      "POST",
      commentsPath(requestId),
      { body },
      opts?.idempotencyKey ? { "Idempotency-Key": opts.idempotencyKey } : {},
    );
    return mapComment(data.comment);
  },

  async updateComment(requestId, commentId, body, opts) {
    const data = await request<{ comment: ApiComment }>(
      "PATCH",
      `${commentsPath(requestId)}/${encodeURIComponent(commentId)}`,
      {
        body,
        expectedVersion: opts?.expectedVersion ?? null,
      },
    );
    return mapComment(data.comment);
  },

  async listAttachments(requestId, commentId, opts) {
    void opts;
    const data = await request<{ attachments: ApiAttachment[] }>(
      "GET",
      attachmentsPath(requestId, commentId),
    );
    return (data.attachments || []).map(mapAttachment);
  },

  async uploadAttachment(requestId, commentId, file) {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(attachmentsPath(requestId, commentId), {
      method: "POST",
      headers: authHeaders(),
      body: form,
    });
    if (!response.ok) {
      let message = `Falha no upload (${response.status}).`;
      try {
        const parsed = await response.json();
        message = parsed?.message || parsed?.detail || message;
      } catch {
        /* resposta não-JSON */
      }
      throw new ApiClientError(response.status, message);
    }
    const parsed = (await response.json()) as Envelope<{
      attachment: ApiAttachment;
    }>;
    return mapAttachment(parsed.data.attachment);
  },

  async downloadAttachment(requestId, commentId, attachmentId, opts) {
    const token = getAccessToken();
    const response = await fetch(
      `${attachmentsPath(requestId, commentId)}/${encodeURIComponent(attachmentId)}`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: opts?.signal,
      },
    );
    if (!response.ok) {
      throw new ApiClientError(
        response.status,
        `Falha no download (${response.status}).`,
      );
    }
    return response.blob();
  },

  async deleteAttachment(requestId, commentId, attachmentId) {
    await request<unknown>(
      "DELETE",
      `${attachmentsPath(requestId, commentId)}/${encodeURIComponent(attachmentId)}`,
    );
  },
};
