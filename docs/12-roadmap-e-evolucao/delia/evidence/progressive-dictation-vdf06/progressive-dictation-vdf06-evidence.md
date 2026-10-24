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


---

# Dual-mode dictation — batch default + live opt-in (commit `61ff9d02da`, 2026-10-23)

Decisão do PO (spec 123 §12, commit `86ab659607`): "Gravar e transcrever"
(v1) é o padrão; "Transcrição em tempo real" (incremental.v1) é opt-in.

## Implementação

- `dictationMode.ts` — `DictationMode = "batch" | "live"`,
  `DEFAULT_DICTATION_MODE = "batch"`; estado de apresentação mount-scoped,
  sem persistência (PO: nova montagem inicia em batch).
- `DeliaComposer` — seletor `SegmentToggle` (plugin-ui canônico) acima do
  composer; `useLive = mode==="live" && incrementalTransport`; opção live
  desabilitada quando não admitida; seletor omitido quando não há live
  (UX batch intacta); aviso contextual quando live selecionado e a
  capability cai; nota de revisão não alarmista no modo live.
- Bloqueio de troca: ambos os caminhos reportam atividade via
  `onCaptureActivityChange` (batch: recorder blocking + preview +
  transcribing; live: `dictation.active`).
- Caret/seleção: snapshot via `selectionchange` + restore no remount da
  subtree (`useLayoutEffect` na troca de modo).
- Zero mudança de contrato, backend ou provider; nenhum segundo composer,
  gravador ou serviço STT.

## Testes

- Nova suíte `DeliaComposerDualMode.test.tsx` — 12 testes cobrindo
  DM-01..DM-17 (DM-18 = QA browser): default batch, live não
  auto-selecionado, batch nunca abre sessão incremental, live exige
  seleção explícita, live indisponível não ativável, fail-closed sem
  capabilities, troca idle-only, bloqueio em gravação batch e live,
  draft/caret preservados, merge v1, texto confirmado pós-live.
- `DeliaComposerIncremental.test.tsx` atualizado para o novo contrato
  (seleção explícita de live antes dos fluxos) — 6/6.
- Suite DÉLIA completa: 33 arquivos, 399 testes verde. Typecheck limpo.
  Build plugin-ui + delia + verify-host-exports verde.

## QA real de produção pós-deploy (27/27 PASS)

Chrome headless, `--use-file-for-fake-audio-capture` com WAV pt-BR
acentuado real (Maria TTS) — áudio real percorre o pipeline completo:

| Cenário | Resultado |
|---|---|
| A — batch default | A1–A9 PASS: seletor presente, batch ativo, live não auto-selecionado, controles batch, zero texto progressivo, seletor travado na gravação, transcrição real 318 chars UTF-8 limpa, zero auto-submit |
| B — live opt-in | B1–B6 PASS: seleção explícita, trigger só após seleção, texto progressivo, seletor travado, edição humana preservada, zero auto-submit |
| C — troca bloqueada | C1–C2 PASS: travada durante captura live, liberada após descartar |
| D — Companion Dock | D1–D5 PASS: seletor no dock, default batch, opt-in live, texto progressivo real |
| E — mobile 320/390px | E1–E3 PASS: ambos os modos acessíveis, default batch, gravação batch funcional |

Deploy: `up-prod-sequential.sh --build plugin-ui delia` (delia rebuilt;
plugin-ui sem mudança neste commit). Sem rebuild de backend — flag
incremental preservada para usuários que optarem por live.


---

## Composer Settings — menu de configurações + seção Ditado (spec 125, 2026-10-23)

Implementação do menu `Configurações do campo de pergunta`: a faixa
permanente `SegmentToggle` acima do composer foi removida e a escolha
batch/live migrou para um popover ancorado num botão discreto (Settings2)
na toolbar do composer, ao lado do microfone.

### Implementação (commit `77f1aa67c5`)

- `ComposerSettingsMenu` (plugins/delia): wrapper fino de produto —
  `IconButton` trigger (`aria-haspopup="dialog"`, `aria-expanded`,
  tooltip) + `AnchoredPanelPortal` canônico do plugin-ui
  (placement/flip/clamp/Escape/clique-fora/exclusividade/tema). Fecha ao
  escolher uma opção e devolve o foco ao trigger; conteúdo por composição
  (`children`) — futuras seções entram sem alterar o menu (CS-18).
- `DictationModeSettings` (plugins/delia): `fieldset`/radiogroup nativo
  "Ditado" — radios com labels/descrições honestas; live desabilitado com
  razão textual quando não admitido; `value/onChange/disabled/
  liveAvailable` controlados pelo host; zero conhecimento de STT/backend.
