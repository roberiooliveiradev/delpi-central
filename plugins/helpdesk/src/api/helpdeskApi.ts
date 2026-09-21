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
  assigned_display_name: string;
};

export type TicketListQuery = {
  q?: string;
  status?: string;
  urgency_id?: string;
  category_id?: string;
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
  created_at: string;
  author_display_name: string;
  mine: boolean;
};

export type TicketDetail = TicketSummary & {
  description: string;
  requester_display_name: string;
  requester_mine: boolean;
  timeline: TimelineEntry[];
  attachments: TicketAttachment[];
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

export function createTicket(
  body: { title: string; description: string; category_id: number; urgency_id: number },
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

export async function beginGlpiLink(): Promise<string> {
  const body = await request<{ authorize_url: string }>("/auth/glpi/start");
  if (!body.authorize_url) {
    throw new HelpdeskApiError("glpi_link_required", 409);
  }
  return body.authorize_url;
}
