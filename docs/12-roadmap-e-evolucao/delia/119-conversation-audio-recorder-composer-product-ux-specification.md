# 119 — DÉLIA | Conversation Audio Recorder — Especificação de produto, UX, estados e contrato de frontend

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
