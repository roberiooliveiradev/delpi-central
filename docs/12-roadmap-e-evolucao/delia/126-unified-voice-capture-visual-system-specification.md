# DÉLIA — Unified Voice Capture Visual System
## Especificação de produto, componentes e subcomponentes — Batch + Live

**Data:** 2026-10-23  
**Status:** IMPLEMENTED (2026-10-23, SHA `252fa11239`) / RUNTIME_CHANGED  
**Owner produto:** DÉLIA (`plugins/delia`)  
**Owner primitivos visuais compartilhados:** `plugins/plugin-ui`  
**Consumers:** DÉLIA full-page, Companion Dock real, mobile  
**Repositório:** `roberiooliveiradev/delpi-central`  
**HEAD inventariado ao redigir:** `aa0a195c0fe7ca054ecdf372a0617b8d8f952dbb` — revalidar HEAD atual antes da implementação.  
**Relacionado:** docs 119, 120, 123, 124, 125; `dictation.transcription.v1` (batch) e `dictation.incremental.v1` (live); ledger no HEAD.

> **Decisão do Product Owner:** harmonizar visualmente os dois modos de ditado da DÉLIA, com **azul institucional**, **botões de áudio circulares da mesma família**, **status legível**, **movimento suave** e **mesma linguagem de componentes**. O batch deve transmitir captura/estabilidade; o live, escuta/continuidade. A diferença funcional entre modos é preservada. Não transformar live em tela de captura exclusiva e não tornar batch um editor progressivo.

## 1. Evidência e inventário, sem presumir implementação

Observação de screenshots reais: batch exibe painel de captura com ponto vermelho, timer, pequenos traços azuis e ações de cancelar/finalizar; live exibe editor com uma fileira de controles mais quadrados, status “Ouvindo...” e tempo abaixo do composer. As diferenças de forma, hierarquia de ações, cor e posição visual geram falta de coesão. Screenshots demonstram a experiência, não a causa técnica ou o contrato de UI.

**PROVEN no HEAD inventariado:**
- `plugins/plugin-ui/src/components/composer/AudioRecorderControl.tsx` — gravação local e superfícies `trigger`/`captureView`, estados de captura, pausa, cancelamento, finalização e prévia; usa `IconButton`; não deve ser duplicado.
- `plugins/plugin-ui/src/components/composer/MessageComposer.tsx` — superfície única, `bodyOverride` e `secondaryActions`.
- `plugins/delia/src/ui/DeliaComposer.tsx` — composição batch, comandos e status live, `delia-dictation-live__controls`, `delia-dictation-live__status`, `delia-dictation-live__duration`; batch monta `AudioRecorderControl`, live controla streaming pelo fluxo existente.
- `plugins/delia/src/index.css` — classes `delia-dictation*` e styling específico existente.
- `ComposerSettingsMenu`, `DictationModeSettings` e `AnchoredPanelPortal` continuam responsáveis pela seleção batch/live; esta especificação **não** altera seu contrato nem o keep-open.

**TO_INVENTORY antes de codificar:** tokens de azul/radius/motion; API pública de `IconButton` (tamanho, variant, estado pressed e radius), elementos de waveform reais versus decorativos, contratos de `AudioRecorderControl` e `audioRecorderTypes`, privilégios/limites de `bodyOverride`, padrões existentes de `VoiceControls`, `Waveform`, `StatusIndicator` e acessibilidade. Pesquisa residual com zero resultados **não prova ausência**.

**REUSE GATE inicial:** `EXISTING_EQUIVALENT=YES` para gravador, composer, estados e botões; `REUSE_DECISION=EXTEND` como direção, sujeito ao inventário detalhado e Abstraction Gate. **Não** introduzir um segundo gravador, serviço STT, composer, controlador de áudio ou status engine.

## 2. Direção visual comum

**Linguagem:** superfície escura/clara conforme tema; azul da DELPI como acento de atividade (token legítimo do design system), bordas de baixo contraste, radius consistente, ícones Lucide coerentes, tipografia hierárquica, feedback suave e reduzido movimento quando solicitado. Nada de vermelho como cor principal de gravação: vermelho somente indicador de captação ou feedback semântico já governado; cancelamento não deve assumir aparência de erro permanente.

**Mesma família visual:** microphone trigger, pause/resume, stop/finalize e discard seguem formato circular, dimensões harmônicas, centralização de ícones, foco e transição. Distinguir semanticamente ações por ícone, rótulo acessível e hierarquia visual, não por cor apenas.

**Tokens:** usar `--delpi-ui-*` / design tokens reais inventariados. Azul profundo/azul luminoso são variações **derivadas do mesmo token/nível semântico**, não paletas independentes hardcoded; dark/light e contraste controlam luminosidade. Não escolher números hex fixos a partir do mock. Batch = atividade azul estável; live = azul levemente mais luminoso, somente se contraste/tokens suportarem.

