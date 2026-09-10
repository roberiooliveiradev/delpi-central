import { API_BASE } from "../api/requestsApi";

export type MyRequestsRealtimeNotification = {
  title: string;
  message: string;
  variant: "info" | "success" | "warning" | "error";
};

export type MyRequestsRealtimeEvent =
  | {
      type: "request.created";
      reason?: string;
      requestId: string;
      requestNumber?: string | null;
      status?: string | null;
      actorUserId?: string | null;
      actorClientId?: string | null;
      ownerUserId?: string | null;
      notification?: MyRequestsRealtimeNotification | null;
    }
  | {
      type: "request.changed";
      reason?: string;
      requestId: string;
      requestNumber?: string | null;
      status?: string | null;
      actorUserId?: string | null;
      actorClientId?: string | null;
      ownerUserId?: string | null;
      notification?: MyRequestsRealtimeNotification | null;
    }
  | {
      type: "request.timeline";
      reason?: string;
      requestId: string;
      requestNumber?: string | null;
      status?: string | null;
      actorUserId?: string | null;
      actorClientId?: string | null;
      ownerUserId?: string | null;
      notification?: MyRequestsRealtimeNotification | null;
    }
  | { type: "connected"; roomKeys?: string[]; userId?: string; clientId?: string }
  | { type: "subscribed"; requestId?: string; roomKey?: string }
  | { type: "unsubscribed"; requestId?: string; roomKey?: string }
  | { type: "error"; code?: string; requestId?: string }
  | { type: "pong" };

export function buildMyRequestsRealtimeWsUrl(options: {
  token: string;
  clientId: string;
}): string {
  const hasWindow = typeof window !== "undefined";
  const protocol =
    hasWindow && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = hasWindow ? window.location.host : "localhost";
  const apiRoot = API_BASE.replace(/\/v1\/?$/, "");
  const base =
    (typeof import.meta !== "undefined" &&
      import.meta.env?.VITE_REQUESTS_WS_BASE?.trim()) ||
    `${protocol}//${host}${apiRoot}/v1/realtime/ws`;

  const url = new URL(base, hasWindow ? window.location.origin : "http://localhost");
  url.searchParams.set("token", options.token);
  url.searchParams.set("client_id", options.clientId);
  return url.toString();
}

export function parseMyRequestsRealtimeEvent(
  raw: string,
): MyRequestsRealtimeEvent | null {
  try {
    const parsed = JSON.parse(raw) as MyRequestsRealtimeEvent;
    if (parsed && typeof parsed === "object" && "type" in parsed) {
      return parsed;
    }
  } catch {
    return null;
  }
  return null;
}

export function buildRequestSubscribePayload(requestId: string): string {
  return JSON.stringify({ type: "subscribe", requestId });
}

export function buildRequestUnsubscribePayload(requestId: string): string {
  return JSON.stringify({ type: "unsubscribe", requestId });
}

export function resolveRemoteNotification(
  event: Extract<
    MyRequestsRealtimeEvent,
    { type: "request.created" | "request.changed" | "request.timeline" }
  >,
): MyRequestsRealtimeNotification | null {
  const fromServer = event.notification;
  if (
    fromServer &&
    typeof fromServer.title === "string" &&
    typeof fromServer.message === "string"
  ) {
    const variant =
      fromServer.variant === "success" ||
      fromServer.variant === "warning" ||
      fromServer.variant === "error" ||
      fromServer.variant === "info"
        ? fromServer.variant
        : "info";
    return {
      title: fromServer.title,
      message: fromServer.message,
      variant,
    };
  }
  return null;
}
