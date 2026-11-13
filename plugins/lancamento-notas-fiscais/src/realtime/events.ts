export type LnfRequestChangedEvent = {
  type: "lnf.request.changed";
  eventId: string;
  occurredAt?: string;
  branch: string;
  requestId: string;
  reason: string;
  actorOrigin?: string;
};

export type LnfQueueReconciledEvent = {
  type: "lnf.queue.reconciled";
  eventId: string;
  occurredAt?: string;
  branch: string;
  updatedCount: number;
};

export type LnfUnmappedProductsChangedEvent = {
  type: "lnf.unmapped-products.changed";
  eventId: string;
  occurredAt?: string;
};

export type LnfRealtimeEvent =
  | LnfRequestChangedEvent
  | LnfQueueReconciledEvent
  | LnfUnmappedProductsChangedEvent;

export type LnfRealtimeControlMessage =
  | { type: "subscribed" | "unsubscribed"; room?: string }
  | { type: "error"; code?: string; room?: string }
  | { type: "pong" };

export function isLnfRequestChanged(value: unknown): value is LnfRequestChangedEvent {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return (
    row.type === "lnf.request.changed" &&
    typeof row.eventId === "string" &&
    typeof row.branch === "string" &&
    typeof row.requestId === "string"
  );
}

export function isLnfQueueReconciled(
  value: unknown,
): value is LnfQueueReconciledEvent {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return (
    row.type === "lnf.queue.reconciled" &&
    typeof row.eventId === "string" &&
    typeof row.branch === "string" &&
    typeof row.updatedCount === "number"
  );
}

export function isLnfUnmappedProductsChanged(
  value: unknown,
): value is LnfUnmappedProductsChangedEvent {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return (
    row.type === "lnf.unmapped-products.changed" &&
    typeof row.eventId === "string"
  );
}

export function isLnfForbiddenRoom(value: unknown): boolean {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return row.type === "error" && row.code === "forbidden_room";
}

export function parseLnfControlMessage(
  raw: string,
): LnfRealtimeControlMessage | null {
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    if (!parsed || typeof parsed.type !== "string") return null;
    if (
      parsed.type === "subscribed" ||
      parsed.type === "unsubscribed" ||
      parsed.type === "error" ||
      parsed.type === "pong"
    ) {
      return parsed as LnfRealtimeControlMessage;
    }
    return null;
  } catch {
    return null;
  }
}

/** Fila: request.changed ou queue.reconciled da filial aberta. */
export function isQueueRefetchEvent(
  value: unknown,
  branch: string,
): boolean {
  if (isLnfRequestChanged(value) && value.branch === branch) return true;
  if (isLnfQueueReconciled(value) && value.branch === branch) return true;
  return false;
}

/** Detalhe / edição: request.changed da solicitação aberta. */
export function isDetailRefetchEvent(
  value: unknown,
  requestId: string,
): boolean {
  return isLnfRequestChanged(value) && value.requestId === requestId;
}
