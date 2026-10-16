# 103 — DÉLIA | DeliaNavigationSidebar — Navegação principal por categorias

**Data:** 2026-10-16  
**Status:** `PRODUCT_UX_SPEC / PLANNED / NOT_IMPLEMENTED`. **Documentação somente**: sem frontend, backend, dados mock de produção, deploy, mudança de fase ou aceite.  
**Produto:** DÉLIA standalone. `plugin-ui` é owner de apresentação compartilhada; `plugins/delia` compõe o produto e seu estado. O Portal continua host/navegação global; Core resolve autorização; APIs de domínio são autoridade final; MCP/A2A não conferem permissão.  
**Reancoragem obrigatória antes de executar:** HEAD/git status e .cursor/Project Instructions → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → documentos temáticos → ledger; evidência conflitante exige `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`.  
**Base verificada nesta documentação:** GitHub `main` `e7159c86756ba05f885cf0ccdbfe6fb2faecb54b`. Não presumir que será o HEAD de implementação.  
**Gates universais:** `read != write`, `draft != send`, `PREPARE != ACT`, `discovery != approval`, `model output != FACT`, `JWT != live AuthZ`; layout não concede authority.  

**Decisão do Product Master:** **rail persistente de categorias + painel expansível**, independente do `ConversationWorkspace` e do card flutuante de Contexto. Esta composição futura substitui a responsabilidade exclusivamente conversacional da sidebar atual, **sem** criar uma segunda sidebar concorrente.

## Objetivo, regiões e propriedade

```text
[Portal — host, fora da DÉLIA]
┌─────────┬────────────────────────────┬──────────────────────────────────┐
│ RAIL    │ PAINEL EXPANSÍVEL           │ CONVERSATION WORKSPACE           │
│ Conversas│ categoria selecionada      │ recepção / timeline / composer   │
│ Projetos│ Fixadas / Recentes etc.    │ [⋯ Contexto = popover flutuante] │
│ Agentes │                            │                                  │
│ Plugins │                            │                                  │
│ ...     │                            │                                  │
└─────────┴────────────────────────────┴──────────────────────────────────┘
```

A navegação possui **duas camadas à esquerda**, não três sidebars. Categoria selecionada não muda a sessão conversacional por si só. O painel contextual direito permanece **popover**, não uma coluna fixa; documentos [98](./98-delia-full-page-three-region-layout-product-ux-specification.md), [99](./99-conversation-sidebar-left-product-ux-specification.md) e [100](./100-conversation-context-panel-right-product-ux-specification.md) são histórico de decisões, com R2/R3/R5 prevalecendo sobre versões visuais antigas. A presente série define apenas a evolução da navegação esquerda.

## Anatomia e hierarquia

1. [104 — NavigationRail](./104-navigation-rail-categories-visual-functional-specification.md): ícones fixos, seleção e expandir/recolher.
2. [105 — NavigationCategoryPanel](./105-navigation-category-panel-visual-functional-specification.md): conteúdo da categoria ativa, header, rolagem e empty state.
3. [106 — ConversationNavigation](./106-conversation-navigation-groups-product-ux-specification.md): Nova conversa, Pesquisa contratual, Fixadas, Recentes, Anteriores.
4. [107 — ConversationHistoryItem](./107-conversation-history-item-product-ux-specification.md): item de histórico real e ações.
5. [108 — PinnedConversations](./108-pinned-conversations-group-product-ux-specification.md): seção e regras de fixação futuras.
6. [109 — ProjectNavigation](./109-project-navigation-product-ux-specification.md): projetos com owner/contrato.
7. [110 — AgentNavigation](./110-agent-navigation-product-ux-specification.md): especialistas/agents autorizados.
8. [111 — PluginNavigation](./111-plugin-navigation-product-ux-specification.md): recursos e aplicativos governados pelo Portal/Core.
9. [112 — NavigationActions](./112-navigation-actions-toggles-search-product-ux-specification.md): toggles, Nova conversa, pesquisa, opções, estados.
10. [113 — NavigationResponsiveMotionA11y](./113-navigation-responsive-motion-accessibility-specification.md): contratos transversais de tela, motion e keyboard.

**Nota:** os nomes são rótulos de UX/boundaries e **não** autorização para criar engines, managers, registries ou 10 componentes de código.

## Estados funcionais do conjunto

