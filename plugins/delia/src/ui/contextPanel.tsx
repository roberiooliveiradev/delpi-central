import type { ReactNode } from "react";

import {
  ActivityViewer,
  ConversationContextPanel,
  EvidenceDetails,
} from "@delpi/plugin-ui/index";
import type { ActivityViewerProps } from "@delpi/plugin-ui/index";

import type { DeliaTurnObservability } from "../api/interactionClient";
import type { ConversationDisplayTurn } from "./ConversationTimeline";

export type DeliaTurnContextPanelProps = {
  turn: ConversationDisplayTurn | null;
};

/** Present observed event time on the matching real step — the
 *  `ev-{sequence}` ids come straight from buildLiveActivityView, so a
 *  timestamp is shown only for an event that actually arrived. */
function withObservedTimestamps(
  view: ActivityViewerProps | undefined,
  turn: ConversationDisplayTurn,
): ActivityViewerProps | undefined {
  if (!view || !turn.activityEvents?.length) return view;
  const byId = new Map(
    turn.activityEvents.map((event) => [`ev-${event.sequence}`, event]),
  );
  const format = (iso: string): string | undefined => {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return undefined;
    return new Intl.DateTimeFormat("pt-BR", {
      timeStyle: "medium",
    }).format(date);
  };
  return {
    ...view,
    steps: (view.steps ?? []).map((step) => {
      const event = byId.get(step.id);
      const label = event ? format(event.timestamp) : undefined;
      return label ? { ...step, timestampLabel: label } : step;
    }),
  };
}

function formatDurationMs(ms: number | null | undefined): string | null {
  if (typeof ms !== "number" || ms < 0) return null;
  if (ms < 1000) return `${ms} ms`;
  const seconds = ms / 1000;
  if (seconds < 60) return `${seconds.toFixed(1)} s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes} min ${Math.round(seconds % 60)} s`;
}

function compositionLabel(mode: string | null | undefined): string {
  switch (mode) {
    case "cri":
      return "Resposta organizada com CRI";
    case "model":
      return "Resposta gerada pelo modelo";
    case "deterministic":
      return "Apresentação determinística";
    default:
      return "Não informado";
  }
}

function tokensLabel(tokens: DeliaTurnObservability["tokens"]): string {
  const input =
    tokens.input != null ? `${tokens.input} de entrada` : null;
  const output =
    tokens.output != null ? `${tokens.output} de saída` : null;
  const parts = [input, output].filter(Boolean).join(" · ");
  if (tokens.status === "reported") {
    return tokens.total != null
      ? `${parts} (total ${tokens.total})`
      : parts || "Não informado pelo provider";
  }
  if (tokens.status === "partial") {
    return parts
      ? `${parts} — dados parciais`
      : "Dados parciais informados pelo provider";
  }
  return "Não informado pelo provider";
}

function row(label: string, value: ReactNode): ReactNode {
  if (value == null || value === "") return null;
  return (
    <div className="delia-context__row" key={label}>
      <dt className="delia-context__term">{label}</dt>
      <dd className="delia-context__value">{value}</dd>
    </div>
  );
}

function timeoutSourceLabel(source: string | null): string | null {
  switch (source) {
    case "model":
      return "Tempo do modelo esgotado";
    case "budget":
      return "Orçamento do turno esgotado";
    case "capability":
      return "Tempo da consulta à fonte esgotado";
    case "cancelled":
      return "Cancelado";
    default:
      return null;
  }
}

