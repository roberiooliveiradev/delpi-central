/** ENG-REALTIME-01 — contrato do tempo real transversal Engineering.
 *
 * Envelope e helpers do canal `/v1/realtime/ws` da Engineering API.
 * Transporte é invalidação leve — nunca transporta ficha, fornecedores,
 * documentos ou tokens. O consumidor faz HTTP refetch na API oficial.
 */

export const ENGINEERING_PRC_DOMAIN = "product-registration";
export const ENGINEERING_RESOURCE_CHANGED = "engineering.resource.changed";

export type EngineeringResourceChangedEvent = {
  type: typeof ENGINEERING_RESOURCE_CHANGED;
  domain: string;
  resourceType: string;
  resourceId: string;
  reason: string;
  version?: number | null;
  status?: string | null;
  eventId?: string | null;
  occurredAt?: string | null;
  actorUserId?: string | null;
  actorClientId?: string | null;
};

export type EngineeringRealtimeMessage =
  | EngineeringResourceChangedEvent
  | { type: "connected"; roomKeys?: string[]; userId?: string; clientId?: string }
  | {
      type: "subscribed" | "unsubscribed";
      domain?: string;
      resourceType?: string;
      resourceId?: string;
      roomKey?: string;
    }
  | { type: "error"; code?: string; domain?: string; resourceId?: string }
  | { type: "pong" };

/** `apiBase` = base HTTP da Engineering API (ex.:
 * `/apps/engineering-api`); o sufixo `/v1/realtime/ws` é adicionado. */
export function buildEngineeringRealtimeWsUrl(options: {
  apiBase: string;
  token: string;
  clientId: string;
}): string {
  const hasWindow = typeof window !== "undefined";
  const protocol =
    hasWindow && window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = hasWindow ? window.location.host : "localhost";
  const base = options.apiBase.replace(/\/+$/, "");
  const url = new URL(
    `${protocol}//${host}${base}/v1/realtime/ws`,
  );
  url.searchParams.set("token", options.token);
  url.searchParams.set("client_id", options.clientId);
  return url.toString();
}

export function buildEngineeringSubscribePayload(
  domain: string,
  resourceId: string,
  resourceType = "request",
): string {
  return JSON.stringify({
    type: "subscribe",
    domain,
    resourceType,
    resourceId,
  });
}

export function buildEngineeringUnsubscribePayload(
  domain: string,
  resourceId: string,
  resourceType = "request",
): string {
  return JSON.stringify({
    type: "unsubscribe",
    domain,
    resourceType,
    resourceId,
  });
}

export function parseEngineeringRealtimeMessage(
  raw: string,
): EngineeringRealtimeMessage | null {
  try {
    const parsed = JSON.parse(raw) as EngineeringRealtimeMessage;
    if (parsed && typeof parsed === "object" && "type" in parsed) {
      return parsed;
    }
  } catch {
    return null;
  }
  return null;
}
