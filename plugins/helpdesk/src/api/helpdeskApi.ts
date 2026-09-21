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
  category: string;
  urgency: string;
  updated_at: string;
};

export type TimelineEntry = {
  id: number;
  kind: string;
  content: string;
  created_at: string;
  author_display_name: string;
};

export type TicketDetail = TicketSummary & {
  description: string;
  timeline: TimelineEntry[];
};

export function listTickets(signal?: AbortSignal) {
  return request<{ items: TicketSummary[] }>("/tickets", { signal });
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

export async function beginGlpiLink(): Promise<string> {
  const body = await request<{ authorize_url: string }>("/auth/glpi/start");
  if (!body.authorize_url) {
    throw new HelpdeskApiError("glpi_link_required", 409);
  }
  return body.authorize_url;
}
