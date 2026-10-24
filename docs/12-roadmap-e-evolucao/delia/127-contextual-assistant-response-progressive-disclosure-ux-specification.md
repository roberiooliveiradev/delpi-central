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

### Implementação registrada (2026-10-24) — contexto da mensagem INLINE

`TASK_ID=DELIA-UX-MESSAGE-CONTEXT-INLINE-EXPANSION-REWORK-01`. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` — zero componente novo de domínio, zero backend, zero contrato novo. Runtime commit `2ad6403b10`.

- **Popover substituído por região inline:** `DeliaAssistantMessage` removeu o uso de `AnchoredPanelPortal` para contexto do turno (o componente permanece na biblioteca compartilhada — outros consumidores legítimos intactos). A ação "Ver contexto" segue visível ao lado de "Copiar" na strip da mensagem e agora alterna uma `<section role="region" aria-label="Contexto desta resposta">` renderizada **no fluxo**, imediatamente abaixo da action strip, dentro do `.delia-turn__bubble`. Conteúdo = `DeliaTurnContextPanel turn={turn}` inalterado — nenhum segundo renderizador de evidências.
- **Disclosure semântico:** `inlineActions` em `ConversationAssistantActions` ganhou `controls` (aria-controls) e `icon` (chevron down/up via lucide, `aria-hidden`) — e perdeu o `aria-haspopup="dialog"` (não é mais diálogo/popover). Região com id estável por `useId`; `aria-expanded`/`aria-controls` coerentes; título "Contexto desta resposta" preservado como heading interno.
- **Comportamento:** estado `contextOpen` 100% local por mensagem (sem `selectedTurnId`, sem exclusividade global). Expansão empurra mensagens seguintes por reflow natural; sem scroll próprio (`overflow: visible`, sem `max-height`); recolhe apenas por "Ocultar contexto", unmount ou troca de sessão. Clique externo, Escape e composer não colapsam — verificado em probe e vitest.
- **Visual/motion:** superfície neutra subordinada (accent 3% + borda 16%, radius 10px, max-width 640px, `overflow-wrap: anywhere`). Entrada com `delia-turn-context-in` 180ms (opacity+translateY −4px) — conteúdo disponível imediatamente, sem timer, sem height animation; `@media (prefers-reduced-motion: reduce)` desliga a animação.
- **Painel global:** `DeliaConversationContextPanel` intocado — segue conversation-scoped, independente, vazio honesto (`GLOBAL_DATA_SOURCE=NONE`, `BLOCKED_PENDING_CONTRACT`).

TESTES: delia 438/438 (+1: describe INLINE-01..14 reescrito — DOM order, portal-free, reflow, multi-open isolado, colapso independente, clique externo/Escape inertes, ARIA, provenance/limitations), plugin-ui 2335/2335 (API de inline action atualizada), typecheck + build + federation verdes.

QA VISUAL PROD 39/39 (`vd-inline-prod.mjs` autenticado, `2ad6403b10`): região abre abaixo da action strip (dy=42px), `position: static`, zero portal/dialog no DOM; mensagem cresce 109→719px e empurra o turno seguinte (dy=844–1107px); scroll container não sobrepõe composer (735<754; 476<495 em 375px); dois contextos abertos simultâneos com dados isolados e colapso independente; clique fora + Escape + digitação no composer não fecham; painel global abre/reabre independente; 375px íntegro (x=103 w=250); `prefers-reduced-motion` → `animation: none`; viewport 640×450 (~zoom 200%) sem overflow. Screenshots `shots-inline/`. Residuais: Companion Dock real, 320/360/390/420px individuais, dark/light visual e screen reader TEST_NOT_RUN; regressão streaming/markdown coberta por vitest (INLINE-12), não por probe E2E.

**STATUS FINAL:** `SPEC_PUBLISHED; RUNTIME_CHANGED (2026-10-24, commit 2ad6403b10); TESTED; DEPLOYED; PHASE_NOT_ADVANCED; GLOBAL_SECTIONS=BLOCKED_PENDING_CONTRACT`.


## Decisão visual posterior — Clean Inline Context Card (2026-10-24)

**STATUS: PRODUCT_UX_DECISION / IMPLEMENTATION_PENDING / DOC_ONLY.** O PO aprovou a referência visual de card técnico clean mostrada na conversa. Esta decisão **substitui exclusivamente o aspecto visual da região inline**, não o contrato de disclosure inline, nem o contexto global da conversa. A implementação corrente (commit histórico 2ad6403b10) usa região inline, mas screenshots reais mostram uma **barra azul vertical** e painel denso com metadados técnicos dominantes. A direção nova remove essa barra e eleva a legibilidade.

### Anatomia visual aprovada

- **Container único:** região inline abaixo de Copiar / Ocultar contexto, no fluxo natural, sem popover, overlay, nested scroll ou barra lateral azul. Fundo de superfície neutra levemente elevada, borda fina sutil, radius consistente com plugin-ui, sombra opcional muito discreta. Largura limitada ao conteúdo da mensagem (nunca maior que a conversa). Não repetir o contorno azul do estado de foco/seleção.
- **Header:** “Contexto desta resposta”, subtítulo opcional **“Detalhes da geração, evidências e atividade relacionada”**. Ícone secundário opcional, sem inventar uma nova ação de colapso se **Ocultar contexto** já controla a região. Sem cabeçalho duplo.
- **Detalhes da geração:** seção de metadados legível em grid adaptativo com pares label/valor; desktop pode usar duas colunas de *pares*, enquanto Dock/mobile vira uma coluna. Preservar campo/valor exatos e sua semântica, inclusive “custo indisponível” e dados de tokens somente se reais; nunca inferir números. Labels secundários, valores em primeiro plano; identificadores longos quebram linha sem overflow.
- **Evidências:** seção separada e menos dominante, preservando proveniência e limitações legítimas. “Sem fonte vinculada” dentro do contexto técnico pode ser informação neutra, **não** alerta ou prova de falha de grounding. Se uma resposta exigir fonte e faltar, manter a limitação material visível no corpo principal conforme contrato; não esconder no card.
- **Atividades relacionadas:** status tipado real, duração quando disponível e detalhes acessíveis, sem confundir execução concluída com business outcome verificado. Não criar status de sucesso fictício.
- **Rastreamento técnico:** nomes de spans/eventos e contagens de tokens por etapa são opcionais e secundários, preferencialmente em disclosure interno **apenas se esses dados já existirem**, sem duplicar o ActivityViewer. Informação técnica essencial à auditabilidade continua acessível; não se deve ocultá-la ou apagá-la por estética.
- **Iconografia e cores:** azul institucional como acento discreto dos ícones/ações, verde somente para estado comprovado de acordo com a semântica existente. Não usar blocos azuis saturados nem “cards dentro de cards” em excesso. Tokens do plugin-ui, dark/light e contraste AA.
- **Motion:** transições leves 160–200ms onde seguras, sem animar height com truncamento, sem causar scroll jump durante streaming, respeitando prefers-reduced-motion.
- **Responsividade:** full-page, Companion Dock real, 320/360/375/390/420px, zoom 200%; grid colapsa, sem truncamento de labels e sem rolagem horizontal. Sem tamanho fixo alto ou scrollbar dentro do contexto.

### Reuse e ownership

Revalidar no HEAD: \`DeliaTurnContextPanel\` é o compositor de conteúdo em \`plugins/delia/src/ui/contextPanel.tsx\`; \`ConversationContextPanel\`, \`EvidenceDetails\`, \`ActivityViewer\` e demais primitivas pertencem ao \`plugin-ui\`. \`DeliaAssistantMessage\` contém a região inline. Preferir extensão de estilos/composição existentes, sem criar um segundo renderer de evidências nem outro painel técnico. **EXISTING_EQUIVALENT=YES / REUSE_DECISION=EXTEND** como direção documental, sujeitos à prova no HEAD. Identificar origem real da barra lateral (estilo da bolha, região inline ou componente compartilhado) antes de alterar CSS; não removê-la globalmente se outros consumidores dependerem dela.

### Critérios CLEANCTX-01..CLEANCTX-16

| ID | Critério |
|---|---|
| CLEANCTX-01 | Barra vertical azul removida somente do contexto/seleção alvo sem afetar foco acessível |
| CLEANCTX-02 | Contexto é card neutro único, borda sutil, sem card pesado |
| CLEANCTX-03 | Cabeçalho e subtítulo com hierarquia clara, sem duplicação de controles |
| CLEANCTX-04 | Metadados em grid responsivo label/valor, com semântica preservada |
| CLEANCTX-05 | Valores de tokens, duração, modelos e custos não inventados |
| CLEANCTX-06 | Evidências/proveniência mantidas e visualmente subordinadas |
| CLEANCTX-07 | Ausência de fonte não apresentada como erro numa saudação |
| CLEANCTX-08 | Limitações materiais não são ocultadas |
| CLEANCTX-09 | Atividade real, status e detalhes preservados |
| CLEANCTX-10 | Rastreamento técnico menos dominante, mas acessível e auditável |
| CLEANCTX-11 | A região segue inline, sem popover, overlay ou scroll aninhado |
| CLEANCTX-12 | Duas mensagens expandidas, fechamento independente e painel global preservados |
| CLEANCTX-13 | Foco, teclado, ARIA, semântica e reduced-motion |
| CLEANCTX-14 | Full-page, Dock real, mobile, zoom 200%, dark/light |
| CLEANCTX-15 | Streaming, Markdown, fila, composer e rich content sem regressões |
| CLEANCTX-16 | RED/GREEN, regressões, QA real por SHA, ledger, deploy e reporte |

**Task bounded:** \`DELIA-UX-INLINE-RESPONSE-CONTEXT-CLEAN-VISUAL-REFACTOR-01\`.

REANCHOR HEAD/status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → specs/contracts/ledger → REUSE/ABSTRACTION GATE → RED visual+semantic tests → menor diff plugin-ui e/ou delia → GREEN → regression → browser visual QA full-page/Dock/mobile/dark-light/reduced-motion → rework → docs/evidence/ledger → commit/push main → scoped frontend deploy → real outcome QA. Se o grid de metadados ou rastreamento depender de alteração relevante em primitiva pública usada por outros apps, usar variante/extensão compatível e documentar consumers antes do diff. Backend/Domain/Core/STT não são parte desta task.

**Esta alteração documental não modifica runtime nem autoriza avanço de fase: RUNTIME_CHANGED=NO; TEST_NOT_RUN; PHASE_NOT_ADVANCED.**

### Implementação registrada (2026-10-24) — Clean Inline Context Card

`TASK_ID=DELIA-UX-INLINE-RESPONSE-CONTEXT-CLEAN-VISUAL-REFACTOR-01`. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` — zero componente novo, zero plugin-ui diff, zero backend. Commits `35e19f60b2` + `26b8646470` + `ca83dc93b9`.

