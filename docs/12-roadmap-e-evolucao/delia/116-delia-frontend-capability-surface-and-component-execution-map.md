# 116 — DÉLIA | Mapa executivo de superfícies, capacidades e componentes de frontend

**Data:** 2026-10-17  
**Tipo:** `EXECUTION_NAVIGATION / DOCUMENTATION_ONLY / NON_CANONICAL_PRIORITY`  
**Owner da análise:** Frontend / MFE / UX DÉLIA + coordenação de arquitetura  
**Produto:** DÉLIA standalone de Continuous Operational Intelligence, não um modo do Minha DELPI Chat.  
**Repositório / referência examinada:** `roberiooliveiradev/delpi-central`, `main`, HEAD observado no reanchor `445f264007e9cb62e165502ed749f080e87f9754` (não confundir com SHA de runtime/deploy).  
**Objetivo:** preservar o entendimento transversal da documentação já planejada e orientar a sequência de implementação dos componentes sem duplicar capabilities nem inferir backends.

> **NATUREZA DO DOCUMENTO.** Este mapa é uma **projeção de acompanhamento** derivada das authorities, não uma nova authority, freeze, fase, CP/RQ, autorização de código ou evidência de produto completo. Ao divergir de `16`, `17`, `24`, `25`, contratos, specifications temáticas ou execution ledger, **STOP → EXECUTION_DRIFT / ARCHITECTURE_DECISION_REQUIRED**; não reconciliar silenciosamente. O estado factual de cada capacidade sempre precisa de prova no HEAD/config avaliados. Os documentos já foram planejados/fechados como direção; isto não significa que todos os runtimes foram construídos.

## 1. Reancoragem e fontes que devem acompanhar cada task

Antes de **qualquer** código, design de adapter/contrato ou mudança de fase, executar `git status`, HEAD e `origin/main`; ler Project Instructions/`AGENTS.md`/`.cursor` → [16](./16-execution-master-plan.md) → [50](./50-standalone-copilot-application-architecture.md) → [17](./17-component-and-contract-map.md) → [49](./49-architecture-and-design-patterns-standard.md) → [51](./51-platform-integration-baseline.md) → [52](./52-standalone-repository-and-bootstrap-plan.md) → [21](./21-data-and-state-model.md) → [20](./20-testing-and-acceptance-matrix.md) → [25](./25-requirements-traceability.md) → arquitetura técnica → [24](./24-product-specification.md) → specs temáticas aplicáveis → [ledger](./evidence/execution-ledger.md).

