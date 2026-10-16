/**
 * DÉLIA interaction API client — C3-INTERACTION-RUNTIME-01.
 *
 * Smallest client for the bounded vertical slice: POST /interaction/turns
 * against the delia-api gateway base path. The bearer token is fetched
 * from the Portal host per request and is never stored, decoded, or
 * logged. No business-domain API is exposed here.
 */

import { parsePresentation } from "./presentation";
import type { DeliaPresentation } from "./presentation";

export const DELIA_API_BASE = "/apps/delia-api";
export const DELIA_INTERACTION_TURNS_PATH = "/interaction/turns";

/**
 * ActivityEvent.v1 — bounded semantic observation of an in-flight
 * turn (doc 70 §16). Presentation only: an event is an observation,
 * never authority — it cannot grant access, authorize writes, or
 * override the final `turn_result`.
 */
export type DeliaActivityEvent = {
  version: "1";
  event_id: string;
  sequence: number;
  timestamp: string;
  session_id: string;
  turn_id: string;
  phase: string;
  state: string;
  label_code: string;
  correlation_id?: string;
  capability_ref?: {
    remote_name?: string;
    protocol?: string;
    operation_class?: string;
  };
  source_ref?: { source_id?: string; source_system?: string };
  owner_ref?: { display_name?: string; owner_ref?: string };
  outcome_ref?: { status: string; record_count?: number };
};

/** Closed wire vocabulary (doc 70 §16). */
const ACTIVITY_PHASES = new Set([
  "REQUEST_RECEIVED",
  "CONTEXTUALIZING",
  "CAPABILITY_SELECTED",
  "SOURCE_QUERY_STARTED",
  "SOURCE_QUERY_COMPLETED",
  "OUTCOME_PREPARING",
  "WAITING_CONFIRMATION",
  "COMPLETED",
  "PARTIAL",
  "BLOCKED",
  "FAILED",
  "CANCELLED",
]);

const ACTIVITY_STATES = new Set([
  "running",
  "completed",
  "partial",
  "failed",
  "blocked",
  "denied",
  "cancelled",
  "waiting",
  "no_data",
]);

const ACTIVITY_OUTCOME_STATUSES = new Set([
  "returned_data",
  "completed_no_data",
  "partial",
  "error",
]);

/** Client-side bounds — a stream can never grow state unboundedly. */
export const ACTIVITY_STREAM_MAX_EVENTS = 64;
export const ACTIVITY_STREAM_MAX_LINE_CHARS = 32_768;

/**
 * Provider-neutral prior-turn context for POST /interaction/turns.
 *
 * Transient UI memory only — built from turns currently rendered on
 * screen. Never carries authority, secrets, provider metadata, or FACT
 * epistemic class.
 */
export type InteractionContextTurn = {
  kind: "USER_INPUT" | "DELIA_RESULT";
  content: string;
  epistemic_class?: string;
};

/**
 * Aggregate context budget mirrors the delia-api bound
 * (MAX_INPUT_CHARS = 16384). The backend remains the enforcing
 * authority; the client only picks a deterministic recent window of
 * complete USER_INPUT/DELIA_RESULT pairs so the request stays bounded.
 * No truncation of individual turns, no summarization.
 */
export const INTERACTION_CONTEXT_CHAR_BUDGET = 16_384;

/**
 * Per-input bound mirrors the delia-api bound enforced on
 * `request.input` (MAX_INPUT_CHARS = 16384, fail-closed). The backend
 * remains the enforcing authority; the client exposes the number only
 * to render an honest character counter — never to authorize.
 */
export const INTERACTION_INPUT_CHAR_LIMIT = 16_384;

export function buildInteractionContext(
  turns: ReadonlyArray<{
    role: "user" | "delia";
    content: string;
    epistemicClass?: string | null;
  }>,
): InteractionContextTurn[] {
  const selected: InteractionContextTurn[] = [];
  let used = 0;
  for (let end = turns.length; end >= 2; end -= 2) {
    const delia = turns[end - 1];
    const user = turns[end - 2];
    if (delia.role !== "delia" || user.role !== "user") break;
    const cost = user.content.length + delia.content.length;
    if (used + cost > INTERACTION_CONTEXT_CHAR_BUDGET) break;
    selected.unshift(
      { kind: "USER_INPUT", content: user.content },
      {
        kind: "DELIA_RESULT",
        content: delia.content,
        ...(delia.epistemicClass
          ? { epistemic_class: delia.epistemicClass }
          : {}),
      },
    );
    used += cost;
  }
  return selected;
}

