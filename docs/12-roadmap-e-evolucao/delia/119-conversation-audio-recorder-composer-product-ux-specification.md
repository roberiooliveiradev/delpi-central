# 119 — DÉLIA | Voice Dictation Composer — Ditado por voz para texto editável

**Data:** 2026-10-19  
**Refinamento visual aprovado (VD-F04):** [120 — Voice Dictation Composer, estados visuais, motion e microinterações](./120-voice-dictation-composer-visual-refinement-ux-specification.md). Este documento 120 é a referência obrigatória para geometria, controles circulares, waveform, processamento, aviso contextual, full-page/Dock, acessibilidade e critérios VD-V01…VD-V14; o runtime de ditado/STT existente permanece inalterado até a implementação.  
**Status:** `PRODUCT_UX_SPEC / AU-F02+AU-F03+AU-F05_QA_INTEGRATION_DONE / VD-F02_MODAL_REWORK_DONE / VD-F03_STT_INTEGRATION_DONE / INDEPENDENT_REVIEW_PENDING`  
**Evidência VD-F03:** [voice-dictation-stt-integration-01](./evidence/voice-dictation-stt-integration-01/voice-dictation-stt-integration-evidence.md) — contrato `dictation.transcription.v1`, owner `delia-api`, provider family OpenAI-compatible (OpenRouter) com modelo dedicado de áudio, STT real pt-BR end-to-end (página + dock), texto editável e envio manual.  
**Evidência VD-F02:** [voice-dictation-composer-rework-01](./evidence/voice-dictation-composer-rework-01/voice-dictation-rework-evidence.md) — composição modal single-surface implementada e testada (vitest + Playwright página/dock); **STT não integrado — sem owner/contrato aprovado**.  
**Evidência de implementação:** [audio-recorder-composer-foundation-01](./evidence/audio-recorder-composer-foundation-01/audio-recorder-foundation-execution-evidence.md) — fundação local implementada e testada; **não** habilita captura em produção sem limites aprovados.  
**Evidência de integração QA:** [audio-recorder-live-qa-integration-01](./evidence/audio-recorder-live-qa-integration-01/audio-recorder-live-qa-integration-evidence.md) — gate `VITE_DELIA_AUDIO_QA=1` + `?delia-audio-qa=1` validado em Portal real (página + dock); produção permanece inerte.  
**Tipo:** documentação de direção e critérios de implementação futura; **não** altera fase, backend, contratos, permissões ou feature flags.  
**Referência GitHub observada:** `cb6ae480e202fc3d2817e1ed52bdb743531cde0f` (revalidar HEAD/status antes de implementar).  
**Produto:** DÉLIA standalone; não reutilizar runtime, serviços ou frontend do Minha DELPI Chat.

**Precedência obrigatória:** Project Instructions/`.cursor` → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → 24/product spec → specs temáticas → execution ledger. Se houver conflito, `STOP → EXECUTION_DRIFT / ARCHITECTURE_DECISION_REQUIRED`.

**Referências verificadas:** [53 — multimodal/voz e captura governada](./53-multimodal-meeting-frontline-and-industrial-copilot.md), [69 — experiência conversacional](./69-conversation-experience-ux-wireframes-and-activity-plan.md), [95 — interrupção da resposta](./95-conversation-stop-response-product-ux-specification.md), [116 — mapa de superfícies](./116-delia-frontend-capability-surface-and-component-execution-map.md), [117 — inventário F-01](./117-frontend-f01-component-export-consumer-and-gap-inventory.md); `MessageComposer.tsx`, `DeliaComposer.tsx`. A spec 54 canônica trata de biometria/governança, **não** é autorização para autenticação por voz.

## 1. Propósito e decisão de produto

Permitir que a pessoa **grave uma mensagem de áudio mediante ação explícita**, revise o material localmente e decida entre descartar ou enviar, quando e somente quando houver contrato real de envio aprovado. Oferecer experiência moderna integrada ao compositor já existente, inspirada na anatomia das capturas de referência fornecidas pelo Product Master (microfone, waveform, tempo, cancelamento, finalização, confirmação), sem replicar identidade visual, código ou detalhes exclusivos de terceiros.

Distinguir claramente três produtos/fluxos, que **não** devem ser confundidos:
1. **Mensagem de áudio:** gravação local → prévia → confirmação → envio por contrato específico quando autorizado.
2. **Ditado/transcrição:** fala → texto editável no composer mediante capacidade de speech-to-text autorizada e consentimento. **Não está incluído no MVP de gravação local.**
3. **Conversa em voz/Live hands-free:** áudio bidirecional contínuo, playback de resposta, sessão/turn-taking e interrupção. **Capability futura distinta, não autorizada por esta spec.**

Áudio é modalidade de entrada, nunca identidade, autorização, policy, FACT nem comando industrial. Nenhum áudio pode virar ACT operacional apenas pela modalidade.

## 2. Evidência atual, owners e reuso

**PROVEN no inventário dirigido:** `plugins/plugin-ui/src/components/composer/MessageComposer.tsx` possui textarea controlada, `secondaryActions?: ReactNode`, toolbar, `onSubmit`, `requestMode` e limite de caracteres; `plugins/delia/src/ui/DeliaComposer.tsx` é wrapper fino; spec 53 prevê microfone, transcrição, consentimento e indicadores visíveis de captura.

**TO_INVENTORY:** componente equivalente de recorder em todo `plugin-ui`, hooks de MediaRecorder, recursos de áudio/preview e contratos de upload/transcrição/armazenamento/retention. Busca residual ou `0 results` não prova ausência. Não há prova nesta verificação de endpoint de áudio DÉLIA, quota, formato admitido, persistência ou provider.

- `EXISTING_EQUIVALENT=YES` para shell, toolbar, botões, feedback e primitives do composer; `REUSE_DECISION=REUSE`.
- `EXISTING_EQUIVALENT=TO_INVENTORY` para captura/reprodução de áudio; `REUSE_DECISION=TO_DECIDE (REUSE|EXTEND|NEW após inventário)`. Se necessário, componente visual/captura local compartilhável pertence a `plugin-ui`, sem segunda toolbar ou outro composer.
- **Owner visual e interação local:** `plugins/plugin-ui` (tokens, UI, browser media adapter local, gestão de mídia temporária, a11y).
- **Consumer e estado da conversa:** `plugins/delia` (feature gate real, integração ao composer, erro, estado de draft, vínculo à mensagem, contrato de envio).
- **Portal:** host/foco e permissões de embedding; não captura por conta da DÉLIA.
- **Backend/Domain/Policy:** admissão de mídia, AuthZ, limites, upload, processamento, retenção, auditoria e autorização para usos posteriores. Provider, MCP/A2A e browser API não são authorities.

## 3. Anatomia visual e aparência esperada

**Estado sem gravação:** manter `MessageComposer` vigente (área de texto, contador/ações, Enviar/Interromper). Acrescentar **botão de microfone** como secondary action somente quando a capacidade local estiver admitida e a interface puder representar honestamente o que faz; ausente/desabilitado com motivo acessível caso não esteja liberada. Não insinuar que o backend aceita áudio.

**Estado gravando (após autorização do microfone):** região compacta associada ao composer, com:
- indicador inequívoco `Gravando`, duração `mm:ss`, ícone de microfone/captura ativa;
- representação de amplitude/onda **derivada do áudio capturado**; se análise não disponível, usar trilho estático e duração, sem waveform fictícia;
- ações de **Cancelar** (descarta) e **Finalizar gravação** (encerra captura e inicia preparação da prévia);
- nenhum `Enviar` concorrente com gravação ativa.

