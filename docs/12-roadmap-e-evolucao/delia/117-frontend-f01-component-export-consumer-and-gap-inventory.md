# 117 — DÉLIA | F-01 — Inventário bounded de componentes, exports, consumidores e lacunas

**TASK_ID:** `DELIA-UX-F01-EXPORTED-COMPONENTS-CONSUMERS-GAP-INVENTORY-01`  
**Data:** 2026-10-17  
**Tipo:** `DOCUMENTATION_FIRST / BOUNDED_DISCOVERY / NO_PRODUCT_CODE`  
**BASE_HEAD observado:** `eab39319c76a67b1227aa7cfd9ebd5ae031c94c1` na `main`  
**Companheiro:** [116 — Mapa executivo de capacidades/superfícies](./116-delia-frontend-capability-surface-and-component-execution-map.md)  
**Authority:** 16 + 17 + 24 + 25 e ledger; este inventário **não** muda arquitetura, fases ou decisions freezes.

## 1. Decisão e delimitação da F-01

O Product Master autorizou **iniciar F-01**: cruzar os requisitos de UI já planejados com os arquivos/exports reais e decidir qual seria a próxima bounded task de frontend. Nesta fase **não** implementar nem ativar nova capability. Não transformar o planejamento de 116/F-02 em autorização automática; conferir HEAD, fase/CP-RQ, contratos e a decisão específica do documento temático antes do código.

**Reanchor via GitHub:** HEAD, 116, INDEX, 16, specs 71/93/96/97/102, `plugins/plugin-ui/src/index.ts`, `conversation/index.ts`, `composer/index.ts`, consumidor `DeliaConversationPage`, `DeliaAssistantMessage`, `DeliaReception`, `DeliaComposer` e primitives de `feedback/` foram consultados. `REANCHOR=PARTIAL`: não existe neste conector `git status` local, nem prova da leitura integral de todas as authorities no workspace. Quando houver nova task de implementação, reancorar novamente conforme [116 §1](./116-delia-frontend-capability-surface-and-component-execution-map.md). `TESTS=TEST_NOT_RUN`; existência de export `PROVEN` não é runtime `PASS`.

## 2. Matriz dirigida: código presente versus integração efetiva

| Superfície | Evidência de implementação/export | Consumidor DÉLIA verificado | Estado/decisão |
|---|---|---|---|
| Layout categoria/rail | `ConversationThreeRegionLayout`, `NavigationRail`, `NavigationCategoryPanel`, `ConversationNavigation`, `ProjectNavigation`, `AgentNavigation`, `PluginNavigation` publicados/exportados | `DeliaConversationPage.tsx` importa e compõe todos | `PROVEN_PRESENT / PROVEN_COMPOSED`; dados de Projetos/Agentes/Plugins `contract_unavailable` |
| Recepção | `ConversationReception` exportado; avatar `UnifiedAvatar` em layout | `DeliaReception.tsx` importa e apresenta sem turno | `PROVEN_PRESENT / PROVEN_COMPOSED` |
| Composer e ações do envio | `MessageComposer`, `ComposerSendButton`, `ComposerStopButton`, `ComposerClearDraftButton`, `ComposerCharacterCounter` em `composer/index.ts` e raiz | `DeliaComposer.tsx` consome `MessageComposer` e delega estado por props | `PROVEN_PRESENT / PROVEN_COMPOSED`; send/stop outcome depende de runtime |
| Resposta, atividades, evidências, confirmação | `ActivityViewer`, `ConversationAssistantActions`, `ConversationStatus`, `ConversationMarkdown`, `EvidenceDetails`, `GovernedConfirmation`, `UnifiedAvatar` via root exports | `DeliaAssistantMessage.tsx` importa a composição | `PROVEN_PRESENT / PROVEN_IMPORTED`; execução/ativação de rich depende de contrato/backend; imports não provam cada branch executado |
| Histórico/fixadas | `ConversationHistoryItem`, `PinnedConversations`, `ConversationSidebarSearch` em export de conversation | Árvore `DeliaConversationPage → ConversationNavigation`; feed não fornecido na composição examinada | `PROVEN_PRESENT`, `DATA_INTEGRATION=TO_INVENTORY`; não criar histórico fake |
| Markdown e code | `ConversationMarkdown`, `MarkdownDocument` via root export | `DeliaAssistantMessage` importa `ConversationMarkdown` | `FRONTEND_PRESENT`, contrato/ativação `PLANNED / GATED` por 82–91/96; `import != activated` |
| Tarefas/Work | `TaskWorkspacePage`, `TaskCardList`, `TaskDetailCard`, `TaskWorklistSection` presentes sob `tasks/` | Nenhum consumidor DÉLIA de Work comprovado nesta amostra | `EXISTING_EQUIVALENT=YES` **para primitives**, `TO_INVENTORY` para semântica de Task/Work e integração |
| Dados/gráficos | `DataTable`, `ConfigurablePresentationTable`, `LineSeriesChart`, `BarSeriesChart`, `ConfigurableSeriesChart` e outros presentes em `data/`, `charts/` | Nenhuma composição DÉLIA de block typed comprovada nesta amostra | `PRESENTATION_PRIMITIVES=PROVEN`; schemas/contract/binding `TO_INVENTORY` |
| Feedback transitório | `FloatingNoticeStack` existente com `action` e `autoDismissMs` | Integração DÉLIA para undo draft não verificada | `EQUIVALENT_FEEDBACK=YES` para primitive; `REUSE` condicionado a acessibilidade/escopo do overlay |