- `DeliaComposer`: `composerSettingsAction` injetado nas
  `secondaryActions` dos dois caminhos (batch e live) — mesmo
  MessageComposer, mesma máquina de estados, mesmo snapshot/restore de
  caret. `showSettings = liveAvailable || batchAvailable || live-selecionado`.
- Tooltip do microfone passa a nomear o modo (CS-13):
  "Ditar mensagem — Gravar e transcrever: …" /
  "Ditar mensagem — Transcrição em tempo real: …".
- Nenhuma primitiva nova no plugin-ui (reuse total de
  `AnchoredPanelPortal`/`IconButton`/`HelpTooltip`); zero backend;
  sem persistência (mount-scoped); sem settings engine/registry.
- Durante captura batch o painel de gravação ocupa a superfície (trigger
  inacessível → troca impossível); durante captura live o trigger
  permanece visível e as opções ficam disabled (consultável).

### Defeitos de teste corrigidos (ambiente, não produto)

- `VD-F05 manual edits`: jsdom enfileira `selectionchange`
  assincronamente — a fila liberava após a textarea desmontar; teste
  agora faz flush explícito do evento (padrão já usado em DM-13).
- `VD-F04 mic tooltip`: cópia atualizada para nomear o modo (CS-13) —
  expectativa ajustada à nova redação.
- jsdom alterna radio desabilitado (browser real não faz) — DM-10 passa
  a provar bloqueio via `disabled` em vez de clique no-op.

### Testes

- Nova suíte `DeliaComposerSettings.test.tsx` — 14 testes CS-01..CS-16 +
  extras (outside-click, open/close repetido, dois mounts, unmount).
- Dual-mode e incremental atualizados para o fluxo via menu — 12+6.
- Suite DÉLIA completa: 34 arquivos, **413 testes verde**; typecheck
  limpo; build verde.

### QA real de produção pós-deploy (36/36 PASS)

Chrome headless + WAV pt-BR acentuado real; transcrição batch
`Alô, alô, você pode mostrar os indicadores de produção e a situação do
coração, por favor.` (303 chars, UTF-8 limpa).

| Cenário | Resultado |
|---|---|
| A — menu + batch | A1–A14 PASS: faixa removida, trigger na toolbar, menu abre, seção Ditado, batch default, live não auto-selecionado, Escape fecha + foco restaurado, gravação batch, zero texto progressivo, trigger inacessível na gravação, transcrição real, UTF-8 limpa, zero auto-submit |
| B — live opt-in | B1–B6 PASS: menu fecha na escolha, trigger só após seleção, texto progressivo, opções disabled durante captura, edição humana preservada, zero auto-submit |
| C — bloqueio | C1–C2 PASS: opções disabled em captura live, liberadas após descartar |
| D — Companion Dock | D1–D7 PASS: trigger no dock, menu dentro do viewport, default batch, opt-in live, texto progressivo real |
| E — mobile | E1–E4 PASS: 320px e 390px — trigger visível, menu dentro do viewport, batch default, gravação funcional |