**Estado prévia:** player com play/pause, posição/duração, ações **Regravar**, **Descartar** e **Confirmar envio** apenas se contrato de envio estiver habilitado. Sem esse contrato, a UI deve indicar com clareza “Envio de áudio indisponível” e permitir descarte/regravação; não exibir envio funcional falso. Se a experiência local não tiver uso legítimo sem envio, a integração de produção permanece **feature-off**; pode existir componente testado/Storybook isolado.

**Requisitos visuais:**
- estética chat-first, institucional, minimalista, sem cards pesados, identidade do `plugin-ui` e tokens `--delpi-ui-*` / Portal;
- mesmos controls e layout adaptativo na página completa e Companion Dock; CSS condicionado por container width, não somente viewport;
- toolbar com um slot claro de ação primária em cada estado; sem salto brusco de altura, clipping ou sobreposição do texto;
- responsivo em 320/360/420px internos e desktop, light/dark, contraste, zoom 200%, touch, fonte aumentada;
- `focus-visible`, controles com ícone+nome, alvos de toque adequados, reduced motion desabilita animações decorativas mas preserva identificação da captura;
- waveform é indicativa, não controle de edição; não representar silêncio como atividade falsa.

```text
IDLE
+--------------------------------------------------------------+
| Pergunte à DÉLIA…                                            |
| [outras ações reais]  [🎙 Gravar áudio]          [Enviar ↗]  |
+--------------------------------------------------------------+

RECORDING
+--------------------------------------------------------------+
| ● Gravando     00:18      [amplitude REAL / linha estática]   |
| [Cancelar]                             [Finalizar ■]          |
+--------------------------------------------------------------+

PREVIEW
+--------------------------------------------------------------+
| [▶/❚❚] 00:18 / 00:31    [trilho de reprodução]               |
| [Descartar]    [Regravar]    [Confirmar envio*]               |
+--------------------------------------------------------------+
* Somente com contrato de envio admitido e autorização.
```

Wireframe conceitual, não UI implementada nem promessa de envio.

## 4. Estados e transições

| Estado | Entrada | UI / ação legítima | Saída |
|---|---|---|---|
| `unavailable` | gate OFF/API ausente/host inelegível | Ocultar ou desabilitar com explicação | `idle` só após habilitação legítima |
| `idle` | composer livre, gate ON | botão Gravar áudio | `requesting_permission` por gesto explícito |
| `requesting_permission` | `getUserMedia` após gesto | texto neutro “Aguardando permissão do microfone” | `recording` ou `permission_denied/error` |
| `recording` | stream+gravador confirmados | indicador persistente, timer real, Cancelar/Finalizar | `stopping` ou `discarded` |
| `stopping` | intenção Finalizar | finalização assíncrona, controls não duplicáveis | `preview` ou `error` |
| `preview` | blob local válido/finalizado | play/pause, descartar/regravar, enviar somente com capability | `sending` (gated) ou `discarded` |
| `sending` | confirmação explícita + contrato aprovado | upload real e progresso somente se medido | `sent`/`error` conforme resposta autoritativa |
| `error` | falha capturável | erro claro, ação de recuperar/descartar | `idle`/`preview` conforme erro |
| `discarded` | cancelar/desmontar/descartar | tracks stop, buffers/URLs liberados | `idle` |

**Não adotar timers artificiais para simular progresso ou duração.** Tempo de gravação acompanha relógio real somente com stream ativo. A decisão de interagir por texto durante captura e manter draft deve ser documentada: default preserva texto e evita apagar/sobrescrever conteúdo; durante recording, desabilitar submit textual concorrente para evitar envio acidental, sem perder draft. Regras de recuperação de aba/navegação devem priorizar descarte seguro; não fazer persistência silenciosa.

## 5. Funcionalidades obrigatórias do componente local

1. Solicitar permissão de microfone **somente após gesto do usuário** e informar porque é necessária.
2. Selecionar formato suportado por `MediaRecorder.isTypeSupported` e fallback honesto quando API não disponível; não assumir `audio/webm` em todos os navegadores.
3. Iniciar, pausar/retomar **somente se suportado e previsto no contrato final**, finalizar e cancelar sem leaks; escopo mínimo do MVP: iniciar, finalizar, descartar, reproduzir/regravar.
4. Detectar `NotAllowedError`, `NotFoundError`, `NotReadableError`, falhas de `MediaRecorder`, dispositivo desconectado, stream encerrado, background/unmount e indisponibilidade de HTTPS/secure context.
5. Impor limites explícitos de duração e tamanho aprovados pelo owner; **números máximos são TO_INVENTORY/CONTRACT_REQUIRED**. Sem limite aprovado, não habilitar captação aberta em produção.
6. Gerar preview local de áudio com controles acessíveis e mostrar duração real.
7. Permitir ouvir, descartar, regravar e confirmar intenção separadamente; nunca auto-send no `stop`.
8. `MediaStreamTrack.stop()` em todas as saídas, remover listeners, revogar `URL.createObjectURL`, encerrar `AudioContext` quando usado, limpar buffers/transient blobs ao descartar/unmount.
9. Não fazer requests de áudio na camada visual. O componente emite eventos tipados/callbacks; a integração real reside no consumer/port apropriado.
10. Não registrar audio bytes, blob URLs, transcrição, token, permissão ou mídia bruta em logs comuns, analytics, prompts ou Personal Memory.

## 6. Contratos propostos — alvo, não congelados

A API abaixo é **ilustrativa** e precisa de verificação no inventário e no Abstraction Gate. Não decidir uma engine/global provider por conveniência.

```ts
type AudioRecorderUiStatus =
  | "unavailable" | "idle" | "requesting_permission"
  | "recording" | "stopping" | "preview"
  | "sending" | "error";

type LocalAudioDraft = {
  blob: Blob;             // transitório, não serializável como knowledge/memory
  mimeType: string;       // negociado com browser/contrato
  durationMs: number;     // medido, não inventado
  sizeBytes: number;
};

type AudioRecorderComposerProps = {
  enabled: boolean;        // admissão de produto/consumer, NÃO AuthZ backend
  disabled?: boolean;
  busy?: boolean;          // bloqueia concorrência no composer
  maxDurationMs?: number;  // valor governado pelo owner, não default inventado
  maxBytes?: number;
  canSendAudio?: boolean;  // deriva de contrato real, não do browser
  onDraftReady?: (draft: LocalAudioDraft) => void;
  onDiscard?: () => void;
  onConfirmSend?: (draft: LocalAudioDraft) => void; // intenção, NÃO sucesso
  onCaptureError?: (reason: string) => void;
};
```

Contrato real de upload antes de `canSendAudio=true`: owner/consumers, request e media types, erros, AuthN/AuthZ live, limite de bytes/duração, idempotência, rate limit, consentimento/propósito, malware/content safety aplicável, storage/retention/revoke, observabilidade mínima, compatibilidade, outcomes e OpenAPI/`operationId` estável quando aplicável. `MediaRecorder` e metadata não aprovam esse contrato. `draft != send`; `upload HTTP 200 != conteúdo processado nem resposta autoritativa`.

## 7. Ditado por voz e processamento futuro (fora do MVP local)

**Ditado:** depende de STT aprovado e consentido; texto aparece no `MessageComposer` como **rascunho editável**, nunca como comando já enviado. Indicar confiança/limitações quando houver contrato; erros e indisponibilidade não podem converter áudio em FACT. Separar rótulos “Gravar mensagem” e “Ditar texto” e evitar misturar intenções.