| Estado | Rail | Painel | Centro |
|---|---|---|---|
| Inicial amplo | visível, Conversas ativa | aberto em Conversas | preservado |
| Recolhido | visível, 56–64px | largura zero | expandido |
| Seleção de outra categoria | muda indicador | abre/atualiza conteúdo autorizado | não reinicia |
| Painel em compact | visível se couber | drawer sob demanda, sem coluna comprimida | preservado |
| Dock muito estreito | entrypoint compacto quando rail inviável | drawer/modal acessível | ocupa espaço prioritário |
| Falha de catálogo | categoria não exibe dados falsos | unavailable/retry legítimo | preservado |
| Contexto aberto | inalterado | inalterado | popover sobreposto independente |

## Geometria candidata e regras de cálculo

Rail 56–64px desktop e ~52px compact. Painel 248–288px aberto, recalculado por largura do container; centro `min-width:0`, conteúdo interno conforme `ConversationWorkspace` e composer existente. Desktop ideal ≥1280px com painel aberto. Largura intermediária usa overlay; mobile/dock prioriza composer e não impõe rail se retirar espaço útil crítico. Não fixar `100vh` dentro do Portal. Bordas hairline, sem containers cinza persistentes em ícones inativos, nem segundo cabeçalho DÉLIA.

## Eventos e fluxo de estado (contrato a congelar antes de código)

`selectedCategory`: `conversations|projects|agents|plugins` (identificadores semânticos estáveis, não nomes de API); `panelMode`: `open|collapsed|overlay`; `viewportMode`: derivado do container; `categoryAvailability`: autorizada/indisponível/oculta. A UI usa callbacks de intenção, não executa fetch no kit.

Clicar no ícone seleciona categoria e abre painel quando aplicável; recolher mantém rail; abrir popover Contexto é independente. Sem navegação automática para projeto/agente/plugin se não houver rota autorizada. A seleção de categoria não troca implicitamente conversa nem limpa draft. O painel pode ter conteúdo virtualizado/paginado no futuro mediante source real.

## Ownership e reuse gate

**PROVEN** no repo consultado: `ConversationThreeRegionLayout` monta rail recolhível (não é navegador multicategoria), `ConversationSidebar` apresenta Nova conversa/Pesquisar/Recentes/Opções, `DeliaConversationPage` os importa, contexto é popover. **TO_INVENTORY**: equivalentes no kit para rail/nav tree/drawer, catálogos, contratos de projeto/agente/plugin e lista persistida.  
`EXISTING_EQUIVALENT=YES` para shell e primitives existentes; `REUSE_DECISION=EXTEND` para evolução visual. Para cada novo boundary de conteúdo: `EXISTING_EQUIVALENT=TO_INVENTORY` e `REUSE_DECISION=PENDING_GATE`. Não duplicar Portal/Core nem o runtime Minha DELPI Chat.

## Sequência sugerida (sem autorização de execução)

A) evoluir shell/rail/painel render-only; B) prover category renderer com estados reais/indisponíveis sem mocks; C) integrar histórico e busca apenas após persistência/contratos; D) integrar projetos/agentes/plugins via owners; E) executar testes end-to-end e revisão. **Documentação não promove fase**. 

## Critérios transversais de qualidade

- **Design system:** usar tokens, typografia, `IconButton`, feedback e superfícies do `plugin-ui`; ícones Lucide, sem cores hardcoded como identidade; no claro e escuro, ícone ghost transparente em repouso, hover tonal, foco visível, estados pressed/selected distinguíveis.
- **Responsividade:** medir container do Portal, não assumir viewport global. Cobrir página ≥1440, 1280, 1024, 768, 420, 375, 320px, zoom 200%, além do Companion Dock; não renderizar lista legível em rail estreito.
- **Movimento:** transição curta 180–240ms conforme tokens existentes; `prefers-reduced-motion` instantâneo; nunca remount do `ConversationWorkspace` nem perda de draft ao selecionar categoria.
- **Acessibilidade:** landmarks únicos, labels de ícones e hints por teclado, `aria-current` para navegação, `aria-expanded`/`aria-controls` para expansão, ordem de Tab previsível, Escape apenas em overlays, restauração de foco, contraste e screen reader.
- **Sem falso runtime:** nada de nomes de conversas, projetos, agentes, plugins, datas, métricas ou permissão inferidos. Loading só com requisição real; vazio = resultado autorizado real, indisponível = contrato inexistente, proibido = sem revelação de recursos.
- **Segurança:** nenhum item visual executa domínio, MCP, ferramenta, automação ou write por clique sem fluxo autorizado. Dados externos são não confiáveis; labels/snippets renderizados como texto inerte.
- **Validação:** testes de props/callbacks/estados e negativos de AuthZ, QA page/dock light/dark, check de exports/federação, prova de generalização em cenários de navegação e revisão independente no SHA executado. `TEST_NOT_RUN` não equivale a PASS.


