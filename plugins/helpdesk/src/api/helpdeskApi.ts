const BASE = "/apps/helpdesk-api";

export class HelpdeskApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly authorizeUrl?: string;

  constructor(code: string, status: number, authorizeUrl?: string) {
    super(code);
    this.code = code;
    this.status = status;
    this.authorizeUrl = authorizeUrl;
  }
}

let accessTokenGetter: (() => string | undefined) | null = null;

export function configureHelpdeskClient(getAccessToken: () => string | undefined) {
  accessTokenGetter = getAccessToken;
}

function headers(extra?: Record<string, string>): Record<string, string> {
  const result: Record<string, string> = {
    Accept: "application/json",
    "X-Delpi-Caller-App": "helpdesk",
    ...extra,
  };
  const token = accessTokenGetter?.();
  if (token) result.Authorization = `Bearer ${token}`;
  return result;
}

async function readError(response: Response): Promise<HelpdeskApiError> {
  let code = "request_failed";
  let authorizeUrl: string | undefined;
  try {
    const body = (await response.json()) as { error?: string; authorize_url?: string };
    if (body.error) code = body.error;
    if (body.authorize_url) authorizeUrl = body.authorize_url;
  } catch {
    if (response.status === 403) code = "forbidden";
  }
  if (response.status === 403 && code === "request_failed") code = "forbidden";
  return new HelpdeskApiError(code, response.status, authorizeUrl);
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: headers(init.headers as Record<string, string> | undefined),
  });
  if (!response.ok) throw await readError(response);
  return (await response.json()) as T;
}

export type TicketSummary = {
  id: number;
  title: string;
  status: string;
  status_id?: number | null;
  category: string;
  urgency: string;
  updated_at: string;
  created_at: string;
  solved_at?: string;
  closed_at?: string;
  sla_ttr?: string;
  sla_tto?: string;
  assigned_display_name: string;
  requester_display_name?: string;
};

export type TicketListQuery = {
  q?: string;
  status?: string;
  urgency_id?: string;
  category_id?: string;
  assignee_id?: string;
  updated_from?: string;
  updated_to?: string;
  created_from?: string;
  created_to?: string;
  sort?: string;
  page?: number;
  page_size?: number;
};

export type TimelineEntry = {
  id: number;
  kind: string;
  content: string;
  content_html?: string;
  created_at: string;
  author_display_name: string;
  mine: boolean;
};

export type TicketValidation = {
  id: number;
  status: number;
  submission_comment?: string;
  approval_comment?: string;
  requested_approver_id?: number | null;
  mine_to_decide?: boolean;
};

export type TicketDetail = TicketSummary & {
  description: string;
  description_html?: string;
  requester_display_name: string;
  requester_mine: boolean;
  can_followup?: boolean;
  can_assign?: boolean;
  can_create_solution?: boolean;
  can_create_task?: boolean;
  can_request_approval?: boolean;
  can_accept_solution?: boolean;
  can_reject_solution?: boolean;
  can_submit_satisfaction?: boolean;
  can_decide_validation?: boolean;
  satisfaction?: number | null;
  satisfaction_comment?: string;
  validations?: TicketValidation[];
  assigned_user_id?: number | null;
  observers_display_name?: string;
  timeline: TimelineEntry[];
  attachments: TicketAttachment[];
};

export type CatalogUser = {
  id: number;
  display_name: string;
  email?: string;
  directory_user_id?: string;
  has_photo?: boolean;
};

export type TicketAttachment = {
  document_id: number;
  filename: string;
  mime: string;
};

export function listTickets(query: TicketListQuery = {}, signal?: AbortSignal) {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.status) params.set("status", query.status);
  if (query.urgency_id) params.set("urgency_id", query.urgency_id);
  if (query.category_id) params.set("category_id", query.category_id);
  if (query.assignee_id) params.set("assignee_id", query.assignee_id);
  if (query.updated_from) params.set("updated_from", query.updated_from);
  if (query.updated_to) params.set("updated_to", query.updated_to);
  if (query.created_from) params.set("created_from", query.created_from);
  if (query.created_to) params.set("created_to", query.created_to);
  if (query.sort) params.set("sort", query.sort);
  if (query.page && query.page > 1) params.set("page", String(query.page));
  if (query.page_size) params.set("page_size", String(query.page_size));
  const suffix = params.toString() ? `?${params}` : "";
  return request<{ items: TicketSummary[]; page: number; page_size: number; has_more: boolean }>(
    `/tickets${suffix}`,
    { signal },
  );
}

export function getTicket(id: string, signal?: AbortSignal) {
  return request<TicketDetail>(`/tickets/${id}`, { signal });
}

export function listCategories(signal?: AbortSignal) {
  return request<{ items: { id: number; name: string }[] }>("/ticket-categories", { signal });
}

export function listUrgencies(signal?: AbortSignal) {
  return request<{ items: { id: number; name: string }[] }>("/urgencies", { signal });
}

export function listUsers(
  query: { q?: string; limit?: number; purpose?: "mention" | "assignee" } = {},
  signal?: AbortSignal,
) {
  const params = new URLSearchParams();
  if (query.q) params.set("q", query.q);
  if (query.limit) params.set("limit", String(query.limit));
  if (query.purpose) params.set("purpose", query.purpose);
  const suffix = params.toString() ? `?${params}` : "";
  return request<{ items: CatalogUser[] }>(`/users${suffix}`, { signal });
}