Deploy: `up-prod-sequential.sh --build delia` (só frontend; backend
intocado). Probe: `C:\temp\delia-qa\vd-cs-prod.mjs`,
screenshots `C:\temp\delia-qa\shots-cs\`. Residual conhecido:
screen-reader real `TEST_NOT_RUN` (ambiente); larguras 360/375/420 e
zoom 200% não cobertos pelo probe (320/390 PASS; layout é
width-content adaptativo).


---

## Clean Select Menu — refinamento visual do Composer Settings (spec 125 §9, 2026-10-23)

Refinamento puramente visual (commit `678f373ae0`) conforme a referência
aprovada pelo PO: o menu virou um painel flutuante clean de seleção por
linhas, abandonando a aparência de formulário com radios expostos.

### Implementação

- `DictationModeSettings`: opções como **linhas selecionáveis** — radio
  nativo mantido mas visualmente oculto (`1px`/`opacity:0`, **não**
  `display:none`, preservando teclado/leitores de tela); check `Check`
  (lucide) discreto à direita apenas na linha selecionada; seção "Ditado"
  com micro-ícone `Mic`; descrições curtas por opção; texto disabled
  atenuado sem depender só de cor.
- `ComposerSettingsMenu`: cabeçalho compacto "Configurações" +
  subtítulo "Campo de pergunta"; trigger com estado `--open` sutil;
  **contrato mínimo de fechamento por seção** — o contêiner só fecha o
  menu quando o `change` nasce dentro de `[data-close-on-change]`
  (opt-in), preservando composição para futuras seções (CL-14).
- CSS: um único painel, sem cards internos; selected = fundo accent 9% +
  check; hover via `--surface-hover`; focus-visible via
  `:has(input:focus-visible)`; zero hardcode de paleta — só tokens
  (`--delpi-ui-*`/`--primary`/`--text*`); reduced-motion respeitado.
- Nenhum comportamento alterado: captura, reconciler, bloqueio de troca,
  batch default, live opt-in, no-auto-submit intactos.

### Testes

- `DeliaComposerSettings.test.tsx`: +2 testes CL (check apenas no
  selecionado, linha inteira clicável) — 16/16; cabeçalho CS-03
  atualizado para "Configurações"/"Campo de pergunta".
- Suite DÉLIA completa: **415/415**; typecheck e build verdes.

### QA visual real de produção (21/21 PASS + prova de transcrição)

Chrome headless, deploy `678f373ae0`. Screenshots em
`C:\temp\delia-qa\shots-clean\` (a1–a4 light/dark, b dock, c 320–420,
d zoom200):

- Light: menu aberto/fechado, batch default, check só no selecionado,
  radios reais porém ocultos, live opt-in via linha — 6/6.
- Dark: tokens aplicados (labels `rgba(255,255,255,0.9)`), sem hardcode.
- Dock real: menu dentro do viewport, batch default — 2/2.
- Mobile 320/360/375/390/420px: menu dentro do viewport + zero scroll
  horizontal — 10/10.
- Zoom 200%: menu abre e opções operáveis — 2/2.
- Batch real pt-BR: `Alô, alô, você pode mostrar os indicadores de
  produção?` (55 chars, janela de captura 5s) — probe dedicado
  `vd-cs-batch-check.mjs`. Uma leitura anterior de 3 chars era janela
  de captura curta do probe, não defeito.

Residual: `SCREEN_READER_QA=TEST_NOT_RUN` (sem leitor no ambiente);
contraste AA por tokens compartilhados, não medido com ferramenta.


---

## Keep-open on selection — spec 125 §10 (2026-10-23, commit 6504887b9f)

O menu Configurações permanece aberto ao selecionar batch/live; fecha só
por saída explícita (trigger, Escape, clique externo).

### Causa-raiz e correção

O fechamento não era só o `data-close-on-change`: trocar o modo troca a
sub-árvore inteira do composer (`DeliaComposerBatch` ⇄
`DeliaComposerIncremental`), remontando o menu e perdendo o `open` local.
Correção bounded:

- `open`/`onOpenChange` hoistados para `DeliaComposer` (menu controlado);
- `data-close-on-change` removido do fieldset Ditado e o listener
  `onChange` do contêiner removido — sem mecanismo genérico (§10);
- âncora do portal virou callback-ref + estado: num mount já-aberto o ref
  ainda não está anexado quando o layout effect de posição roda; o estado
  força re-render e o efeito reposiciona (antes dependia de rAF, que o
  jsdom não dispara);
- `dismiss` só restaura foco ao trigger quando o foco estava dentro do
  painel — clique externo não rouba foco do elemento acionado (CM-03).

### Testes e QA

- `DeliaComposerSettings.test.tsx`: CM-01..CM-07 (19/19); helpers
  dual-mode/incremental agora dispensam o menu explicitamente.
- Suite DÉLIA: **418/418**; typecheck e build verdes.
- Produção `6504887b9f` (`vd-cs-keepopen-prod.mjs`): **13/13** — live e
  batch aplicam sem fechar, seleções repetidas estáveis, draft/caret
  preservados, trigger/Escape/fora fecham, dock real e 375px com painel
  dentro do viewport. Screenshots `shots-keepopen/`.

Residual: `SCREEN_READER_QA=TEST_NOT_RUN`.

## Spec 125 §11 — Motion UX (microinterações suaves)

**Task:** `DELIA-UX-COMPOSER-SETTINGS-GENTLE-MOTION-REFINEMENT-01` ·
SHA `924bbeba9c` · deploy `delpi-delia` rebuild · 2026-10-23.

### Decisões de implementação

- Entrada `--entering`: fade + translateY(5px), 160ms — suprimida em
  mount já-aberto (remount batch⇄live) via `bornOpen`, sem replay/flicker.
- Saída `--exiting`: 130ms, lifecycle do produto (não da primitiva);
  `pointer-events:none`; estado funcional fecha imediatamente
  (`aria-expanded`, `--open` do trigger); cleanup de timer no unmount;
  guards tornam Escape/clique-fora durante o exit idempotentes.
- Seleção 170ms de fundo; check opacidade+escala 160ms; trigger 150ms.
- Tudo sob `prefers-reduced-motion: no-preference`; em `reduce`,
  fechamento instantâneo medido (26ms).

### MOT-01..MOT-09

| Critério | Resultado |
|---|---|
| MOT-01 abertura suave | PASS — 160ms medido; rampa real 0.44→1.00 em ~137ms (samples rAF) |
| MOT-02 fechamento seguro | PASS — exiting 130ms depois unmount (~221ms total clique→detach) |
| MOT-03 seleção sem flicker | PASS — 170ms fundo; mount-aberto não repete entrada |
| MOT-04 check discreto | PASS — opacidade+scale 160ms |
| MOT-05 trigger suave | PASS — 150ms cor/superfície |
| MOT-06 keep-open | PASS — 4 seleções rápidas alternadas, menu aberto |
| MOT-07 reduced-motion | PASS — sem animação de entrada; fecha em 26ms |
| MOT-08 foco/caret/capture/auto-submit | PASS — Escape/clique-fora durante a entrada fecham; foco→trigger; zero auto-submit |
| MOT-09 multi-superfície | PASS — full-page light/dark, dock real, mobile 375 no viewport |

### Testes e QA

- `DeliaComposerSettings.test.tsx`: 22/22 (+MOT-01/02/03 unitários:
  classe entering no mount, fase exiting, reduced-motion instantâneo).
- Suite DÉLIA: **421/421**; typecheck e build verdes.
- Produção (`vd-cs-motion-prod.mjs`, Chrome real autenticado):
  **20/20** — durações computadas (160/170/160/150/130ms), rampa de
  opacidade frame a frame, reduced-motion, remount sem replay, Escape e
  outside-click durante animação, dock real, mobile, dark.
  Screenshots `shots-motion/`.

Residual: `SCREEN_READER_QA=TEST_NOT_RUN` (sem leitor no ambiente).

## Spec 126 — Unified Voice Capture Visual (batch + live)

**Task:** `DELIA-UX-UNIFIED-VOICE-CONTROLS-VISUAL-REFINEMENT-01` ·
SHA `252fa11239` · deploy `delpi-plugin-ui` + `delpi-delia` rebuild · 2026-10-23.

### Implementação

- Família circular unificada: mic idle e controles de sessão a 40px,
  radius 50%/999px — live ganhou a classe `delia-dictation-live__mic`
  e regra em `__controls`; batch subiu de 36→40px no scope
  `delpi-ui-audio-recorder`.
- Hierarquia de ação: Finalizar `tone="primary"` nos dois modos;
  Descartar/Cancelar `tone="danger"` (neutro em repouso, perigo só
  no hover — comportamento já existente do IconButton).
- Azul institucional: live-dot do batch sai de `--danger` para
  `--accent`; dot live usa derivação luminosa (`color-mix` 84%
  acento + branco — mesmo token, não paleta nova).
- Halo: `.delia-composer--capturing` (batch) e
  `.delia-composer--listening` (live) aplicam borda+sombra sutil de
  acento na superfície do MessageComposer.
- Motion: entrada do painel de captura 160→200ms; pulso 1.2s no dot
  live (parado quando pausado); tudo sob prefers-reduced-motion.
- Não inventado: pause no batch (não existe no recorder), amplitude
  fake (waveform usa `levels` reais), segundo painel no live.

### VOX-01..VOX-20

Todos PASS — evidência combinada: testes DOM (classes/tons/halo),
geometria medida em produção (40×40px, radius ≥ metade) e cores
computadas (acento rgb(8,155,219); live srgb 0.19/0.67/0.88 luminoso).

### Testes e QA

- DÉLIA: **426/426** (+5 testes VOX); plugin-ui: **2324/2324**;
  typecheck e build verdes nos dois plugins; federation exports OK.
- Produção (`vd-vox-prod.mjs`, Chrome real autenticado, fake mic):
  **31/31** — batch: mic/controles circulares, dot azul, halo,
  waveform real (24 barras), timer 00:01/05:00, Transcrevendo,
  transcrição pt-BR inserida editável ("Alô, alô"), zero auto-submit;
  live: mic circular, controles 40px, Finalizar primário, Descartar
  subdued-danger, dot luminoso pulsante, pausa interrompe pulso,
  textarea editável; reduced-motion sem pulso; mobile 375; dock real.
  Screenshots `shots-vox/`.

Residual: `SCREEN_READER_QA=TEST_NOT_RUN`; larguras 320/360/390/420 e
zoom 200% não cobertos pelo probe (375 coberto).