- **Barra azul removida:** origem = `delia-turn__bubble--context-open` (accent inset 2px introduzido na implementação anterior, consumidor único: `DeliaAssistantMessage`). Classe e regra CSS removidas — foco de teclado (`focus-visible`) intacto.
- **Card neutro único:** `.delia-turn__context` passa de tint de accent para `var(--delia-surface)` + `border: 1px solid var(--delia-border)` + sombra 1px 5% — superfície elevada neutra, radius 12px, sem glow azul, sem altura fixa, sem scroll próprio.
- **Cabeçalho hierarquizado:** título semibold "Contexto desta resposta" + subtítulo muted "Detalhes da geração, evidências e atividade relacionada." + divisor neutro. Nenhum segundo controle de ocultação dentro do card.
- **Detalhes da geração:** seção renomeada ("Detalhes" → "Detalhes da geração"); `<dl>` virou grid adaptativo `repeat(auto-fit, minmax(200px,1fr))` — 2 colunas de pares label/valor no desktop, 1 coluna no Dock/mobile; labels 0.75rem muted, valores 0.8125rem com peso 500, `overflow-wrap: anywhere` para identificadores longos. Valores seguem 100% de contrato ("Custo indisponível" preservado).
- **Rastreamento técnico:** `ModelCalls` (spans reais `obs.calls`) movido para `<details className="delia-context__trace">` recolhido por padrão, summary "Rastreamento técnico" com chevron CSS próprio, focus-visible e reduced-motion. Auditoria permanece a um clique — nada removido.
- **Atividades relacionadas:** seção renomeada, `ActivityViewer` real preservado (estado/duração/detalhes). Evidências idem via `EvidenceDetails`.
- **Seções internas subordinadas:** dentro do card, headings do `ConversationContextPanel` compartilhado recebem apenas ajuste de ritmo (min-height/padding menores) via escopo `.delia-turn__context` — o painel global e outros consumidores ficam intactos.

