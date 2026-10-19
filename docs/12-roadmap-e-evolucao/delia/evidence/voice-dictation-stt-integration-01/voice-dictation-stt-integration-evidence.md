# VD-F03 — Voice Dictation STT Integration — Evidence Report

**TASK_ID:** `DELIA-UX-VOICE-DICTATION-STT-INTEGRATION-01`
**DATA:** 2026-10-19
**EXECUTION MODE:** `REANCHOR → AUTHORITY REVIEW → CAPABILITY INVENTORY → REUSE GATE → CONTRACT-FIRST → IMPLEMENT → TEST → BROWSER QA → EVIDENCE → DOCUMENT → COMMIT → PUSH → REPORT`

---

## 1. Capability STT — inventário e legitimidade

| Item | Resultado |
|---|---|
| `STT_CAPABILITY_OWNER` | `delia-api` (bounded context da DÉLIA — port `SpeechTranscriptionPort`, use case `TranscribeDictation`, rotas HTTP `/dictation/*`) |
| `STT_EXISTING_EQUIVALENT` | `NO` — nenhum serviço/adapter/contrato de transcrição pré-existente; inventário VD-F01 reconfirmado; `domain/media` provê apenas vocabulário provider-neutral (`MediaObservation`, observation-only, nunca autoridade) |
| `STT_REUSE_DECISION` | `NEW` (menor integração legítima) para o boundary de aplicação; `REUSE` da família de provider **já aprovada** (`openai_compatible` / OpenRouter — mesma conta/credencial do `DELIA_LLM_*`) |
| `STT_PROVIDER` | `openai_compatible_audio` — `POST {base}/chat/completions` com `input_audio`; modelo **dedicado** `DELIA_STT_MODEL` (default de prova `google/gemini-2.5-flash`), **nunca** o modelo de interação (`kimi-k3` não aceita áudio — provado) |
| `STT_CONTRACT_STATUS` | `dictation.transcription.v1` formalizado antes do transporte: [contracts/dictation-transcription-contract-v1.md](../../contracts/dictation-transcription-contract-v1.md) |
| `STT_IMPLEMENTATION_ADMISSION` | fail-closed: capability só ativa se `provider=openai_compatible_audio` + base URL + model + API key configurados; incompleto → status `available:false`, frontend permanece local-only |
| Prova empírica do provider | `input_audio` testado com fala real pt-BR (WAV TTS + WebM real) antes da implementação; formatos aceitos `webm/ogg/mp4/wav/mp3` |

## 2. Contrato `dictation.transcription.v1`

- `GET /dictation/status` → `{available, contract_version:"1", language:"pt-BR", max_audio_bytes, max_duration_ms}`. AuthN bearer obrigatória.
- `POST /dictation/transcriptions` → `{audio_base64, mime, duration_ms, language}` → `{transcription_id, text, language}`.
- Gates: AuthN (`auth_middleware`), AuthZ Core (`delia.access` via `PlatformAccessContext`, nunca claims locais), MIME allowlist, `pt-BR` exato, duração >0 e ≤ limite, bytes >0 e ≤ 4 MiB, rate limit fixo 10/min por usuário (mapa bounded 10k), invocação do port, postcondition texto não-vazio.
- Erros tipados → HTTP 400/401/403/413/415/429/502/503/504; nunca ecoa áudio ou transcrição.
- Retenção zero: áudio transitório em memória; **logs só com metadados** (`transcription_id`, mime, bytes, duration_ms, request_id). Verificado: `docker logs` contém 0 ocorrências de conteúdo de áudio/transcrição.
- Transcrição = rascunho editável não confiável; nunca Evidence/FACT/AuthZ/ação.

## 3. Implementação

**Backend (`delia-api`):**
- `app/application/ports/speech_transcription_port.py` — port provider-neutral.
- `app/application/dictation/` — `contracts.py` (request/response), `errors.py` (tipados), `transcribe_dictation.py` (use case com todos os gates).
- `app/interfaces/http/dictation_routes.py` — blueprint `/dictation`; rejeita JSON malformado, campos desconhecidos, base64 inválido e payload oversized antes de decodificar.
- `app/infrastructure/model_invocation/openai_compatible_transcription_adapter.py` — `input_audio` base64, temperature 0, output bounded, non-streaming; mapeia timeout/transporte/429/rejeição/indisponível → `DictationError` tipado.
- `app/infrastructure/config/settings.py` + `app/composition/root_composer.py` + `app/create_app.py` — wiring fail-closed.
- `infra/docker-compose.yml` + `docker-compose.dev.yml` — passthrough `DELIA_STT_*` (secrets só via `.env`).

