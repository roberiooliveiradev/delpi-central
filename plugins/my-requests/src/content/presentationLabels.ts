/**
 * Camada única de apresentação PT-BR (E20).
 * Códigos técnicos permanecem nas chamadas à API; só labels/formatters aqui.
 */

const STATUS_LABELS: Record<string, string> = {
  submitted: "Enviada",
  pending: "Pendente",
  in_progress: "Em andamento",
  needs_information: "Aguardando informações",
  returned: "Devolvida para ajuste",
  awaiting_requester_confirmation: "Aguardando confirmação do solicitante",
  awaiting_confirmation: "Aguardando confirmação do solicitante",
  completed: "Concluída",
  issued: "Emitida",
  cancelled: "Cancelada",
  rejected: "Rejeitada",
};

const ACTION_LABELS: Record<string, string> = {
  view: "Visualizar",
  edit: "Editar",
  start: "Iniciar atendimento",
  return: "Devolver para ajuste",
  resubmit: "Reenviar solicitação",
  complete: "Concluir",
  issue: "Emitir nota fiscal",
  confirm_fulfillment: "Confirmar atendimento",
  reject_fulfillment: "Devolver para correção",
  cancel: "Cancelar solicitação",
  reject: "Rejeitar",
};

/** Toast de sucesso após transição (frase completa, não «rótulo + concluído»). */
const ACTION_SUCCESS_MESSAGES: Record<string, string> = {
  start: "Atendimento iniciado.",
  return: "Solicitação devolvida para ajuste.",
  resubmit: "Solicitação reenviada.",
  complete: "Solicitação concluída.",
  issue: "Emissão registrada.",
  confirm_fulfillment: "Atendimento confirmado.",
  reject_fulfillment: "Atendimento devolvido para correção.",
  cancel: "Solicitação cancelada.",
  reject: "Solicitação rejeitada.",
};

const EVENT_LABELS: Record<string, string> = {
  created: "Solicitação criada",
  updated: "Dados atualizados",
  transition: "Etapa atualizada",
  transitioned: "Etapa atualizada",
  status_changed: "Status atualizado",
  commented: "Comentário adicionado",
  comment_added: "Comentário adicionado",
  attachment_added: "Documento anexado",
  attachment_removed: "Documento removido",
  artifact_added: "Documento gerado anexado",
  artifact_removed: "Documento gerado removido",
  resubmitted: "Reenviada",
  started: "Atendimento iniciado",
  returned: "Devolvida",
  issued: "Emitida",
  cancelled: "Cancelada",
};

const TRANSITION_EVENT_TYPES = new Set([
  "transition",
  "transitioned",
  "status_changed",
]);