TESTES: delia 443/443 (+5 CLEANCTX: sem accent bar, header único+subtítulo, grid real, trace colapsado→expansível, seções Evidências/Atividades relacionadas/"Sem fonte vinculada" neutra), plugin-ui 2335/2335 (inalterado — zero diff), typecheck + build verdes.

DEFECT+REWORK=1: primeiro deploy deixou regras legadas `flex` depois do novo grid (mesma especificidade, ordem venceu) — metadata continuava lista única; deduplicação (`26b8646470`) + minmax 200px (`ca83dc93b9`, largura real do card ~436px) → 2 colunas confirmadas em prod.

QA VISUAL PROD 26/26 (`vd-cleanctx-prod.mjs` autenticado, `ca83dc93b9`): sem `--context-open`/inset azul; card `position:static` neutro rgb(255,255,255) radius 12; header único + subtítulo, sem controle duplicado; grid 2 col desktop / 1 col mobile (medido); trace recolhido, expande e mostra spans reais; scroll não cobre composer; dois contextos simultâneos + colapso independente; painel global independente com vazio honesto; 375px íntegro; reduced-motion → animation none; Enter colapsa. Screenshots `shots-cleanctx/`. Residuais: Companion Dock real, 320/360/390/420 individuais, zoom 200% real, dark/light visual e screen reader TEST_NOT_RUN.

**STATUS FINAL:** `SPEC_PUBLISHED; RUNTIME_CHANGED (2026-10-24, commits 35e19f60b2/26b8646470/ca83dc93b9); TESTED; DEPLOYED; PHASE_NOT_ADVANCED; GLOBAL_SECTIONS=BLOCKED_PENDING_CONTRACT`.


## Decisão posterior do Product Owner — Responsive Multi-Column Inline Context (2026-10-24)

**STATUS: PRODUCT_UX_DECISION / IMPLEMENTATION_PENDING / DOC_ONLY.** O PO aprovou a referência visual de contexto inline multicolunas mostrada na conversa. Esta decisão **complementa** a expansão inline e o Clean Inline Context Card — não os apaga nem volta ao popover. Capturas reais mostraram que o card clean permanecia excessivamente estreito em telas amplas, criando uma coluna vertical longa com grande espaço horizontal ocioso.

### Regras da decisão

- O contexto permanece **inline**, abaixo das ações, no fluxo da conversa — sem popover, portal, overlay, scroll aninhado ou barra lateral azul.
- Em telas amplas, o card utiliza a largura útil da conversa e distribui o conteúdo em áreas semânticas: **Detalhes da geração**, **Evidências + Atividades relacionadas** e **Rastreamento técnico** (recolhível, secundário).
- Em larguras intermediárias, duas áreas (Detalhes à esquerda; demais agrupadas à direita). Em telas estreitas/Dock/mobile, uma única coluna.
- A transição depende da **largura real disponível do container**, não apenas da viewport global — o Companion Dock deve funcionar dentro de uma viewport desktop ampla.
- A resposta textual mantém largura confortável de leitura (`68ch`); o card expandido pode usar área maior da conversa.
- Nenhuma altura fixa, nenhum scroll vertical próprio, nenhum overflow horizontal, nenhuma coluna preenchida com dados falsos.
- Visual clean preservado: card único neutro, borda discreta, divisórias leves, acento institucional apenas em ícones/ações.