/**
 * Bounded provenance projection of a grounded governed read
 * (C4-MCP-GOVERNED-READS-01). Presentation only — never authority.
 */
export type DeliaInteractionProvenance = {
  source?: {
    source_id: string;
    source_system: string;
    observed_at?: string | null;
  } | null;
  specialist_id?: string;
  protocol?: string;
  remote_capability?: string;
  action_id?: string;
  observed_at?: string;
  correlation_id?: string;
  is_complete?: boolean;
};

/**
 * Bounded confirmation surface emitted when a governed write awaits a
 * structured user decision (ledger §6.126). Presentation/echo only:
 * the MFE carries the non-reversible digests back verbatim on the
 * confirmation turn — it never sees, stores, or derives the raw owner
 * proposal handle, and never decides anything itself.
 */
export type DeliaConfirmationRequest = {
  session_id: string;
  capability_ref?: string;
  proposal_digest: string;
  preview_fingerprint: string;
  expires_at_epoch?: number;
  /** Why the proposal awaits a bound decision (§6.184):
   *  `execution_scope_choice` — the owner declared no additional
   *  confirmation, so Executar is the user's scope choice only;
   *  `execution_scope_plus_owner_confirmation` — the same Executar
   *  also satisfies the owner-required confirmation. Presentation
   *  copy only — never authority. */
  pending_purpose?:
    | "execution_scope_choice"
    | "execution_scope_plus_owner_confirmation";
};

/** Structured decision echoed back on a confirmation turn. */
export type DeliaConfirmationDecision = {
  decision: "CONFIRM" | "REJECT";
  proposal_digest: string;
  preview_fingerprint: string;
  session_id: string;
};

/**
 * Typed turn command (§6.184): MESSAGE carries free text and can
 * never reach material ACT in the same turn; APPLY_PREPARED /
 * REJECT_PREPARED are bound decision commands carrying NO free text —
 * the `confirmation` payload alone binds them to the exact pending
 * proposal. The client sends commands verbatim; it never invents
 * scope.
 */
export type DeliaTurnCommand =
  | { type: "MESSAGE" }
  | { type: "APPLY_PREPARED" }
  | { type: "REJECT_PREPARED" };

export type DeliaInteractionResult = {
  session_id: string;
  user_turn_id: string;
  result_turn_id: string;
  content: string;
  epistemic_class: string | null;
  limitations: string[];
  generated_at: string;
  model_invocation_id: string;
  grounding_status: "GROUNDED" | "NON_GROUNDED" | null;
  provenance: DeliaInteractionProvenance | null;
  confirmation_request: DeliaConfirmationRequest | null;
  /** Additive presentation.v1 projection — null for legacy/malformed/
   *  unknown-version payloads; never authority. */
  presentation: DeliaPresentation | null;
};

export class DeliaInteractionError extends Error {
  readonly code: string;

  constructor(code: string, message: string) {
    super(message);
    this.name = "DeliaInteractionError";
    this.code = code;
  }
}

const ERROR_MESSAGES: Record<string, string> = {
  unauthenticated: "Sessão inválida ou expirada. Entre novamente.",
  authority_unavailable: "Serviço de autorização indisponível no momento.",
  forbidden: "Acesso à DÉLIA não autorizado para este usuário.",
  invalid_request: "Pedido inválido.",
  model_unavailable: "Serviço de interação indisponível no momento.",
  model_timeout: "A resposta demorou demais. Tente novamente.",
  context_too_large:
    "O contexto da conversa ficou grande demais para ser enviado.",
  invalid_model_output: "Resposta da DÉLIA inválida.",
  forbidden_model_output: "Resposta da DÉLIA bloqueada por política.",
  internal_error: "Erro interno. Tente novamente.",
};

/**
 * Bounded workspace hint published by the host app through the Portal
 * (§6.130). Transient and untrusted: host app identity, route/view
 * and entity references only — never authority, secrets, or provider
 * payloads. The backend resolves and enforces.
 */
