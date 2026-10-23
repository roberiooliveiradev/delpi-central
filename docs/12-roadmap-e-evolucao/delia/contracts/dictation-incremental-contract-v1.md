# Dictation Incremental Contract v1 — `dictation.incremental.v1`

**Task:** `DELIA-VD-F06-PROGRESSIVE-DICTATION-END-TO-END-IMPLEMENT-TEST-REWORK-DEPLOY-01` (VD-F06)
**Spec:** [123 — Voice Dictation Progressive Live Editing](../123-voice-dictation-progressive-live-editing-ux-specification.md) §5–§6, [124 — Execution Plan](../124-vd-f06-end-to-end-implementation-execution-plan.md)
**Status:** `CONTRACT_DEFINED` — owner `delia-api`, consumer `plugins/delia` MFE
**Compatibilidade:** aditivo sobre `dictation.transcription.v1` (preservado integralmente; v1 segue o fallback honesto quando incremental está ausente/desabilitado).

## 1. Purpose, owner and boundary

Transcreve fala **durante a captura**, em segmentos WAV completos
produzidos pelo cliente (PCM → AudioWorklet → WAV mono 16 kHz). Cada
segmento é um áudio independente e real: o backend encaminha ao
adapter STT (`openai_compatible_audio`, `stream: true`) e emite os
deltas reais do provider como eventos parciais e o texto consolidado
como evento final. **Nenhum texto é fabricado** — parcial é sempre
saída real do provider.

| Papel | Owner |
|---|---|
| Contract owner | `delia-api` (DÉLIA backend boundary) |
| Consumer | DÉLIA MFE (`plugins/delia`) — single consumer |
| Provider family | `openai_compatible` chat completions `input_audio` + SSE `stream:true` — mesma família aprovada do VD-F03 |
| Capability | `speech_transcription_incremental` — áudio segmentado → eventos parcial/final |

Limites fora de escopo: streaming de áudio contínuo (WebSocket/WebRTC),
análise multimodal, TTS, biometria. O texto é **input não confiável** —
nunca autoriza ACT/PREPARE/decisões e nunca envia mensagem.

## 2. Transporte

Base path: `/apps/delia-api` (gateway). JSON + NDJSON stream.
Autenticação idêntica ao v1 (Bearer + contexto Core; AuthZ
`delia.access` fail-closed). Sem segredo, áudio ou texto em logs —
apenas metadados (ids, sequência, mime, bytes, duração, request id).

### 2.1 `POST /dictation/transcription-sessions`

Abre sessão limitada. `403 forbidden` sem `delia.access`;
`503 transcription_unavailable` quando o serviço não está configurado
ou `DELIA_STT_INCREMENTAL_ENABLED` está off (gate explícito de
ativação — deploy do código não equivale a ativação).

Response 200:

```json
{
  "contract": "dictation.incremental.v1",
  "contract_version": "1",
  "session_id": "dss_…",
  "max_session_ms": 300000,
  "max_segments": 120,
  "max_segment_duration_ms": 15000
}
```

### 2.2 `POST /dictation/transcription-sessions/{session_id}/segments`

Um segmento de áudio concluído → stream NDJSON de eventos reais.
`application/x-ndjson`, `Cache-Control: no-cache`.

Request (JSON, chaves allowlistadas):

```json
{
  "segment_id": "seg-1",
  "sequence": 1,
  "audio_base64": "<base64 WAV>",
  "mime_type": "audio/wav",
  "duration_ms": 4200,
  "language_hint": "pt-BR"
}
```

Erros de admissão (antes do stream abrir): JSON tipado
`{detail, code}` — `invalid_request` 400, `unsupported_media` 415,
`payload_too_large` 413, `rate_limited` 429, `session_not_found` 404,
`invalid_sequence` 409 (duplicado/fora de ordem), `forbidden` 403
(sessão de outro usuário ou sem acesso), `duration_exceeded` 400.

### 2.3 `POST /dictation/transcription-sessions/{session_id}/end`

Encerra a sessão e libera recursos (idempotente). `200 {"ended": true}`.

### 2.4 Eventos do stream (uma linha NDJSON por evento)

```json
{"type":"started","session_id":"dss_…","segment_id":"seg-1","sequence":1,"revision":0}
{"type":"partial","session_id":"dss_…","segment_id":"seg-1","sequence":1,"revision":1,"is_final":false,"text":"Mostre os"}
{"type":"partial","session_id":"dss_…","segment_id":"seg-1","sequence":1,"revision":2,"is_final":false,"text":"Mostre os indicadores"}
{"type":"final","session_id":"dss_…","segment_id":"seg-1","sequence":1,"revision":3,"is_final":true,"text":"Mostre os indicadores.","language":"pt-BR"}
{"type":"error","session_id":"dss_…","segment_id":"seg-1","sequence":1,"revision":0,"code":"provider_unavailable"}
```

- `partial.text` é o snapshot **cumulativo** real do provider (não delta).
- `revision` é monotônica por segmento; o cliente descarta revisões
  duplicadas, antigas ou pós-final.
- `error` encerra o stream do segmento com o código tipado — o draft
  mantém o que já foi contribuído.

## 3. Session e bounds

- `session_id` por usuário (sessão de outro usuário → 403).
- `sequence` inteiro estritamente crescente por sessão; duplicado/fora
  de ordem → `invalid_sequence` (nunca reordena arbitrariamente).
- TTL de sessão (`max_session_ms` + margem), `max_segments`,
  `max_segment_duration_ms`, `max_segment_bytes`, `max_total_bytes`
  (mesmo teto de áudio do v1), `max_in_flight` (backpressure) e rate
  limit por usuário — todos fail-closed com erros tipados.

## 4. Privacidade e autoridade

- Logs: metadados apenas; nunca áudio, texto transcrito ou payloads do
  provider.
- Nada persiste: sessão em memória, sem armazenamento de áudio/texto.
- Cancelamento local aborta o stream; remoto é best-effort (`/end`).
- Texto transcrito segue sendo input não confiável — nunca Evidence,
  FACT, autorização, PREPARE/ACT ou envio automático.

## 5. Fallback

`incremental.available=false` (config incompleta, flag off, AudioWorklet
ausente no cliente) → consumidor usa `dictation.transcription.v1`
(VD-F03) com a UX "Transcrevendo após finalizar". Nunca simular
transcrição ao vivo.
