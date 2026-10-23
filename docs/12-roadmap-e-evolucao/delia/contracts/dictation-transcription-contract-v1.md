# Dictation Transcription Contract v1 — `dictation.transcription.v1`

**Task:** `DELIA-UX-VOICE-DICTATION-STT-INTEGRATION-01` (VD-F03)
**Spec:** [119 — Voice Dictation Composer](../119-conversation-audio-recorder-composer-product-ux-specification.md) §0
**Status:** `CONTRACT_DEFINED` — owner `delia-api`, consumer `plugins/delia` MFE

## 1. Purpose, owner and boundary

Converts one completed local voice-dictation capture into **editable
untrusted text** for the DÉLIA composer.

| Papel | Owner |
|---|---|
| Contract owner | `delia-api` (DÉLIA backend boundary) |
| Consumer | DÉLIA MFE (`plugins/delia`) — single consumer |
| Provider family | `openai_compatible` chat completions with `input_audio` (same family already approved for DÉLIA model invocation; OpenRouter account in production/dev) |
| Capability | `speech_transcription` — audio → text only |

Not in scope: multimodal audio analysis, audio messages, live voice,
TTS, biometrics. The transcript is **untrusted user input** — it never
authorizes ACT, PREPARE, domain decisions or OT commands, and it is
never auto-submitted.

## 2. Transport contract

Base path: `/apps/delia-api` (gateway). JSON request/response.

### 2.1 `GET /dictation/status`

Admission/status read. AuthN: Bearer token + Core context (same
middleware as interaction turns). AuthZ: `delia.access` (or
superadmin) enforced on the same Core-resolved context — an
authenticated user without access receives `403 forbidden`; the
capability surface is not disclosed (VD-F03 hardening).

```json
{
  "contract_version": "1",
  "available": true,
  "language": "pt-BR",
  "max_audio_bytes": 8388608,
  "max_duration_ms": 300000,
  "incremental": {
    "available": false,
    "contract": "dictation.incremental.v1",
    "contract_version": "1",
    "max_session_ms": 300000,
    "max_segments": 120,
    "max_segment_duration_ms": 15000
  }
}
```

O bloco `incremental` é **aditivo** (VD-F06): consumidores v1 o ignoram;
quando `available=false` a capability incremental está ausente e o
consumidor permanece no caminho v1 — ver
[dictation-incremental-contract-v1.md](dictation-incremental-contract-v1.md).

`available=false` (limits `null`) when `DELIA_STT_*` config is
incomplete — fail closed; the frontend keeps the local-only capture
behavior.

### 2.2 `POST /dictation/transcriptions`

Request (JSON, allowlisted keys only):

```json
{
  "audio_base64": "<base64>",
  "mime_type": "audio/webm;codecs=opus",
  "duration_ms": 4800,
  "language_hint": "pt-BR"
}
```

Response `200`:

```json
{
  "transcription_id": "<uuid4>",
  "text": "Mostre os indicadores de produção desta semana.",
  "language": "pt-BR"
}
```

`transcription_id` is the log-correlation reference; raw audio and
transcript text are never logged.

### 2.3 Allowed MIME → provider audio format

| `mime_type` | provider `format` |
|---|---|
| `audio/webm`, `audio/webm;codecs=opus` | `webm` |
| `audio/ogg`, `audio/ogg;codecs=opus` | `ogg` |
| `audio/mp4` | `mp4` |
| `audio/wav` | `wav` |
| `audio/mpeg` | `mp3` |

`webm` and `wav` were proven end-to-end against the approved provider
(real pt-BR speech → exact transcript). Other containers remain in the
allowlist because the provider accepts the `format` vocabulary; an
unsupported submission surfaces as a typed `provider_rejected` error,
never a silent fallback.

### 2.4 Error taxonomy (`{detail, code}`)

