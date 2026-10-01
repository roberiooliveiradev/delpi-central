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

export type DeliaInteractionResult = {
  session_id: string;
  user_turn_id: string;
  result_turn_id: string;
  content: string;
  epistemic_class: string | null;
  limitations: string[];
  generated_at: string;
  model_invocation_id: string;
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
  invalid_model_output: "Resposta da DÉLIA inválida.",
  forbidden_model_output: "Resposta da DÉLIA bloqueada por política.",
  internal_error: "Erro interno. Tente novamente.",
};

export type SubmitInteractionTurnOptions = {
  getAccessToken: () => string | undefined;
  signal?: AbortSignal;
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
      body: JSON.stringify({ input }),
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
  };
}