### 2.1 Quadro visual — tabela de tokens / tratamentos

| Elemento | Batch | Live | Invariante |
|---|---|---|---|
| Mic idle | neutro circular | neutro circular | mesma dimensão/ícone |
| Captura ativa | botão/controle primário azul profundo | acento azul mais luminoso | token de brand/contraste |
| Pause / resume | círculo secundário | círculo secundário | mesma dimensão/radius |
| Finalizar (Square) | círculo azul de ação principal | círculo azul de ação principal | mesmo significado e aria-label específico |
| Descartar | círculo neutro; hover crítico discreto | círculo neutro; hover crítico discreto | não confundir com Finalizar |
| Status | “Gravando” + elapsed/limite | “Ouvindo...” + elapsed | mesmo nível tipográfico |
| Indicador | atividade de áudio suave | escuta/atividade mais viva | visual não é prova de áudio reconhecido |
| Fundo ativo | superfície elevada leve | composer/editor preservado + borda sutil | mesmo sistema de sombras/bordas |
| Pausado | estado atenuado, movimento imóvel | estado atenuado, movimento imóvel | status explícito |
| Processando | feedback “Transcrevendo...” | finalizando segmentos / conclusão honesta | sem fake progress |
| Concluído | texto final editável no composer | texto confirmado editável | sem auto-submit |

## 3. Quadro visual A — batch “Gravar e transcrever”

**Layout funcional alvo (esquemático, não pixel-perfect):**

```text
┌─────────────────────────────────────────────────────────────┐
│ ●  Gravando          00:06 / 05:00     ▁▂▃▂▁▃▂▁▂           │
│                                                             │
│  (◯ Pausar)    (◯ Descartar)               (● Finalizar)    │
│                                                             │
│  Sua fala será usada para transcrição; revise antes de enviar.│
└─────────────────────────────────────────────────────────────┘
```

- O batch **substitui temporariamente o corpo do composer pela superfície de gravação existente** (`MessageComposer.bodyOverride`), sem criar modal externo ou editor concorrente. Quando finalizar, a transcrição v1 ocorre e o editor volta para revisão do texto.
- Timer `elapsed / limite` permanece verdadeiro ao limite admitido, sem valores hardcoded.
- Waveform: reutilizar amplitude real **apenas se captura/contrato já fornecem amplitude**; se não houver, usar indicador de atividade não enganoso, sem fingir áudio real.
- Área de captura mantém disclosure de finalidade e privacidade já aprovado, com texto pequeno e legível.
- Ação primária “Finalizar gravação” é circular azul; secundárias “Pausar/Retomar” e “Descartar/Cancelar” são circulares neutras, com feedback ao hover/foco.
- Em erro/negação de microfone, apresentar tratamento contextual real, sem animação contínua nem perda de draft.

## 4. Quadro visual B — live “Transcrição em tempo real”

**Layout funcional alvo (esquemático):**

```text
┌─────────────────────────────────────────────────────────────┐
│ Pergunte à DÉLIA...                                        │
│ Preciso consultar os indicadores de produção desta semana. │
│                                                             │
│ (⚙) (◯ Pausar) (◯ Finalizar) (◯ Descartar)          Enviar  │
└─────────────────────────────────────────────────────────────┘
  ● Ouvindo...                                      00:06
  Sua fala será usada para transcrição; revise antes de enviar.
```

- **Editor permanece ativo e editável durante fala**: não substituir textarea por painel de waveform, não bloquear cursor/seleção, não animar o próprio texto reconhecido de forma que interrompa IME/edição. Informações transitórias permanecem no status strip existente.
- Controls de `DeliaComposer` devem ser visualmente equivalentes aos controles do batch: **circulares**, mesmo diâmetro e padding, ícones centrados, mesma hierarquia primária/secundária, azul de atividade; `settings` pode seguir sua aparência neutra própria e não precisa virar comando de gravação.
- Status “Ouvindo...” + timer seguem linguagem do batch, mas preservam limite/status real de live; sinal de pulso comunica mic ativo, **não** reconhecimento garantido ou progresso fictício.
- Não expor comportamento batch no live: streaming/parciais seguem mecanismos existentes, sem criação de novo serviço.
- Indicadores e textos não devem saltar ao receber deltas. Respeitar `reconciler`, seleção humana e ausência de envio automático.

## 5. Quadro visual C — inventário de subcomponentes e boundaries