**Mensagem de áudio enviada:** requer endpoint/capability real, upload governado, vínculo com turno e uma projeção multimodal de mensagem aprovada; não inventar chat attachment ou mock de áudio persistido.

**Live/hands-free, TTS, meetings e biometria:** trilhas independentes governadas pela spec 53 e demais authorities. Não reutilizar a simples captura local como autorização para gravação contínua, identificação do falante ou output de voz.

## 8. Privacidade, segurança e consentimento

- Indicador visível enquanto houver track ativa, inclusive em espera/erro de finalização; nenhuma gravação automática ao abrir DÉLIA ou Portal.
- Permissão do navegador não substitui consentimento de finalidade nem política organizacional.
- Não registrar mídia bruta por padrão e não persistir sem contrato explícito de retenção; minimização e limpeza segura são requisitos.
- Se browser negar permissão, manter texto funcionando normalmente; fornecer orientação neutra e acessível para alterar permissão manualmente.
- Captura de terceiros/reunião/ambiente industrial requer gates adicionais de finalidade, avisos e legalidade; esta spec NÃO habilita captura contínua de reunião.
- Não permitir que captura/trilha de áudio amplie Core/Domain AuthZ ou dirija ações OT/safety sem políticas e gates específicos.

## 9. Acessibilidade e QA

**A11y:** labels explícitos “Gravar áudio”, “Cancelar gravação”, “Finalizar gravação”, “Reproduzir áudio”, “Pausar áudio”, “Descartar áudio”, “Regravar” e “Confirmar envio de áudio” (último somente quando disponível). Mensagens de erro legíveis, estado de captura não comunicado apenas por cor, `role=status` único sem anúncio por segundo, foco previsível ao entrar/sair de recording/preview, teclado/Space/Enter, dispositivos assistivos, `prefers-reduced-motion`.

**Matriz mínima de testes:**
- Vitest: gate OFF, permissão concedida/negada, API ausente, captura e dados MIME, finalização, preview, play/pause, descartar, regravar, tamanho/duração, duplicação de ações, erro, cleanup/unmount, revoke URLs, no auto-send, preservação do draft, ausência de logs.
- TypeScript: `plugin-ui`, DÉLIA e consumidores afetados; build/exports/federation.
- Playwright com mocks controlados para transições; navegador real para permissão/captura quando disponível; **não declarar LIVE de microfone só com jsdom**.
- Integração: Dock 320/360/420px e full-page, dark/light, zoom 200%, reduced motion, foco/teclado, acesso ao composer texto enquanto feature OFF, coexistência com Stop Response.
- E2E envio/STT: `TEST_NOT_RUN` enquanto contratos não estiverem aprovados.
- Privacy/security: nenhum request/upload implícito, tracks sempre encerradas, nenhuma retenção ao fechar, erro não revela bytes.

## 10. Acceptance criteria

| ID | Critério |
|---|---|
| AU-01 | Captura só inicia por gesto explícito e gate legítimo |
| AU-02 | Microfone ativo sempre tem indicador perceptível |
| AU-03 | Permissão negada/indisponibilidade deixa chat de texto funcional |
| AU-04 | Finalizar não envia nada sem confirmação |
| AU-05 | Preview reproduz áudio capturado e permite descartar/regravar |
| AU-06 | Cancelar/fechar/unmount encerra tracks e libera buffers/URLs |
| AU-07 | Duração/waveform refletem captura real; sem simulação de sinal |
| AU-08 | Limites aprovados de mídia são aplicados ou feature permanece OFF |
| AU-09 | Envio só aparece/atua com contrato backend autorizado |
| AU-10 | Light/dark, Dock/full-page, focus, reduced motion, teclado e zoom sem regressão |
| AU-11 | Zero auto-submit e zero expansão indevida de autoridade |
| AU-12 | Testes, build, federation, QA e evidência no SHA/config efetivamente executados |

Sem evidência usar `PENDING | TEST_NOT_RUN | INCONCLUSIVE`, jamais PASS.

## 11. Decomposição futura e gates

- **AU-F01 — Reanchor e inventário dirigido:** HEAD/status, authorities 16→…→ledger, owner/contratos, componentes existentes, browser media APIs, limitações; saída: `EXISTING_EQUIVALENT`/`REUSE_DECISION` comprovados.
- **AU-F02 — Componente local em `plugin-ui`:** implementação tipada, render/capture/preview/cleanup, testes e Storybook/harness se já existente. **Não enviar áudio**; qualquer publicação para produção exige gate do produto e limites admitidos.
- **AU-F03 — Composição DÉLIA:** adicionar botão via `MessageComposer.secondaryActions` ou slot equivalente legítimo, sob feature gate comprovado; conservar text composer; integração audio upload/STT **OFF** até contratos.
- **AU-F04 — Integração de transporte/STT:** task distinta após contrato owner-approved; autorização live, idempotência, limites, tratamento de mídia, audit e outcome.
- **AU-F05 — Browser QA integrado:** navegação, dispositivos, permission model, transições e acessibilidade em ambiente suportado.

A sequência real e CP/RQ dependem do documento 16 e ledger no HEAD aplicável; estas IDs são organização temática, não fase aprovada. Não mudar doc 53, owners ou contratos congelados por inferência.

## 12. Decisão e status de encerramento documental

```text
DOC=119_CONVERSATION_AUDIO_RECORDER_COMPOSER
PRODUCT_DIRECTION=DOCUMENTED
IMPLEMENTATION=AU_F02_AU_F03_LOCAL_FOUNDATION_DONE (2026-10-19, evidência linkada no cabeçalho)
AUDIO_CAPTURE_RUNTIME=IMPLEMENTED_LOCAL_GATED_OFF
QA_ADMISSION=IMPLEMENTED (VITE_DELIA_AUDIO_QA bundle flag + ?delia-audio-qa=1 explícito; param inerte em produção — provado live)
PROD_DEPLOYMENT_DIAGNOSTIC=DONE (bundle prod App-CXTCxdME contém a feature com VITE_DELIA_AUDIO_QA:"" → gate OFF por design; ausência do mic em minhadelpi.com.br é comportamento projetado, não defeito — evidência audio-recorder-deployment-diagnostic-01)
CONTROLLED_TEST_ADMISSION=SUPERSEDED (permissão `delia.audio-capture.test` removida por decisão do PM — introduzida sem solicitação; evidência audio-recorder-controlled-production-test-01 mantida como histórico)
AUDIO_CAPTURE_AVAILABILITY=IMPLEMENTED (mic para todo usuário com `delia.access` — sem permissão dedicada, param ou flag; limites bounded 60s/256KB de teste; browser/secure-context fail-closed no componente; deploy prod pendente — evidência audio-recorder-remove-extra-permission-fix-01)
AUDIO_UPLOAD_CONTRACT=TO_INVENTORY
SPEECH_TO_TEXT_CONTRACT=TO_INVENTORY
PRODUCTION_MEDIA_LIMITS=CONTRACT_REQUIRED (maxDurationMs/maxBytes exigidos pelo gate; sem valores aprovados)
EXISTING_EQUIVALENT_COMPOSER=YES
REUSE_DECISION_COMPOSER=REUSE
EXISTING_EQUIVALENT_RECORDER=NO (após inventário repo-wide)
REUSE_DECISION_RECORDER=NEW (AudioRecorderControl + useLocalAudioRecorder em plugin-ui)
NO_FAKE_SEND=MANDATORY (canSendAudio=false na DÉLIA; sending/sent não implementados)
PHASE_PROGRESSION=NONE
```