```text
MASTER_SPEC = DOCUMENTED
MULTICATEGORY_NAVIGATION = NOT_IMPLEMENTED
CATEGORY_RAIL = TARGET
EXPANDABLE_PANEL = TARGET
CONVERSATION_HISTORY = CONTRACT_DEPENDENT
AGENTS_PROJECTS_PLUGINS = OWNER_CONTRACT_DEPENDENT
TESTS = TEST_NOT_RUN
PHASE_PROGRESSION = NONE
```

## Rework R1 — contrato consolidado para implementação futura (2026-10-16)

**Origem:** parecer documental [114](./114-navigation-sidebar-103-113-independent-document-review.md), achados R-01 a R-08. Esta seção **prevalece sobre orientações conflitantes anteriores dos documentos 103–113**. **Escopo desta entrega: documentação apenas.** `DESIGN_BASELINE=DOCUMENTED_WITH_GATES` não equivale a `IMPLEMENTATION_AUTHORIZED`.

### 1. Estrutura de composição congelada visualmente (R-01/R-06)

```text
DeliaConversationPage (owner do estado de seleção e expansão)
├─ left = área de navegação já existente (EXTEND, nunca segunda sidebar)
│  ├─ NavigationRail (categorias e controle único quando painel fechado)
│  └─ NavigationCategoryPanel (quando aberto; controle único em seu header)
├─ center = ConversationWorkspace EXISTENTE (preservado/montado)
└─ context = ContextPopover EXISTENTE (independente, sem coluna direita)
```

- **Único estado controlado** `selectedCategory` e `panelPresentation = expanded | rail_only | overlay | launcher_only`, mantido no consumer DÉLIA; `plugin-ui` render-only e callbacks de intenção. A distinção `expanded/overlay` é apresentação, não mudança de categoria.
- **Exatamente um botão toggle presente e operável por vez**: painel inline/overlay aberto → botão no header do painel; painel recolhido → botão no topo do rail; `launcher_only` → disparador único no header central/slot aprovado. Não renderizar toggles simultâneos com `display:none` apenas; evitar duplicação no DOM e tab order.
- Clique na categoria ativa quando recolhida abre painel; clique noutra categoria seleciona e apresenta o painel se categoria estiver autorizada para apresentação; nunca cria sessão, muda conversa, envia draft ou reexecuta turnos.
- O `ConversationWorkspace` permanece com identidade e instância estáveis ao selecionar categoria ou cruzar breakpoint. A composição não introduz segundo header da DÉLIA.

### 2. Matriz única de disponibilidade (R-02/R-07)

| Status fornecido por consumer/owner | Rail | Painel | Clique |
|---|---|---|---|
| `approved_visible` | mostrar ícone | conteúdo autorizado ou estado real | selecionar categoria |
| `contract_unavailable` | ícone da categoria aprovada em estado **disabled** com label explicativo | orientação curta apenas se painel já selecionado em contexto autorizado | sem ação fake |
| `loading_real` | ícone ativo sem presumir permissão | loading apenas após consulta real | não abrir recurso ainda |
| `authorized_empty` | mostrar | vazio confirmado pela API | pode navegar a lista vazia |
| `forbidden` | **ocultar** categoria e metadados | não mostrar | negar no servidor |
| `error` | mostrar somente quando categoria já era aprovada para visualização | erro tipado e retry real | ação somente se retry aprovado |
| `revoked` | remover/neutralizar conforme contrato sem vazar conteúdo | limpar dados anteriores | bloquear link/launch |

**Decisão de produto já expressa:** Conversas, Projetos, Agentes e Plugins constituem as **quatro categorias-alvo de UX**. Sua presença na especificação não comprova contrato nem permissão. Para entrega frontend puramente visual, uma categoria pode ser apresentada com `contract_unavailable` como affordance **se aprovada no escopo da task**, nunca como catálogo funcional. `forbidden` não deve mostrar label/quantidade/tooltip. Evitar estados vazios duplicados. **Fonte de availability de backend = TO_INVENTORY**, nenhum boolean frontend substitui AuthZ live.

### 3. Algoritmo de layout proposto, com gate de QA (R-03)