### Referência visual é conceitual

A referência aprovada ilustra estrutura e hierarquia. Itens ilustrativos (data/hora, ambiente, versão, plataforma, explicações extras sobre fontes e métricas adicionais) **não autorizam novos campos ou valores sem contratos legítimos**. Somente dados reais já presentes na projeção `turn_result`/`observability`/`provenance`/`activityView` podem ser exibidos.

### Estados de implementação

| Item | Estado |
|---|---|
| Expansão inline (sem popover/overlay) | PROVEN (`2ad6403b10`, §6.424) |
| Clean Inline Context Card (barra azul removida, card neutro, trace recolhível) | PROVEN (`ca83dc93b9`, §6.425) |
| Ocupação horizontal ampla / layouts wide-medium-compact | PLANNED — esta task |
| Companion Dock real, todos os widths/zoom/temas | TO_INVENTORY — QA desta task |
| Novos campos de contexto (ambiente, versão, data/hora, métricas extras) | TARGET/BLOCKED_PENDING_CONTRACT — não implementar |
| Seções globais do painel lateral | TARGET/BLOCKED_PENDING_CONTRACT |

**Task bounded:** `DELIA-UX-INLINE-CONTEXT-RESPONSIVE-MULTICOLUMN-REFACTOR-01`. REANCHOR → correção documental (esta seção) → diagnóstico de largura → REUSE/CONTRACT gates → RED → implement → GREEN → QA responsivo autenticado → rework → evidência/ledger → commit/push main → deploy frontend → verify → report.

**Esta alteração documental não modifica runtime: RUNTIME_CHANGED=NO; TEST_NOT_RUN; PHASE_NOT_ADVANCED.**


### Implementação (Responsive Multi-Column) — 2026-10-24 — `664eec398c`

**Task:** `DELIA-UX-INLINE-CONTEXT-RESPONSIVE-MULTICOLUMN-REFACTOR-01`. Base `7237b92a5d` (após correção documental). Scope: frontend/CSS apenas — backend, Core, Keycloak, Domain APIs, providers inalterados.

**Causa-raiz do card estreito (diagnóstico §5):** o `max-width:640px` do card **não era** o constraint real. A cadeia era: `--delpi-ui-conversation-column-max: 760px` (plugin-ui) → coluna de leitura ~712px → `.delia-turn--delia { align-self:flex-start }` shrink-wrap → card delimitado pela largura do texto (~550px em 1440 e em 1920 — medido em produção antes do diff).

**Implementação (menor diff, owner-correto):**
- `index.css`: `.dashboard-delia .delpi-ui-conversation-workspace { --delpi-ui-conversation-column-max: 1120px }` — escopo DÉLIA apenas; token default inalterado para outros consumidores. Texto da resposta continua `max-width:68ch`; composer/header acompanham a coluna.
- `index.css`: `.delia-turn:has(.delia-turn__context) { max-width:100%; width:100% }` — o turno com contexto aberto usa a largura da coluna (antes shrink-wrap ao texto). Demais turnos inalterados (88%).
- `index.css`: `.delia-turn__context` remove `max-width:640px`, vira `container-type: inline-size`. Container queries no **próprio card** (não viewport): `<560px` 1 coluna (flex do painel compartilhado), `≥560px` 2 áreas (Detalhes à esquerda `grid-row:1/-1`; demais + trace à direita com divisória `border-left` sutil), `≥860px` 3 áreas (Detalhes | Evidências+Atividades | Rastreamento técnico). Fallback: só detalhes+trace → trace na 2ª coluna (sem coluna vazia). Sem altura fixa, sem scroll aninhado, sem overflow-x.
- `ConversationContextPanel` (plugin-ui): EXTEND — novo prop opcional `trailing?: ReactNode` renderizado após as seções dentro do painel (genérico, sem lógica DÉLIA). Compatível com consumidores existentes (prop ausente = sem mudança).
- `DeliaTurnContextPanel`: `<details className="delia-context__trace">` sai de dentro da seção "Detalhes" e vira `trailing` — item de layout próprio (3ª área) sem duplicar DOM; ordem semântica preservada.

**Medições reais em produção (autenticado, getBoundingClientRect + computed styles):**

| Viewport | Card width | Áreas (tracks) | Observações |
|---|---|---|---|
| 1920 | 1030px | 3 | detalhes \| ev+atividades \| trace; texto 550px |
| 1600 | 898px | 3 | threshold ≥860 atinge wide |
| 1440 | 738px | 2 | detalhes esq., resto dir. |
| 320–420 | 210–305px | 1 | compacto, sem overflow |

**QA autenticado (vd-wide-prod.mjs): 34/34 PASS** — WIDE-01..15 cobertos: largura ampla, 3/2/1 áreas, sem overflow, sem scroll aninhado, sem popover, sem barra azul, trace recolhível com spans reais, texto 68ch < card, composer não coberto, dois contextos independentes, painel global independente, teclado, reduced-motion.

**Regressão:** delia Vitest 446/446 (+3 testes WIDE estruturais); plugin-ui Vitest 2335/2335; tsc ambos OK; build ambos OK; federation exports verify OK (`ConversationContextPanel` exportado). Deploy canônico `up-prod-sequential.sh --build plugin-ui delia`; SHA produção `664eec398c`.