function DetailRows({ turn }: { turn: ConversationDisplayTurn }) {
  const obs = turn.observability;
  const provenance = turn.provenance;
  const duration = formatDurationMs(obs?.duration_ms);
  const semanticLabel =
    turn.groundingStatus === "GROUNDED"
      ? "Resposta com fonte vinculada"
      : turn.groundingStatus === "NON_GROUNDED"
        ? "Resposta sem fonte vinculada"
        : null;
  return (
    <dl className="delia-context__list">
      {row("Estado", semanticLabel)}
      {row(
        "Especialista",
        provenance?.specialist_id ?? undefined,
      )}
      {row("Capability", provenance?.remote_capability ?? undefined)}
      {row("Composição", compositionLabel(obs?.composition_mode))}
      {row(
        "Modelo",
        obs?.model?.id
          ? `${obs.model.id}${obs.model.version ? ` (${obs.model.version})` : ""}`
          : undefined,
      )}
      {row("Responsável pelo modelo", obs?.model?.owner ?? undefined)}
      {row("Tempo total", duration)}
      {row(
        "Chamadas ao modelo",
        obs != null ? String(obs.model_calls) : undefined,
      )}
      {row(
        "Tentativas governadas",
        obs?.governed_attempts != null && obs.governed_attempts > 1
          ? String(obs.governed_attempts)
          : undefined,
      )}
      {row(
        "Tempo no modelo",
        obs?.elapsed_ms?.model != null
          ? formatDurationMs(obs.elapsed_ms.model)
          : undefined,
      )}
      {row(
        "Tempo na fonte",
        obs?.elapsed_ms?.operational != null && obs.elapsed_ms.operational > 0
          ? formatDurationMs(obs.elapsed_ms.operational)
          : undefined,
      )}
      {row(
        "Encerramento",
        timeoutSourceLabel(obs?.timeout_source ?? null),
      )}
      {row("Tokens", obs ? tokensLabel(obs.tokens) : undefined)}
      {row(
        "Custo",
        obs?.cost?.status === "unavailable"
          ? "Custo indisponível"
          : undefined,
      )}
    </dl>
  );
}

function ModelCalls({ obs }: { obs: DeliaTurnObservability }) {
  if (!obs.calls.length) return null;
  return (
    <ul className="delia-context__calls">
      {obs.calls.map((call, index) => {
        const duration = formatDurationMs(call.duration_ms);
        const usage =
          call.input_tokens != null || call.output_tokens != null
            ? `E ${call.input_tokens ?? "—"} · S ${call.output_tokens ?? "—"}`
            : null;
        return (
          <li key={`${call.stage}-${index}`} className="delia-context__call">
            <span className="delia-context__call-stage">{call.stage ?? "estágio"}</span>
            <span className="delia-context__call-meta">
              {[
                call.attempt != null && call.attempt > 1
                  ? `tentativa ${call.attempt}`
                  : null,
                call.finish_status === "completed" ? null : call.finish_status,
                duration,
                usage,
              ]
                .filter(Boolean)
                .join(" · ")}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

function EvidenceSection({ turn }: { turn: ConversationDisplayTurn }) {
  const source = turn.provenance?.source;
  const observedLabel = source?.observed_at
    ? new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
      }).format(new Date(source.observed_at))
    : null;
  const sourceSummary = source
    ? `Fonte · ${source.source_system || source.source_id}${
        observedLabel ? ` · consultado em ${observedLabel}` : ""
      }`
    : turn.groundingStatus === "NON_GROUNDED"
      ? "Sem fonte vinculada"
      : undefined;
  const items = source
    ? [
        { label: "Sistema", value: source.source_system ?? "" },
        { label: "Identificador", value: source.source_id ?? "" },
      ].filter((item) => item.value)
    : [];
  const hasContent =
    Boolean(sourceSummary) || items.length > 0 ||
    (turn.limitations?.length ?? 0) > 0;
  if (!hasContent) return null;
  return (
    <EvidenceDetails
      sourceSummary={sourceSummary}
      items={items}
      limitations={turn.limitations}
    />
  );
}

/**
 * Prompt 5 — Context panel bound to a REAL selected message. Render-only:
 * every value arrives via the existing turn_result projection and the
 * observed activity events already kept on the turn; nothing is
 * inferred, estimated, or fetched separately. Absent data stays absent
 * (honest "Não informado" labels), and no authority is surfaced —
 * model metadata never grants permission.
 */
export function DeliaTurnContextPanel({ turn }: DeliaTurnContextPanelProps) {
  if (turn == null || turn.role !== "delia") {
    return <ConversationContextPanel />;
  }
  const activityView = withObservedTimestamps(
    turn.activityView,
    turn,
  );
  const obs = turn.observability;
  return (
    <ConversationContextPanel
      details={
        <>
          <DetailRows turn={turn} />
          {obs ? <ModelCalls obs={obs} /> : null}
        </>
      }
      evidence={<EvidenceSection turn={turn} />}
      activities={
        activityView ? (
          <ActivityViewer
            {...activityView}
            durationLabel={
              formatDurationMs(obs?.duration_ms) ?? activityView.durationLabel
            }
          />
        ) : null
      }
    />
  );
}