> **DECISÃO DE PRODUTO ATUAL — 2026-10-19 (supersede o enquadramento anterior desta spec).** O componente em desenvolvimento é **DITADO POR VOZ**, não envio de mensagem de áudio. A experiência-alvo é `falar → transcrever → revisar/editar → enviar TEXTO por ação explícita`. O envio de áudio bruto para análise pela DÉLIA é uma **capability multimodal FUTURA e DISTINTA**, com contrato, governança e UX próprios. As seções históricas abaixo sobre recorder, preview e `canSendAudio` documentam a fundação já implementada e sua evolução; **não definem mais o objetivo funcional desta superfície**. Em conflito de linguagem entre esta decisão e trechos legados deste documento, prevalece esta decisão de produto, subordinada às authorities canônicas. Nenhuma transcrição real é afirmada como implementada.

## 0. Direção atual — Voice Dictation Composer (produto-alvo)

### 0.1 Escopo e exclusões

**Agora — `VoiceDictationComposer`:** captura deliberada de voz pelo microfone, transcrição real via capacidade Speech-to-Text legítima quando contratada, retorno de texto editável ao `MessageComposer` e envio textual **somente** por iniciativa do usuário. Português brasileiro e vocabulário operacional da DELPI devem fazer parte dos critérios de avaliação; resultado de STT é rascunho não autoritativo, não FACT e não permissão.

**Futuro separado — áudio para análise multimodal:** receber arquivo ou gravação como mídia, vincular à interação e interpretar o conteúdo de áudio; não habilitado por esta spec. Pode reutilizar captura local, **não** a autoridade, o transporte ou as decisões de retenção do ditado. Live voice/hands-free, TTS e biometria são outros escopos da spec 53.

**Estado factual:** `AudioRecorderControl`/`useLocalAudioRecorder` existem (`PROVEN`, evidências AU-F02/F03/F05); **substituição modal exclusiva da área de escrita = DONE (VD-F02)** — `MessageComposer.bodyOverride` faz o painel de captura ocupar a mesma moldura do composer (textarea/toolbar/envio não renderizados durante `requesting_permission`/`recording`/`stopping`/`preview`), com rascunho do host preservado e restauração de foco; **Speech-to-Text integrado = DONE (VD-F03)** — contrato `dictation.transcription.v1` ([doc](./contracts/dictation-transcription-contract-v1.md)), owner `delia-api` (`SpeechTranscriptionPort` + `TranscribeDictation` + rotas `/dictation/*`), provider family `openai_compatible_audio` (OpenRouter, modelo dedicado de áudio — nunca o modelo de interação); capability admitida por `GET /dictation/status`, fail-closed sem config; **envio de áudio à DÉLIA = NOT_IMPLEMENTED** (escopo futuro separado). Finalizar captura inicia `transcribing` real quando a capability é admitida (cancelável, resposta tardia invalidada por sessão), caso contrário produz **prévia local** (ouvir/descartar/regravar), nunca `transcribing` fictício nem envio.

### 0.2 Comportamento obrigatório da interface

| Estado | Interface | Efeito permitido |
|---|---|---|
| `writing` | textarea normal, microfone e envio textual existentes | editar/escrever/enviar texto conforme contrato |
| `requesting_permission` | modo de ditado **substitui** o textarea/toolbar de escrita dentro da **mesma superfície** | solicitar captura somente após gesto; cancelar retorna ao draft anterior |
| `recording` | **sem campo de digitação**, sem botão Enviar texto; indicador de mic ativo, waveform de amplitude real ou trilho neutro, duração real, Cancelar/Finalizar | capturar bounded; nenhuma submissão |
| `finalizing` | mesmo lugar do composer, estado de finalização real | parar tracks/preparar entrada sem auto-send |
| `transcribing` | indicador de operação real, cancelar se contratado; campo textual indisponível durante processamento | chamar STT apenas via contrato admitido, sem progresso fictício |
| `review` | textarea retorna com texto transcrito **editável** e foco apropriado; Enviar texto explícito | revisar, corrigir, complementar e enviar manualmente |
| `error` | erro específico + retry quando legítimo + voltar a escrever | preservar draft anterior, não inventar transcrição |
| `cancelled` | libera recursos, restaura modo escrita e draft anterior | nenhum upload/submit adicional |

**Composição visual:** não empilhar player de áudio acima de um textarea ainda visível como na versão atual. Uma única moldura do `MessageComposer` muda de conteúdo/estado; mesma API visual na página completa e no Companion Dock. Não criar segundo composer nem segundo gravador. Ícones e animação discretos, tokens `plugin-ui`, light/dark, reduced motion, keyboard/IME/focus, 320/360/420px e zoom 200%. Controles de ditado acessíveis por teclado; duração não é anunciada a cada segundo por leitor de tela.

**Draft:** manter snapshot do texto digitado ao entrar em ditado. Cancelamento, indisponibilidade e erro restauram exatamente esse texto. Após transcrição, **não sobrescrever silenciosamente** texto existente: preservar e aplicar a regra explícita de composição/edição aprovada (p.ex. inserir na posição do cursor se contratada); sem regra aprovada, requer decisão UX antes da integração. Não enviar automaticamente texto reconhecido. Reconhecimento incorreto deve poder ser editado ou descartado.

**Sem STT real:** o modo visual pode ser preparado e testado separadamente, mas **não** apresentar `transcribing` simulado, texto fictício ou indicação de funcionalidade completa em produção. Se o ditado não puder ser finalizado em texto, manter a feature de ditado OFF ou rotulada honestamente como teste isolado, sem prometer capacidade inexistente.

### 0.3 Owner, reuso e contrato

- `plugin-ui`: `MessageComposer` e primitivos de captura/apresentação, estados visuais e acesso ao microfone; **`EXISTING_EQUIVALENT=YES` para composer e captura, `REUSE_DECISION=REUSE/EXTEND` após inventário no HEAD**.
- DÉLIA MFE: composição e sessão do ditado, preservação/restauração do draft, recepção de texto transcrito, feature availability; **não** cria outro componente-base.
- Capability STT: **owner = `delia-api`** (port `SpeechTranscriptionPort`, use case `TranscribeDictation`, rotas `/dictation/status` + `/dictation/transcriptions`); provider family `openai_compatible_audio` — mesma família já aprovada para invocação de modelo da DÉLIA (OpenRouter), com **modelo dedicado de áudio** configurável via `DELIA_STT_MODEL` (prova empírica `input_audio` wav+webm pt-BR). Contrato `dictation.transcription.v1`: request/response typed, MIME allowlist, limites de bytes/duração, idioma `pt-BR`, AuthN + AuthZ Core (`delia.access`), rate limit por usuário, timeout, erros tipados, retenção zero, logs só com metadados, postcondition de transcrição não-vazia. `MCP result != FACT` e model/provider output nunca autoriza — transcrição é rascunho editável não confiável.
- Core/Portal/Keycloak mantêm owners canônicos; ditado não exige uma permissão de áudio extra e **não amplia** `delia.access` nem acesso a ações de domínio.
- A transmissão do áudio ao STT (se necessário) ocorre apenas após finalidade/consentimento informados e contrato admitido. Áudio não entra em prompts, embeddings, Personal Memory ou logs comuns. Nenhuma captura automática ou contínua de reunião/ambiente.

### 0.4 Critérios de aceite adicionais (VD-01 a VD-12)

