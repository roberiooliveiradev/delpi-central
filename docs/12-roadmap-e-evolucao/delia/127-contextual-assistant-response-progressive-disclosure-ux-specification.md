# DÉLIA — Resposta Conversacional com Contexto Progressivo — Especificação de UX

**Data:** 2026-10-23. **Status:** IMPLEMENTED_AND_HOMOLOGATED (2026-10-24, commit `3c89d222b5`, deploy prod + QA autenticado 18/18). **HEAD de referência:** cd5f349f7148bfc6ee059f37980b08216a0fc05a. **Produto:** DÉLIA (standalone). **Escopo:** apresentação de mensagens do assistente em full-page e Companion Dock, sem alteração de autorização, evidence/decision gate, runtime, protocolos ou modelos.

## 1. Motivação e intenção do Product Owner

Na captura de conversa real, a saudação “Olá! Tudo bem? Sou a sua DÉLIA...” apareceu dentro de card azul alto, com “Atividade concluída”, “Ver detalhes”, “Sem fonte vinculada” e “Detalhes da evidência”. O conteúdo conversacional simples ficou visualmente secundário frente aos indicadores de execução/proveniência. A decisão é priorizar **resposta legível e natural**, oferecendo **contexto progressivo** quando acrescentar informação sem esconder incerteza relevante.

Os screenshots são evidência de problema de UX, **não** prova de defeito de grounding/authority. Não remover contextos ou metadados estruturados para obter visual mais limpo.

## 2. Direção visual

- A resposta da DÉLIA integra o fluxo da conversa, com avatar institucional, identificação discreta e corpo de mensagem como protagonista; **sem card azul pesado/envelope de altura mínima** para uma resposta simples.
- Hierarquia: identidade discreta → conteúdo real → ações legítimas (ex.: Copiar) → contexto/proveniência colapsável quando aplicável. Não repetir “DÉLIA” e avatares sem necessidade.
- Fundo majoritariamente transparente/neutral; borda/realce apenas para elementos semânticos (alerta real, outcome, referências, blocos estruturados). Preservar Markdown, listas, código, tabelas e demais componentes já aprovados.
- Espaçamento determinado pelo conteúdo, legibilidade tipográfica e alinhamento consistente com mensagens do usuário; evitar espaços vazios em card longo.
- Hover e transições suaves de 160–200ms para expandir contexto sem provocar layout jump; não atrasar conteúdo, não animar palavras ou prejudicar screen readers. Reduced-motion respeitado.

## 3. Variantes de apresentação — não classificações de autoridade

As seguintes são **variantes de apresentação derivadas de dados estruturados existentes**, sem segundo planner, novo classificador LLM, novos fatos ou branches baseados em palavras da resposta.

### Variante A — Conversacional

Saudação, orientação geral ou conteúdo que não exigiu consulta de fonte operacional, **quando isso for sustentado pelo contrato real**. Mostrar avatar, nome, conteúdo e ações disponíveis. Não exibir “Sem fonte vinculada” como anomalia, nem “Atividade concluída” se não houver atividade operacional material a destacar. Não falsificar a existência/ausência de fontes só pelo texto “olá”.

### Variante B — Resposta contextualizada

Quando houver observações/fonte/proveniência real no envelope de resposta, apresentar corpo e indicador discreto “Fontes”/“Contexto” com acesso à proveniência autoritativa e suas limitações. Não converter provider/tool metadata em FACT. Não criar links ou citações fictícias.

### Variante C — Atividade, investigação ou ação governada

Para activity/work/outcome real e tipado, mostrar estado importante e resultado na mensagem, com detalhes de execução/evidências progressivamente acessíveis. **HTTP 200, completion técnico e texto do modelo não provam business outcome.** Estados de erro, pendência, preparação/confirmação e riscos materiais permanecem visíveis, não ficam escondidos exclusivamente dentro de popover.

As variantes podem coexistir; usar composição dos componentes reais conforme contrato. Não usar strings/regex sobre resposta para decidir modo.

## 4. Disclosure de contexto e evidência