**Notas de escopo:** `conversation/` continha 54 entradas no diretório consultado; nenhuma tinha `Starter`/`Suggestion` no nome. `src/index.ts` exporta os componentes de conversa e composer, mas isso não substitui uma verificação por AST/build no SHA/config. `0` matches **não prova ausência em todo o repositório**. Nenhuma busca de conteúdo exaustiva foi executada; categorias de Diretórios e superfícies complexas são inventário dirigido, não coverage total.

## 3. Lacunas priorizadas com gate individual

| ID | Especificação | Gap observado | Reuse gate / owner | Decisão F-01 |
|---|---|---|---|---|
| F02-A | [93 — Starter Suggestions](./93-conversation-starter-suggestions-product-ux-specification.md) | Composição dedicada não identificada no `conversation/` nem no export consultado; recepção não possui slot de sugestões atualmente | `EXISTING_EQUIVALENT=YES` para recepção/composer/primitives; `TO_INVENTORY` para composição dedicada; `REUSE_DECISION=EXTEND_OR_NEW_PENDING_GATE`; owner `plugin-ui`, consumer `plugins/delia` | **Primeira candidata render-only**, mas `IMPLEMENTATION_DEFERRED` explícito no doc 93; precisa autorização bounded/CP-RQ e revisão final do inventário de equivalentes |
| F02-B | [96 — Code Block](./96-conversation-code-block-future-ux-specification.md) | Componentização conversacional ampliada deferida | `EXISTING_EQUIVALENT=YES` para bloco de code inerte no Markdown; `REUSE_DECISION=EXTEND_WHEN_AUTHORIZED` | **DEFER** até gates Markdown B2/presentation.v2 e decisão de fase |
| F02-C | [97 — Conversation Search](./97-conversation-search-backend-first-future-ux-specification.md) | Serviço/backend de histórico/pesquisa não provado | `EXISTING_EQUIVALENT=YES` para search primitives; `TO_INVENTORY` para Domain/Search; `REUSE_DECISION=PENDING_GATE` | **DEFER**: decisão `BACKEND_FIRST`; proibido index client-side fake |
| F02-D | [102 — Draft Recovery](./102-conversation-draft-recovery-future-product-ux-specification.md) | Undo recovery ainda deferido | `EXISTING_EQUIVALENT=YES` para composer e `FloatingNoticeStack` com action; `REUSE_DECISION=EXTEND_WHEN_AUTHORIZED` | **DEFER** respeitando doc 102; sem nova persistência/timer autônomo |
| F03-A | [71 — Queue / My Work](./71-conversation-queue-and-my-work-ux-specification.md) + 36/43 | Experiência própria DÉLIA ainda não comprovada; primitives task existentes | `EXISTING_EQUIVALENT=YES` para primitives, `TO_INVENTORY` para work/queue backend; owner DÉLIA Work; `REUSE_DECISION=PENDING` | **NEXT_FUTURE_TRACK**, não misturar fila da conversa com scheduler/Hub |
| F04+ | 37–41, 53–66 | UI de Inbox/Watch/Board/Decision/Analysis/Multimodal/Control Tower deve ser construída por composição governada quando contratada | primitives de `tasks/data/charts/feedback/conversation` existentes; contratos/owners específicos `TO_INVENTORY` | **PLANNED/TARGET**; uma bounded capability de cada vez |