| ID | Critério | Estado atual |
|---|---|---|
| VD-01 | Um único composer alterna escrita ↔ ditado, sem textarea enquanto grava | **DONE** — `bodyOverride` remove textarea/toolbar durante captura; sem player empilhado |
| VD-02 | Mic começa apenas após gesto e autorização do navegador | DONE — captura existente revalidada |
| VD-03 | Indicador, tempo e waveform correspondem à captura real | DONE — revalidado (mesmo componente, níveis reais) |
| VD-04 | Cancelar restaura draft e libera tracks/URLs | **DONE** — rascunho exato restaurado; tracks/object URLs liberadas pelo hook |
| VD-05 | Finalizar inicia STT real e retorna texto editável | **DONE** — `dictation.transcription.v1`; POST real com áudio webm/opus; texto real inserido no draft (QA: *"Mostre os indicadores de produção desta semana."*) |
| VD-06 | Texto reconhecido nunca é enviado automaticamente | **DONE** — `turnCalls=0` após transcrição (Playwright); submit exclusivamente manual |
| VD-07 | Texto pré-existente não é sobrescrito silenciosamente | **DONE** — merge na posição do cursor/seleção registrada ao iniciar o ditado (decisão de produto §7 do prompt VD-F03); prefixo preservado no QA (`"nota prévia: "` + transcrição) |
| VD-08 | Erro, timeout e permission denied retornam a escrita sem perda | **DONE** — erro renderizado no slot do composer com rascunho preservado |
| VD-09 | Full page e Dock com mesmo ciclo responsivo e acessível | **DONE** — Playwright 20/20 (página + dock) |
| VD-10 | STT pt-BR com termos DELPI avaliado por casos reais, correções e métricas | **DONE parcial** — fala pt-BR real transcrita corretamente com vocabulário operacional ("indicadores de produção"); corpus WER/CER formal = residual |
| VD-11 | Nenhum upload/análise de mídia multimodal ou ação operacional surge implicitamente | DONE — `canSendAudio=false`, sem envio de áudio |
| VD-12 | SHA/config/evidências QA/segurança/outcome versionadas e review independente | DONE nesta task — evidências `voice-dictation-composer-rework-01` + `voice-dictation-stt-integration-01`; review pendente |

**Sequência bounded executada:** `VD-F01` reanchor + inventory STT e contrato → `VD-F02` composição modal render-only em `plugin-ui` e DÉLIA → `VD-F03` contrato `dictation.transcription.v1` + backend (`delia-api`) + integração frontend + testes + browser QA integrado (página + dock, STT real pt-BR). Resta: review independente e deploy canônico. O roadmap/fase permanecem 16 + ledger.

---

## 1–12. Histórico da fundação Audio Recorder (legado documental)

As seções abaixo permanecem para rastreabilidade das implementações anteriores. Descrições de mensagem de áudio, prévia com player e `canSendAudio` são históricas ou relativas a uma capacidade futura e **não substituem a decisão vigente da seção 0**.

**Data:** 2026-10-19  
**Status:** `PRODUCT_UX_SPEC / AU-F02+AU-F03+AU-F05_QA_INTEGRATION_DONE / INDEPENDENT_REVIEW_PENDING`  
**Evidência de implementação:** [audio-recorder-composer-foundation-01](./evidence/audio-recorder-composer-foundation-01/audio-recorder-foundation-execution-evidence.md) — fundação local implementada e testada; **não** habilita captura em produção sem limites aprovados.  
**Evidência de integração QA:** [audio-recorder-live-qa-integration-01](./evidence/audio-recorder-live-qa-integration-01/audio-recorder-live-qa-integration-evidence.md) — gate `VITE_DELIA_AUDIO_QA=1` + `?delia-audio-qa=1` validado em Portal real (página + dock); produção permanece inerte.  
**Tipo:** documentação de direção e critérios de implementação futura; **não** altera fase, backend, contratos, permissões ou feature flags.  
**Referência GitHub observada:** `cb6ae480e202fc3d2817e1ed52bdb743531cde0f` (revalidar HEAD/status antes de implementar).  
**Produto:** DÉLIA standalone; não reutilizar runtime, serviços ou frontend do Minha DELPI Chat.

**Precedência obrigatória:** Project Instructions/`.cursor` → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → 24/product spec → specs temáticas → execution ledger. Se houver conflito, `STOP → EXECUTION_DRIFT / ARCHITECTURE_DECISION_REQUIRED`.

**Referências verificadas:** [53 — multimodal/voz e captura governada](./53-multimodal-meeting-frontline-and-industrial-copilot.md), [69 — experiência conversacional](./69-conversation-experience-ux-wireframes-and-activity-plan.md), [95 — interrupção da resposta](./95-conversation-stop-response-product-ux-specification.md), [116 — mapa de superfícies](./116-delia-frontend-capability-surface-and-component-execution-map.md), [117 — inventário F-01](./117-frontend-f01-component-export-consumer-and-gap-inventory.md); `MessageComposer.tsx`, `DeliaComposer.tsx`. A spec 54 canônica trata de biometria/governança, **não** é autorização para autenticação por voz.

## 1. Propósito e decisão de produto

Permitir que a pessoa **grave uma mensagem de áudio mediante ação explícita**, revise o material localmente e decida entre descartar ou enviar, quando e somente quando houver contrato real de envio aprovado. Oferecer experiência moderna integrada ao compositor já existente, inspirada na anatomia das capturas de referência fornecidas pelo Product Master (microfone, waveform, tempo, cancelamento, finalização, confirmação), sem replicar identidade visual, código ou detalhes exclusivos de terceiros.

Distinguir claramente três produtos/fluxos, que **não** devem ser confundidos:
1. **Mensagem de áudio:** gravação local → prévia → confirmação → envio por contrato específico quando autorizado.
2. **Ditado/transcrição:** fala → texto editável no composer mediante capacidade de speech-to-text autorizada e consentimento. **Não está incluído no MVP de gravação local.**
3. **Conversa em voz/Live hands-free:** áudio bidirecional contínuo, playback de resposta, sessão/turn-taking e interrupção. **Capability futura distinta, não autorizada por esta spec.**

Áudio é modalidade de entrada, nunca identidade, autorização, policy, FACT nem comando industrial. Nenhum áudio pode virar ACT operacional apenas pela modalidade.

## 2. Evidência atual, owners e reuso

**PROVEN no inventário dirigido:** `plugins/plugin-ui/src/components/composer/MessageComposer.tsx` possui textarea controlada, `secondaryActions?: ReactNode`, toolbar, `onSubmit`, `requestMode` e limite de caracteres; `plugins/delia/src/ui/DeliaComposer.tsx` é wrapper fino; spec 53 prevê microfone, transcrição, consentimento e indicadores visíveis de captura.

**TO_INVENTORY:** componente equivalente de recorder em todo `plugin-ui`, hooks de MediaRecorder, recursos de áudio/preview e contratos de upload/transcrição/armazenamento/retention. Busca residual ou `0 results` não prova ausência. Não há prova nesta verificação de endpoint de áudio DÉLIA, quota, formato admitido, persistência ou provider.

