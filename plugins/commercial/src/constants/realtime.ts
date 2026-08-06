import { COMMERCIAL_API_BASE } from "../api/httpClient";

export type WorklistChangeReason =
  | "task.created"
  | "task.updated"
  | "task.completed"
  | "task.deferred"
  | "task.reassigned"
  | "task.deleted"
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
  /** Nome amigável de quem originou a mutação (nunca UUID). */
  actorDisplayName?: string | null;
  /** Nome do responsável atual (assigneeUserIds[0]). */
  assigneeDisplayName?: string | null;
  actorClientId?: string | null;
  notification?: CommercialRealtimeNotification | null;
};

export type CommercialRealtimeEvent =
  | CommercialWorklistChangedEvent
  | { type: "connected"; roomKeys?: string[]; userId?: string; clientId?: string }
  | { type: "pong" };

const GENERIC_ACTOR_LABELS = new Set(["alguém", "alguém da equipe"]);

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

export function isGenericActorDisplayName(value: string | null | undefined): boolean {
  const name = (value || "").trim();
  if (!name) return true;
  return GENERIC_ACTOR_LABELS.has(name.toLowerCase());
}

function actorLabel(event: CommercialWorklistChangedEvent): string {
  const name = (event.actorDisplayName || "").trim();
  if (name && !isGenericActorDisplayName(name)) return name;
  return "Alguém da equipe";
}

function assigneeLabel(event: CommercialWorklistChangedEvent): string {
  const name = (event.assigneeDisplayName || "").trim();
  if (name && !isGenericActorDisplayName(name)) return name;
  return "alguém";
}

export type WorklistNotificationAudience = "assignee" | "previous" | "team";

/**
 * Quem é o usuário atual em relação ao evento.
 * `assigneeUserIds[0]` = responsável atual; demais = anteriores (reatribuição).
 */
export function resolveWorklistNotificationAudience(
  event: CommercialWorklistChangedEvent,
  currentUserId: string | null | undefined,
): WorklistNotificationAudience {
  const me = (currentUserId || "").trim();
  if (!me) return "team";
  const ids = (event.assigneeUserIds || [])
    .map((id) => (id || "").trim())
    .filter(Boolean);
  if (ids[0] === me) return "assignee";
  if (ids.slice(1).includes(me)) return "previous";
  return "team";
}

/** Monta o texto do toast (sempre no cliente para «atribuiu a você»). */
export function resolveWorklistNotification(
  event: CommercialWorklistChangedEvent,
  currentUserId?: string | null,
): CommercialRealtimeNotification {
  return fallbackWorklistNotification(event, {
    audience: resolveWorklistNotificationAudience(event, currentUserId),
  });
}

/** Fallback / personalização local por audiência. */
export function fallbackWorklistNotification(
  event: CommercialWorklistChangedEvent,
  options?: { audience?: WorklistNotificationAudience },
): CommercialRealtimeNotification {
  const titleLabel = (event.taskTitle || "").trim() || "Tarefa sem título";
  const actor = actorLabel(event);
  const assignee = assigneeLabel(event);
  const audience = options?.audience ?? "assignee";
  const assigneeChanged = (event.assigneeUserIds || []).length > 1;

  switch (event.reason) {
    case "task.created":
      return {
        title: "Nova tarefa",
        message:
          audience === "assignee"
            ? `${actor} atribuiu a você: ${titleLabel}`
            : `${actor} atribuiu a ${assignee}: ${titleLabel}`,
        variant: "info",
      };
    case "task.updated":
      if (assigneeChanged && audience === "assignee") {
        return {
          title: "Tarefa reatribuída",
          message: `${actor} atribuiu a você: ${titleLabel}`,
          variant: "info",
        };
      }
      if (assigneeChanged && audience === "previous") {
        return {
          title: "Tarefa reatribuída",
          message: `${actor} reatribuiu a ${assignee}: ${titleLabel}`,
          variant: "info",
        };
      }
      return {
        title: "Tarefa atualizada",
        message: `${actor} alterou a tarefa: ${titleLabel}`,
        variant: "info",
      };
    case "task.completed":
      return {
        title: "Tarefa concluída",
        message: `${actor} concluiu: ${titleLabel}`,
        variant: "success",
      };
    case "task.deferred":
      return {
        title: "Prazo adiado",
        message: `${actor} adiou o prazo: ${titleLabel}`,
        variant: "warning",
      };
    case "task.reassigned":
      return {
        title: "Tarefa reatribuída",
        message:
          audience === "assignee"
            ? `${actor} atribuiu a você: ${titleLabel}`
            : `${actor} reatribuiu a ${assignee}: ${titleLabel}`,
        variant: "info",
      };
    case "task.deleted":
      return {
        title: "Tarefa excluída",
        message: `${actor} excluiu: ${titleLabel}`,
        variant: "warning",
      };
    case "attachment.changed":
      return {
        title: "Anexo na tarefa",
        message: `${actor} alterou anexo em: ${titleLabel}`,
        variant: "info",
      };
    default:
      return {
        title: "Fila atualizada",
        message: `${actor}: ${titleLabel}`,
        variant: "info",
      };
  }
}