## 4. Primeiro candidato — decisão limitada

**`F02-A / ConversationStarterSuggestions` é o primeiro candidato para análise de implementação, não uma decisão congelada de criar componente.** Por ser uma experiência pequena e estritamente render-only (doc 93), pode ser desenvolvida sem confundir input com uma ação. Contudo, a documentação temática determina `IMPLEMENTATION_DEFERRED`; F-01 **não a revoga**.

**Contrato UX congelado no doc 93 a preservar em eventual execução:** sugestões opcionais na recepção vazia; clicar **preenche somente o rascunho editável** (`draft != send`), não executa submit, não afirma capabilities autorizadas nem sugere informações inventadas. Inputs são fornecidos por consumer legitimamente autorizado; sem sugestões, não renderizar. Não reutilizar estado global ou runtime do Minha DELPI Chat.

**Antes da próxima implementação:**
1. Novo reanchor HEAD/git status + authorities e estado de fase do 16/ledger + CP/RQ aplicáveis.
2. Verificar equivalentes não óbvios no `plugin-ui` completo (cards/action chips/quick prompts) e a API de composição `ConversationReception`.
3. Confirmar alteração explícita do estado `IMPLEMENTATION_DEFERRED` mediante autorização bounded do Product Master e eventual gate superior; se inviável, **STOP e selecionar outra task autorizável**, sem redesenho.
4. Definir props `suggestions?`, label/id, `onSelectDraft`, empty/disabled/focus/responsive; nenhum submit implícito, token/permission em UI ou string que prometa acesso.
5. Implementar o menor diff, testes, build/federation, integração DÉLIA **quando permitida**, QA e registro de evidence/ledger pós-execução.

## 5. F-01 resultado, gaps e continuidade

```text
TASK_ID=DELIA-UX-F01-EXPORTED-COMPONENTS-CONSUMERS-GAP-INVENTORY-01
BASE_HEAD=eab39319c76a67b1227aa7cfd9ebd5ae031c94c1
SCOPE=BOUNDED_DOCUMENTATION_ONLY
FRONTEND_CODE_CHANGED=NO
DOCUMENTS_116_93_96_97_102_71=REVIEWED
PLUGINS_UI_EXPORTS=INSPECTED
DELIA_CONSUMERS=INSPECTED_SELECTED
F01_INVENTORY=COMPLETE_FOR_BOUNDED_SAMPLE
GLOBAL_EXHAUSTIVE_INVENTORY=NO
EXISTING_EQUIVALENT=YES_FOR_SHARED_BASE
NEXT_CANDIDATE=F02-A_CONVERSATION_STARTER_SUGGESTIONS
NEXT_CANDIDATE_AUTHORIZATION=NOT_GRANTED_BY_F01
TESTS=TEST_NOT_RUN
CANONICAL_REANCHOR=PARTIAL_GITHUB_ONLY
PHASE_PROGRESSION=NONE
REVIEW_VERDICT=INCONCLUSIVE_FOR_RUNTIME; DOCUMENTED_FOR_F01
NEXT=COORDINATION_REVIEW_AND_BOUNDED_AUTHORIZATION_FOR_F02-A_OR_ALTERNATIVE
```

**Handoff:** chat `4. DÉLIA — Frontend / MFE / UX`, reancorar 16/17/24/25/ledger, 116/117, 93 e export/consumer atual antes de escrever código. Não reabrir roadmap 115/E02–E08 sem novo defeito real. E09/E10 continuam residuais formais independentes.