- `EXISTING_EQUIVALENT=YES` para shell, toolbar, botões, feedback e primitives do composer; `REUSE_DECISION=REUSE`.
- `EXISTING_EQUIVALENT=TO_INVENTORY` para captura/reprodução de áudio; `REUSE_DECISION=TO_DECIDE (REUSE|EXTEND|NEW após inventário)`. Se necessário, componente visual/captura local compartilhável pertence a `plugin-ui`, sem segunda toolbar ou outro composer.
- **Owner visual e interação local:** `plugins/plugin-ui` (tokens, UI, browser media adapter local, gestão de mídia temporária, a11y).
- **Consumer e estado da conversa:** `plugins/delia` (feature gate real, integração ao composer, erro, estado de draft, vínculo à mensagem, contrato de envio).
- **Portal:** host/foco e permissões de embedding; não captura por conta da DÉLIA.
- **Backend/Domain/Policy:** admissão de mídia, AuthZ, limites, upload, processamento, retenção, auditoria e autorização para usos posteriores. Provider, MCP/A2A e browser API não são authorities.

## 3. Anatomia visual e aparência esperada

**Estado sem gravação:** manter `MessageComposer` vigente (área de texto, contador/ações, Enviar/Interromper). Acrescentar **botão de microfone** como secondary action somente quando a capacidade local estiver admitida e a interface puder representar honestamente o que faz; ausente/desabilitado com motivo acessível caso não esteja liberada. Não insinuar que o backend aceita áudio.

**Estado gravando (após autorização do microfone):** região compacta associada ao composer, com:
- indicador inequívoco `Gravando`, duração `mm:ss`, ícone de microfone/captura ativa;
- representação de amplitude/onda **derivada do áudio capturado**; se análise não disponível, usar trilho estático e duração, sem waveform fictícia;
- ações de **Cancelar** (descarta) e **Finalizar gravação** (encerra captura e inicia preparação da prévia);
- nenhum `Enviar` concorrente com gravação ativa.

**Estado prévia:** player com play/pause, posição/duração, ações **Regravar**, **Descartar** e **Confirmar envio** apenas se contrato de envio estiver habilitado. Sem esse contrato, a UI deve indicar com clareza “Envio de áudio indisponível” e permitir descarte/regravação; não exibir envio funcional falso. Se a experiência local não tiver uso legítimo sem envio, a integração de produção permanece **feature-off**; pode existir componente testado/Storybook isolado.

**Requisitos visuais:**
- estética chat-first, institucional, minimalista, sem cards pesados, identidade do `plugin-ui` e tokens `--delpi-ui-*` / Portal;
- mesmos controls e layout adaptativo na página completa e Companion Dock; CSS condicionado por container width, não somente viewport;
- toolbar com um slot claro de ação primária em cada estado; sem salto brusco de altura, clipping ou sobreposição do texto;
- responsivo em 320/360/420px internos e desktop, light/dark, contraste, zoom 200%, touch, fonte aumentada;
- `focus-visible`, controles com ícone+nome, alvos de toque adequados, reduced motion desabilita animações decorativas mas preserva identificação da captura;
- waveform é indicativa, não controle de edição; não representar silêncio como atividade falsa.

```text
IDLE
+--------------------------------------------------------------+
| Pergunte à DÉLIA…                                            |
| [outras ações reais]  [🎙 Gravar áudio]          [Enviar ↗]  |
+--------------------------------------------------------------+

RECORDING
+--------------------------------------------------------------+
| ● Gravando     00:18      [amplitude REAL / linha estática]   |
| [Cancelar]                             [Finalizar ■]          |
+--------------------------------------------------------------+

PREVIEW
+--------------------------------------------------------------+
| [▶/❚❚] 00:18 / 00:31    [trilho de reprodução]               |
| [Descartar]    [Regravar]    [Confirmar envio*]               |
+--------------------------------------------------------------+
* Somente com contrato de envio admitido e autorização.
```

Wireframe conceitual, não UI implementada nem promessa de envio.

## 4. Estados e transições

| Estado | Entrada | UI / ação legítima | Saída |
|---|---|---|---|
| `unavailable` | gate OFF/API ausente/host inelegível | Ocultar ou desabilitar com explicação | `idle` só após habilitação legítima |
| `idle` | composer livre, gate ON | botão Gravar áudio | `requesting_permission` por gesto explícito |
| `requesting_permission` | `getUserMedia` após gesto | texto neutro “Aguardando permissão do microfone” | `recording` ou `permission_denied/error` |
| `recording` | stream+gravador confirmados | indicador persistente, timer real, Cancelar/Finalizar | `stopping` ou `discarded` |
| `stopping` | intenção Finalizar | finalização assíncrona, controls não duplicáveis | `preview` ou `error` |
| `preview` | blob local válido/finalizado | play/pause, descartar/regravar, enviar somente com capability | `sending` (gated) ou `discarded` |
| `sending` | confirmação explícita + contrato aprovado | upload real e progresso somente se medido | `sent`/`error` conforme resposta autoritativa |
| `error` | falha capturável | erro claro, ação de recuperar/descartar | `idle`/`preview` conforme erro |
| `discarded` | cancelar/desmontar/descartar | tracks stop, buffers/URLs liberados | `idle` |

**Não adotar timers artificiais para simular progresso ou duração.** Tempo de gravação acompanha relógio real somente com stream ativo. A decisão de interagir por texto durante captura e manter draft deve ser documentada: default preserva texto e evita apagar/sobrescrever conteúdo; durante recording, desabilitar submit textual concorrente para evitar envio acidental, sem perder draft. Regras de recuperação de aba/navegação devem priorizar descarte seguro; não fazer persistência silenciosa.

## 5. Funcionalidades obrigatórias do componente local

1. Solicitar permissão de microfone **somente após gesto do usuário** e informar porque é necessária.
2. Selecionar formato suportado por `MediaRecorder.isTypeSupported` e fallback honesto quando API não disponível; não assumir `audio/webm` em todos os navegadores.
3. Iniciar, pausar/retomar **somente se suportado e previsto no contrato final**, finalizar e cancelar sem leaks; escopo mínimo do MVP: iniciar, finalizar, descartar, reproduzir/regravar.
4. Detectar `NotAllowedError`, `NotFoundError`, `NotReadableError`, falhas de `MediaRecorder`, dispositivo desconectado, stream encerrado, background/unmount e indisponibilidade de HTTPS/secure context.
5. Impor limites explícitos de duração e tamanho aprovados pelo owner; **números máximos são TO_INVENTORY/CONTRACT_REQUIRED**. Sem limite aprovado, não habilitar captação aberta em produção.
6. Gerar preview local de áudio com controles acessíveis e mostrar duração real.
7. Permitir ouvir, descartar, regravar e confirmar intenção separadamente; nunca auto-send no `stop`.
8. `MediaStreamTrack.stop()` em todas as saídas, remover listeners, revogar `URL.createObjectURL`, encerrar `AudioContext` quando usado, limpar buffers/transient blobs ao descartar/unmount.
9. Não fazer requests de áudio na camada visual. O componente emite eventos tipados/callbacks; a integração real reside no consumer/port apropriado.
10. Não registrar audio bytes, blob URLs, transcrição, token, permissão ou mídia bruta em logs comuns, analytics, prompts ou Personal Memory.

## 6. Contratos propostos — alvo, não congelados

A API abaixo é **ilustrativa** e precisa de verificação no inventário e no Abstraction Gate. Não decidir uma engine/global provider por conveniência.

```ts
type AudioRecorderUiStatus =
  | "unavailable" | "idle" | "requesting_permission"
  | "recording" | "stopping" | "preview"
  | "sending" | "error";

type LocalAudioDraft = {
  blob: Blob;             // transitório, não serializável como knowledge/memory
  mimeType: string;       // negociado com browser/contrato
  durationMs: number;     // medido, não inventado
  sizeBytes: number;
};

type AudioRecorderComposerProps = {
  enabled: boolean;        // admissão de produto/consumer, NÃO AuthZ backend
  disabled?: boolean;
  busy?: boolean;          // bloqueia concorrência no composer
  maxDurationMs?: number;  // valor governado pelo owner, não default inventado
  maxBytes?: number;
  canSendAudio?: boolean;  // deriva de contrato real, não do browser
  onDraftReady?: (draft: LocalAudioDraft) => void;
  onDiscard?: () => void;
  onConfirmSend?: (draft: LocalAudioDraft) => void; // intenção, NÃO sucesso
  onCaptureError?: (reason: string) => void;
};
```