function payloadText(
  payload: Record<string, unknown> | null | undefined,
  ...keys: string[]
): string {
  if (!payload) return "";
  for (const key of keys) {
    const value = payload[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return "";
}

/**
 * Prefer the action the user requested (alias like `issue`) over the
 * canonical transition action (`complete`). Legacy rows without
 * `action_requested` still get a sensible label when destination is known.
 */
function resolveTimelineActionCode(
  payload: Record<string, unknown> | null | undefined,
): string {
  const requested = payloadText(payload, "action_requested", "action");
  const toStatus = payloadText(payload, "to_status");
  if (
    requested === "complete" &&
    toStatus === "awaiting_requester_confirmation"
  ) {
    return "issue";
  }
  return requested;
}

function joinTimelineParts(parts: Array<string | null | undefined>): string {
  return parts
    .map((part) => (part || "").trim())
    .filter(Boolean)
    .join(" · ");
}

const BRANCH_SCOPE_LABELS: Record<string, string> = {
  required: "Filial obrigatória",
  optional: "Filial opcional",
  none: "Sem filial",
};

const PRESENTATION_MODE_LABELS: Record<string, string> = {
  specialized: "Formulário especializado",
  schema_driven: "Formulário configurável",
  generic: "Formulário genérico",
};

const ARTIFACT_KIND_LABELS: Record<string, string> = {
  generic: "Outro documento",
  invoice_pdf: "Nota fiscal — PDF",
};

const TYPE_NAME_FALLBACKS: Record<string, string> = {
  "invoice-issuance": "Emissão de Notas Fiscais",
  "raw-material-creation": "Criação de matéria-prima",
};

function humanizeCode(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return "—";
  return trimmed
    .replace(/[._-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^\w/, (c) => c.toUpperCase());
}

export function statusLabel(
  status: string | null | undefined,
  alias?: string | null,
): string {
  const preferred = (alias || "").trim();
  if (preferred && STATUS_LABELS[preferred]) return STATUS_LABELS[preferred];
  if (preferred && !/^[a-z0-9_:-]+$/i.test(preferred)) return preferred;
  const code = (status || preferred || "").trim();
  return STATUS_LABELS[code] || humanizeCode(code);
}

export function actionLabel(action: string): string {
  const code = action.trim();
  return ACTION_LABELS[code] || humanizeCode(code);
}

export function actionSuccessMessage(action: string): string {
  const code = action.trim();
  if (ACTION_SUCCESS_MESSAGES[code]) return ACTION_SUCCESS_MESSAGES[code];
  return `${actionLabel(code)} realizado com sucesso.`;
}

/** Variant hint for ActionButton — only kit-supported values. */
export function actionButtonVariant(
  action: string,
): "primary" | "ghost" | "default" {
  const code = action.trim();
  if (code === "cancel" || code === "reject" || code === "return") return "ghost";
  if (code === "reject_fulfillment") return "ghost";
  if (code === "view" || code === "edit") return "ghost";
  return "primary";
}

export function eventLabel(eventType: string | null | undefined): string {
  const code = (eventType || "").trim();
  return EVENT_LABELS[code] || humanizeCode(code);
}

/** Human-readable timeline title from event type + payload (API remains coded). */
export function timelineEventTitle(event: {
  event_type?: string | null;
  payload?: Record<string, unknown> | null;
}): string {
  const type = (event.event_type || "").trim();
  const payload = event.payload || null;

  if (TRANSITION_EVENT_TYPES.has(type)) {
    const actionCode = resolveTimelineActionCode(payload);
    const fromStatus = payloadText(payload, "from_status");
    const toStatus = payloadText(payload, "to_status");
    if (actionCode && toStatus) {
      return `${actionLabel(actionCode)} — ${statusLabel(toStatus)}`;
    }
    if (actionCode) return actionLabel(actionCode);
    if (fromStatus && toStatus) {
      return `${statusLabel(fromStatus)} → ${statusLabel(toStatus)}`;
    }
    return eventLabel(type);
  }

  if (type === "artifact_added" || type === "artifact_removed") {
    const name = payloadText(payload, "name");
    const kindRaw = payloadText(payload, "kind", "artifact_kind");
    const kind = kindRaw ? artifactKindLabel(kindRaw) : "";
    return joinTimelineParts([eventLabel(type), kind || null, name || null]);
  }

  if (type === "attachment_added" || type === "attachment_removed") {
    const name = payloadText(payload, "name");
    return joinTimelineParts([eventLabel(type), name || null]);
  }

  return eventLabel(type);
}

/** Optional reason shown under the actor for return/cancel/reject. */
export function timelineEventJustification(
  payload?: Record<string, unknown> | null,
): string | null {
  const text = payloadText(payload, "justification", "return_reason", "cancel_justification");
  return text || null;
}

export function branchScopeLabel(scope: string | null | undefined): string {
  const code = (scope || "").trim().toLowerCase();
  return BRANCH_SCOPE_LABELS[code] || humanizeCode(code);
}

export function presentationModeLabel(mode: string | null | undefined): string {
  const code = (mode || "").trim().toLowerCase();
  return PRESENTATION_MODE_LABELS[code] || humanizeCode(code);
}

export function artifactKindLabel(kind: string | null | undefined): string {
  const code = (kind || "").trim();
  return ARTIFACT_KIND_LABELS[code] || humanizeCode(code);
}

export function requestTypeLabel(
  typeCode: string | null | undefined,
  typeName?: string | null,
): string {
  const name = (typeName || "").trim();
  if (name) return name;
  const code = (typeCode || "").trim();
  return TYPE_NAME_FALLBACKS[code] || humanizeCode(code);
}

export function formatDateTimePtBr(value: string | null | undefined): string {
  const raw = (value || "").trim();
  if (!raw) return "—";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;
  const datePart = new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }).format(date);
  const timePart = new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
  return `${datePart} às ${timePart}`;
}

/** Creation time; when `updatedAt` is set, appends «editada às …». */
export function commentTimeLabel(
  createdAt: string | null | undefined,
  updatedAt?: string | null,
): string {
  const created = formatDateTimePtBr(createdAt);
  const editedRaw = (updatedAt || "").trim();
  if (!editedRaw) return created === "—" ? "" : created;
  const edited = formatDateTimePtBr(editedRaw);
  if (!created || created === "—") return `Editada às ${edited}`;
  return `${created} · editada às ${edited}`;
}

/** Options for list status filter — values stay technical for the API. */
export const REQUEST_STATUS_FILTER_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "submitted", label: STATUS_LABELS.submitted },
  { value: "in_progress", label: STATUS_LABELS.in_progress },
  { value: "needs_information", label: STATUS_LABELS.needs_information },
  { value: "awaiting_requester_confirmation", label: STATUS_LABELS.awaiting_requester_confirmation },
  { value: "completed", label: STATUS_LABELS.completed },
  { value: "cancelled", label: STATUS_LABELS.cancelled },
  { value: "rejected", label: STATUS_LABELS.rejected },
] as const;

export const ARTIFACT_KIND_OPTIONS = [
  { value: "generic", label: ARTIFACT_KIND_LABELS.generic },
  { value: "invoice_pdf", label: ARTIFACT_KIND_LABELS.invoice_pdf },
] as const;
