# VD-F05 — Ditado de 5 minutos + continuidade do rascunho — Relatório de evidência

**TASK_ID:** `DELIA-VD-F05-FIVE-MINUTE-DICTATION-CONTINUITY-01`
**DATA:** 2026-10-20
**SPEC primária:** [119 §VD-F05](../../119-conversation-audio-recorder-composer-product-ux-specification.md)
**Spec visual preservada:** [120 — VD-F04](../../120-voice-dictation-composer-visual-refinement-ux-specification.md)
**Contrato:** [dictation.transcription.v1](../../contracts/dictation-transcription-contract-v1.md)
**BASE_HEAD:** `38c5118e914c4acbdfabaf73b698985215775685`
**Escopo:** limite de 300 s por trecho, auto-finalização única, contador + aviso contextual, continuidade textual do draft, alinhamento de limites backend/bytes. Zero mudança de provider, AuthZ, orquestração LLM ou endpoints.

## 1. Reuse gate

| Conceito | Equivalente existente | Decisão |
|---|---|---|
| Gravador | `AudioRecorderControl` + `useLocalAudioRecorder` | EXTEND — auto-stop/limit já existiam; adicionados contador `/05:00`, aviso pré-limite e clamp de duração reportada |
| STT | `dictation.transcription.v1` (`dictationClient`, `delia-api`) | EXTEND_LIMITS_ONLY — nenhum código de backend novo; apenas defaults de settings/compose |
| Merge de draft | `handleDraftReady` + `pendingCaretRef` (VD-F03/F04) | EXTEND — `mergeTranscriptIntoDraft` normaliza espaço limítrofe e aplica o limite de caracteres |
| Composer | `MessageComposer`, `DeliaComposer` | REUSE |
| Help | `HelpTooltip` modo `wrap` | REUSE — tooltip do mic passa a anunciar o limite admitido |

## 2. Limites efetivos (governança)

| Camada | Antes | Depois | Justificativa |
|---|---|---|---|
| Produto (`DELIA_AUDIO_PRODUCT_*`) | 60 000 ms / 256 000 B | 300 000 ms / 8 388 608 B | decisão de produto VD-F05 |
| Backend default (`settings.py`, compose dev/prod) | 120 000 ms / 4 194 304 B | 300 000 ms / 8 388 608 B | env-driven, fail-closed preservado |
| Admissão efetiva frontend | fixa 60 s/256 KB | `resolveAudioCaptureLimits` = `min(produto, contrato)` a partir de `GET /dictation/status` | frontend nunca anuncia mais do que o backend aceita |
| Gateway | inalterado | inalterado | rota `delia-api` herda `client_max_body_size 20m`; payload 8 MiB → ~11,2 MB JSON base64 < 20 m |

**Evidência de compatibilidade (VD-T07, teste real ~5 min):** captura Chrome `audio/webm;codecs=opus` de 300 s produziu **4 387 114 bytes** — acima do bound antigo de 4 MiB (primeiro run real falhou com `limit_bytes`, draft preservado, sem transcrição — comportamento fail-closed confirmado). Com 8 MiB o mesmo cenário transcreveu integralmente. Timeout do provider (30 s) comportou a transcrição real de ~5 min sem alteração.

## 3. Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `plugins/plugin-ui/src/components/composer/useLocalAudioRecorder.ts` | `durationMs` reportado clampa ao `maxDurationMs` admitido (intervalo pode superar o limite em um tick — nunca reporta acima do contrato) |
| `plugins/plugin-ui/src/components/composer/AudioRecorderControl.tsx` | contador `mm:ss / limite`; nota discreta `role="status"` nos últimos 30 s (“A gravação será finalizada em breve.”); limite atingido em preview vira nota informativa (muted, `role="status"`) em vez de alerta de erro |
| `plugins/plugin-ui/src/styles/audio-recorder.css` | `__duration-limit`, `__limit-note`, `__limit-banner` |
| `plugins/delia/src/audio/audioCaptureTestAdmission.ts` | `DELIA_AUDIO_PRODUCT_*` 300 s/8 MiB; `resolveAudioCaptureLimits` (min produto × contrato) |
| `plugins/delia/src/App.tsx` | admissão de captura passa a derivar dos limites publicados pelo contrato |
| `plugins/delia/src/ui/DeliaComposer.tsx` | `mergeTranscriptIntoDraft` (espaço limítrofe + limite de caracteres com aviso honesto); clamp defensivo de `durationMs`; tooltip do mic anuncia “fale até 5 minutos”; dictationError para truncamento |
| `delia-api/app/infrastructure/config/settings.py` | defaults `stt_max_duration_ms`/`stt_max_audio_bytes` → 300000/8388608 |
| `infra/docker-compose.yml`, `infra/docker-compose.dev.yml` | defaults env `DELIA_STT_MAX_DURATION_MS`/`DELIA_STT_MAX_AUDIO_BYTES` → 300000/8388608 |
| contrato v1 + spec 119 + este relatório + ledger §6.329 (implantação) + §6.331 (deploy) | documentação |

Backend de transcrição (`transcribe_dictation.py`, rotas, adapter, rate limit, AuthZ): **diff zero**.