A fonte de dimensão é o **container disponível do Portal/Companion Dock**, nunca `window.innerWidth`. Ordem de prioridade: (1) preservar `ConversationWorkspace` e largura útil do composer; (2) reservar rail se ainda houver espaço suficiente; (3) abrir painel inline somente quando `containerWidth - railWidth - panelWidth >= minCenterWidth`; (4) caso contrário, painel como overlay; (5) em largura extrema, trocar rail por launcher único.

**Alvos candidatos para primeiro teste**, não constantes congeladas: `railWidth = 56–64px` (52px compacto); `panelWidth = 248–288px`; `minCenterWidth = 600px` em desktop, recalibrado com composer/Dock; `launcher_only` em containers ≤420px se o rail reduzir área útil. **Se QA mostrar quebra, STOP e decisão visual**, não alterar silently. Ao passar para compact, fechar overlay aberto e manter `selectedCategory` em memória da sessão; ao voltar ao amplo, preferir estado do painel definido pelo usuário quando não conflitar com centro. `ContextPopover` continua flutuante, mas em tela estreita deve fechar ao abrir drawer de navegação e vice-versa, sem perturbar confirmação governada.

### 4. Matriz de ações e gates mínimos (R-04)

| Ação da UI | Natureza | Owner da capacidade | Prérequisito para habilitar |
|---|---|---|---|
| Expandir/recolher | UI local | DÉLIA + `plugin-ui` | apresentação válida e foco seguro |
| Selecionar categoria | UI local | DÉLIA | categoria autorizada/visível; nenhum ACT |
| Nova conversa persistida | write/session | owner de sessões DÉLIA **TO_INVENTORY** | contrato, guardas de draft/stream/decisão, AuthZ, idempotência, postcondition |
| Selecionar conversa | read/context switch | owner de histórico DÉLIA **TO_INVENTORY** | sessão persistida, ACL live, recuperação de turns, preservação de pending flows |
| Pesquisar conversas | read | owner de busca backend **TO_INVENTORY** | doc 97, persistência/index, ACL, paginação |
| Fixar/desafixar | write | owner de metadados **TO_INVENTORY** | AuthZ, idempotência, audit, postcondition |
| Renomear/arquivar/excluir | write | owner de conversas **TO_INVENTORY** | consentimento/confirm quando aplicável, AuthZ, regras, audit, rollback/revoke |
| Abrir projeto/agente/plugin | navigation/read ou delegated action | Portal/Core/Domain/owner **TO_INVENTORY** | catálogo/rota autorizados; launch não implica ACT |
| Opções | UI/menu local | DÉLIA + owner de settings | menu de comandos efetivamente implementados, sem duplicar Portal |

Botão disabled/sem handler não vira “contrato pronto”. Ação técnico-sucedida não significa outcome. Não inferir listagem de conversations pela memória React.

### 5. Limites de decisão e gates

- `EXISTING_EQUIVALENT=YES` para shell, rail atual, `ConversationSidebar`, `ConversationWorkspace`, `ContextPopover`, `IconButton`; `REUSE_DECISION=EXTEND` a composição compartilhada **sem duplicar shell**.
- `EXISTING_EQUIVALENT=TO_INVENTORY` para registry ou UI nav universal do kit, sessão persistida, projetos, agents e apps; `REUSE_DECISION=PENDING_GATE` para contratos/feeds. Search result vazio **não prova inexistência**.
- **Plugins/Aplicações:** owner Portal/Core. Uma eventual lista na DÉLIA deve ser **atalhos/deeplinks autorizados do Portal**. Se exigir catálogo paralelo, criar decisão explícita `ARCHITECTURE_DECISION_REQUIRED` antes de código.
- Projetos e Agentes: categoria visual planejada, **fonte, RBAC e ação não provados**. Nenhum adapter/integration autorizado por esta spec.
- Este rework documental **não** muda ledger/fase, não executa testes e não dá aceite do runtime. Antes de code task, reancorar fontes canônicas e resolver drift.

```text
DOCUMENTATION_R1 = REWORK_APPLIED
VISUAL_COMPOSITION = SPECIFIED
FULL_CANONICAL_REANCHOR = INCONCLUSIVE
RUNTIME_IMPLEMENTATION = NOT_AUTHORIZED_BY_DOCS
CONTRACTS_DATA_CATALOGS = TO_INVENTORY
TESTS = TEST_NOT_RUN
INDEPENDENT_RUNTIME_ACCEPTANCE = PENDING
```
