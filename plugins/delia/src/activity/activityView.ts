import type {
  ActivitySourceView,
  ActivityState,
  ActivityStepView,
  ActivityViewerProps,
} from "@delpi/plugin-ui/index";

import type { DeliaActivityEvent } from "../api/interactionClient";
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

// ---------------------------------------------------------------------
// Progressive activity (ActivityEvent.v1 → ActivityViewerProps, doc 70
// §16). Every step below is a real observed event — the adapter only
// translates the closed backend vocabulary into pt-BR labels and never
// fabricates steps, durations or provider claims.
// ---------------------------------------------------------------------

/** Backend event state → render-only ActivityViewer state. */
const LIVE_STATE: Record<string, ActivityState> = {
  running: "running",
  completed: "completed",
  partial: "partial",
  failed: "failed",
  blocked: "blocked",
  denied: "denied",
  cancelled: "cancelled",
  waiting: "pending",
  no_data: "no_data",
};

const LIVE_STEP_LABEL: Record<string, string> = {
  REQUEST_RECEIVED: "Solicitação recebida",
  CONTEXTUALIZING: "Entendendo a solicitação",
  CONTINUING: "Continuando a consulta",
  CAPABILITY_SELECTED: "Capacidade selecionada",
  SOURCE_QUERY_STARTED: "Consultando especialista",
  SOURCE_QUERY_COMPLETED: "Consulta finalizada",
  OUTCOME_PREPARING: "Organizando a resposta",
  WAITING_CONFIRMATION: "Aguardando decisão",
  COMPLETED: "Atividade concluída",
  PARTIAL: "Atividade parcialmente concluída",
  BLOCKED: "Atividade bloqueada",
  FAILED: "Não foi possível concluir a consulta",
  CANCELLED: "Interação interrompida",
};

const LIVE_TITLE: Record<string, string> = {
  REQUEST_RECEIVED: "Solicitação recebida",
  CONTEXTUALIZING: "Entendendo sua solicitação…",
  CONTINUING: "Continuando sua consulta…",
  CAPABILITY_SELECTED: "Capacidade selecionada",
  SOURCE_QUERY_STARTED: "Consultando fonte autorizada…",
  SOURCE_QUERY_COMPLETED: "Consulta finalizada",
  OUTCOME_PREPARING: "Organizando a resposta…",
  WAITING_CONFIRMATION: "Aguardando uma decisão governada",
  COMPLETED: "Atividade concluída",
  PARTIAL: "Atividade parcialmente concluída",
  BLOCKED: "Atividade bloqueada",
  FAILED: "Atividade não concluída",
  CANCELLED: "Atividade cancelada",
};

function liveOutcomeLabel(event: DeliaActivityEvent): string | undefined {
  const outcome = event.outcome_ref;
  if (!outcome) return undefined;
  switch (outcome.status) {
    case "returned_data":
      return typeof outcome.record_count === "number"
        ? `${outcome.record_count} registro(s) localizado(s)`
        : "dados retornados pela fonte";
    case "completed_no_data":
      return "consulta concluída sem dados";
    case "partial":
      return "resultado parcial";
    case "error":
      return "consulta falhou";
    default:
      return undefined;
  }
}

/**
 * Reduces the observed ActivityEvent.v1 sequence into the render-only
 * ActivityViewer projection. Returns null when there is nothing real
 * to show — the generic pending label stays as the honest fallback.
 */