/** Foto person-profile Minha DELPI (directory_user_id). Soft-fail no consumidor. */
export async function downloadDirectoryUserPhoto(
  directoryUserId: string,
  signal?: AbortSignal,
): Promise<Blob> {
  const uid = directoryUserId.trim();
  if (!uid) throw new HelpdeskApiError("validation_error", 422);
  const response = await fetch(
    `${BASE}/person-profiles/${encodeURIComponent(uid)}/photo`,
    { signal, headers: headers({ Accept: "application/octet-stream" }) },
  );
  if (!response.ok) throw await readError(response);
  return response.blob();
}

export function getSessionCapabilities(signal?: AbortSignal) {
  return request<{ can_assign: boolean }>("/session/capabilities", { signal });
}

export function createTicket(
  body: {
    title: string;
    description: string;
    category_id: number;
    urgency_id: number;
    observer_ids?: number[];
    assignee_id?: number | null;
  },
  idempotencyKey: string,
) {
  return request<{ id: number }>("/tickets", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify(body),
  });
}

export function setTicketAssignee(ticketId: string, userId: number, idempotencyKey: string) {
  return request<{ user_id: number; assigned_display_name: string }>(`/tickets/${ticketId}/assignee`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({ user_id: userId }),
  });
}

export function createFollowup(ticketId: string, content: string, idempotencyKey: string) {
  return request<{ id: number }>(`/tickets/${ticketId}/followups`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({ content }),
  });
}

export function createTicketSolution(ticketId: string, content: string, idempotencyKey: string) {
  return request<{ id: number; status_id: number | null }>(`/tickets/${ticketId}/solutions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({ content }),
  });
}

export function createTicketTask(ticketId: string, content: string, idempotencyKey: string) {
  return request<{ id: number }>(`/tickets/${ticketId}/tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({ content }),
  });
}

export function requestTicketApproval(
  ticketId: string,
  body: { approver_user_id: number; content?: string },
  idempotencyKey: string,
) {
  return request<{ id: number; status: number; requested_approver_id: number | null }>(
    `/tickets/${ticketId}/validations`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({
        approver_user_id: body.approver_user_id,
        content: body.content ?? "",
      }),
    },
  );
}

export function acceptTicketSolution(ticketId: string, content: string, idempotencyKey: string) {
  return request<{ id: number; status_id: number | null }>(`/tickets/${ticketId}/solution/accept`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({ content }),
  });
}

export function rejectTicketSolution(ticketId: string, content: string, idempotencyKey: string) {
  return request<{ id: number; status_id: number | null }>(`/tickets/${ticketId}/solution/reject`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({ content }),
  });
}

export function submitTicketSatisfaction(
  ticketId: string,
  body: { satisfaction: number; comment?: string },
  idempotencyKey: string,
) {
  return request<{ satisfaction: number; comment: string }>(`/tickets/${ticketId}/satisfaction`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey,
    },
    body: JSON.stringify({
      satisfaction: body.satisfaction,
      comment: body.comment ?? "",
    }),
  });
}

export function acceptTicketValidation(
  ticketId: string,
  validationId: number,
  content: string,
  idempotencyKey: string,
) {
  return request<{ id: number; status: number; can_decide_validation: boolean }>(
    `/tickets/${ticketId}/validations/${validationId}/accept`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({ content }),
    },
  );
}

export function rejectTicketValidation(
  ticketId: string,
  validationId: number,
  content: string,
  idempotencyKey: string,
) {
  return request<{ id: number; status: number; can_decide_validation: boolean }>(
    `/tickets/${ticketId}/validations/${validationId}/reject`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({ content }),
    },
  );
}

export async function fetchTicketAttachmentBlob(ticketId: string, documentId: number): Promise<Blob> {
  const response = await fetch(`${BASE}/tickets/${ticketId}/attachments/${documentId}`, {
    headers: headers(),
  });
  if (!response.ok) throw await readError(response);
  return response.blob();
}

export async function downloadTicketAttachment(ticketId: string, documentId: number, filename: string) {
  const blob = await fetchTicketAttachmentBlob(ticketId, documentId);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename || "anexo";
  link.click();
  URL.revokeObjectURL(url);
}

export async function uploadTicketAttachment(
  ticketId: string,
  file: File,
  idempotencyKey: string,
): Promise<TicketAttachment> {
  const form = new FormData();
  form.append("file", file, file.name || "anexo");
  const response = await fetch(`${BASE}/tickets/${ticketId}/attachments`, {
    method: "POST",
    headers: headers({ "Idempotency-Key": idempotencyKey }),
    body: form,
  });
  if (!response.ok) throw await readError(response);
  const body = (await response.json()) as {
    document_id: number;
    filename: string;
    mime: string;
  };
  return {
    document_id: body.document_id,
    filename: body.filename,
    mime: body.mime,
  };
}

export async function beginGlpiLink(): Promise<string> {
  const body = await request<{ authorize_url: string }>("/auth/glpi/start");
  if (!body.authorize_url) {
    throw new HelpdeskApiError("glpi_link_required", 409);
  }
  return body.authorize_url;
}