- **Autoridade de sequência/fase:** 16 + ledger vigente, não esta lista. **Rastreabilidade:** CP/RQ e gates em 25/20, não ranges inferidos.
- **Autoridade de produto:** 24; capabilities, contracts e ownership em 17, 49–52 e specs 36–43, 53–66; UX/visual em 69–115 e `personality/`.
- **Portas de reuso por item:** `RESPONSIBILITY → OWNER → SOURCE → CONSUMERS → CONTRACT → IMPLEMENTATION → TEST → OUTCOME`; registrar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`.
- **Estados de fatos/planejamento:** `PROVEN | TO_INVENTORY | PLANNED | TARGET`. **Execução:** `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`. Uma existência de TSX ou export é `PROVEN_PRESENT` de código, **não** `PASS` de integração, autorização, safety ou outcome.
- **Backend pode evoluir em paralelo:** a UI deve aceitar contratos semânticos, provider-neutral, com `read != write`, `draft != send`, `simulate != apply`, `PREPARE != ACT` e `technical success != business outcome`. MCP/A2A discovery, metadata, modelo e memória não autorizam.

## 2. Inventário factual pontual do código e de seus limites

### 2.1 Presente no `plugin-ui` (consulta direta de diretórios e exports)

| Famílias | Arquivos/componentes confirmados no GitHub | Limite da evidência |
|---|---|---|
| Shell e navegação | `ConversationThreeRegionLayout`, `NavigationRail`, `NavigationCategoryPanel`, `ConversationNavigation`, `ConversationHistoryItem`, `PinnedConversations`, `ProjectNavigation`, `AgentNavigation`, `PluginNavigation`, `NavigationActions`, `ConversationSidebarSearch` | presença e exports da série 104–112 `PROVEN`; integrações de histórico/projeto/agente/plugin são condicionadas |
| Conversa | `ConversationWorkspace`, `ConversationHeader`, `ConversationUserMessage`, `ConversationReception`, `ConversationStatus`, `ConversationError`, `ConversationScrollNavigator`, `ConversationAssistantActions`, `MessageActionBar` | UI `PROVEN_PRESENT`; comportamentos e deploy por evidências específicas |
| Evidence/Policy visual | `EvidenceDetails`, `GovernedConfirmation`; `ActivityViewer` em `activity/` | não provam aprovação live, Outcome ou APIs de política |
| Composer | `MessageComposer`, `ComposerSendButton`, `ComposerStopButton`, `ComposerClearDraftButton`, `ComposerCharacterCounter` | controles UI existentes não provam cancelamento no backend, recovery persistente ou send autorizado |
| Markdown | `ConversationMarkdown` e `MarkdownDocument` em `markdown/` | contrato/ativação conversacional de rich blocks ainda depende de 82–91/96; `FILE_EXISTS != RUNTIME_ENABLED` |
| Primitivos de tarefas | `TaskWorkspacePage`, `TaskCardList`, `TaskDetailCard`, `TaskItemsTable`, `TaskWorklistSection`, `TaskEmptyState` e afins em `tasks/` | são candidatos a reuso; não declarar que DÉLIA Work/Case já os consome |
| Data e gráficos | `DataTable`, `ConfigurablePresentationTable`, `DataCardsGrid`, `KanbanBoard`, `Timeline`; charts `LineSeriesChart`, `BarSeriesChart`, `ConfigurableSeriesChart` e outros | apresentação reutilizável, **não** contrato aprovado de séries/métricas DÉLIA |
| Outras primitivas | `feedback/`, `layout/`, `forms/`, `menu/`, `document/`, `preview/`, `collaboration/` etc. | diretórios provados, equivalência funcional de cada item ainda `TO_INVENTORY` |

### 2.2 Consumidor DÉLIA

Em `plugins/delia/src/ui/` foram confirmados `DeliaConversationPage`, `DeliaAssistantMessage`, `DeliaComposer`, `DeliaReception` e `ConversationTimeline`. O código de `DeliaConversationPage` importa shell, rail, painel e categorias do `@delpi/plugin-ui`; `projects`, `agents` e `plugins` são renderizados com `contract_unavailable/catalog_unavailable` por default. Assim, os componentes **existem e são compostos**, mas catálogos/ações reais não são inferidos ou habilitados. Não tratar a simples seleção visual do rail como grant.

### 2.3 Série 69–115 — estado documental interpretado com cuidado

| Specs | Fato útil |
|---|---|
| 73–81 | Base de recepção, avatar, composer, resposta, workspace, erro, atividade, evidence: várias specs registram `IMPLEMENTED / ACCEPTED_CURRENT_SCOPE` ou `INTEGRATED`; revalidar provas específicas antes de novos aceites |
| 82–91 | Conteúdo rico/presentation.v2 e Markdown possuem gates B2/segurança/contratos; código de Markdown pode existir com ativação runtime OFF; não inferir rich blocks ativos |
| 92 | Assistant Actions frontend implementado; feedback/regeneração backend sem contrato provado |
| 93 | Starter Suggestions: `FUTURE_CANDIDATE / IMPLEMENTATION_DEFERRED` |
| 94 | Scroll Navigator: `CODE_COMMITTED_CANDIDATE`, testes/QA no SHA ainda devem ser reconciliados |
| 95 | Stop Response: UI e documentação possuem registros incrementais; sem prova automática de cancelamento end-to-end no backend |
| 96 | Code Block: `IMPLEMENTATION_DEFERRED`, dependência Markdown B2 |
| 97 | Search: `BACKEND_FIRST / IMPLEMENTATION_DEFERRED`; proíbe busca local fictícia |
| 98–101 | Shell/sidebar/contexto/composer e clear draft: já há componentes existentes; aplicar revisões modernas (103–115) em conflito de layout histórico |
| 102 | Draft Recovery: `IMPLEMENTATION_DEFERRED` |
| 103–113 | Navegação visual implementada pelo rework; alguns cabeçalhos históricos continuam `PLANNED/NOT_IMPLEMENTED` apesar dos adendos — `DOCUMENT_STATUS_STALE`, não componente ausente |
| 115 | E01–E08 com aceite registrado; E09 QA autenticado/Dock `INCONCLUSIVE` e E10 revisão final aberta nos registros examinados; não transformar implementation-track encerrado em formal full acceptance |

## 3. Mapa transversal de superfícies futuras (derivado das specs)

| Surface/capability | Fonte(s) de produto | Candidato de apresentação / reuse gate | Status **da superfície DÉLIA** e dependência |
|---|---|---|---|
| Chat/reception/timeline/composer | 69, 73–81, 92, 98–115 | `ConversationWorkspace`, `MessageComposer`, `EvidenceDetails`, `ActivityViewer` | `PROVEN_PARTIAL`: base funcional visual; evolução rich/voice/contract pendente |
| Starter Suggestions | 93 | `ConversationReception`, primitives de ação (`EXTEND` sujeito à spec) | `PLANNED/DEFERRED`; sem autorização implícita |
| Code blocks e presentation rica | 82–91, 96 | `ConversationMarkdown`, markdown, data/charts; `REUSE/EXTEND` condicionado a allowlist e sanitize | `PLANNED/CONTRACT_GATED`; não ativar Markdown/mermaid/chart por output não confiável |
| Search/history/draft recovery | 97, 102, 106–108 | sidebar/search, history item, pinned, composer | UI parcial; `BACKEND_FIRST/TO_INVENTORY` para persistência, search e pin writes |
| Fila conversacional e Meus Trabalhos | 36, 43, 71 | `MessageComposer`, `TaskWorklistSection`, `TaskCardList`, `TaskWorkspacePage` | `TARGET`; fila da conversa != workflow runner/scheduler, Work durável com owner/contrato próprio |
| Inbox/Watch/notificações | 37, 57 | `WorklistItem`, status/banner, tasks cards, timeline (equivalência `TO_INVENTORY`) | `TARGET C6`; Watch C6 OBSERVE/ADVISE/PREPARE; sem ACT autônomo C6 |
| Evidence Board/provenance | 36, 38, 80 | `EvidenceDetails`, tabelas/sections, detail cards (`EXTEND` após contract fit) | base de evidência conversacional existe; **Evidence Board** futuro `TARGET` |
| Decision Gates/approvals/Outcomes | 39, 57 | `GovernedConfirmation`, `ConfirmModalPanel`, status, evidence | `TARGET` além da confirmação já existente; live Core + Domain + Policy/Decision + idempotência + Outcome |
| Simulações e What-if | 39, 64 | dados/formulários, `DataTable`, charts | `TARGET`; `simulate != apply`, Twin não é source of truth |
| MCP/A2A activity e capability transparency | 60, 70, 79 | `ActivityViewer`, `EvidenceDetails`, `ConversationStatus`, `GovernedConfirmation` | apresentação provider-neutral reutilizável; MCP/A2A é interop, não permission; não criar componente por servidor MCP |
| Personal Memory e personalização | 61, personality | user profile/avatar, settings/form components `TO_INVENTORY` | `TARGET`; controle inspect/correct/delete/disable, memory não autoriza |
| Organizational Knowledge/Expertise | 28–29, 40–41 | forms, review lists, cards e provenance `TO_INVENTORY` | `TARGET`; Evidence→candidate→review/eval/version/publish |
| Research/external connectors/Teams | 55–56, 60 | Activity/Evidence, conexão e consent settings `TO_INVENTORY` | `TARGET`; oficiais OAuth/API, nunca tokens em frontend/prompt |
| Analysis Sandbox/Artifact Workspace | 63 | `DataTable`, charts, document/preview/editor primitives | `TARGET`; sandbox bounded, artefatos editáveis governados |
| Process Intelligence/Graph/semantic metrics | 35, 58, 62 | charts, tables, flow/diagram primitives | `TARGET`; cálculo/fatos só por APIs/owners reais |
| Prediction/Operational Twin | 64 | charts comparativos, cenários e evidence | `TARGET`; prediction != FACT |
| AI Control Tower/model lifecycle/marketplace | 59, 66–67 | dashboards, tables, list/detail/governance primitives | `TARGET`; Control Tower não é segundo planner; instalação não concede permissão |
| Meeting/Voice/Frontline/biometric | 53–54, 56 | composer, avatar, captura/media/consent primitives `TO_INVENTORY` | `TARGET`; opt-in/capture indicators, closed-set biometrics não autentica; sem LLM→PLC/CNC/robô |
| Edge/offline/industrial | 53, 65 | status, offline indicators, governança `TO_INVENTORY` | `TARGET`; OT/safety permanece autoridade e interlocks são obrigatórios |
| Operational Incident Intelligence | 24 §25, 57 | alert status, timeline, evidence, tasks | `TARGET`; observar/investigar/verificar, **sem self-healing/code/deploy autônomo** |

**Classificação desta tabela:** `PROVEN_PARTIAL` se há código/apresentação identificável; `TARGET/PLANNED` é **direção documental**. Cada `TO_INVENTORY` exige rastreio de path/export/owner/contrato no HEAD aplicável antes de implementação. Em nenhum ponto assume-se que frontend tem autorização material porque backend MCP/inteligência está sendo desenvolvido em paralelo.

## 4. Backlog de execução de componentes — proposta não canônica

A sequência abaixo é **candidata para coordenação Frontend**, não `NEXT` de C0–C7. Prioridade depende do 16 + ledger/CP-RQ vigentes; cada bounded task requer autorização.

| Faixa candidata | Próximo resultado útil | Tipo de trabalho e gates |
|---|---|---|
| F-01 | Reconciliação do inventário + exports/consumers completos | `DOCUMENTATION_FIRST`; classificar `PRESENT / INTEGRATED / CONTRACT_GATED / MISSING / DEFERRED`; sem inventário infinito |
| F-02 | Lacunas render-only da conversa: sugestões iniciais, code block, ações/progress/scroll conforme docs 92–96 | `REUSE/EXTEND` apenas após verificar itens existentes; quando gate backend ausente, componente desacoplado **disabled**, não mock funcional |
| F-03 | Fila conversacional compacta + Meus Trabalhos apresentação | distinguir fila local/Work durável; reutilizar primitives `tasks/`; não criar scheduler/engine |
| F-04 | Evidence Board e Decision/Outcome composition | reutilizar `EvidenceDetails`/confirmation/tables; estados authoritative, read/PREPARE/ACT governados |
| F-05 | Inbox/Watch e notificações | UI de `OBSERVE/ADVISE/PREPARE`, dedupe e status; actions gated por backend |
| F-06 | Analysis/Artifacts, simuladores e indicadores | reuse de `data/`, `charts/`, `document/` com typed payload, provenance e safe rendering |
| F-07 | Settings de memória/conexões, Meeting/Voice/Frontline | consentimento, minimização, governança; implementação conforme fases e contracts |
| F-08 | Control Tower/Process/Twin/advanced | somente com owners/contratos e fase vigentes, sem false authority |

**Regra operacional:** construir o componente visual que é responsabilidade do frontend, incluindo estado `unavailable/disabled` honesto, **não** inventar dados ou esperar indefinidamente por backend. Depois integrar por contract adapter ao owner verdadeiro; never provider branches in planner/UI. Se o componente já existir no kit, `REUSE` ou `EXTEND`, não `NEW` por conveniência.

## 5. Checklist obrigatório para cada próxima task bounded

1. **Reanchor** HEAD/local status + authorities/ledger/CP-RQ/fase; verificar mudanças concorrentes.
2. **Uma capability/surface por task**: responsabilidade, owner e 1+ consumers comprovados; spec com link e RQ/AC do 25, fase do 16.
3. **Reuse Gate:** procurar `plugin-ui`, consumer DÉLIA, Portal host/Dock, contract/presentation schemas, Domain API, MCP/A2A, Automation Hub, adapter e projections antes de conceber novo componente; `0 search != ausência`.
4. **Contrato UI antes do código:** props/read states, loading/error/empty/disabled, accessible names, callbacks somente intent, quebra em narrow/Dock, light/dark/reduced motion, autorização e permissões derivadas do owner (não do componente).
5. **Menor diff correto**: componente shared render-only em `plugin-ui` quando owner legítimo; adapter/composição em `plugins/delia`; nada do runtime Minha DELPI Chat.
6. **Gates**: Vitest, TS, build/federation, browser quando disponível, security/epistemic/safety, regressão de draft/timeline, outcome evidence por SHA/config. Falta de execução = `TEST_NOT_RUN`.
7. **Documentação**: spec temática + log/ledger após resultado; publicar na `main` conforme regras do repo, sem fase avançada por doc ou commit; review `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