export function buildLiveActivityView(
  events: readonly DeliaActivityEvent[],
): ActivityViewerProps | null {
  if (!events.length) return null;

  const steps: ActivityStepView[] = [];
  const sources: ActivitySourceView[] = [];
  const seenSources = new Set<string>();
  let lastTerminal: DeliaActivityEvent | null = null;
  let openQueryIndex = -1;

  const closeRunningSteps = () => {
    for (const step of steps) {
      if (step.state === "running") step.state = "completed";
    }
    openQueryIndex = -1;
  };

  for (const event of events) {
    const state = LIVE_STATE[event.state] ?? "running";
    const label = LIVE_STEP_LABEL[event.phase] ?? event.phase;
    switch (event.phase) {
      case "REQUEST_RECEIVED":
        steps.push({ id: `ev-${event.sequence}`, label, state });
        break;
      case "CONTEXTUALIZING":
      case "CONTINUING":
      case "OUTCOME_PREPARING": {
        closeRunningSteps();
        steps.push({ id: `ev-${event.sequence}`, label, state });
        break;
      }
      case "CAPABILITY_SELECTED": {
        closeRunningSteps();
        steps.push({
          id: `ev-${event.sequence}`,
          label,
          state,
          // `capability_ref.remote_name`/`protocol` are technical
          // control-plane identifiers — never surfaced as labels (doc 79
          // §8). The owner display name is the legitimate user-facing
          // source label.
          sourceLabel: event.owner_ref?.display_name,
        });
        break;
      }
      case "SOURCE_QUERY_STARTED": {
        closeRunningSteps();
        steps.push({
          id: `ev-${event.sequence}`,
          label,
          state: "running",
          sourceLabel: event.owner_ref?.display_name,
        });
        openQueryIndex = steps.length - 1;
        break;
      }
      case "SOURCE_QUERY_COMPLETED": {
        const outcomeLabel = liveOutcomeLabel(event);
        const step: ActivityStepView = {
          id: `ev-${event.sequence}`,
          label,
          state,
          sourceLabel:
            event.source_ref?.source_system ??
            event.owner_ref?.display_name,
          description: outcomeLabel,
        };
        if (openQueryIndex >= 0) {
          // Completion resolves its own query step in place — the
          // started step becomes the observed finished step.
          const started = steps[openQueryIndex];
          steps[openQueryIndex] = {
            ...started,
            label,
            state,
            description: outcomeLabel,
            sourceLabel:
              event.source_ref?.source_system ?? started.sourceLabel,
          };
          openQueryIndex = -1;
        } else {
          steps.push(step);
        }
        if (event.source_ref && !seenSources.has(event.source_ref.source_id ?? event.source_ref.source_system ?? "")) {
          const key =
            event.source_ref.source_id ??
            event.source_ref.source_system ??
            `src-${sources.length}`;
          seenSources.add(key);
          sources.push({
            id: key,
            label:
              event.source_ref.source_system ??
              event.source_ref.source_id ??
              "fonte",
            statusLabel: outcomeLabel,
          });
        }
        break;
      }
      case "WAITING_CONFIRMATION":
      case "COMPLETED":
      case "PARTIAL":
      case "BLOCKED":
      case "FAILED":
      case "CANCELLED": {
        closeRunningSteps();
        steps.push({ id: `ev-${event.sequence}`, label, state });
        lastTerminal = event;
        break;
      }
      default:
        break;
    }
  }

  const state: ActivityState = lastTerminal
    ? (LIVE_STATE[lastTerminal.state] ?? "completed")
    : "running";

  const lastEvent = events[events.length - 1];
  const title =
    (lastTerminal
      ? LIVE_TITLE[lastTerminal.phase]
      : LIVE_TITLE[lastEvent.phase]) ?? TITLE_BY_STATE[state];

  const outcomeEvent = lastTerminal ?? lastEvent;
  const outcomeLabel =
    outcomeEvent.phase === "BLOCKED" && outcomeEvent.state === "denied"
      ? "Operação não autorizada ou recusada."
      : outcomeEvent.phase === "FAILED"
        ? "Não foi possível concluir a solicitação."
        : outcomeEvent.phase === "PARTIAL"
          ? "Parte da consulta não respondeu."
          : liveOutcomeLabel(outcomeEvent);

  return {
    title,
    state,
    steps: steps.length ? steps : undefined,
    sources: sources.length ? sources : undefined,
    outcome: outcomeLabel
      ? {
          label: outcomeLabel,
          tone:
            state === "denied" || state === "failed"
              ? "danger"
              : state === "blocked" || state === "partial"
                ? "warning"
                : state === "completed"
                  ? "success"
                  : "neutral",
          persistent:
            state === "denied" ||
            state === "failed" ||
            state === "blocked",
        }
      : undefined,
  };
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
    // `remote_capability`/`protocol` are technical identifiers — the
    // step keeps the honest label plus the legitimately known
    // specialist name only (doc 79 §8).
    const sourceLabel = provenance.specialist_id;
    if (sourceLabel) {
      steps.push({
        id: "capability",
        label: "Capacidade acionada",
        state: provenance.is_complete === false ? "partial" : "completed",
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
        detail: formatObservedAt(source.observed_at)
          ? `observado em ${formatObservedAt(source.observed_at)}`
          : undefined,
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
