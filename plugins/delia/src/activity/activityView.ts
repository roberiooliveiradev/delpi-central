import type {
  ActivitySourceView,
  ActivityState,
  ActivityStepView,
  ActivityViewerProps,
} from "@delpi/plugin-ui/index";

import type { ConversationDisplayTurn } from "../ui/ConversationTimeline";

/**
 * DÉLIA → ActivityViewer adapter (DELIA-UX-ACTIVITY-01).
 *
 * Maps only contract fields that actually exist on a completed turn:
 * `presentation.messageKind`, `groundingStatus`, `provenance` and
 * `limitations`. It never reconstructs tool sequences that were not
 * recorded, never infers state from HTTP status, never invents
 * timestamps/durations, and never branches on provider names.
 * Everything produced here is presentation — never authority.
 */

export const DELIA_ACTIVITY_PENDING_TITLE =
  "A DÉLIA está processando sua solicitação…";

/** Running summary for an in-flight turn — deliberately free of any
 *  provider/tool/specialist claim. */
export const DELIA_ACTIVITY_PENDING_VIEW: ActivityViewerProps = {
  title: DELIA_ACTIVITY_PENDING_TITLE,
  state: "running",
};

type ActivityOutcomeTone =
  | "neutral"
  | "info"
  | "success"
  | "warning"
  | "danger";

const OUTCOME_BY_KIND: Record<
  string,
  { state: ActivityState; label: string; tone?: ActivityOutcomeTone }
> = {
  CLARIFICATION_REQUIRED: {
    state: "completed",
    label: "A solicitação precisa de esclarecimento.",
    tone: "info",
  },
  CONFIRMATION_REQUIRED: {
    state: "pending",
    label: "Aguardando uma decisão governada do usuário.",
    tone: "warning",
  },
  AUTHZ_DENIED: {
    state: "denied",
    label: "Autorização negada para esta operação.",
    tone: "danger",
  },
  WRITE_REJECTED: {
    state: "denied",
    label: "Operação recusada pela política vigente.",
    tone: "danger",
  },
  SOURCE_UNAVAILABLE: {
    state: "blocked",
    label: "A fonte necessária está indisponível no momento.",
    tone: "warning",
  },
  PRECONDITION_REQUIRED: {
    state: "blocked",
    label: "A fonte informou uma pré-condição necessária.",
    tone: "warning",
  },
};

const TITLE_BY_STATE: Record<ActivityState, string> = {
  pending: "Aguardando decisão",
  running: "A DÉLIA está processando sua solicitação…",
  completed: "Atividade concluída",
  partial: "Atividade parcialmente concluída",
  blocked: "Atividade bloqueada",
  denied: "Atividade não autorizada",
  failed: "Atividade não concluída",
  cancelled: "Atividade cancelada",
  no_data: "Atividade sem dados",
};

function formatObservedAt(value: string | undefined | null): string | undefined {
  if (!value) return undefined;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return undefined;
  return date.toLocaleString("pt-BR");
}

/**
 * Builds the visual activity projection for a completed DÉLIA turn.
 * Returns the summary + only the details the contract legitimately
 * provides; a bare RESULT still yields an expandable view because the
 * honest minimal steps (recebida/elaborada) are true by construction.
 */
export function buildDeliaActivityView(
  turn: ConversationDisplayTurn,
): ActivityViewerProps | null {
  if (turn.role !== "delia") return null;
  if (turn.activityView) return turn.activityView;

  const kind = turn.presentation?.messageKind ?? "RESULT";
  const mapping = OUTCOME_BY_KIND[kind];
  const state: ActivityState = mapping?.state ?? "completed";

  const steps: ActivityStepView[] = [
    { id: "received", label: "Solicitação recebida", state: "completed" },
  ];
  const sources: ActivitySourceView[] = [];

  const provenance = turn.provenance;
  if (provenance) {
    const capabilityLabel = provenance.remote_capability;
    const sourceLabel = provenance.specialist_id;
    if (capabilityLabel || sourceLabel) {
      steps.push({
        id: "capability",
        label: "Capacidade acionada",
        state: provenance.is_complete === false ? "partial" : "completed",
        capabilityLabel,
        sourceLabel,
      });
    }
    if (provenance.source) {
      const source = provenance.source;
      steps.push({
        id: "source",
        label: "Fonte consultada",
        state: provenance.is_complete === false ? "partial" : "completed",
        sourceLabel: source.source_system || source.source_id,
        timestampLabel: formatObservedAt(source.observed_at),
      });
      sources.push({
        id: source.source_id || "source",
        label: source.source_system || source.source_id,
        statusLabel:
          turn.groundingStatus === "GROUNDED"
            ? "resultado fundamentado"
            : "consultada",
        detail:
          [
            provenance.protocol
              ? `protocolo ${provenance.protocol}`
              : null,
            formatObservedAt(source.observed_at)
              ? `observado em ${formatObservedAt(source.observed_at)}`
              : null,
          ]
            .filter(Boolean)
            .join(" · ") || undefined,
      });
    }
  }

  steps.push({
    id: "answered",
    label:
      state === "completed" || state === "pending"
        ? "Resposta elaborada"
        : "Resposta registrada",
    state: "completed",
  });

  return {
    title: TITLE_BY_STATE[state],
    state,
    steps,
    sources: sources.length > 0 ? sources : undefined,
    outcome: mapping
      ? {
          label: mapping.label,
          tone: mapping.tone,
          persistent: true,
        }
      : turn.groundingStatus === "GROUNDED" && provenance
        ? {
            label: "Resultado fundamentado na fonte consultada.",
            tone: "success",
          }
        : undefined,
  };
}