- “Contexto”, “Fontes”, “Detalhes da execução” ou “Evidências” são affordances **somente quando há conteúdo correspondente legítimo**; nomenclatura ajustada ao tipo real.
- Em saudação comum, omitir rótulos de origem não exigida; **não** converter ausência de fonte em warning. Quando uma pergunta precisar de fonte, mas grounding estiver ausente/inconclusivo, preservar limitação de forma clara e visível.
- Um bloco de contexto progressivo pode reunir, por composição, status, proveniência e evidências sem duplicar a fonte de verdade.
- Conteúdo de execução só deve declarar “Concluída” se esse for o estado de activity real, e não confundir com outcome aceito.
- Citações, links, provas, segurança e políticas permanecem ligados aos contratos de backend, sem inferências do UI.
- Não excluir tracking, audit, evidência ou disclaimers por estética. Avisos materiais não podem depender de clique para serem conhecidos.

## 5. Contratos e ownership

Reancorar e localizar no HEAD os documentos canônicos de conversation UI, presentation envelope, evidence projection, activity status, Markdown e componentes compartilhados antes de codificar. **Nenhum caminho de documento ou nome de componente hipotético é evidência de existência.**

**Owner:** `plugins/plugin-ui` para componentes reutilizáveis de mensagem, avatar, ações, disclosure e design system; `plugins/delia` para composição e interpretação de apresentação **de contratos tipados já admitidos**; DÉLIA backend mantém Evidence/Policy/Decision/Outcome; Domain APIs são autoridade sobre dados, Core sobre AuthZ. Nunca transportar essas autoridades para o frontend.

**Reuse Gate na execução:** `EXISTING_EQUIVALENT=TO_INVENTORY`, `REUSE_DECISION=TO_DECIDE`. Primeiro inventariar componentes de assistant message, evidence footer, activity details, status, avatar, copy, Markdown, rich responses e seus consumers. Se existir componente canônico, REUSE/EXTEND. Não criar `ConversationAssistantMessage`/registry/engine novo apenas por similaridade conceitual.

**Contratos antes do diff:** identificar owner/consumers, campos de status, evidência, source, errors, postcondition, compatibilidade e estados negativos. Não produzir classificações de autoridade a partir da aparência.

## 6. Comportamento e acessibilidade

- Progressive disclosure acessível por botão real com `aria-expanded`, heading e foco coerentes; estado inicial fechado somente quando não oculta informação material.
- Copiar copia somente o conteúdo apropriado, segundo componente atual, sem permitir divulgar material protegido.
- Abas/popovers não devem roubar foco, truncar resposta ou fechar antes de interação; teclado, Escape e screen reader.
- Full-page, Companion Dock nativo, 320/360/375/390/420px, 200% zoom, light/dark, reduced motion.
- Respeitar leitura incremental/streaming existente; não desmontar conteúdo ou perder scroll/seleção nas transições.
- Respostas longas e rich content mantêm estrutura tipográfica e controles interativos.

## 7. Critérios de aceite ARC-01..ARC-18

| ID | Critério |
|---|---|
| ARC-01 | Saudação simples é visualmente leve, com corpo como protagonista |
| ARC-02 | Sem card obrigatório de fundo azul ou altura mínima excessiva |
| ARC-03 | Avatar e identificação sem repetição desnecessária |
| ARC-04 | Mensagem conversacional sem “Sem fonte vinculada” decorativo |
| ARC-05 | Status operacional aparece quando contratualmente relevante |
| ARC-06 | Contexto real e fontes acessíveis por disclosure |
| ARC-07 | Ausência de grounding obrigatório não é escondida |
| ARC-08 | Warnings e bloqueios materiais continuam visíveis |
| ARC-09 | Evidence/Policy/Outcome não são reclassificados pelo frontend |
| ARC-10 | Mensagens com Markdown, code blocks e rich data não regrediram |
| ARC-11 | Ações legítimas como Copiar continuam funcionando |
| ARC-12 | Progressive disclosure e foco acessíveis a teclado e leitor de tela |
| ARC-13 | Motion suave, reduced motion e layout sem saltos |
| ARC-14 | Full-page e Companion Dock real |
| ARC-15 | Mobile 320–420px, zoom 200%, dark/light |
| ARC-16 | Streaming/scroll e estados in-flight/error preservados |
| ARC-17 | Reuse gate e ownership/contratos provados antes de novo componente |
| ARC-18 | RED/GREEN, regressão e QA autenticado no SHA implantado |

