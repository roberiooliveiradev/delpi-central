# VD-F06 — Ditado progressivo end-to-end — evidência de execução

TASK_ID: `DELIA-VD-F06-PROGRESSIVE-DICTATION-END-TO-END-IMPLEMENT-TEST-REWORK-DEPLOY-01`
Data: 2026-10-23. Commits: `9a46c81e65` (implementação), `3acf70b5e2` (wiring da flag de ativação).
Contratos: `dictation.transcription.v1` (preservado) + `dictation.incremental.v1` (novo, bounded).

## C0 — Capacidade real de STT incremental

- `STT_INCREMENTAL_SUPPORTED=YES`, `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND`.
- Provider real: OpenRouter `google/gemini-2.5-flash` via família `openai_compatible_audio`
  (config existente `KIMI_*`/`DELIA_STT_*`; secrets nunca em código/log).
- PoC com WAV pt-BR real (`/tmp/poc-ptbr.wav`, 22050 Hz mono 16-bit, 5.54 s, 244 KB):
  `stream:true` → `FIRST_DELTA_S=2.51`, `N_DELTAS=2`, `TOTAL_S=2.61`, transcrição real.
- Modelo honesto escolhido: **segmentação incremental real** — captura PCM contínua
  (AudioWorklet) fatiada em segmentos WAV completos (~4 s); cada segmento é transcrito
  de verdade pelo provider e `stream:true` entrega parciais intra-segmento reais.
  Zero pseudo-streaming: todo texto exibido é saída do provider.

## C2 — Backend `dictation.incremental.v1`

- `IncrementalDictationService`: sessão → segmentos NDJSON → end; valida AuthN/AuthZ
  (`delia.access`), ownership por usuário, TTL, sequência, limites de bytes/duração/
  segmentos/sessão, in-flight, rate limit, erros tipados, cleanup.
- `OpenAICompatibleTranscriptionAdapter.stream_transcribe`: SSE real do provider,
  snapshots cumulativos, deadline wall-clock compartilhado, timeout/429/4xx/5xx tipados,
  close garantido.
- Fail-closed por construção: serviço só existe se flag `DELIA_STT_INCREMENTAL_ENABLED=1`
  **e** config completa `DELIA_STT_*`. Flag default OFF; ativação é gate pós-deploy.
- Testes: 45 backend focados (incremental unit+route+regressão v1) e suite completa verdes.

## C3 — Reconciliação determinística (`dictationSegmentReconciler.ts`)

- Ownership de ranges em coordenadas do draft atual; segmento só revisa o range que
  ainda possui; edição humana que toca range provisório remove autoridade do segmento;
  edições fora deslocam âncoras deterministicamente; duplicados/stale descartados;
  cancel remove somente ranges provisórios ainda pertencentes; caret avança na inserção
  no ponto do usuário; seleção substituída exata; UTF-16/emoji correto. 14/14 testes.
- Controller (`incrementalDictationController.ts`): estados `requesting_permission`,
  `recording_listening`, `partial_transcript`, `reconciling`, `paused`, `finalizing`,
  `review`, `recoverable_error`, `unavailable`; nunca submete; preserva draft nas
  falhas. 10/10 testes.

## C4 — Frontend

- `DeliaComposer` mantém textarea nativa editável durante captura incremental;
  controles `Iniciar ditado` / `Pausar ditado` / `Retomar ditado` / `Finalizar ditado`
  / `Descartar captura`; strip de status textual + aria-live; waveform reutiliza
  classes CSS existentes; sem segundo composer nem segundo gravador
  (`segmentedPcmCapture` estende a família do recorder em plugin-ui).
- `App.tsx` admite incremental somente quando `status.incremental.available` e
  `isSegmentedPcmCaptureSupported` (export plugin-ui — plugins/delia sem APIs de mídia).
- Fallback VD-F03 (`dictation.transcription.v1`) intacto e preferido quando
  incremental indisponível.

## Deploy e ativação

- Push ff em `main` (`9a46c81e65`, `3acf70b5e2`); deploy canônico
  `./infra/scripts/up-prod-sequential.sh --build plugin-ui delia delia-api`.
- Pós-deploy, `GET /dictation/status` autenticado retornava `incremental.available=false`
  (fail-closed confirmado em produção).
- Ativação: `DELIA_STT_INCREMENTAL_ENABLED=1` no `.env` do host (config, não código),
  restart só de `delia-api`; status passou a `incremental.available=true` com limites
  canônicos (sessão 300 s, segmento 15 s, 120 segmentos).

## Smoke autenticado em produção (API)

Identidade `user` (password grant público `delpi-central`):

```
SESSION_OPENED dictation.incremental.v1 1
EVENT @0.342s started seg-1 seq=1 rev=0
EVENT @3.421s partial rev=1 "Mostre os indicadores"
EVENT @3.466s partial rev=2 "Mostre os indicadores de producal desta semana, por favor."
EVENT @3.479s final rev=2 is_final=true language=pt-BR
SESSION_ENDED {"ended":true}  →  SMOKE_RESULT=PASS
```

("producal" é acurácia do provider sobre "produção", não defeito de plataforma.)

## QA real de produção com voz pt-BR (Chrome + fake-audio WAV real)

Chrome headless com `--use-fake-ui-for-media-stream`,
`--use-fake-device-for-media-stream`,
`--use-file-for-fake-audio-capture=poc-ptbr.wav` — áudio pt-BR real percorre
getUserMedia → AudioWorklet → segmentos WAV → NDJSON → provider → reconciler → textarea.