## 6. Gaps de documentação e reconciliação futura

- **Status cabeçalho 103–113** é baseline histórico e pode afirmar `NOT_IMPLEMENTED` apesar da implementação incremental no corpo/roadmap 115; `DOCUMENT_STATUS_STALE`. Corrigir com adendos pontuais, não reescrever decisão congelada.
- **Specs 92–102** apresentam graus diferentes de implementação, deferimento ou dependência de backend; não usar rótulo genérico `pendente`. Verificar as implementações/reviews mais recentes ao iniciar um componente.
- **Readme/plan metadata históricos** podem descrever etapa antiga: 16 + ledger HEAD prevalecem. Divergências devem ser registradas, não ajustadas silenciosamente.
- **Ledger com número duplicado:** durante esta consulta foram encontrados dois registros identificados como `§6.230` (um para E09 local standalone, outro para encerramento do implementation track). `DOCUMENT_INDEX_COLLISION=PROVEN`; preservar texto/ordem e solicitar correção editorial específica, sem renumerar nesta task e sem usar `§6.230` como referencial unívoco.
- **Contratos de produto/backend atuais:** leitura do documento 24 e do mapa 17 fornece targets, não prova que runtime de C4–C7 ou integrações estão disponíveis. Revalidar com owners e ledger antes de expor como operacionais.
- **Inventário de equivalência detalhada:** diretórios `tasks, charts, data, feedback, layout, composer, markdown, conversation` localizados; consumidores/export APIs de cada componente multi-surface ainda `TO_INVENTORY` (não alegar inventário exaustivo).
- **Cadeia de reanchor desta sessão:** HEAD, 16/17/24/25, specs temáticas e código amostrado via GitHub foram consultados; status de workspace, todas as authorities, testes e ambiente do Cursor não foram reexecutados. `REANCHOR=PARTIAL`, `TESTS_THIS_DOCUMENTATION_TASK=TEST_NOT_RUN`.