## 8. Roadmap de execução bounded

**Task proposta:** `DELIA-UX-CONTEXTUAL-ASSISTANT-RESPONSE-PROGRESSIVE-DISCLOSURE-01`.

REANCHOR: git HEAD/status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → arquitetura/product spec → presentation/Markdown/evidence/activity specs e ledger. INVENTORY: identificar envelopes/owners/consumers/componentes reais. REUSE/CONTRACT GATES: provar equivalentes; manter classificação e provenance por dados autoritativos. Testes RED em saudação, resposta com fontes, evidência insuficiente, activity/outcome, erro/streaming. Implementar **o menor diff correto** no plugin-ui/composição, sem backend presumido. QA visual, regressão, documentação, ledger e deploy após gates. Se contrato não distinguir variantes com segurança, documentar `ARCHITECTURE_DECISION_REQUIRED` para essa parte e não inventar classificação textual; ainda executar melhorias puramente visuais seguras.

**STATUS FINAL DA PUBLICAÇÃO:** `SPEC_PUBLISHED; RUNTIME_CHANGED (2026-10-24, commit 3c89d222b5); TESTED; PHASE_NOT_ADVANCED`.

### Implementação registrada (2026-10-24)

`EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` — zero componente novo, zero diff em `plugin-ui`, zero backend. Mudança confinada à composição em `plugins/delia/src/ui/DeliaAssistantMessage.tsx`:

- **Variante A (conversacional):** gate por dado tipado de contrato — `observability.composition_mode === "model"` + `messageKind === "RESULT"` (sem `semanticState`) + ausência de `provenance` e `confirmationRequest`. Nesse caso o `ActivityViewer` ("Atividade concluída"/"Ver detalhes") e o resumo decorativo "Sem fonte vinculada" são suprimidos; `EvidenceDetails` permanece somente se houver `limitations` (avisos materiais não dependem de estética). Avatar, rótulo DÉLIA, conteúdo Markdown e ações (Copiar etc.) preservados.
- **Variantes B/C (contextualizada/operacional):** inalteradas — provenance GROUNDED, semantic states, confirmation, activity real continuam com ActivityViewer + EvidenceDetails completos. Presença de `provenance` força tratamento completo mesmo sob composição model.
- Nenhuma classificação por texto/regex; nenhuma autoridade movida ao frontend.

**Evidência:** `vd-arc-prod.mjs` + `vd-arc-prod-m.mjs` autenticados — 18/18 (saudação leve h=82px sem chrome operacional; resposta SIPOC rica com Markdown; mobile 320/375 sem overflow). Testes: delia 431/431 (+5 ARC), typecheck/build verdes. Residuais: estado `stopping`-análogo transitório e resposta realmente GROUNDED não reproduzidos no probe (cobertos por vitest); 360/390/420px, zoom 200%, dark visual e screen reader TEST_NOT_RUN.

### Implementação registrada (2026-10-24) — separação message context × conversation context