Contrato real de upload antes de `canSendAudio=true`: owner/consumers, request e media types, erros, AuthN/AuthZ live, limite de bytes/duração, idempotência, rate limit, consentimento/propósito, malware/content safety aplicável, storage/retention/revoke, observabilidade mínima, compatibilidade, outcomes e OpenAPI/`operationId` estável quando aplicável. `MediaRecorder` e metadata não aprovam esse contrato. `draft != send`; `upload HTTP 200 != conteúdo processado nem resposta autoritativa`.

## 7. Ditado por voz e processamento futuro (fora do MVP local)

**Ditado:** depende de STT aprovado e consentido; texto aparece no `MessageComposer` como **rascunho editável**, nunca como comando já enviado. Indicar confiança/limitações quando houver contrato; erros e indisponibilidade não podem converter áudio em FACT. Separar rótulos “Gravar mensagem” e “Ditar texto” e evitar misturar intenções.

**Mensagem de áudio enviada:** requer endpoint/capability real, upload governado, vínculo com turno e uma projeção multimodal de mensagem aprovada; não inventar chat attachment ou mock de áudio persistido.

**Live/hands-free, TTS, meetings e biometria:** trilhas independentes governadas pela spec 53 e demais authorities. Não reutilizar a simples captura local como autorização para gravação contínua, identificação do falante ou output de voz.

## 8. Privacidade, segurança e consentimento

- Indicador visível enquanto houver track ativa, inclusive em espera/erro de finalização; nenhuma gravação automática ao abrir DÉLIA ou Portal.
- Permissão do navegador não substitui consentimento de finalidade nem política organizacional.
- Não registrar mídia bruta por padrão e não persistir sem contrato explícito de retenção; minimização e limpeza segura são requisitos.
- Se browser negar permissão, manter texto funcionando normalmente; fornecer orientação neutra e acessível para alterar permissão manualmente.
- Captura de terceiros/reunião/ambiente industrial requer gates adicionais de finalidade, avisos e legalidade; esta spec NÃO habilita captura contínua de reunião.
- Não permitir que captura/trilha de áudio amplie Core/Domain AuthZ ou dirija ações OT/safety sem políticas e gates específicos.

## 9. Acessibilidade e QA

**A11y:** labels explícitos “Gravar áudio”, “Cancelar gravação”, “Finalizar gravação”, “Reproduzir áudio”, “Pausar áudio”, “Descartar áudio”, “Regravar” e “Confirmar envio de áudio” (último somente quando disponível). Mensagens de erro legíveis, estado de captura não comunicado apenas por cor, `role=status` único sem anúncio por segundo, foco previsível ao entrar/sair de recording/preview, teclado/Space/Enter, dispositivos assistivos, `prefers-reduced-motion`.

**Matriz mínima de testes:**
- Vitest: gate OFF, permissão concedida/negada, API ausente, captura e dados MIME, finalização, preview, play/pause, descartar, regravar, tamanho/duração, duplicação de ações, erro, cleanup/unmount, revoke URLs, no auto-send, preservação do draft, ausência de logs.
- TypeScript: `plugin-ui`, DÉLIA e consumidores afetados; build/exports/federation.
- Playwright com mocks controlados para transições; navegador real para permissão/captura quando disponível; **não declarar LIVE de microfone só com jsdom**.
- Integração: Dock 320/360/420px e full-page, dark/light, zoom 200%, reduced motion, foco/teclado, acesso ao composer texto enquanto feature OFF, coexistência com Stop Response.
- E2E envio/STT: `TEST_NOT_RUN` enquanto contratos não estiverem aprovados.
- Privacy/security: nenhum request/upload implícito, tracks sempre encerradas, nenhuma retenção ao fechar, erro não revela bytes.

## 10. Acceptance criteria

| ID | Critério |
|---|---|
| AU-01 | Captura só inicia por gesto explícito e gate legítimo |
| AU-02 | Microfone ativo sempre tem indicador perceptível |
| AU-03 | Permissão negada/indisponibilidade deixa chat de texto funcional |
| AU-04 | Finalizar não envia nada sem confirmação |
| AU-05 | Preview reproduz áudio capturado e permite descartar/regravar |
| AU-06 | Cancelar/fechar/unmount encerra tracks e libera buffers/URLs |
| AU-07 | Duração/waveform refletem captura real; sem simulação de sinal |
| AU-08 | Limites aprovados de mídia são aplicados ou feature permanece OFF |
| AU-09 | Envio só aparece/atua com contrato backend autorizado |
| AU-10 | Light/dark, Dock/full-page, focus, reduced motion, teclado e zoom sem regressão |
| AU-11 | Zero auto-submit e zero expansão indevida de autoridade |
| AU-12 | Testes, build, federation, QA e evidência no SHA/config efetivamente executados |

Sem evidência usar `PENDING | TEST_NOT_RUN | INCONCLUSIVE`, jamais PASS.

## 11. Decomposição futura e gates

- **AU-F01 — Reanchor e inventário dirigido:** HEAD/status, authorities 16→…→ledger, owner/contratos, componentes existentes, browser media APIs, limitações; saída: `EXISTING_EQUIVALENT`/`REUSE_DECISION` comprovados.
- **AU-F02 — Componente local em `plugin-ui`:** implementação tipada, render/capture/preview/cleanup, testes e Storybook/harness se já existente. **Não enviar áudio**; qualquer publicação para produção exige gate do produto e limites admitidos.
- **AU-F03 — Composição DÉLIA:** adicionar botão via `MessageComposer.secondaryActions` ou slot equivalente legítimo, sob feature gate comprovado; conservar text composer; integração audio upload/STT **OFF** até contratos.
- **AU-F04 — Integração de transporte/STT:** task distinta após contrato owner-approved; autorização live, idempotência, limites, tratamento de mídia, audit e outcome.
- **AU-F05 — Browser QA integrado:** navegação, dispositivos, permission model, transições e acessibilidade em ambiente suportado.

A sequência real e CP/RQ dependem do documento 16 e ledger no HEAD aplicável; estas IDs são organização temática, não fase aprovada. Não mudar doc 53, owners ou contratos congelados por inferência.

## 12. Decisão e status de encerramento documental