**Frontend (`plugins/delia` + `plugins/plugin-ui`):**
- `plugin-ui AudioRecorderControl` — EXTEND mínimo: `draft`/`discard` expostos via render props (necessário para entregar o blob ao boundary e cancelar a prévia local).
- `api/dictationClient.ts` — `fetchDictationStatus` (fail-closed em rede/malformado/não-200/versão errada) e `transcribeDictationAudio` (Blob→base64, só em ação explícita; `AbortSignal` com `code:"cancelled"`).
- `ui/DeliaComposer.tsx` — estado `transcribing` real na mesma superfície; merge do texto na posição do cursor/seleção registrada no início do ditado; erro → draft anterior preservado; resposta tardia descartada por invalidação de sessão; foco/caret restaurados; **zero `onSubmit` automático**.
- `App.tsx` — admission por `GET /dictation/status` no mount (só com token); `available===true` + limites válidos → passa `dictationTranscriber`; caso contrário captura local honesta.

## 4. Testes automatizados

| Gate | Resultado |
|---|---|
| Backend pytest (suíte completa) | **PASS 1636/1636** — `tests/test_dictation_transcription.py` = 22 testes (status admission, AuthN 401, AuthZ 403, sucesso, JSON malformado, base64 inválido, MIME não suportado, payload/duração excedidos, rate limit, erros de provider tipados, postcondition vazio, config indisponível) |
| Vitest `plugin-ui` | **PASS 2250/2250** (377 arquivos) |
| Vitest `delia` | **PASS 251/251** (21 arquivos) — ciclo ditado, merge, cancel, late-response, erros, no-auto-submit, Enter bloqueado |
| Typecheck `plugin-ui` / `delia` | **PASS** / **PASS** |
| Build `plugin-ui` / `delia` | **PASS** (`verify-host-exports` OK) / **PASS** |
| Federation | **PASS** (`verify-federation-react-patch`) |
| Ajuste honesto de testes | helpers `deliaApiCalls` afunilados para `/apps/delia-api/interaction*` (escopo correto: chamadas de turno) e mocks sequenciais passaram a responder `/dictation/*` com 404 — sem alterar expected para esconder regressão |

## 5. Browser QA (Chrome real, `e2e-delia`, stack local prod-parity)

| Check | Resultado |
|---|---|
| `GET /dictation/status` chamado e `available:true` | PASS (curl: `{"available":true,"contract_version":"1","language":"pt-BR",...}`) |
| Full page — gravar (fala real pt-BR via `--use-file-for-fake-audio-capture`) | PASS |
| `transcribing` real na mesma superfície, sem textarea/envio | PASS |
| `POST /dictation/transcriptions` disparado | PASS |
| Texto real mergeado no draft existente (`"nota prévia: "` + transcrição) | PASS — *"nota prévia: Mostre os indicadores de produção desta semana."* |
| Vocabulário operacional pt-BR transcrito corretamente | PASS |
| `turnCalls=0` após transcrição (sem auto-submit) | PASS |
| Edição + envio manual → `POST /interaction/turns` | PASS |
| Áudio sem fala (tom sintético) → erro honesto, draft preservado, sem submit | PASS |
| Companion Dock — mesmo ciclo completo com transcrição real | PASS — *"Mostre os indicadores de produção desta semana."* |
| **Total** | **20/20 PASS** |
| Logs backend | só metadados; **0** áudio/transcrição |

`FAKE_MEDIA_TEST=PASS`, `REAL_STT_TEST=PASS` (fala real sintetizada via TTS pt-BR alimentada no dispositivo fake — pipeline getUserMedia/MediaRecorder/STT reais), `HUMAN_SPEECH_ACCURACY=TEST_NOT_RUN` (fala humana presencial pendente).

## 6. Residuais e blockers

- `WER/CER formal` sobre corpus pt-BR curado = residual (avaliação qualitativa realizada com sucesso em vocabulário operacional; métricas formais requerem corpus com referências).
- Rate limit é in-process por réplica — múltiplas réplicas futuras precisam de limiter compartilhado (registrado no contrato §limits).
- Mic físico humano: `TEST_NOT_RUN` (ambiente headless); pipeline de captura idêntico.
- Deploy produção: requer rebuild `plugin-ui` + `delia` + `delia-api` e `DELIA_STT_*` materializado no `.env` do host.
- `docker-compose.yml` declara `keycloak:24.0` mas credenciais argon2 (KC 26) — ao recriar o container local foi necessário override `26.0.7` (drift local de ambiente, não de código; **fora do escopo do commit**).

## 7. Fase

`C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `C5_AUTHORIZED=NO`, `PRODUCTION_READINESS=NOT_PROVEN`. Nenhuma fase avançada; ditado é capability de entrada de texto da DÉLIA, não ACT.

**EXECUTION_STATUS:** `EVIDENCE_READY_FOR_REVIEW`