**Residual:** REAL_DOCK_QA TEST_NOT_RUN (container-query por largura do card garante compacto em dock estreito, mas probe do Dock real no Portal não executado); zoom 200%, dark/light visual, screen reader TEST_NOT_RUN (ARIA/ordem DOM/keyboard/reduced-motion verificados por probe+vitest).

**WIDE-01..18:** 01–15 PASS; 16 PASS (regressão completa executada); 17 PASS (34/34 + medições + screenshots `shots-wide/`); 18 PASS (docs+ledger+push+deploy+verify). PHASE_NOT_ADVANCED.


## Decisão posterior do PO — Right Rail integrado, sem sobreposição no desktop (2026-10-24)

**STATUS: PRODUCT_UX_DECISION / PLANNED / DOC_ONLY.** Capturas reais do PO mostram que o painel global “Contexto” sobrepõe a região central e o contexto inline da resposta. A nova direção é reservar **espaço real de layout à direita** para o **Contexto da conversa**, mantendo a navegação à esquerda e a conversa (incluindo “Contexto desta resposta”) ao centro. Esta decisão **substitui apenas o padrão de sobreposição da lateral global em desktop largo**, não a decisão de inline da mensagem, nem os contratos e o ownership dos dados.

### Contrato visual e comportamental

- **Desktop com espaço suficiente:** layout efetivo de três regiões: navegação à esquerda, conversa/composer central, e **right rail** global integrado no fluxo do grid/flex, sem position fixed/absolute sobre a conversa. Abrir/fechar o rail altera a largura útil da região central de maneira governada, evitando clipping, sobreposição e saltos de scroll. O painel poderá ser redimensionável **somente se a primitiva existente e seu contrato o suportarem**; não criar resizer por conveniência.
- **Right rail global:** título **Contexto da conversa**; superfícies neutras, divisórias leves, padding e hierarquia clean, toggle de abrir/fechar acessível. Conteúdo e navegação pertencem ao escopo conversation/session, não ao turno. O painel não se transforma em outro visualizador de evidência individual.
- **Seções pretendidas:** Arquivos, Fontes, Links e Dados gerais/Contexto, **somente quando houver dados e contratos reais**. O runtime atualmente tem \`DeliaConversationContextPanel\` com \`sections=[]\` e estado vazio honesto. Não criar upload, arquivo, fonte, link, resumo, memória, campo de sessão ou métricas fictícios para preencher o espaço; não apresentar seções vazias como capabilities disponíveis. Sem contrato, manter o estado vazio coerente e indicar o bloqueio documentalmente.
- **Centro:** respostas e ações continuam no fluxo; “Ver contexto” expande **inline por turno**. O card inline clean e seu grid 3/2/1 respondem à largura real **do centro depois de reservar a lateral direita**, não à viewport total. Não forçar três colunas no card quando o right rail reduzir espaço; preservar largura confortável de leitura da resposta, composer e queue/status.
- **Responsividade:** quando não couberem rail + centro legível + navegação, recolher o painel direito no layout, mantendo toggle visível e acessível; em breakpoint compacto ou Companion Dock, usar o padrão responsive legítimo da plataforma (overlay/drawer quando justificável, sem sobrepor indevidamente o composer). Não afirmar que drawer seja implementado antes de provar sua primitiva e comportamento real. Não inventar breakpoint: medir mínimo dos três regions e testar 1920/1600/1440 e 1280, além de 320/360/375/390/420 e Dock real.
- **Foco e interação:** Escape, clique externo, toggle e light-dismiss adequados a cada variante de layout. No **right rail desktop integrado**, um clique na conversa **não deve dispensar automaticamente** o painel (não é light-dismiss). Em overlay compacto, light-dismiss pode ser apropriado. Preservar focus, aria-expanded/controls, scrolling e leitura por teclado.
- **Separação de dados:** \`MESSAGE_CONTEXT != CONVERSATION_CONTEXT\`. Fontes e evidências de turno não são promovidas automaticamente a fontes globais; ausência de contratos globais segue \`BLOCKED_PENDING_CONTRACT\`. DÉLIA não cria nova fonte de verdade; Core/AuthZ e Domain APIs mantêm suas autoridades.

### Ownership e reuse gate

Inventário atual no HEAD de documentação: \`DeliaConversationPage\` compõe \`ConversationThreeRegionLayout\` de \`plugin-ui\`, passando \`right\`, \`rightOpen\`, \`onRightOpenChange\` e \`center\`; \`App\` passa \`DeliaConversationContextPanel\`; o painel global usa \`ConversationContextPanel\` com estado vazio real. O **owner compartilhado do layout** é \`plugin-ui\`; a **composição de produto** permanece em \`plugins/delia\`. A execução deve ler contratos, CSS, consumidores e teste do \`ConversationThreeRegionLayout\` antes de alterá-lo e verificar \`EXISTING_EQUIVALENT=YES\`, \`REUSE_DECISION=EXTEND\` ou justificativa diferente com evidência. Não criar segundo ThreeRegionLayout ou duplicar regras por consumer. Alterações de API compartilhada devem ser compatíveis e testadas nos consumidores reais.

### Critérios RIGHTRAIL-01..RIGHTRAIL-18

| ID | Critério |
|---|---|
| RIGHTRAIL-01 | Em desktop amplo, right rail ocupa coluna própria e não sobrepõe centro/composer |
| RIGHTRAIL-02 | Toggle abre/fecha sem light-dismiss externo na variante integrada |
| RIGHTRAIL-03 | Região central se adapta à largura restante, sem perder resposta, ações e composer |
| RIGHTRAIL-04 | Contexto por mensagem permanece inline e independente do global |
| RIGHTRAIL-05 | Grid inline 3/2/1 recalcula pela largura real do centro |
| RIGHTRAIL-06 | Não há scroll horizontal, conteúdo cortado ou sobreposição do botão Ir para o final |
| RIGHTRAIL-07 | Navegação esquerda/rail de categorias preservados |
| RIGHTRAIL-08 | Right rail com título, hierarquia e estilo clean da DÉLIA |
| RIGHTRAIL-09 | Estado vazio legítimo sem arquivos/fontes/links inventados |
| RIGHTRAIL-10 | Proveniência de turno jamais promovida silenciosamente a dado global |
| RIGHTRAIL-11 | Breakpoints derivados de medições; comportamento intermediário/compacto governado |
| RIGHTRAIL-12 | Companion Dock real operável com toggle, composer e painel apropriado |
| RIGHTRAIL-13 | Full-page 1280/1440/1600/1920 e mobile 320/360/375/390/420 |
| RIGHTRAIL-14 | Zoom 200%, dark/light, reduced motion e contraste adequados |
| RIGHTRAIL-15 | Foco/teclado/ARIA/fechamento corretos em rail integrado e overlay compacto |
| RIGHTRAIL-16 | Scroll, streaming, Markdown, fila, lifecycle/S2 shell, confirmações preservados |
| RIGHTRAIL-17 | Reuse de primitives/owners e nenhum contrato/backend paralelo |
| RIGHTRAIL-18 | RED/GREEN, QA autenticado, evidência por SHA, ledger, deploy scoped e report |

**Task bounded:** \`DELIA-UX-CONVERSATION-CONTEXT-RIGHT-RAIL-LAYOUT-REFINEMENT-01\`. Reanchor HEAD/git status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → arquitetura/product specs → spec 127/layout/contracts/ledger; contract + reuse gate; RED testes dos casos de sobreposição, contexto inline e light-dismiss; mínimo diff no \`ConversationThreeRegionLayout\` e composição DÉLIA; regressão full; QA full-page/Dock real/mobile/zoom/temas; rework → evidência/ledger → commit/push main → deploy frontend scoped → pós-deploy. Se integração compartilhada exigir decisão fora do escopo, registrar \`ARCHITECTURE_DECISION_REQUIRED\` e limitar o diff ao que é seguro.

**Esta publicação é somente documental:** \`RUNTIME_NOT_CHANGED; TEST_NOT_RUN; PHASE_NOT_ADVANCED\`. Histórico de releases anteriores permanece preservado.


### Implementação (Right Rail integrado) — 2026-10-24 — `f00c6ea739`

**Task:** `DELIA-UX-CONVERSATION-CONTEXT-RIGHT-RAIL-LAYOUT-REFINEMENT-01`. Base `2ca5c5ea42`+`f00c6ea739`. Scope: frontend/layout apenas — backend, contratos e dados inalterados.

**Causa-raiz da sobreposição (diagnóstico §5):** `ConversationThreeRegionLayout` sempre renderizou o contexto global como `__context-popover` — `position:absolute; top:66px; right:16px; z-index:30` com light-dismiss via `pointerdown` no documento e Escape. A classe `__right` com CSS de coluna real existia no stylesheet, mas o componente nunca a instanciava. Owner do layout: `plugin-ui`; composição: `plugins/delia`.

**Implementação (EXTEND — direção preferencial da spec):**
- `ConversationThreeRegionLayout` +prop `rightVariant?: "popover" | "rail"` (default `"popover"` — retrocompatível; DÉLIA é a única consumidora).
- Variante `rail`: `<aside role="complementary" aria-label="Contexto da conversa">` como coluna flex real `flex:0 0 var(--delpi-ui-three-right)` (clamp 296–344px), `position:static`, sem overlay/z-index, sempre montada com `flex-basis:0` fechada → transição de largura suave (240ms ease, `--delpi-ui-conversation-motion-*` existente), `visibility:hidden` + `aria-hidden` quando fechada.
- Sem light-dismiss na variante rail (`pointerdown` externo removido apenas no modo rail); Escape continua fechando e devolve foco ao toggle; close button interno preservado; `aria-expanded`/`aria-controls` intactos.
- Fallback governado: rail apenas quando o centro projetado permanece ≥480px legível (`hostW − leftW − railIconW − clamp(296,23%,344) ≥ 480`, medido via ResizeObserver no host real, não na viewport). Abaixo disso — e sempre em compact (host ≤920px, inclui Dock e mobile) — a superfície flutuante legítima existente é usada.
- `DeliaConversationPage` passa `rightVariant="rail"`; `DeliaConversationContextPanel` inalterado (estado vazio honesto).
- Grid inline do contexto de mensagem adapta automaticamente (container-query no card): medido em produção — 3→2 áreas @1920/1600 com rail aberto, 2→1 @1440.

**Medições reais em produção (autenticado, getBoundingClientRect):**

| Viewport | Centro fechado→aberto | Rail | Card inline (tracks) |
|---|---|---|---|
| 1920 | 1267→924px | 344px, static | 1030→834px (3→2) |
| 1600 | 987→689px | 299px, static | 897→599px (3→2) |
| 1440 | 827→532px | 296px, static | 737→442px (2→1) |
| 1280 | 668→668px | fallback popover | 578px (1) |
| 375 | — | fallback popover | — |

`centerR ≤ railL` em todas as larguras (zero sobreposição), `docOverflow=0`, composer sempre dentro do centro.

**QA autenticado (vd-rightrail-prod.mjs): 50/50 PASS** — RR-01..15: coluna real, sem overlay/light-dismiss, composer preservado, Escape, dois contextos inline + rail simultâneos, mobile fallback, reduced-motion, vazio honesto, centro recupera largura ao fechar.

**Regressão:** plugin-ui 2340/2340 (+5 RIGHTRAIL), delia 447/447 (+1 page rail + 1 asserção dialog→complementary atualizada), tsc+build+federation OK. Deploy `up-prod-sequential.sh --build plugin-ui delia`; SHA `f00c6ea739`.

**Residual:** REAL_DOCK_QA TEST_NOT_RUN (compact ≤920px host → popover é o contrato; probe do Dock real não executado); zoom 200%/dark-light visual/screen reader TEST_NOT_RUN; streaming/fila cobertos por vitest.

**RIGHTRAIL-01..18:** 01–15 PASS; 16 PASS (regressão); 17 PASS (EXTEND, zero duplicação); 18 PASS (docs+ledger+push+deploy+verify). PHASE_NOT_ADVANCED.


## Decisão posterior de UX — Contexto inline com duas zonas semânticas e densidade adaptativa (2026-10-24)

**STATUS: PRODUCT_UX_DECISION / PLANNED / DOC_ONLY.** O PO apresentou capturas reais em dark/light comprovando desequilíbrio do componente: detalhes em lista vertical longa à esquerda, evidências quase vazias no topo, atividades deslocadas para baixo e rastreamento ocupando terceira área pouco aproveitada. A nova direção de produto **substitui a distribuição rígida em três áreas como padrão visual**. Mantém a largura responsiva do contexto e seu vínculo inline ao turno, porém organiza o conteúdo conforme os dados de fato disponíveis.

### Layout aprovado

- **Desktop com largura suficiente:** duas zonas semânticas flexíveis: (1) **Geração** — metadados compactos em grid interno de pares label/valor, incluindo modelo, composição, tempos, tokens, chamadas, custo e estado quando existentes; (2) **Evidências e atividades** — fontes/proveniência e atividades relacionadas próximas, seguidas de **Rastreamento técnico** em disclosure recolhível na mesma zona. As zonas devem distribuir a altura de modo equilibrado, sem criar regiões artificialmente vazias.
- **Intermediário:** duas zonas quando a largura real comportar boa leitura; grid de metadados adapta o número de pares por linha. **Compacto/Dock/mobile:** uma zona vertical na ordem lógica Geração → Evidências → Atividades → Rastreamento.
- **Densidade:** reduzir altura desnecessária, espaçamento e repetições, mas preservar legibilidade, todos os valores reais, auditabilidade e a semântica. Não truncar identificadores, não esconder limitações materiais e não forçar cards para cada campo se isso poluir o layout.
- **Ausência de conteúdo:** não reservar coluna ou altura inteira para evidências vazias. A informação “Sem fonte vinculada”, quando legítima, aparece neutra dentro do contexto técnico. Não apresentar ausência de fonte como erro para saudação; não inferir inexistência de necessidade de grounding.
- **Valores:** exibir números, custos, nomes de modelo, duração, atividade e fonte apenas conforme contrato real; a referência ilustrativa não adiciona novos campos nem valores. Não converter activity success em business outcome.
- **Visual:** uma única superfície clean, borda neutra, ícones de baixa ênfase, títulos claros, divisórias mínimas, sem barra azul e sem três painéis aninhados. Dark/light via tokens legítimos. Preservar expansão inline, rolagem única, múltiplos turnos abertos, ações de mensagem, foco e reduced-motion.

### Ownership, reuse e compatibilidade

Antes do código, reancorar no HEAD e mapear consumidores de \`ConversationContextPanel\` (plugin-ui) e a composição \`DeliaTurnContextPanel\` (DÉLIA). A implementação anterior introduziu slot opcional \`trailing\`; **não apagá-lo nem quebrar consumidores compartilhados** sem prova de paridade. \`EvidenceDetails\`, \`ActivityViewer\` e rastreamento continuam sendo a fonte da apresentação real. \`EXISTING_EQUIVALENT=YES\`, \`REUSE_DECISION=EXTEND\` como direção sujeita a inventário do HEAD. A mudança é de layout/presentação, sem backend nem contrato de dados novo. O right rail global conversation-scoped permanece independente e com seções futuras \`BLOCKED_PENDING_CONTRACT\`.

### Critérios DENSECTX-01..DENSECTX-16

| ID | Critério |
|---|---|
| DENSECTX-01 | Em wide, duas zonas semânticas equilibradas em vez de três áreas rígidas |
| DENSECTX-02 | Metadados da geração reorganizados em grid interno legível |
| DENSECTX-03 | Ausência de grande área vazia para evidência/atividade inexistente |
| DENSECTX-04 | Evidências e atividades agrupadas em proximidade visual |
| DENSECTX-05 | Rastreamento técnico secundário e recolhível na mesma zona |
| DENSECTX-06 | Compacto/Dock usa uma coluna em ordem semântica |
| DENSECTX-07 | O layout responde à largura real do card/centro, com right rail aberto/fechado |
| DENSECTX-08 | Valores reais, proveniência e ausência legítima de fonte preservados |
| DENSECTX-09 | Limitações materiais e confirmações continuam perceptíveis |
| DENSECTX-10 | Atividade concluída não se transforma em outcome empresarial |
| DENSECTX-11 | Superfície clean sem barra azul, overlays ou scroll aninhado |
| DENSECTX-12 | Vários contextos inline expandidos, foco/ARIA/teclado intactos |
| DENSECTX-13 | Dark/light, mobile 320–420px, zoom 200%, Dock real e reduced motion |
| DENSECTX-14 | Compatibilidade de API, slot trailing e consumidores plugin-ui |
| DENSECTX-15 | Regressão queue/lifecycle/S2/streaming/Markdown/composer |
| DENSECTX-16 | RED/GREEN, QA autenticado, evidência por SHA, ledger, deploy e report |

**TASK_ID:** \`DELIA-UX-INLINE-CONTEXT-SEMANTIC-DENSITY-REFACTOR-01\`.

**MODE:** REANCHOR → CONTRACT/REUSE GATE → RED TESTS → MINIMAL PRESENTATION DIFF → GREEN → VISUAL QA → REGRESSION → REWORK → DOCUMENT EVIDENCE → COMMIT/PUSH MAIN → DEPLOY SCOPED → PRODUCTION VERIFICATION → REPORT.

**Document-only nesta publicação:** \`RUNTIME_CHANGED=NO\`, \`TEST_NOT_RUN\`, \`PHASE_NOT_ADVANCED\`. As medições e commits das versões anteriores são histórico, não evidência da nova organização.

### Registro de implementação — duas zonas semânticas (2026-10-24, PROVEN)

**STATUS: PROVEN / DEPLOYED / PHASE_NOT_ADVANCED.** Implementação CSS-bounded em `plugins/delia/src/index.css`, sem alteração de componente, DOM, contrato ou backend. `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND` (CSS da superfície existente). Commits: `c21c4cd0d1` (duas zonas + grid de metadados), `65e2f1b2ee` (min 160px), `121b98b55f` (min 140px), `97f393390b` (share assimétrico + cap de 2 pares). Deploy `up-prod-sequential.sh --build delia`; SHA de produção verificado `97f393390b`.

**Layout efetivamente implementado:** o container `.delia-turn__context` permanece o query container (largura real do card, não viewport). Card ≥560px de conteúdo com ≥2 seções: grid de duas zonas `minmax(0,1.15fr) minmax(0,1fr)` — zona A = "Detalhes da geração" com `padding-right`+hairline; zona B = seções 2..n + `.delia-context__trace` empilhadas (Evidências → Atividades → Rastreamento). Card com apenas 1 seção ou <560px: flex de coluna única na ordem semântica Geração → Evidências → Atividades → Rastreamento — nenhuma zona vazia reservada. Grid interno `.delia-context__list`: `repeat(auto-fit, minmax(140px,1fr))` com cap `repeat(2, minmax(0,1fr))` acima de 860px de card — 2 pares/linha em wide, 1 par quando a zona A é estreita demais, até 3 pares no modo coluna cheia (<560px, largura total).

**Componentes reutilizados (zero novos):** `ConversationContextPanel` (plugin-ui, com slot `trailing` intacto), `DeliaTurnContextPanel`, `EvidenceDetails`, `ActivityViewer`, trace `<details>` existente. Ordem DOM inalterada — o posicionamento é puramente visual via grid.

**Medições em produção (probe autenticado `vd-densectx-prod.mjs`, 43/43 PASS):** altura do card — @1920: 607→494px (−19%, card 1030px, 2 zonas, 2 pares/linha); @1600: 624→511px (−18%, card 897px); @1440: 653→528px (−19%, card 737px); @1280: card 578px → coluna única legítima (conteúdo <560), metadados em 3 pares/linha; @375: card 262px, coluna única, sem overflow. Right rail aberto: @1920 card 834px mantém 2 zonas; @1600 card 599px 2 zonas; @1440 card 442px coluna única; @1280 fallback popover governado, sem overflow em nenhum modo. Zero scroll aninhado e zero overflow horizontal em todos os cenários. Dark mode: duas zonas sem scroll; `prefers-reduced-motion`: animação `none`.

**Causa-raiz registrada:** a versão em três áreas + lista vertical de metadados causava a coluna alta e vazia; o mínimo de par inicial (200px) não cabia na zona A em 1600/1440 — corrigido com share assimétrico 1.15fr + min 140px + cap de 2 colunas em wide.

**DENSECTX-01..16:** 01–07, 11 PASS via probe medido; 08–10 PASS por invariante (diff apenas CSS, zero mudança de dados/semântica); 12, 14, 15 PASS por regressão (suites verdes); 13 PARCIAL (dark + reduced-motion + mobile PASS; zoom 200% / Dock real / screen reader `TEST_NOT_RUN`); 16 PASS. Residual: REAL_DOCK_QA, ZOOM_200_QA, SCREEN_READER_QA `TEST_NOT_RUN` — sem claim integral.
