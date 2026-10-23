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
export const DELIA_DICTATION_SESSIONS_PATH =
  "/dictation/transcription-sessions";
export const DELIA_DICTATION_LANGUAGE = "pt-BR";

export type DeliaDictationIncrementalStatus = {
  available: boolean;
  contract: string | null;
  contractVersion: string | null;
  maxSessionMs: number | null;
  maxSegments: number | null;
  maxSegmentDurationMs: number | null;
};

export type DeliaDictationStatus = {
  contractVersion: string;
  available: boolean;
  language: string;
  maxAudioBytes: number | null;
  maxDurationMs: number | null;
  incremental: DeliaDictationIncrementalStatus;
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
  | "session_not_found"
  | "invalid_sequence"
  | "session_expired"
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
      incremental: parseIncrementalStatus(body.incremental),
    };
  } catch {
    return null;
  }
}

function parseIncrementalStatus(
  raw: unknown,
): DeliaDictationIncrementalStatus {
  const empty: DeliaDictationIncrementalStatus = {
    available: false,
    contract: null,
    contractVersion: null,
    maxSessionMs: null,
    maxSegments: null,
    maxSegmentDurationMs: null,
  };
  if (typeof raw !== "object" || raw === null) return empty;
  const block = raw as Record<string, unknown>;
  return {
    available: block.available === true,
    contract:
      typeof block.contract === "string" ? block.contract : null,
    contractVersion:
      typeof block.contract_version === "string"
        ? block.contract_version
        : null,
    maxSessionMs:
      typeof block.max_session_ms === "number" ? block.max_session_ms : null,
    maxSegments:
      typeof block.max_segments === "number" ? block.max_segments : null,
    maxSegmentDurationMs:
      typeof block.max_segment_duration_ms === "number"
        ? block.max_segment_duration_ms
        : null,
  };
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


// ---------------------------------------------------------------------------
// dictation.incremental.v1 (VD-F06) — bounded session + NDJSON segment stream.
// Same admission rules as v1: bearer per request, never stored/decoded/logged;
// transcript text is untrusted user input and is never auto-submitted.
// ---------------------------------------------------------------------------

export type DeliaDictationSession = {
  sessionId: string;
  contract: string;
  contractVersion: string;
  maxSessionMs: number | null;
  maxSegments: number | null;
  maxSegmentDurationMs: number | null;
};

export type DeliaIncrementalEvent = {
  type: "started" | "partial" | "final" | "error";
  sessionId: string;
  segmentId: string;
  sequence: number;
  revision: number;
  isFinal?: boolean;
  text?: string;
  language?: string;
  code?: string;
};

export async function openDictationSession(
  options: DeliaDictationClientOptions,
): Promise<DeliaDictationSession> {
  const token = options.getAccessToken();
  if (!token) {
    throw new DeliaDictationError("unauthenticated", "unauthenticated");
  }
  let response: Response;
  try {
    response = await fetch(`${DELIA_API_BASE}${DELIA_DICTATION_SESSIONS_PATH}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      signal: options.signal ?? null,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new DeliaDictationError("cancelled", "cancelled by user");
    }
    throw new DeliaDictationError("network_error", "network error");
  }
  if (!response.ok) {
    const code = await readErrorCode(response);
    throw new DeliaDictationError(code, `dictation session failed: ${code}`);
  }
  let body: Record<string, unknown>;
  try {
    body = (await response.json()) as Record<string, unknown>;
  } catch {
    throw new DeliaDictationError(
      "invalid_response",
      "invalid session response",
    );
  }
  if (typeof body.session_id !== "string" || !body.session_id) {
    throw new DeliaDictationError(
      "invalid_response",
      "session response missing session_id",
    );
  }
  return {
    sessionId: body.session_id,
    contract: typeof body.contract === "string" ? body.contract : "",
    contractVersion:
      typeof body.contract_version === "string" ? body.contract_version : "",
    maxSessionMs:
      typeof body.max_session_ms === "number" ? body.max_session_ms : null,
    maxSegments:
      typeof body.max_segments === "number" ? body.max_segments : null,
    maxSegmentDurationMs:
      typeof body.max_segment_duration_ms === "number"
        ? body.max_segment_duration_ms
        : null,
  };
}

export type DeliaSegmentInput = {
  sessionId: string;
  segmentId: string;
  sequence: number;
  blob: Blob;
  mimeType: string;
  durationMs: number;
};

/**
 * Stream one finished audio segment through the incremental contract.
 * Yields real server events as NDJSON lines arrive; a mid-stream
 * provider failure surfaces as an `error` event (honest state, not a
 * thrown transport error). Throws DeliaDictationError on admission
 * failures before the stream opens.
 */
export async function* streamDictationSegment(
  input: DeliaSegmentInput,
  options: DeliaDictationClientOptions,
): AsyncGenerator<DeliaIncrementalEvent> {
  const token = options.getAccessToken();
  if (!token) {
    throw new DeliaDictationError("unauthenticated", "unauthenticated");
  }
  const audioBase64 = await blobToBase64(input.blob);
  let response: Response;
  try {
    response = await fetch(
      DELIA_API_BASE +
        DELIA_DICTATION_SESSIONS_PATH +
        "/" +
        encodeURIComponent(input.sessionId) +
        "/segments",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          Accept: "application/x-ndjson",
        },
        signal: options.signal ?? null,
        body: JSON.stringify({
          segment_id: input.segmentId,
          sequence: input.sequence,
          audio_base64: audioBase64,
          mime_type: input.mimeType,
          duration_ms: Math.max(1, Math.round(input.durationMs)),
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
    throw new DeliaDictationError(code, `dictation segment failed: ${code}`);
  }
  if (!response.body) {
    throw new DeliaDictationError(
      "invalid_response",
      "segment stream missing body",
    );
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for (;;) {
      const read = await reader.read();
      if (read.done) break;
      buffer += decoder.decode(read.value, { stream: true });
      let nl = buffer.indexOf("\n");
      while (nl >= 0) {
        const line = buffer.slice(0, nl).trim();
        buffer = buffer.slice(nl + 1);
        nl = buffer.indexOf("\n");
        if (!line) continue;
        const event = parseIncrementalEvent(line);
        if (event) yield event;
      }
    }
    const tail = buffer.trim();
    if (tail) {
      const event = parseIncrementalEvent(tail);
      if (event) yield event;
    }
  } finally {
    try {
      reader.cancel();
    } catch {
      /* stream already closed */
    }
  }
}

function parseIncrementalEvent(line: string): DeliaIncrementalEvent | null {
  let raw: Record<string, unknown>;
  try {
    raw = JSON.parse(line) as Record<string, unknown>;
  } catch {
    return null;
  }
  const type = raw.type;
  if (
    type !== "started" &&
    type !== "partial" &&
    type !== "final" &&
    type !== "error"
  ) {
    return null;
  }
  return {
    type,
    sessionId: typeof raw.session_id === "string" ? raw.session_id : "",
    segmentId: typeof raw.segment_id === "string" ? raw.segment_id : "",
    sequence: typeof raw.sequence === "number" ? raw.sequence : 0,
    revision: typeof raw.revision === "number" ? raw.revision : 0,
    isFinal: raw.is_final === true,
    text: typeof raw.text === "string" ? raw.text : undefined,
    language: typeof raw.language === "string" ? raw.language : undefined,
    code: typeof raw.code === "string" ? raw.code : undefined,
  };
}

export async function endDictationSession(
  sessionId: string,
  options: DeliaDictationClientOptions,
): Promise<void> {
  const token = options.getAccessToken();
  if (!token) return; // nothing to revoke without auth anyway
  try {
    await fetch(
      DELIA_API_BASE +
        DELIA_DICTATION_SESSIONS_PATH +
        "/" +
        encodeURIComponent(sessionId) +
        "/end",
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        signal: options.signal ?? null,
      },
    );
  } catch {
    /* best-effort cleanup — local state is already closing */
  }
}