## 7. Handoff de novo chat frontend especializado

**Chat:** `4. DÉLIA — Frontend / MFE / UX`. **Scope:** executar próximo bounded slice da trilha de componentes, não modificar owners/fase/CP-RQ.  
**Entrada mínima:** HEAD atual + full authorities + ledger; [este 116](./116-delia-frontend-capability-surface-and-component-execution-map.md); [115](./115-navigation-ux-rework-execution-roadmap.md) (implementation track encerrado com residuais E09/E10); docs [69](./69-conversation-experience-ux-wireframes-and-activity-plan.md), [71](./71-conversation-queue-and-my-work-ux-specification.md), [82](./82-conversation-rich-content-and-structured-presentation-specification.md), 92–102; spec temática e contratos da task.  
**Primeira entrega:** bounded proof de equivalência e escolha de **um componente ausente real** (ou extensão legítima) com props/AC de frontend e flags `INTEGRATED/CONTRACT_GATED` explícitas. **Não iniciar implementação sem reanchor/autorizações necessárias.**  
**Coordenação:** decisões de fase/contrato/escalonamento retornam ao chat Architecture / Coordination.

```text
TASK_ID=DELIA-UX-FRONTEND-CAPABILITY-SURFACE-EXECUTION-MAP-01
TYPE=DOCUMENTATION_ONLY
CANONICAL_DOCS_CHANGED=NO
HEAD_REFERENCED=445f264007e9cb62e165502ed749f080e87f9754
EXISTING_EQUIVALENT=YES_FOR_CURRENT_CONVERSATION_SHELL_AND_NAV
REUSE_DECISION=REUSE_OR_EXTEND_PER_COMPONENT
FUTURE_SURFACES=PLANNED_OR_TARGET_NOT_RUNTIME_PROVEN
EXECUTION_PHASE_CHANGE=NO
CODE_CHANGED=NO
TESTS=TEST_NOT_RUN
NEXT=BOUND_F1_RECONCILE_EXPORTS_CONSUMERS_AND_SELECT_FIRST_FRONTEND_COMPONENT
```
