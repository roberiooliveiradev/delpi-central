import { COMMERCIAL_API_BASE } from "../api/httpClient";

export type WorklistChangeReason =
  | "task.created"
  | "task.updated"
  | "task.completed"
  | "task.deferred"
  | "task.reassigned"
  | "attachment.changed";

export type CommercialRealtimeNotification = {
  title: string;
  message: string;
  variant: "info" | "success" | "warning" | "error";
};

export type CommercialWorklistChangedEvent = {
  type: "worklist.changed";
  reason: WorklistChangeReason;
  taskId: string;
  taskTitle?: string | null;
  assigneeUserIds?: string[];
  actorUserId?: string | null;
  actorClientId?: string | null;
  notification?: CommercialRealtimeNotification | null;
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

/** Fallback local se o payload vier sem `notification` (clientes antigos). */
export function fallbackWorklistNotification(
  event: CommercialWorklistChangedEvent,
): CommercialRealtimeNotification {
  const titleLabel = (event.taskTitle || "").trim() || "Tarefa sem título";
  switch (event.reason) {
    case "task.created":
      return {
        title: "Nova tarefa",
        message: `Foi atribuída a você (ou à equipe): ${titleLabel}`,
        variant: "info",
      };
    case "task.updated":
      return {
        title: "Tarefa atualizada",
        message: `Alteração na fila: ${titleLabel}`,
        variant: "info",
      };
    case "task.completed":
      return {
        title: "Tarefa concluída",
        message: `Concluída: ${titleLabel}`,
        variant: "success",
      };
    case "task.deferred":
      return {
        title: "Prazo adiado",
        message: `Adiada em +1 dia: ${titleLabel}`,
        variant: "warning",
      };
    case "task.reassigned":
      return {
        title: "Tarefa reatribuída",
        message: `Responsável alterado: ${titleLabel}`,
        variant: "info",
      };
    case "attachment.changed":
      return {
        title: "Anexo na tarefa",
        message: `Anexo alterado em: ${titleLabel}`,
        variant: "info",
      };
    default:
      return {
        title: "Fila atualizada",
        message: titleLabel,
        variant: "info",
      };
  }
}