```text
DOC=119_CONVERSATION_AUDIO_RECORDER_COMPOSER
PRODUCT_DIRECTION=DOCUMENTED
IMPLEMENTATION=AU_F02_AU_F03_LOCAL_FOUNDATION_DONE (2026-10-19, evidência linkada no cabeçalho)
AUDIO_CAPTURE_RUNTIME=IMPLEMENTED_LOCAL_GATED_OFF
QA_ADMISSION=IMPLEMENTED (VITE_DELIA_AUDIO_QA bundle flag + ?delia-audio-qa=1 explícito; param inerte em produção — provado live)
PROD_DEPLOYMENT_DIAGNOSTIC=DONE (bundle prod App-CXTCxdME contém a feature com VITE_DELIA_AUDIO_QA:"" → gate OFF por design; ausência do mic em minhadelpi.com.br é comportamento projetado, não defeito — evidência audio-recorder-deployment-diagnostic-01)
CONTROLLED_TEST_ADMISSION=SUPERSEDED (permissão `delia.audio-capture.test` removida por decisão do PM — introduzida sem solicitação; evidência audio-recorder-controlled-production-test-01 mantida como histórico)
AUDIO_CAPTURE_AVAILABILITY=IMPLEMENTED (mic para todo usuário com `delia.access` — sem permissão dedicada, param ou flag; limites bounded 60s/256KB de teste; browser/secure-context fail-closed no componente; deploy prod pendente — evidência audio-recorder-remove-extra-permission-fix-01)
AUDIO_UPLOAD_CONTRACT=TO_INVENTORY
SPEECH_TO_TEXT_CONTRACT=TO_INVENTORY
PRODUCTION_MEDIA_LIMITS=CONTRACT_REQUIRED (maxDurationMs/maxBytes exigidos pelo gate; sem valores aprovados)
EXISTING_EQUIVALENT_COMPOSER=YES
REUSE_DECISION_COMPOSER=REUSE
EXISTING_EQUIVALENT_RECORDER=NO (após inventário repo-wide)
REUSE_DECISION_RECORDER=NEW (AudioRecorderControl + useLocalAudioRecorder em plugin-ui)
NO_FAKE_SEND=MANDATORY (canSendAudio=false na DÉLIA; sending/sent não implementados)
PHASE_PROGRESSION=NONE
```

## VD-F05 — Duração de ditado de 5 minutos e continuidade do rascunho (decisão de produto de 2026-10-20)

**Status:** `PRODUCT_TARGET_APPROVED / IMPLEMENTED_AWAITING_PRODUCTION_VERIFICATION`. Implementado e validado localmente com teste real de ~5 minutos (auto-stop único, transcrição real, continuidade do draft); evidência em `voice-dictation-five-minute-vdf05`.

**Intenção:** permitir até **300 segundos por trecho de voz**; ao alcançar o limite temporal, finalizar automaticamente a captura e iniciar transcrição real quando a capacidade STT estiver disponível. Ao término, devolver o texto editável ao mesmo draft (merge na posição/cursor definida pelo VD-F03), **sem enviar mensagem**. O usuário pode acionar novamente **Ditar mensagem** para outro trecho de até 300 segundos e continuar redigindo o mesmo texto. Não acumular áudio bruto entre trechos nem alegar continuidade de uma única sessão de áudio; trata-se de múltiplas capturas independentes com um draft textual contínuo.

**Estado factual antes da implementação (GitHub main observado em 2026-10-20):** `plugins/delia/src/audio/audioCaptureTestAdmission.ts` contém `DELIA_AUDIO_TEST_MAX_DURATION_MS=60000` e `DELIA_AUDIO_TEST_MAX_BYTES=256000`; o contrato `dictation.transcription.v1` documenta padrões backend `DELIA_STT_MAX_DURATION_MS=120000` e `DELIA_STT_MAX_AUDIO_BYTES=4194304` (4 MiB), com admissão frontend pelo mínimo dos limites.

**Estado pós-implementação:** limites de produto `DELIA_AUDIO_PRODUCT_*` = 300000 ms / 8388608 bytes; resolução efetiva = `min(produto, contrato)` via `resolveAudioCaptureLimits` a partir do status do backend. Backend permanece env-driven: defaults `DELIA_STT_MAX_DURATION_MS=300000` e `DELIA_STT_MAX_AUDIO_BYTES=8388608` (compose dev/prod + `settings.py`). Evidência real: captura Chrome webm/opus de 300 s ≈ **4,39 MB** — o bound antigo de 4 MiB era insuficiente (provocado por teste real); 8 MiB cobre com margem. Auto-stop aos 300 s reutiliza o caminho `recorder.stop()` → `onstop` → `finalizeBlob` (executado uma única vez); contador `mm:ss / 05:00`; aviso discreto nos últimos 30 s; limite atingido renderiza nota informativa, nunca alerta de erro; merge respeita cursor/seleção, separa trechos com espaço limítrofe e trunca honestamente no limite de caracteres do composer.

**Requisitos de implementação:**
1. Fonte de limites deve permanecer governada pelo contrato/admission existente, sem hardcode divergente no componente. Alinhar frontend, backend e limites efetivos do provider; confirmar envelope MIME/bytes com evidência de captura real em 300s (bitrate pode variar por dispositivo/navegador). Não elevar bytes arbitrariamente, contornar limites por client ou supor que o modelo aceita 5 minutos.
2. Ao chegar em 300s, executar o mesmo caminho seguro de Finalizar existente (stop/cleanup → STT → edição), com idempotência no estado do frontend, não descartar trecho por transição `duration_exceeded`. Interromper antecipadamente se chegar ao limite legítimo de bytes, reportando a causa e preservando o draft; tentar preservar/transcrever a captura se o contrato permitir e for segura, sem prometer transcrição quando inviável.
3. Cronômetro discreto `mm:ss / 05:00`; aviso não intrusivo perto do limite (por exemplo, aos 4m30s) **sem** banner global nem spam `aria-live`; diferenciação clara entre Finalizar, Cancelar e auto-finalizar; reduced motion/HelpTooltip compartilhado.
4. Transcrição concluída: inserir o trecho na posição do cursor segundo regra existente; preservar texto anterior e seu limite de caracteres; novo clique em mic inicia captura independente e mantém o draft; cancelar ou falhar não apaga texto anterior e respostas tardias continuam descartadas.
5. Estado de transcrição honesto, sem auto-submit, sem envio de áudio para análise multimodal, sem criar novo recorder/provider/permission. Limites de custo, privacidade, tempo de retenção e taxa de requisição devem continuar governados.
6. Testes de relógio falso nos limites 4:30/5:00, at-most-once Finalizar, limpeza do MediaStream, bytes-limit-first, cancelamento, falha de STT, draft com dois trechos sucessivos, merge com cursor, 16.384 caracteres, página e Dock, foco, a11y e revisão do contrato; um teste real de áudio próximo ao teto no SHA/config avaliado para comprovar tamanho e compatibilidade.

**Gates:** `EXISTING_EQUIVALENT_RECORDER=YES / REUSE_DECISION=EXTEND`; `EXISTING_EQUIVALENT_STT=YES / REUSE_DECISION=EXTEND` apenas limites/contrato se owner aprovar; sem novo serviço. Se o backend/modelo/host não admitir 300s e payload correspondente, documentar `ARCHITECTURE_DECISION_REQUIRED` antes de mudar mecanismo. Não alterar STT em produção ou claims de disponibilidade sem evidência.

**Critérios locais:** `VD-T01` 300s configurados e admitidos end-to-end — **PASS** (status live `max_duration_ms=300000`; resolver `min` testado); `VD-T02` auto-finalizar uma vez e transcrever — **PASS** (auto-stop único medido aos ~300s, `transcribeCalls=1`); `VD-T03` dois ditados acumulam texto — **PASS** (vitest + QA real); `VD-T04` sem perda de draft/auto-submit — **PASS** (`turns=0`, draft preservado em falha e cancelamento); `VD-T05` limite de bytes com tratamento seguro — **PASS** (captura real 300s >4MiB → `limit_bytes` fail-closed honesto; bound elevado a 8MiB com evidência); `VD-T06` QA full-page + Dock — **PASS** (15/15 página, 8/8 dock); `VD-T07` prova real de cinco minutos sob limites efetivos — **PASS** (payload real 4.387.114 bytes, transcrição real 10.939 chars, sem auto-submit).