| Componente/subcomponente | Owner legítimo | Papel | Direção |
|---|---|---|---|
| `MessageComposer` | plugin-ui | superfície única, bodyOverride, ações | REUSE |
| `AudioRecorderControl` | plugin-ui | fluxo batch e subestados de gravação | EXTEND visual, sem API paralela |
| `IconButton` ou primitive equivalente | plugin-ui | botões semânticos e acessíveis | REUSE/EXTEND tokens |
| `DeliaComposerBatch` / trecho batch existente | plugins/delia | adaptação da captura/STT v1 | REUSE |
| `DeliaComposerIncremental` / trecho live existente | plugins/delia | contexto live e botões/status | EXTEND apresentação |
| `VoiceCaptureActionControls` | candidato, **não aprovado** | possível composição visual comum caso prova de dois consumidores reais | ABSTRACTION_GATE |
| `VoiceActivityIndicator` / `VoiceStatusRow` | candidatos, **não aprovados** | semântica visual unificada para status | INVENTORY_FIRST |
| `ComposerSettingsMenu` / `DictationModeSettings` | plugins/delia + primitivas plugin-ui | preferência de modo | REUSE UNCHANGED |
| STT batch/live, hook/reconciler | owners atuais | captura/transcrição/edição | NO CHANGE |

**O objetivo não é criar necessariamente novos subcomponentes.** Se os dois consumidores reais tiverem contrato compartilhável, justificar a extração render-only em `plugin-ui`; caso contrário, reaproveitar `IconButton`, tokens, classes/variants documentadas e composição legítima no respectivo owner. Qualquer nova prop exige API e testes de consumers. Proibir generic registry e imports cruzados de implementation detail.

## 6. Estados visuais e transições — quadro completo

| Estado | Tratamento | Interação/semântica | Motion |
|---|---|---|---|
| `idle` | mic neutro circular, sem halo | clique solicita captura admitida | hover 140–180ms |
| `requesting_permission` | estado de espera neutro | sem simular captação | indicador discreto |
| `recording` (batch) | acento azul profundo; timer e sinal | pause/finalize/discard reais | halo lento se aprovado |
| `listening` (live) | acento azul luminoso; editor intacto | partials/finais reais | pulso suave e não intrusivo |
| `paused` | fundo atenuado e ícone Play | retoma capture conforme contrato | pulso interrompido |
| `finalizing` | feedback azul informativo | bloquear duplicidade de submit/click | fade curto |
| `transcribing` | rótulo honesto, sem barra fake | preservar texto/draft | indicador suave |
| `review` | controles de áudio deixam modo ativo | texto editável, envio manual | volta suave ao idle |
| `recoverable_error` | aviso contextual, sem pânico cromático | recuperar quando permitido | sem loop decorativo |
| `terminal_error` | mensagem útil, fail-closed | não fingir sucesso | sem loop |
| `cancelled/discarded` | retorno ao idle | respeitar cancelamento e draft | transição discreta |

### Motion tokens alvo (sujeitos a design system)

- Hover/press/focus background: **140–180ms**; foco acessível imediato.
- Entrada/saída de estado capture: **180–220ms**, somente transform/opacity/color/border/shadow compositável sem layout shift.
- Pulso ativo: lento, leve, não distrativo; sem tremulação nem informação falsa; pausa cancela pulso.
- Waveform: sinal real quando disponível; não inventar amplitude. `prefers-reduced-motion: reduce` desabilita pulso, waveform decorativa animada e movimentos não essenciais.
- Não animar texto digitado, caret, layout, width/height, coordenadas do portal nem controle de machine state. Não criar timer extra para estado operacional apenas por animação.

## 7. Especificação geométrica e ergonomia

- Ícones e botões de ações de áudio devem usar **mesma família de tamanhos** do `plugin-ui`; alvo visual inicial: círculos com área de interação **40–44px**, mobile com target confortável conforme design system e critérios de acessibilidade.
- Botão principal mais destacado que secundários por preenchimento e contraste, não por diâmetro radicalmente diferente. Todos os controles devem ter `border-radius: 50%` ou token `full` legítimo, sem deformação em flex shrink. `width=height` efetivos.
- Espaçamento horizontal de controles consistente. Agrupar comandos da sessão (pause, finish, discard) semanticamente; não tirar settings/Enviar da ordem ou tornar ações conflitantes.
- Status/timer usam `tabular-nums` para evitar jitter. Disclosure ocupa altura estável, não altera foco/editor nem causa jumps por evento parcial.
- Full-page, Dock real e mobile 320/360/375/390/420; zoom 200%; dark/light, mínimo 44px de hit target onde contrato/padrão permitir; sem clipping/scroll horizontal global.
- A transição do `bodyOverride` batch para editor ao finalizar deve preservar snapshot/caret/draft conforme mecanismo vigente. Live permanece contínuo.

## 8. Acessibilidade, segurança e credibilidade

