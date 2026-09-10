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
  issue: "Registrar emissão",
  cancel: "Cancelar solicitação",
  reject: "Rejeitar",
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
  resubmitted: "Reenviada",
  started: "Atendimento iniciado",
  returned: "Devolvida",
  issued: "Emitida",
  cancelled: "Cancelada",
};

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

/** Variant hint for ActionButton — only kit-supported values. */
export function actionButtonVariant(
  action: string,
): "primary" | "ghost" | "default" {
  const code = action.trim();
  if (code === "cancel" || code === "reject" || code === "return") return "ghost";
  if (code === "view" || code === "edit") return "ghost";
  return "primary";
}

export function eventLabel(eventType: string | null | undefined): string {
  const code = (eventType || "").trim();
  return EVENT_LABELS[code] || humanizeCode(code);
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

/** Options for list status filter — values stay technical for the API. */
export const REQUEST_STATUS_FILTER_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "submitted", label: STATUS_LABELS.submitted },
  { value: "in_progress", label: STATUS_LABELS.in_progress },
  { value: "needs_information", label: STATUS_LABELS.needs_information },
  { value: "completed", label: STATUS_LABELS.completed },
  { value: "cancelled", label: STATUS_LABELS.cancelled },
  { value: "rejected", label: STATUS_LABELS.rejected },
] as const;

export const ARTIFACT_KIND_OPTIONS = [
  { value: "generic", label: ARTIFACT_KIND_LABELS.generic },
  { value: "invoice_pdf", label: ARTIFACT_KIND_LABELS.invoice_pdf },
] as const;