export type DeliaWorkspaceEntityRef = {
  entity_type: string;
  entity_id: string;
  source_system: string;
  label?: string;
};

export type DeliaWorkspaceContext = {
  host_app_id: string;
  route?: string;
  view_ref?: string;
  selected_entity_ref?: DeliaWorkspaceEntityRef;
  entity_refs?: DeliaWorkspaceEntityRef[];
};

export type SubmitInteractionTurnOptions = {
  getAccessToken: () => string | undefined;
  signal?: AbortSignal;
  /** Bounded prior-turn context built from transient UI state. */
  context?: InteractionContextTurn[];
  /** Bounded untrusted workspace hint from the host app. */
  workspace?: DeliaWorkspaceContext;
  /** Structured confirmation for a pending write (digests only). */
  confirmation?: DeliaConfirmationDecision;
  /** Typed turn command (§6.184). Decision commands carry no free
   *  text — `input` is omitted from the wire for APPLY/REJECT. */
  command?: DeliaTurnCommand;
  /** Progressive activity observations (ActivityEvent.v1). Called at
   *  most once per accepted event, in sequence order, while the turn
   *  still runs. Presentation only — never authorization. */
  onActivityEvent?: (event: DeliaActivityEvent) => void;
};

export async function submitInteractionTurn(
  input: string,
  options: SubmitInteractionTurnOptions,
): Promise<DeliaInteractionResult> {
  const token = options.getAccessToken();
  if (!token) {
    throw new DeliaInteractionError(
      "unauthenticated",
      ERROR_MESSAGES.unauthenticated,
    );
  }

  let response: Response;
  try {
    response = await fetch(`${DELIA_API_BASE}${DELIA_INTERACTION_TURNS_PATH}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // Opt-in progressive transport (doc 70 §16): a server that does
        // not stream simply answers the legacy JSON body — the same
        // request doubles as the fallback, never re-sent.
        Accept: "application/x-ndjson, application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        // Decision commands are bound decisions, not messages — free
        // text must never ride on APPLY_PREPARED/REJECT_PREPARED.
        ...(options.command?.type === "APPLY_PREPARED" ||
        options.command?.type === "REJECT_PREPARED"
          ? {}
          : { input }),
        ...(options.command ? { command: options.command } : {}),
        ...(options.context && options.context.length > 0
          ? { context: options.context }
          : {}),
        ...(options.workspace ? { workspace: options.workspace } : {}),
        ...(options.confirmation
          ? { confirmation: options.confirmation }
          : {}),
      }),
      signal: options.signal ?? null,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw error;
    }
    throw new DeliaInteractionError(
      "network_error",
      "Falha de comunicação com a DÉLIA.",
    );
  }

  const contentType = response.headers.get("content-type") ?? "";

  if (response.ok && contentType.includes("application/x-ndjson")) {
    return readNdjsonTurnStream(response, options.onActivityEvent);
  }

  const payload = (await response
    .json()
    .catch(() => null)) as Record<string, unknown> | null;

  if (!response.ok) {
    const code =
      typeof payload?.code === "string" ? payload.code : "internal_error";
    throw new DeliaInteractionError(
      code,
      ERROR_MESSAGES[code] ?? `Erro HTTP ${response.status}`,
    );
  }

  return parseInteractionResultPayload(payload);
}

function parseInteractionResultPayload(
  payload: Record<string, unknown> | null,
): DeliaInteractionResult {
  if (
    !payload ||
    typeof payload.content !== "string" ||
    typeof payload.session_id !== "string" ||
    typeof payload.user_turn_id !== "string" ||
    typeof payload.result_turn_id !== "string"
  ) {
    throw new DeliaInteractionError(
      "invalid_response",
      "Resposta da DÉLIA inválida.",
    );
  }

  return {
    session_id: payload.session_id,
    user_turn_id: payload.user_turn_id,
    result_turn_id: payload.result_turn_id,
    content: payload.content,
    epistemic_class:
      typeof payload.epistemic_class === "string"
        ? payload.epistemic_class
        : null,
    limitations: Array.isArray(payload.limitations)
      ? payload.limitations.filter(
          (item): item is string => typeof item === "string",
        )
      : [],
    generated_at:
      typeof payload.generated_at === "string" ? payload.generated_at : "",
    model_invocation_id:
      typeof payload.model_invocation_id === "string"
        ? payload.model_invocation_id
        : "",
    grounding_status:
      payload.grounding_status === "GROUNDED" ||
      payload.grounding_status === "NON_GROUNDED"
        ? payload.grounding_status
        : null,
    provenance:
      payload.provenance &&
      typeof payload.provenance === "object"
        ? (payload.provenance as DeliaInteractionProvenance)
        : null,
    confirmation_request: parseConfirmationRequest(
      payload.confirmation_request,
    ),
    presentation: parsePresentation(payload.presentation),
  };
}

/**
 * Incremental NDJSON consumer for the progressive transport.
 *
 * Semantics (doc 70 §16): the stream is a sequence of `activity_event`
 * records followed by exactly one terminal `turn_result` or
 * `turn_error`. The parser tolerates arbitrarily split chunks and
 * UTF-8 boundaries, deduplicates/order-enforces by `sequence`,
 * drops malformed non-terminal lines (presentation-only data), bounds
 * the event count and line size, and fails closed when no terminal
 * record arrives — an HTTP-200 stream is never mistaken for a
 * successful turn.
 */
async function readNdjsonTurnStream(
  response: Response,
  onActivityEvent?: (event: DeliaActivityEvent) => void,
): Promise<DeliaInteractionResult> {
  const body = response.body;
  if (!body) {
    throw new DeliaInteractionError(
      "invalid_response",
      "Resposta da DÉLIA inválida.",
    );
  }

  const reader = body.getReader();
  const decoder = new TextDecoder();
  const seenEventIds = new Set<string>();
  let buffer = "";
  let maxSequence = 0;
  let eventCount = 0;
  let terminal: Record<string, unknown> | null = null;

  const handleLine = (line: string): Record<string, unknown> | null => {
    const trimmed = line.trim();
    if (!trimmed || trimmed.length > ACTIVITY_STREAM_MAX_LINE_CHARS) {
      return null;
    }
    let record: Record<string, unknown>;
    try {
      record = JSON.parse(trimmed) as Record<string, unknown>;
    } catch {
      // A malformed non-terminal line is presentation-only data —
      // drop it; a missing terminal is rejected at stream end.
      return null;
    }
    if (
      (record?.type === "turn_result" ||
        record?.type === "turn_error") &&
      record.version === "1"
    ) {
      return record;
    }
    if (record?.type === "activity_event" && record.version === "1") {
      if (eventCount >= ACTIVITY_STREAM_MAX_EVENTS) return null;
      const event = parseActivityEvent(record);
      if (!event) return null;
      if (seenEventIds.has(event.event_id)) return null;
      // Ordering contract: sequence is strictly increasing; stale or
      // out-of-order events are dropped, never replayed.
      if (event.sequence <= maxSequence) return null;
      seenEventIds.add(event.event_id);
      maxSequence = event.sequence;
      eventCount += 1;
      onActivityEvent?.(event);
    }
    // Unknown record kinds are ignored — forward-compatible.
    return null;
  };

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let newline = buffer.indexOf("\n");
      while (newline >= 0) {
        const hit = handleLine(buffer.slice(0, newline));
        buffer = buffer.slice(newline + 1);
        if (hit) {
          terminal = hit;
          buffer = "";
          break;
        }
        newline = buffer.indexOf("\n");
      }
      if (terminal) break;
      if (buffer.length > ACTIVITY_STREAM_MAX_LINE_CHARS) {
        // A runaway line can never be a valid record — bound memory.
        buffer = "";
      }
    }
    if (!terminal) {
      buffer += decoder.decode();
      terminal = handleLine(buffer);
    }
  } finally {
    reader.releaseLock();
  }

  if (!terminal) {
    // The contract requires exactly one terminal record; an absent
    // one means the stream was truncated — never a silent success.
    throw new DeliaInteractionError(
      "invalid_response",
      "Resposta da DÉLIA inválida.",
    );
  }
  if (terminal.type === "turn_error") {
    const code =
      typeof terminal.code === "string" ? terminal.code : "internal_error";
    throw new DeliaInteractionError(
      code,
      ERROR_MESSAGES[code] ??
        (typeof terminal.message === "string"
          ? terminal.message
          : "Erro interno. Tente novamente."),
    );
  }
  return parseInteractionResultPayload(
    terminal.result as Record<string, unknown> | null,
  );
}

/** Bounded syntactic projection of one ActivityEvent.v1 record —
 *  allowlisted keys only; anything else cannot reach the UI. */
function parseActivityEvent(
  record: Record<string, unknown>,
): DeliaActivityEvent | null {
  if (
    typeof record.event_id !== "string" ||
    !Number.isInteger(record.sequence) ||
    (record.sequence as number) < 1 ||
    typeof record.timestamp !== "string" ||
    typeof record.session_id !== "string" ||
    typeof record.turn_id !== "string" ||
    typeof record.phase !== "string" ||
    typeof record.state !== "string" ||
    !ACTIVITY_PHASES.has(record.phase) ||
    !ACTIVITY_STATES.has(record.state)
  ) {
    return null;
  }

  const text = (value: unknown): string | undefined =>
    typeof value === "string" && value.trim() ? value : undefined;

  const capability = record.capability_ref as
    | Record<string, unknown>
    | undefined;
  const source = record.source_ref as Record<string, unknown> | undefined;
  const owner = record.owner_ref as Record<string, unknown> | undefined;
  const outcome = record.outcome_ref as
    | Record<string, unknown>
    | undefined;

  const event: DeliaActivityEvent = {
    version: "1",
    event_id: record.event_id,
    sequence: record.sequence as number,
    timestamp: record.timestamp,
    session_id: record.session_id,
    turn_id: record.turn_id,
    phase: record.phase,
    state: record.state,
    label_code: text(record.label_code) ?? record.phase,
    ...(text(record.correlation_id)
      ? { correlation_id: text(record.correlation_id) }
      : {}),
  };

  if (capability && typeof capability === "object") {
    const ref = {
      remote_name: text(capability.remote_name),
      protocol: text(capability.protocol),
      operation_class: text(capability.operation_class),
    };
    if (ref.remote_name || ref.protocol || ref.operation_class) {
      event.capability_ref = ref;
    }
  }
  if (source && typeof source === "object") {
    const ref = {
      source_id: text(source.source_id),
      source_system: text(source.source_system),
    };
    if (ref.source_id || ref.source_system) event.source_ref = ref;
  }
  if (owner && typeof owner === "object") {
    const ref = {
      display_name: text(owner.display_name),
      owner_ref: text(owner.owner_ref),
    };
    if (ref.display_name || ref.owner_ref) event.owner_ref = ref;
  }
  if (outcome && typeof outcome === "object") {
    const status = text(outcome.status);
    if (status && ACTIVITY_OUTCOME_STATUSES.has(status)) {
      event.outcome_ref = {
        status,
        ...(Number.isInteger(outcome.record_count) &&
        (outcome.record_count as number) >= 0
          ? { record_count: outcome.record_count as number }
          : {}),
      };
    }
  }
  return event;
}

/**
 * Bounded syntactic parse of the confirmation surface — digests only.
 * Any malformed shape degrades to null (no card rendered); the backend
 * remains the enforcing authority for binding semantics.
 */
function parseConfirmationRequest(
  raw: unknown,
): DeliaConfirmationRequest | null {
  if (!raw || typeof raw !== "object") return null;
  const record = raw as Record<string, unknown>;
  if (
    typeof record.proposal_digest !== "string" ||
    typeof record.preview_fingerprint !== "string" ||
    typeof record.session_id !== "string"
  ) {
    return null;
  }
  return {
    session_id: record.session_id,
    capability_ref:
      typeof record.capability_ref === "string"
        ? record.capability_ref
        : undefined,
    proposal_digest: record.proposal_digest,
    preview_fingerprint: record.preview_fingerprint,
    expires_at_epoch:
      typeof record.expires_at_epoch === "number"
        ? record.expires_at_epoch
        : undefined,
    pending_purpose:
      record.pending_purpose === "execution_scope_choice" ||
      record.pending_purpose === "execution_scope_plus_owner_confirmation"
        ? record.pending_purpose
        : undefined,
  };
}