- `aria-label` contextual: “Iniciar gravação”, “Pausar gravação”, “Retomar gravação”, “Finalizar gravação”, “Descartar gravação”; live usa “ditado”/“captura” conforme semântica existente. Ícones não substituem labels.
- `aria-pressed` apenas quando realmente semanticamente apropriado; estados disabled e busy explicáveis. Fokus order previsível e restaurado, foco visível, Escape conforme mecanismo existente.
- Não usar só azul/vermelho para comunicar estados; status textual obrigatório.
- `prefers-reduced-motion` respeitado, sem motion que cause mal-estar.
- Seguir admissão backend e browser permission existentes; model output e STT são conteúdo não confiável; áudio não vai para provider novo; nenhum auto-submit.
- **Nunca equiparar waveform/pulso com confirmação de captação ou reconhecimento**, nem usar visual de sucesso até postcondition real.

## 9. Acceptance matrix — VC-01 a VC-24

| ID | Critério observável |
|---|---|
| VC-01 | Mic batch e live mesma geometria circular e affordance |
| VC-02 | Pausar/retomar mesmo estilo de controles secundários |
| VC-03 | Finalizar ambos com ícone Square e destaque azul primário |
| VC-04 | Descartar ambos neutro por default, sem aparência destrutiva excessiva |
| VC-05 | Hierarquia azul institucional, dark/light tokenized |
| VC-06 | Batch + live diferenças apenas por estado/nuance, mesma família |
| VC-07 | Status textual “Gravando”/“Ouvindo” e timer sem jitter |
| VC-08 | Batch waveform real quando provido; fallback honesto |
| VC-09 | Live não inventa waveform ou audio-level |
| VC-10 | Layout batch como capture bodyOverride; retorna editor para review |
| VC-11 | Live textarea permanece editável com caret livre |
| VC-12 | Pulso suave somente em captura ativa, pausa interrompe |
| VC-13 | Motion curto de hover/press/enter/exit sem layout shift |
| VC-14 | Reduced-motion remove decorativos sem perder feedback |
| VC-15 | Identidade visual da toolbar/coordenadas estável; settings preservado |
| VC-16 | Full-page dark/light QA real |
| VC-17 | Companion Dock nativo e seus estados |
| VC-18 | Mobile 320/360/375/390/420 + zoom 200% |
| VC-19 | Foco, teclado, accessible names e disabled states |
| VC-20 | Batch v1 envia áudio só após finalizar e gera texto revisável |
| VC-21 | Live v1 incremental, falhas segment-scoped, sem regressão do reconciler |
| VC-22 | Texto, seleção, draft recovery e fila preservados; no auto-submit |
| VC-23 | Reuse proven, sem duplicar capture ou provider/contratos |
| VC-24 | Evidência visual e funcional SHA/config + ledger + deploy pós-gates |

## 10. QA requerido e produção

1. Inventariar `AudioRecorderControl`/variants de botão/status e CSS, com owners/consumers/contratos; revisar spec 125 e `plugin-ui` guidance antes de propor abstração.
2. Gravar baseline com screenshots/vídeo de **ambos os modos em idle, gravando/ouvindo, pausado, finalizando, revisando**, com numeração consistente.
3. RED tests para semântica de estilo/controle (classes, foco, labels, aria), e testes de estado reais; não congelar pixels em snapshots frágeis como único teste.
4. Implementar menor diff nos owners. Se `plugin-ui` for alterado, verificar API pública e consumers existentes, exports/federation e regressões compartilhadas.
5. Browser visual QA com áudio real autorizado em full-page e Dock; mobile/zoom e temas; evidência de motion por gravação/frame, não somente screenshot.
6. Regressões de batch, live, ditado, composer, settings, DraftRecovery, ConversationQueue, Stop/Cancel, Markdown B2, accessibility e privacy gates. `SCREEN_READER_QA=TEST_NOT_RUN` se indisponível.
7. Reworks até PASS ou bloqueio comprovado; documentar gaps honestamente. Commit/push ff main, deploy frontend scoped após gates, verificar deployed SHA e postcondition real. `HTTP 200` sozinho não aceita tarefa.

## 11. Gates de decisão / não escopo

`EXISTING_EQUIVALENT=YES` (captura, composer, botões); `REUSE_DECISION=EXTEND` alvo, revalidar. **Não escopo:** mudança STT, novo provider, nova capability, modo default, seleção do menu, scheduler, Authorization, settings engine, wavefake baseada em temporizador, LLM para animação, transcrição palavra a palavra não suportada, design system paralelo.

Se amplitude de áudio não estiver disponível no contrato compartilhado, registrar `TO_INVENTORY/ARCHITECTURE_DECISION_REQUIRED` para visualização signal-driven, sem abrir outro processor por conveniência.

**Task futura sugerida:** `DELIA-UX-UNIFIED-VOICE-CONTROLS-VISUAL-REFINEMENT-01`. **Documentação apenas — nenhum código, teste ou deploy executado por esta alteração.**