| # | Critério | Resultado |
|---|----------|-----------|
| A1 | Incremental admitido no full-page | PASS |
| A2 | Controles de captura visíveis | PASS |
| A3 | `REAL_PARTIAL_BEFORE_STOP` — 58 chars durante captura ativa | PASS |
| A4 | Pausar → Retomar | PASS |
| A5 | Digitação humana durante captura ativa | PASS |
| A6 | Finalizar preserva ditado + edição humana (107 chars) | PASS |
| A7 | `NO_AUTO_SUBMIT` — zero novos turnos após finalizar | PASS |
| B1/B2 | Mobile 390 px — ditado progressivo real | PASS |
| B3 | Descartar remove provisório ("" após discard) | PASS |
| C1–C3 | Companion Dock real — texto progressivo no dock | PASS |

13/13 PASS, 0 defeitos reproduzidos em produção.

## Cobertura de critérios DoD

- `REAL_PARTIAL_BEFORE_STOP=PASS` (API @3.42s e DOM durante captura)
- `FREE_CARET_EDITING=PASS` (reconciler 14/14: início/meio/fim/seleção/IME/undo/emoji)
- `SELECTION_REPLACEMENT=PASS` (reconciler) | `HUMAN_EDIT_PRIORITY=PASS` (reconciler+controller+A5/A6)
- `LATE_EVENTS_SAFETY=PASS` (revision/sequence descarte) | `NO_DRAFT_LOSS=PASS` | `NO_AUTO_SUBMIT=PASS` (A7 + controller sem submit)
- `BACKEND_CONTRACT=PASS` `STT_PROVIDER_INTEGRATION=PASS` `FRONTEND_INTEGRATION=PASS`
- `FULLPAGE_QA=PASS` `REAL_DOCK_QA=PASS` `MOBILE_QA=PASS`
- `FALLBACK_V1=PASS` (endpoint intacto; 45 testes de regressão; preferido quando incremental off)
- `SECURITY_NEGATIVES=PASS` (401 sem bearer em prod; sessão de outro usuário 403; flag off fail-closed)
- `SCREEN_READER_QA=TEST_NOT_RUN` (sem leitor de tela no ambiente; aria-live/estados textuais implementados)

## Residuais

1. Screen reader real pendente de ambiente (mesmo residual do QA Markdown B2).
2. Acurácia de transcrição é do provider (observado "producal"); fora de escopo de plataforma.
3. Flags auxiliares (`MAX_*`) usam defaults canônicos; ajuste futuro via config.



---

# Rework pos-go-live — QUALITY-AND-SEGMENT-RECOVERY (commit `91a3913d02`, 2026-10-23)

Incidentes reportados pelo PO em produção e causa-raiz comprovada:

## Incidente B — mojibake `AlÃ´, alÃ´` — ROOT_CAUSE comprovada

- Causa: `requests.iter_lines(decode_unicode=True)` decodifica `text/event-stream`
  sem charset como **ISO-8859-1** (default histórico da lib para `text/*`).
  UTF-8 do provider era corrompido antes do `json.loads`.
- Fix: `iter_lines()` em **bytes** + decode UTF-8 por linha — seguro contra
  multibyte quebrado em fronteira de chunk (UTF-8 nunca contém `0x0A`).
- Prova prod pós-deploy: WAV pt-BR acentuado retornou
  `Alô, alô, você pode mostrar os indicadores de produção e a situação do
  coração, por favor?` — `UTF8_CLEAN`, texto correto no composer (A3b).

## Incidente C — `empty_transcription` exposto e sessão morta

- Causa: erro segment-scoped era tratado como `recoverable_error` terminal —
  sessão parava e o código cru aparecia ao usuário.
- Fix: classificação no controller — códigos terminais
  (`session_not_found`, `session_expired`, `forbidden`, `unauthenticated`)
  encerram a sessão; qualquer outra falha de segmento marca apenas o segmento
  (`reconciler.failSegment`: provisional vira user-owned, pending cancelado,
  eventos tardios descartados), exibe aviso contextual
  ("Não consegui reconhecer esse trecho. Você pode continuar falando.") e a
  captura continua ouvindo. Códigos técnicos nunca chegam ao usuário.
- `recoverable_error` agora permite reiniciar o ditado (antes dead-end).
- Avisos limpos ao finalizar/descartar; sem texto fabricado, sem auto-submit.

## Incidente A — progressividade/latência

- Medições reais em prod: primeiro partial do provider ~flat por segmento
  (2s→2.0s, 3s→2.4s, 4s→2.6s). O termo dominante do tempo até o primeiro
  texto visível era o próprio `segmentMs=4000` (TTFV ~6.5-7s).
- Fix honesto dentro do contrato: `firstSegmentMs=2000` +
  `segmentMs=3000` (100 segmentos < limite 120 em sessão de 5 min).
- Medido pós-deploy em browser real: `TIME_TO_FIRST_VISIBLE_MS=4550`
  (antes ~7s). Zero pseudo-streaming — todo texto é saída real do provider.

## Regressão e QA pós-fix

- Backend: 2150 passed (51 streaming-protocol, incl. 4 casos UTF-8 RED→GREEN);
  1 flake de timing em activity_streaming passa isolado 3/3 (não-transcrição).
- plugin-ui Vitest: 2322. DÉLIA Vitest: 387. Typecheck ambos: limpo.
- Smoke NDJSON prod: session → started @0.32s → 3 partials progressivos →
  final UTF-8 íntegro → end. SECURITY: 401 sem bearer (open e status).
- QA browser prod (Chrome + WAV pt-BR acentuado real): **14/14 PASS**
  incluindo novo A3b UNICODE_PTBR_INTEGRITY; TTFV=4550ms.

## Residuais adicionais do rework

- Provider alucina em silêncio puro (24 chars) — comportamento do provider,
  documentado; aplicação trata vazio real como segmento recuperável.
- `producal` por `produção` = erro de reconhecimento do provider, não encoding.
