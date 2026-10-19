/**
 * DÉLIA dictation API client — dictation.transcription.v1 (VD-F03).
 *
 * Bounded client for GET /dictation/status (capability admission) and
 * POST /dictation/transcriptions (one completed local capture →
 * untrusted editable text). The bearer token is fetched from the Portal
 * host per request and is never stored, decoded, or logged.
 *
 * The transcript is user input: it carries no authority, is never
 * auto-submitted, and a cancelled/aborted request is surfaced as a
 * local interruption — never confused with a backend-confirmed cancel.
 */

export const DELIA_API_BASE = "/apps/delia-api";
export const DELIA_DICTATION_STATUS_PATH = "/dictation/status";
export const DELIA_DICTATION_TRANSCRIPTIONS_PATH =
  "/dictation/transcriptions";
export const DELIA_DICTATION_LANGUAGE = "pt-BR";

export type DeliaDictationStatus = {
  contractVersion: string;
  available: boolean;
  language: string;
  maxAudioBytes: number | null;
  maxDurationMs: number | null;
};

export type DeliaDictationErrorCode =
  | "unauthenticated"
  | "forbidden"
  | "invalid_request"
  | "unsupported_language"
  | "duration_exceeded"
  | "unsupported_media"
  | "payload_too_large"
  | "rate_limited"
  | "transcription_unavailable"
  | "provider_unavailable"
  | "provider_rejected"
  | "provider_timeout"
  | "empty_transcription"
  | "cancelled"
  | "network_error"
  | "invalid_response"
  | "internal_error";

export class DeliaDictationError extends Error {
  readonly code: DeliaDictationErrorCode;

  constructor(code: DeliaDictationErrorCode, message: string) {
    super(message);
    this.name = "DeliaDictationError";
    this.code = code;
  }
}

export type DeliaDictationTranscription = {
  transcriptionId: string;
  text: string;
  language: string;
};

export type DeliaDictationClientOptions = {
  getAccessToken: () => string | null;
  signal?: AbortSignal;
};

/** Fetch the dictation capability admission. Null on transport failure —
 *  treated as unavailable (fail closed to local-only capture). */
export async function fetchDictationStatus(
  options: DeliaDictationClientOptions,
): Promise<DeliaDictationStatus | null> {
  const token = options.getAccessToken();
  if (!token) return null;
  let response: Response;
  try {
    response = await fetch(`${DELIA_API_BASE}${DELIA_DICTATION_STATUS_PATH}`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      signal: options.signal ?? null,
    });
  } catch {
    return null;
  }
  if (!response.ok) return null;
  try {
    const body = (await response.json()) as Record<string, unknown>;
    if (body.contract_version !== "1") return null;
    return {
      contractVersion: "1",
      available: body.available === true,
      language:
        typeof body.language === "string"
          ? body.language
          : DELIA_DICTATION_LANGUAGE,
      maxAudioBytes:
        typeof body.max_audio_bytes === "number" ? body.max_audio_bytes : null,
      maxDurationMs:
        typeof body.max_duration_ms === "number" ? body.max_duration_ms : null,
    };
  } catch {
    return null;
  }
}

export type DeliaDictationDraftInput = {
  blob: Blob;
  mimeType: string;
  durationMs: number;
};

/** Transcribe one finished capture. Throws DeliaDictationError on every
 *  typed failure; `cancelled` marks a LOCAL abort (AbortSignal). */
export async function transcribeDictationAudio(
  draft: DeliaDictationDraftInput,
  options: DeliaDictationClientOptions,
): Promise<DeliaDictationTranscription> {
  const token = options.getAccessToken();
  if (!token) {
    throw new DeliaDictationError("unauthenticated", "unauthenticated");
  }
  const audioBase64 = await blobToBase64(draft.blob);

  let response: Response;
  try {
    response = await fetch(
      `${DELIA_API_BASE}${DELIA_DICTATION_TRANSCRIPTIONS_PATH}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        signal: options.signal ?? null,
        body: JSON.stringify({
          audio_base64: audioBase64,
          mime_type: draft.mimeType,
          duration_ms: Math.max(1, Math.round(draft.durationMs)),
          language_hint: DELIA_DICTATION_LANGUAGE,
        }),
      },
    );
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new DeliaDictationError("cancelled", "cancelled by user");
    }
    throw new DeliaDictationError("network_error", "network error");
  }

  if (!response.ok) {
    const code = await readErrorCode(response);
    throw new DeliaDictationError(code, `dictation failed: ${code}`);
  }

  let body: Record<string, unknown>;
  try {
    body = (await response.json()) as Record<string, unknown>;
  } catch {
    throw new DeliaDictationError(
      "invalid_response",
      "invalid dictation response",
    );
  }
  const text = typeof body.text === "string" ? body.text : "";
  const transcriptionId =
    typeof body.transcription_id === "string" ? body.transcription_id : "";
  if (!transcriptionId || !text.trim()) {
    // Contract postcondition mirrored on the client: an empty or
    // malformed transcript is a typed failure, never fabricated text.
    throw new DeliaDictationError(
      "invalid_response",
      "dictation response missing transcript",
    );
  }
  return {
    transcriptionId,
    text: text.trim(),
    language:
      typeof body.language === "string"
        ? body.language
        : DELIA_DICTATION_LANGUAGE,
  };
}

async function readErrorCode(
  response: Response,
): Promise<DeliaDictationErrorCode> {
  const fallback: DeliaDictationErrorCode =
    response.status === 429
      ? "rate_limited"
      : response.status === 504
        ? "provider_timeout"
        : response.status >= 500
          ? "provider_unavailable"
          : "invalid_request";
  try {
    const body = (await response.json()) as Record<string, unknown>;
    const code = body.code;
    return typeof code === "string"
      ? (code as DeliaDictationErrorCode)
      : fallback;
  } catch {
    return fallback;
  }
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("blob read failed"));
    reader.onload = () => {
      const result = reader.result;
      if (typeof result !== "string") {
        reject(new Error("blob read failed"));
        return;
      }
      const comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.readAsDataURL(blob);
  });
}
