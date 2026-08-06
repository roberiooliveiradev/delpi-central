import { COMMERCIAL_API_BASE } from "../api/httpClient";

export type WorklistChangeReason =
  | "task.created"
  | "task.updated"
  | "task.completed"
  | "task.deferred"
  | "task.reassigned"
  | "attachment.changed";

export type CommercialWorklistChangedEvent = {
  type: "worklist.changed";
  reason: WorklistChangeReason;
  taskId: string;
  assigneeUserIds?: string[];
  actorClientId?: string | null;
};

export type CommercialRealtimeEvent =
  | CommercialWorklistChangedEvent
  | { type: "connected"; roomKeys?: string[]; userId?: string; clientId?: string }
  | { type: "pong" };

export function buildCommercialRealtimeWsUrl(options: {
  token: string;
  clientId: string;
}): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const base =
    import.meta.env.VITE_COMMERCIAL_WS_BASE?.trim() ||
    `${protocol}//${window.location.host}${COMMERCIAL_API_BASE}/commercial/realtime/ws`;

  const url = new URL(base, window.location.origin);
  url.searchParams.set("token", options.token);
  url.searchParams.set("client_id", options.clientId);
  return url.toString();
}

export function parseCommercialRealtimeEvent(raw: string): CommercialRealtimeEvent | null {
  try {
    const parsed = JSON.parse(raw) as CommercialRealtimeEvent;
    if (parsed && typeof parsed === "object" && "type" in parsed) {
      return parsed;
    }
  } catch {
    return null;
  }
  return null;
}