`TASK_ID=DELIA-UX-MESSAGE-CONTEXT-AND-GLOBAL-CONVERSATION-PANEL-01`. Regra aplicada: `MESSAGE_CONTEXT != CONVERSATION_CONTEXT`. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` — zero componente novo de domínio, zero backend, zero contrato novo.

- **Contexto da mensagem (popover):** "Ver contexto" deixou o menu "Mais opções" e virou ação inline visível na strip da própria mensagem, ao lado de "Copiar" — `inlineActions` (EXTEND) em `ConversationAssistantActions` com semântica de disclosure (`aria-expanded` + `aria-haspopup="dialog"` quando `expanded` definido; `aria-pressed` preservado para toggles). O popover usa `AnchoredPanelPortal` (`variant="shape"`, `role="dialog"`, `aria-label="Contexto desta resposta"`, `preferredPlacement="top"` com flip adaptativo) e reutiliza `DeliaTurnContextPanel` — agora filtrando seções vazias (Detalhes/Evidências/Atividades só quando há conteúdo legítimo de contrato). Estado 100% local à mensagem (`useState`), Escape/clique externo/trigger fecham, exclusividade via `claimExclusiveAnchoredPanel`. Indicador visual discreto: acento lateral via `delia-turn__bubble--context-open`.
- **Contexto da conversa (painel global):** `ConversationContextPanel` ganhou `sections`/`emptyState` genéricos (EXTEND) — sem conhecimento DÉLIA-específico em `plugin-ui`. Novo `DeliaConversationContextPanel` renderiza apenas o estado vazio honesto: `GLOBAL_DATA_SOURCE=NONE` (não existe contrato conversation-scoped de arquivos/links/fontes/sessão) → sem seções fake, sem agregado de evidências por turno, sem segundo mecanismo de memória. Gate documentado no JSDoc: `OWNER=delia-api (session contract, futuro)`, `AUTHORIZATION=session-scoped`, `FRONTEND_CONSUMER=none yet` — `ARCHITECTURE_DECISION_REQUIRED` para quaisquer seções globais futuras.
- **Desacoplamento:** `selectedTurnId`/`onSelectTurn` removidos de `App`/`ConversationTimeline`/`DeliaAssistantMessage` — a seleção só existia para alimentar o painel como visualizador de mensagem. O painel abre por seu toggle próprio ("Abrir contexto"), independente de turno selecionado; o popover não o abre nem depende dele.

TESTES: delia 437/437 (+13: MC-01..08, GC-01..08, isolamento por turno), plugin-ui 2335/2335 (+7: inlineActions + sections/emptyState), typecheck + build + federation verdes. DEFECT_FOUND=1: `setSelectedTurnId` residual no caminho de sucesso (ReferenceError pós-append → error+queuePaused) — detectado por regressão (queue/lifecycle/s2), fix 1 linha, re-verde 47/47+437/437.

QA VISUAL PROD 32/32 (`vd-mctx-prod.mjs` autenticado, `da1794d68d`): "Ver contexto" visível com `aria-expanded`; popover compacto w=340px ancorado à action strip (gap 4–8px, flip adaptativo); abre sem tocar o painel global; fecha por trigger/Escape/clique externo; duas mensagens → exclusividade e reancoragem sem mistura; painel "Contexto da conversa" independente com vazio honesto e zero seções fake/turno promovido; mobile 375 sem overflow (x=27 w=340). Screenshots `shots-mctx/`. Residuais: light-dismiss do painel global (contrato vigente do `ConversationThreeRegionLayout` — qualquer interação externa o fecha, inclusive o trigger do popover); Companion Dock real, 360/390/420px, zoom 200%, dark/light visual e screen reader TEST_NOT_RUN.

**STATUS FINAL:** `SPEC_PUBLISHED; RUNTIME_CHANGED (2026-10-24, commit da1794d68d); TESTED; PHASE_NOT_ADVANCED; GLOBAL_SECTIONS=BLOCKED_PENDING_CONTRACT`.


## Decisão posterior do Product Owner — contexto da mensagem INLINE (2026-10-24)

**STATUS=PRODUCT_UX_DECISION / PLANNED; substitui expressamente a decisão anterior de POPOVER para contexto do turno.** O comportamento de popover introduzido na implementação `da1794d68d` foi inspecionado em produção e rejeitado visualmente: sobrepõe outras mensagens e a área do composer, gera rolagem interna própria e dificulta comparar respostas. A nova decisão é **expansão dentro do fluxo vertical da conversa**, semelhante à experiência de detalhes inline de um chat moderno.

### Contrato de UX congelado

- A ação **Ver contexto**, localizada junto a **Copiar**, alterna uma seção **inline sob as ações daquela própria mensagem**, usando o mesmo `turn` e o componente de conteúdo real `DeliaTurnContextPanel` (ou sua apresentação reutilizável), sem overlay, popover, `AnchoredPanelPortal`, portal ou camada flutuante.
- **Ver contexto → Ocultar contexto** é controlado por botão com `aria-expanded`, `aria-controls` e região identificada acessivelmente conforme padrões existentes. Abrir expande a altura da mensagem e **empurra naturalmente mensagens seguintes**; usa **somente o scroll da conversa**, sem scroll aninhado exclusivo da seção contextual.
- Clicar fora, interagir com o composer ou abrir o contexto de outra mensagem **não fecha automaticamente** o primeiro. Vários turnos podem permanecer expandidos ao mesmo tempo. Fecha apenas pela ação explícita de recolher, desmontagem legítima da conversa ou mudança de sessão, preservando isolamento por `turn_id`/identificador real.
- Animação suave, curta (aprox. 160–200ms) e opcional, sem atrasar o conteúdo, prejudicar o foco, capturar o scroll ou deslocar texto artificialmente; `prefers-reduced-motion` respeitado. **Não usar timer, height arbitrária nem `max-height` que corte evidências**. A atualização de tamanho deve ser segura para histórico longo e streaming.
- Visual: superfície neutra/subordinada à resposta, título **Contexto desta resposta**, seções reais de Detalhes/Fontes/Evidências/Execução apenas quando o contrato permitir. Sem card azul dominante, sem moldura de altura fixa, sem repetir fontes falsas ou ocultar avisos materiais. Conteúdo do contexto pode ter subseções próprias, mas não criar scroll vertical concorrente dentro da mensagem.
- **Painel lateral Contexto da conversa permanece global** e independente. Nunca abrir/selecionar o painel lateral ao expandir contexto de um turno. Global Files/Links/Sources continuam `BLOCKED_PENDING_CONTRACT` enquanto não houver fontes conversation-scoped legítimas.
- Preservar os consumidores de `ConversationAssistantActions`, os dados de `DeliaTurnContextPanel`, Evidence/Policy/Outcome e a semântica de aviso material. Sem mudança de backend ou promoção de fontes de turno a fontes globais.

### Acceptance criteria INLINE-01..INLINE-14

| ID | Critério |
|---|---|
| INLINE-01 | Botão Ver contexto expande conteúdo no DOM imediatamente abaixo das ações da própria mensagem |
| INLINE-02 | Não usa AnchoredPanelPortal, popover, overlay nem position fixed/absolute para conteúdo de contexto |
| INLINE-03 | O contexto expande o fluxo e empurra a mensagem seguinte, sem cobrir composer |
| INLINE-04 | Não há scrollbar própria na região inline; usa scroll da conversa |
| INLINE-05 | Ocultar contexto recolhe apenas a região daquele turno |
| INLINE-06 | Clique fora e interação no composer não recolhem o contexto |
| INLINE-07 | Dois ou mais turnos podem permanecer expandidos simultaneamente e isolados |
| INLINE-08 | aria-expanded/aria-controls e foco/teclado corretos; leitor de tela quando disponível |
| INLINE-09 | Conteúdo real de provenance/limitações/activity preservado, sem dados inventados |
| INLINE-10 | Avisos materiais e confirmações continuam visíveis na mensagem |
| INLINE-11 | Painel global continua conversation-scoped e independente |
| INLINE-12 | Streaming, markdown, rich content, copiar, fila e scroll continuam corretos |
| INLINE-13 | Full-page, Companion Dock nativo, 320–420px, zoom 200%, light/dark e reduced-motion |
| INLINE-14 | RED/GREEN, regressão, screenshots reais, deploy e QA no SHA avaliado |

**Task bounded:** `DELIA-UX-MESSAGE-CONTEXT-INLINE-EXPANSION-REWORK-01`. Reanchor HEAD e authorities; revalidar contratos/owners; `EXISTING_EQUIVALENT=YES` (turn panel, actions e turn state), `REUSE_DECISION=EXTEND` sujeito a inventário; trocar somente o invólucro flutuante por conteúdo inline e estilos; RED→GREEN, regressão do lifecycle/queue/shell (especialmente o antigo `setSelectedTurnId`), QA full-page/Dock/mobile; atualizar evidência e ledger; commit/push/deploy frontend após gates.

**Esta publicação é DOC-ONLY: `RUNTIME_NOT_CHANGED`, `TEST_NOT_RUN`, `PHASE_NOT_ADVANCED`.** A seção anterior documenta o runtime popover histórico e não deve ser interpretada como direção UX futura.
