import { PRODUCTION_PULSE_API_BASE } from "../api/httpClient";

export type ProductionPulseRealtimeEvent =
  | {
      type: "device.updated";
      reason?: string;
      deviceId: string;
      branch?: string | null;
      actorUserId?: string | null;
      actorClientId?: string | null;
    }
  | {
      type: "firmware.catalog.updated";
      reason?: string;
      firmwareId?: string | null;
      firmwareKey?: string | null;
      actorUserId?: string | null;
      actorClientId?: string | null;
    }
  | {
      type: "ota.job.updated";
      reason?: string;
      jobId: string;
      branch?: string | null;
      status?: string | null;
      actorUserId?: string | null;
      actorClientId?: string | null;
    }
  | {
      type: "ota.target.updated";
      reason?: string;
      targetId: string;
      jobId: string;
      deviceId: string;
      branch?: string | null;
      status?: string | null;
      progressPercent?: number | null;
    }
  | { type: "connected"; roomKeys?: string[]; userId?: string; clientId?: string }
  | { type: "subscribed"; deviceId?: string; jobId?: string; roomKey?: string }
  | { type: "unsubscribed"; deviceId?: string; jobId?: string; roomKey?: string }
  | { type: "error"; code?: string; deviceId?: string; jobId?: string }
  | { type: "pong" };

export const PP_REALTIME_HUB_EVENT_TYPES = [
  "device.updated",
  "firmware.catalog.updated",
  "ota.job.updated",
  "ota.target.updated",
] as const;

export type ProductionPulseHubRealtimeEventType =
  (typeof PP_REALTIME_HUB_EVENT_TYPES)[number];

export function buildProductionPulseRealtimeWsUrl(options: {
  token: string;
  clientId: string;
}): string {
  const hasWindow = typeof window !== "undefined";
  const protocol =
    hasWindow && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = hasWindow ? window.location.host : "localhost";
  const base =
    (typeof import.meta !== "undefined" &&
      import.meta.env?.VITE_PRODUCTION_PULSE_WS_BASE?.trim()) ||
    `${protocol}//${host}${PRODUCTION_PULSE_API_BASE}/v1/realtime/ws`;

  const url = new URL(base, hasWindow ? window.location.origin : "http://localhost");
  url.searchParams.set("token", options.token);
  url.searchParams.set("client_id", options.clientId);
  return url.toString();
}

export function parseProductionPulseRealtimeEvent(
  raw: string,
): ProductionPulseRealtimeEvent | null {
  try {
    const parsed = JSON.parse(raw) as ProductionPulseRealtimeEvent;
    if (parsed && typeof parsed === "object" && "type" in parsed) {
      return parsed;
    }
  } catch {
    return null;
  }
  return null;
}

export function isHubRealtimeHint(
  event: ProductionPulseRealtimeEvent,
): event is Extract<
  ProductionPulseRealtimeEvent,
  { type: ProductionPulseHubRealtimeEventType }
> {
  return (PP_REALTIME_HUB_EVENT_TYPES as readonly string[]).includes(event.type);
}
