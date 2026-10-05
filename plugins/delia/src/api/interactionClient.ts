/**
 * DÉLIA interaction API client — C3-INTERACTION-RUNTIME-01.
 *
 * Smallest client for the bounded vertical slice: POST /interaction/turns
 * against the delia-api gateway base path. The bearer token is fetched
 * from the Portal host per request and is never stored, decoded, or
 * logged. No business-domain API is exposed here.
 */

export const DELIA_API_BASE = "/apps/delia-api";
export const DELIA_INTERACTION_TURNS_PATH = "/interaction/turns";

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
};

/** Structured decision echoed back on a confirmation turn. */
export type DeliaConfirmationDecision = {
  decision: "CONFIRM" | "REJECT";
  proposal_digest: string;
  preview_fingerprint: string;
  session_id: string;
};

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
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        input,
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
  };
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
  };
}