## 4. Verificação automatizada

| Gate | Resultado |
|---|---|
| Vitest `plugin-ui` (suíte completa) | 377 arquivos / 2254 testes — 1 falha transitória em `UserDirectoryPicker` (não relacionada; 7/7 no re-run isolado) |
| Vitest `delia` (suíte completa) | PASS — 21 arquivos / 268 testes |
| Pytest dictation (`delia-api`) | PASS — 25/25 |
| Typecheck `plugin-ui` + `delia` | PASS (exit 0) |
| Build `plugin-ui` + `delia` | PASS |
| Module Federation | PASS |

Novos testes: `audioCaptureTestAdmission.test.ts` (resolver min/contrato), `AudioRecorderControl.test.tsx` VD-F05 (par de contador, auto-stop único com relógio falso, aviso 4:30/4:29, limit-bytes seguro), `DeliaComposer.test.tsx` VD-F05 (acumulo de dois ditados, falha do segundo preserva o primeiro, edição entre ditados, tooltip de 5 min, auto-stop→transcrição com draft bounded, truncamento no limite de caracteres).

## 5. Browser QA real (Playwright, Chrome headless, `e2e-delia`, STT real)

Script `C:\temp\delia-qa\qa-vdf05.mjs` com `--use-file-for-fake-audio-capture` alimentado por WAV de **312 s de fala pt-BR real** (`speech-ptbr-long.wav`, loop do fixture real). Resultado **15/15 PASS**:

- `GET /dictation/status` live: `max_duration_ms=300000`, `max_audio_bytes=8388608`;
- contador `00:02 / 05:00` durante a gravação;
- aviso “A gravação será finalizada em breve.” aparece aos ~281 s (4:41);
- auto-stop aos ~311 s (limite + tick), sem clique em Finalizar;
- POST `/dictation/transcriptions` **exatamente 1×** com payload de áudio real ≈ 4 387 114 bytes;
- transcrição real: 10 939 chars editáveis, `rascunho anterior.` preservado;
- **zero** `POST /interaction/turns` (sem auto-submit);
- segundo ditado acumulou no mesmo draft (10 939 → 10 987 chars), segunda chamada de transcrição, ainda sem auto-submit.

Run anterior com bound de 4 MiB (pré-ajuste) registrou: auto-stop correto, erro contextual “A gravação atingiu o tamanho máximo permitido.”, draft preservado, nenhuma transcrição — prova fail-closed honesta do caminho de bytes (VD-T05 real).

Script `qa-vdf05-dock.mjs` (Companion Dock, fixture curto de fala): **8/8 PASS** — mic, tooltip “fale até 5 minutos” dentro do viewport, região de gravação, contador `…/05:00`, sem overflow horizontal, transcrição real (33 chars) sem auto-submit.

Screenshots: `C:\temp\delia-qa\shots-vdf05\`.

## 6. Produção

Deploy executado via `infra/scripts/up-prod-sequential.sh --cpu --build plugin-ui delia` + recreate do `delia-api` (mudança só de env) em `operador@srv-api` (`192.168.1.237`), checkout `a835a97ac` — mesmo SHA testado localmente.

Configuração efetiva atualizada no mecanismo protegido do host (`infra/.env`, valores não secretos):

- `DELIA_STT_MAX_DURATION_MS=300000` (antes 120000);
- `DELIA_STT_MAX_AUDIO_BYTES=8388608` (antes 4194304);
- provider, modelo, timeout (30 s), rate limit (10/min) e `delia.access` **inalterados**.

Verificação pós-deploy (live):

- `docker exec delpi-delia-api env` → `DELIA_STT_MAX_DURATION_MS=300000`, `DELIA_STT_MAX_AUDIO_BYTES=8388608` — container healthy;
- `delpi-delia` e `delpi-plugin-ui` recriados e servindo bundles novos: `App-C5dbkJxV.js` (delia) contém o tooltip VD-F05 “fale até 5 minutos … texto editável”; `Index-DRC41Uyf.js` (plugin-ui) contém “A gravação será finalizada em breve.”;
- `GET /apps/delia-api/dictation/status` → **401** sem credencial (hardening preservado);
- `remoteEntry.js` de `delia` e `plugin-ui` → 200; gateway healthy;
- nenhum outro serviço tocado.

Verificação física de microfone em produção permanece `PENDING_USER_VERIFICATION` — exige sessão `delia.access` real (mesmo gate das entregas VD-F03/F04).

## 7. Residuais

- `VD-F05` assume bitrate típico de voz do Chrome (~128 kbps); dispositivos com bitrate maior podem atingir 8 MiB antes de 300 s → o fluxo fail-closed (`limit_bytes`, erro contextual, draft preservado) é o comportamento correto e observado.
- Timeout do provider permanece 30 s: evidência local cobriu ~5 min com folga; se produção apresentar `provider_timeout` em áudios longos, elevar `DELIA_STT_TIMEOUT_SECONDS` com evidência própria.
- Rate limit 10/min inalterado: 5 ditados longos sucessivos permanecem dentro do envelope.