| HTTP | code | meaning |
|---|---|---|
| 401 | `unauthenticated` | auth middleware |
| 403 | `forbidden` | no `delia.access` |
| 400 | `invalid_request` | malformed JSON/body/params |
| 400 | `unsupported_language` | `language_hint != pt-BR` in v1 |
| 400 | `duration_exceeded` | `duration_ms` out of bounds |
| 415 | `unsupported_media` | MIME not in allowlist |
| 413 | `payload_too_large` | decoded audio over `max_audio_bytes` |
| 429 | `rate_limited` | per-user window exceeded |
| 503 | `transcription_unavailable` | capability not configured |
| 503 | `provider_unavailable` | provider unreachable/5xx/auth |
| 502 | `provider_rejected` | provider 4xx rejection |
| 502 | `empty_transcription` | postcondition failed (empty text) |
| 504 | `provider_timeout` | bounded deadline exceeded |
| 500 | `internal_error` | unexpected |

## 3. Gates and semantics

- **AuthN/AuthZ:** same boundary as `/interaction/turns` — Bearer +
  Core-resolved context; `delia.access` (or superadmin) enforced in the
  use case. No new permission (PM decision: no audio-specific RBAC).
- **Consent/purpose:** dictation banner states the audio is sent only
  for transcription; capture still requires explicit gesture + browser
  mic consent.
- **Limits:** backend `DELIA_STT_MAX_AUDIO_BYTES` (default 8 MiB —
  VD-F05 raised it from 4 MiB: a measured real 300 s Chrome
  `audio/webm;codecs=opus` capture is ~4.4 MB, over the old bound),
  `DELIA_STT_MAX_DURATION_MS` (default 300000 — VD-F05 raised the
  governed segment bound from 120000 to the product-approved five
  minutes). Frontend applies `min(product admission, contract limits)`
  per segment; each segment is an independent capture — draft text
  accumulates across segments, never the audio.
- **Rate limit:** per-user fixed window
  (`DELIA_STT_RATE_LIMIT_PER_MINUTE`, default 10) inside the use case —
  in-process, single-replica honest bound (residual: no cross-replica
  enforcement).
- **Timeout/cancel:** bounded wall-clock deadline
  (`DELIA_STT_TIMEOUT_SECONDS`, default 30s) via the governed deadline
  transport. Client cancel = local abort; the provider call cannot be
  recalled mid-flight and a late result is discarded by session
  correlation on the client — never applied to the draft.
- **Idempotency:** pure read-compute; no server state mutated, so no
  idempotency key is required.
- **Retention:** zero — audio lives only in request memory; no files,
  no tables, no logs with audio content or transcript text.
- **Observability:** structured logs with `request_id`,
  `transcription_id`, mime, bytes, duration, error code — no media.
- **Postcondition:** non-empty `text` after strip; otherwise
  `empty_transcription` (502). HTTP 200 alone is never treated as
  semantic success by the client.
- **Versioning:** `contract_version: "1"` in status; additive fields
  only within v1.

## 4. Configuration (fail closed)

| env | default | required |
|---|---|---|
| `DELIA_STT_PROVIDER` | — | yes (`openai_compatible_audio`) |
| `DELIA_STT_BASE_URL` | — | yes |
| `DELIA_STT_MODEL` | — | yes (audio-capable model, e.g. `google/gemini-2.5-flash`) |
| `DELIA_STT_API_KEY` | — | yes |
| `DELIA_STT_TIMEOUT_SECONDS` | `30` | no |
| `DELIA_STT_MAX_AUDIO_BYTES` | `8388608` | no |
| `DELIA_STT_MAX_DURATION_MS` | `300000` | no |
| `DELIA_STT_RATE_LIMIT_PER_MINUTE` | `10` | no |

Any missing required key → `available=false`, `503
transcription_unavailable` — no implicit fallback, no shared key reuse.

## 5. Draft merge rule (product decision — VD-07 resolved)

PM VD-F03 prompt §7 freezes the deterministic composition:

- Empty composer → transcript becomes the draft.
- Non-empty composer → transcript **replaces the selection** or is
  **inserted at the caret** snapshotted when dictation started (no
  silent append); default caret = end of text when none was recorded.
- Cancel/error/timeout/local interruption → the pre-dictation text is
  preserved verbatim (the draft is never mutated before a successful
  transcript).
- Late response after cancel → discarded by session correlation.
- Result stays fully editable; submit is exclusively the user's action.
