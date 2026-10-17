# 115 — DÉLIA | Navigation UX Rework — Roadmap de execução e aceite

**Data de abertura:** 2026-10-17
**Produto:** DÉLIA standalone — não é Minha DELPI Chat.
**Tipo:** `EXECUTION_ROADMAP / DOCUMENTATION_ONLY`
**Status inicial:** `PLAN_REGISTERED / 0_OF_10_ACCEPTED`
**Baseline do plano (GitHub main, antes deste documento):** `faecfd8a3e2070eec87f45ac39b3534c452db9e7`
**Owner de coordenação:** arquitetura/coordenação DÉLIA. **Implementação:** frontend DÉLIA + `plugins/plugin-ui`; Portal é host/owner de navegação global; Core é owner de apps/rotas/RBAC; Domain APIs são autoridade de domínio.
**Autoridade:** este documento acompanha execução, mas **não substitui** authorities canônicas, decisões congeladas, contratos ou ledger; não declara fase/NEXT.

> **Instrução expressa do Product Master:** primeiro documentar o roadmap no GitHub; depois implementar **uma etapa por vez**, registrando conclusão/pendências para não perder o estado. A publicação deste plano não autoriza iniciar automaticamente a etapa 01.

## 1. Problema e evidência inicial

O usuário apresentou capturas do Portal `/apps/delia` após `git pull` e build/deploy sequencial dos serviços `plugin-ui` e `delia`. O pull avançou de `e7159c867` para `faecfd8a3`; os logs mostraram `npm run build` do plugin-ui e `npx vite build` da DÉLIA concluídos, imagens criadas e containers recriados. **Isso não comprova QA de navegador nem business outcome.**

Observações das capturas enviadas pelo usuário (evidência visual pontual, não suíte automatizada):
- **Desktop:** painel Conversas aparece sozinho, sem rail de categorias simultâneo; pequena diferença aparente versus sidebar anterior.
- **Mobile recolhido:** rail com quatro ícones é visível e a conversa permanece em primeiro plano, mas consome largura útil.
- **Mobile expandido:** painel esquerdo ocupa grande parte da tela, conteúdo central fica atrás/parcialmente cortado; comportamento de drawer, backdrop e foco não está completo.
- **Contexto no mobile:** popover ocupa área proporcionalmente grande e cobre o centro; é necessário redimensionar/posicionar e coordenar exclusividade de superfícies.
- O código do consumer `DeliaConversationPage` escolhe `collapsed ? NavigationRail : NavigationCategoryPanel`. Portanto o objetivo `rail + painel` concomitantes no desktop ainda não está realizado.

**Veredicto inicial restrito ao UX observado:** `REWORK`. **Testes automatizados, resize QA, live permissions e regressão em múltiplas larguras:** `TEST_NOT_RUN` nesta abertura.

## 2. Resultado esperado e escopo

**Objetivo único:** concluir a **experiência visual, responsiva e acessível** da navegação DÉLIA segundo os documentos [103](./103-delia-navigation-sidebar-master-product-ux-specification.md), [104](./104-navigation-rail-categories-visual-functional-specification.md), [105](./105-navigation-category-panel-visual-functional-specification.md), [112](./112-navigation-actions-toggles-search-product-ux-specification.md) e [113](./113-navigation-responsive-motion-accessibility-specification.md), sem regressão de [97](./97-conversation-search-backend-first-future-ux-specification.md) e do `ConversationWorkspace`.

**Inclui:** rail de categorias persistente quando houver espaço; painel expansível independente; troca de categoria sem fechar o painel no desktop; drawer/launcher governado no compacto; contexto flutuante adaptado ao container; Escape/foco/backdrop; temas e motion; execução de testes, builds federados, QA real e aceite independente.

**Não inclui:** criar persistência de conversas, catálogos de projetos/agentes/apps, instalações de plugins, autenticação/RBAC, execução de agentes, MCP/A2A, Automation Hub, criação real de sessões, fixar/renomear/excluir, alterações em Domain API, Core ou Portal sem contrato. Indicadores de categorias sem contrato permanecem honestos e sem inventar listas/autorização. `C5/C6/C7` e autonomia não mudam.

**Não confundir 100% UX com 100% do produto:** este plano mede **somente** a navegação frontend. Conclusão não significa backends/capabilities integrados.

## 3. Reancoragem e reuse gates antes de cada etapa

Em **cada task bounded**, no HEAD corrente e workspace:
1. `git status` + HEAD/branch/remote, verificar ausência de mudanças concorrentes; preservar alterações de terceiros.
2. **Ordem canônica obrigatória:** Project Instructions + `.cursor` → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática 103–114/115 → ledger.
3. Identificar owner/consumer, fase/NEXT e CP/RQ **do HEAD + ledger**, contrato real e limite do escopo. Não inferir de chat, memória, exemplos ou de `0 search results`.
4. `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW`. Inventariar os equivalentes envolvidos: `ConversationThreeRegionLayout`, `NavigationRail`, `NavigationCategoryPanel`, `ConversationSidebar`, `ConversationNavigation`, `NavigationActions`, `ConversationSidebarSearch`, `ConversationContextPanel/ContextPopover`, design tokens, `ConversationWorkspace`, host Portal e módulo de Dock. **Baseline visual: `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=EXTEND`; não construir segundo shell.**
5. Se evidência invalidar uma decisão documental, **STOP → `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`**, sem reconciliação silenciosa. O documento 115 não autoriza contornar conflitos.
6. Aplicar menor diff; testes/evals, build/federação, QA conforme a etapa; residual search; registrar commits/SHA, outcome evidence e ledger **após** resultado factual. Não declarar PASS por documentação ou HTTP 200.

**Status documentais:** `PLANNED|TARGET|TO_INVENTORY|PROVEN`. **Execução:** `PENDING|PASS|FAIL|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`. **Review independente:** `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.

## 4. Quadro mestre — checklist de progresso

**Regra:** `[x]` apenas depois do critério de aceite daquela etapa ter sido verificado no SHA/config aplicável, com evidências registradas na seção 7; `commit/push` sozinho não fecha item. Se houver falha, manter `[ ]` e registrar `FAIL/REWORK`. Nenhum item é retroativamente aceito pelas entregas isoladas 104–112.

| Etapa | Entrega bounded | Dependência | Estado | Evidência mínima para marcar |
|---|---|---|---|---|
| E01 | Reanchor, baseline e critérios de aceite | Nenhuma | **ACCEPTED_WITH_RESIDUAL** | Authorities+ledger+workspace+SSH+code baseline+unit/build; browser autenticado → residual E09 |
| E02 | Composição Rail + Panel desktop | E01 | **PENDING** | rail e painel simultâneos, centro sem remount, testes + screenshot |
| E03 | Troca direta das quatro categorias | E02 | **PENDING** | troca no rail sem recolher, estados honestos, testes de navegação |
| E04 | Sidebar responsiva + drawer mobile | E03 | **PENDING** | largura baseada no host; overlay, backdrop, Escape e foco sem corte |
| E05 | ContextPopover responsivo | E04 | **PENDING** | limites, scroll, posicionamento, sem cobrir composer indevidamente |
| E06 | Convivência de painéis + acessibilidade | E04+E05 | **PENDING** | exclusividade mobile, teclado/foco/ARIA, não cancelar fluxo governado |
| E07 | Polimento visual e motion | E02–E06 | **PENDING** | tokens/themes/light-dark, zoom, reduced-motion, regressão visual |
| E08 | Regressão integrada e gates de build | E02–E07 | **PENDING** | Vitest/TS/build/federation no SHA, draft/stream/context preservados |
| E09 | QA de navegador Portal + Dock | E08 | **PENDING** | matriz de larguras/temas/overlays com evidência executada |
| E10 | Review independente e encerramento | E09 | **PENDING** | veredicto, residuais resolvidos/aceitos, ledger/docs sincronizados |

- [x] **E01** — Baseline e critérios de aceite (`ACCEPT_WITH_RESIDUAL`; residual browser autenticado → E09; review independente PENDING)
- [ ] **E02** — Rail + Panel simultâneos no desktop
- [ ] **E03** — Categorias alternáveis diretamente
- [ ] **E04** — Sidebar/drawer mobile
- [ ] **E05** — Contexto responsivo
- [ ] **E06** — Convivência/foco/acessibilidade
- [ ] **E07** — Consistência visual/motion
- [ ] **E08** — Testes/TypeScript/build/federação/regressão
- [ ] **E09** — QA visual integrado no Portal/Dock
- [ ] **E10** — Aceite independente e fechamento

**Progresso: `1/10 ACCEPTED (10%)` — E01 `ACCEPT_WITH_RESIDUAL`.** Quantidade de commits ou componentes não altera esse indicador. Aceite E01 não autoriza E02 automaticamente sem task bounded.

## 5. Especificação bounded de cada etapa

### E01 — Reancoragem, baseline e critérios de aceite

**TASK_ID:** `DELIA-UX-NAV-REWORK-E01-BASELINE-01`
**Responsabilidade:** coordenação + frontend QA; documentação e descoberta dirigidas aos arquivos/contratos do escopo (sem inventários infinitos).
**Executar:** validar as autoridades e decisões atuais; identificar fase e ledger; registrar hashes de plugin-ui/DÉLIA implantados e origem das capturas; inventariar apenas slots/toggles/layout CSS/host container/Dock, tests e a origem do `ContextPopover`; reproduzir cenários e tirar baseline das larguras.
**Saída:** matriz de critérios verificáveis, estado atual real, dependências e limitações; decisão de reuse explícita.
**Aceite:** baseline com screenshots e evidências de código/HEAD, gaps identificados; sem design drift; `NEXT=E02` somente após aceite.

### E02 — Composição Rail + Panel simultâneos no desktop

**TASK_ID:** `DELIA-UX-NAV-REWORK-E02-DESKTOP-COMPOSITION-01`
**Responsabilidade:** `plugin-ui` (shell), DÉLIA (seleção/composição).
**Executar:** alterar a composição exclusiva `collapsed ? rail : panel`; manter um rail persistente e painel adjacente quando cabe; apenas **um** toggle operável por estado; dimensionamento dependente do host; não recriar nav, não duplicar header.
**Aceite:** rail 56–64px + painel 248–288px como **alvos sujeitos a QA**; centro útil; panel recolhido mantém rail; `ConversationWorkspace` não é remontado e o draft não se perde.

### E03 — Categorias alternáveis no rail

**TASK_ID:** `DELIA-UX-NAV-REWORK-E03-CATEGORY-SWITCH-01`
**Responsabilidade:** DÉLIA estado `selectedCategory`, `plugin-ui` apresentação.
**Executar:** quatro categorias configuradas e permitidas conforme contrato visual, clique troca painel sem recolher nem mexer no centro; indicar seleção acessível; manter indisponibilidade real de Projetos/Agentes/Plugins.
**Aceite:** Conversas/Projetos/Agentes/Plugins diretamente alternáveis, sem catálogo fictício, nem autorização inferida, sem nova sessão/ACT; manter draft/stream e contexto.

### E04 — Sidebar responsiva e drawer mobile

**TASK_ID:** `DELIA-UX-NAV-REWORK-E04-MOBILE-DRAWER-01`
**Responsabilidade:** `plugin-ui` shell/CSS, host DÉLIA.
**Executar:** decidir por **largura do container Portal**, não viewport global: rail compacto ou launcher único conforme espaço do composer; painel vira drawer com limite de largura, fundo/backdrop, Escape, close e return-focus, scroll interno e sem elementos ocultos tabuláveis.
**Aceite:** 420/375/320 e Dock sem vazamento ou corte do composer, drawer fecha corretamente por botões/backdrop/Escape e centro mantém instância.

### E05 — ContextPopover responsivo

**TASK_ID:** `DELIA-UX-NAV-REWORK-E05-CONTEXT-RESPONSIVE-01`
**Responsabilidade:** `plugin-ui` shell e card Contexto; DÉLIA apenas consumo.
**Executar:** preservar a opção de card flutuante no desktop; aplicar dimensões pelo host, limites e rolagem no mobile; não virar coluna fixa, não cobrir controles críticos indevidamente.
**Aceite:** 1440/1024/768/420/375/320, overflow e scroll corretos; conteúdo Contexto legível, fecha sem cancelar turnos, foco seguro.

### E06 — Convivência de superfícies e acessibilidade

**TASK_ID:** `DELIA-UX-NAV-REWORK-E06-OVERLAYS-A11Y-01`
**Responsabilidade:** `plugin-ui` interaction shell.
**Executar:** coordenar drawer/contexto no compacto; garantir que só uma superfície sobreposta fique ativa; gerenciar Escape, foco de abertura/fechamento, backdrop, `aria-expanded`/`aria-controls`, teclado/leitor de tela e resize com overlay aberto; não tocar estado de autorização ou PREPARE/ACT.
**Aceite:** matriz de teclado/foco aprovada; nenhuma navegação interage com conteúdo invisível; nenhuma confirmação governada é cancelada involuntariamente.

### E07 — Polimento visual e movimento

**TASK_ID:** `DELIA-UX-NAV-REWORK-E07-VISUAL-MOTION-01`
**Responsabilidade:** `plugin-ui` design system e CSS local.
**Executar:** uniformizar rail/painel/ícones/spacing/hover/selected, dark/light/contraste, label/truncation, transições e reduced-motion; não criar segunda biblioteca de componentes, animations engine ou paleta nova.
**Aceite:** screenshots coerentes, foco distinguível, nenhuma quebra em zoom 200% e `prefers-reduced-motion`.

### E08 — Regressão funcional, TypeScript, testes e Federation

**TASK_ID:** `DELIA-UX-NAV-REWORK-E08-INTEGRATION-REGRESSION-01`
**Responsabilidade:** frontend `plugin-ui` + `plugins/delia`.
**Executar:** executar e corrigir testes anteriores 104–112, testes novos 113 e regressões; TypeScript, build do remote plugin-ui, verificação host exports, build da DÉLIA, compatibilidade de federação e de consumer/Portal; preservar draft, composer, mensagens, scroll, streaming, contexto, confirmação.
**Aceite:** evidência de comandos, resultados por SHA/config; sem regressões bloqueantes; se falhar, `FAIL` com correção bounded antes de E09. `BUILD_PASS != RUNTIME_ACCEPT`.

### E09 — QA integrado de navegador no Portal e Companion Dock

**TASK_ID:** `DELIA-UX-NAV-REWORK-E09-LIVE-BROWSER-QA-01`
**Responsabilidade:** QA frontend + host Portal.
**Executar:** validar desktop 1440/1280/1024/768, mobile 420/375/320, zoom 200%, Dock, light/dark, reduced-motion; alternar painel, quatro categorias, contexto, voltar ao centro, resize e teclado; guardar screenshots/logs/ambiente autenticado quando autorizado.
**Aceite:** matriz completa com PASS/FAIL, evidência de ausência de corte/overlap, nenhum recurso falso habilitado; problemas residuais classificados e correções reexecutadas no mesmo SHA/config final. Se credencial/browser não estiver disponível, `TEST_NOT_RUN` e **não marcar E09**.

### E10 — Review independente e encerramento

**TASK_ID:** `DELIA-UX-NAV-REWORK-E10-INDEPENDENT-ACCEPTANCE-01`
**Responsabilidade:** revisor independente da implementação.
**Executar:** ler o HEAD final, diff, authorities/ledger, evidências E01–E09 e deployed SHA; revisar segurança/ownership/reuse, QA e regressões, fechar ou classificar residuais; atualizar documentos de conclusão/ledger com resultados factuais após veredicto.
**Aceite:** `ACCEPT` ou `ACCEPT_WITH_RESIDUAL` com residuais explicitamente aceitos (nenhum bloqueante); verificar push/HEAD, produção no SHA avaliado. `REWORK`, `INCONCLUSIVE` ou `EXECUTION_DRIFT` não permitem marcar a etapa como concluída.

## 6. Gates de saída e política de passagem

- **Gate A — estrutura (E01–E03):** rail/painel e categorias coexistem no desktop com center estável; se não, E04 não inicia.
- **Gate B — responsividade (E04–E07):** drawer/contexto e teclado/motion demonstrados sem perda de draft/composer/fluxo governado; se não, E08 não libera E09.
- **Gate C — integração/aceite (E08–E10):** comandos executados, QA real, SHA/config coerentes e review independente; sem isso o plano não atinge 100%.
- Uma etapa de código só pode passar à seguinte com checklist aceito e evidência mínima; `ACCEPT_WITH_RESIDUAL` exige owner, risco, prazo/gate de resolução e revalidação posterior. Residual bloqueante = não concluir.
- Se discovery mostrar um mecanismo já existente que muda a direção, parar, marcar drift e retornar à coordenação.

## 7. Registro de execução — editar a cada interação

Cada execução deve adicionar um registro **após** as seções fixas com este modelo (não preencher PASS antecipado):

```text
STAGE: E0X
TASK_ID:
BASE_HEAD:
FINAL_HEAD:
PUSH_VERIFIED:
DEPLOYED_SHA: (quando aplicável, ou NOT_DEPLOYED)
OWNER / CP-RQ / PHASE: (citados da autoridade, ou TO_INVENTORY)
EXISTING_EQUIVALENT:
REUSE_DECISION:
FILES_CHANGED:
TEST_COMMANDS + RESULTS:
BROWSER_QA + SCREENSHOTS:
REGRESSION / SAFETY EVIDENCE:
GAPS / RESIDUALS:
REVIEW_VERDICT: ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE
CHECKLIST_CHANGED: YES | NO
LEDGER_UPDATED: YES | NO | NOT_APPLICABLE
NEXT: E0Y | BLOCKED
```

Para concluir uma etapa: **(1)** append do registro factual nesta seção, **(2)** atualizar linha no quadro mestre para `ACCEPTED` e `[x]`, **(3)** atualizar contador aceito, **(4)** referenciar commit e evidências, **(5)** sincronizar ledger canônico se a tarefa o exigir. Registrar `PENDING`/falha sem marcar checkbox. Nunca apagar histórico de execução ou reclassificar silenciosamente.

### Registro inicial R0 — documentação do roadmap

```text
ROADMAP_STATUS = PLAN_REGISTERED
BASE_HEAD_BEFORE_ROADMAP = faecfd8a3e2070eec87f45ac39b3534c452db9e7
STAGES_TOTAL = 10
STAGES_ACCEPTED = 0
STAGES_PENDING = 10
CODE_CHANGED = NO
DEPLOYED_SHA_VERIFICATION = NOT_RUN
FULL_CANONICAL_REANCHOR = INCONCLUSIVE
TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
PHASE_PROGRESSION = NONE
NEXT = E01 (REQUIRES_NEW_USER_AUTHORIZATION)
```

## 8. Fonte e reconciliação de status

- Docs [103–113](./103-delia-navigation-sidebar-master-product-ux-specification.md) estabelecem UX/product targets por assunto; [114](./114-navigation-sidebar-103-113-independent-document-review.md) registra revisão e gates. Este **115 registra execução e contagem do rework** — não muda as decisões canônicas.
- **Chat = working context; GitHub = persistent truth; authorities = architecture/product truth; ledger = execution state.** Quando divergir, autoridades+ledger+HEAD prevalecem.
- O contador neste roadmap é **do rework visual**, não da fase C3/C4 ou da DÉLIA inteira. Atualizar ledger apenas mediante fatos e regras canônicas.
- **Próxima ação autorizável após esta publicação:** E01 isolada; não agrupar E01+E02 automaticamente.

## 9. Registro E01 — reancoragem dirigida, baseline e critérios (2026-10-17)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E01-BASELINE-01`
**BASE_HEAD observado:** `fe7df91879bca2957127833923f0ca80f2fb44ef` na GitHub `main`; **repositório/branch:** `roberiooliveiradev/delpi-central/main`.
**Execution mode:** análise documental e leitura read-only de componentes pelo conector GitHub; **nenhum código/CSS, deploy ou backend alterado nesta task**.

### 9.1 Evidência confirmada e restrições

1. **PROVEN no GitHub HEAD:** `DeliaConversationPage.tsx` ainda compõe o slot esquerdo com `collapsed ? <NavigationRail ...> : <NavigationCategoryPanel ...>`. Logo os dois não estão presentes simultaneamente ao lado do centro no desktop. O `ConversationWorkspace` permanece como prop `center={conversation}` do mesmo shell, mas permanência da instância e draft **não foram testados ao vivo**.
2. **PROVEN no GitHub HEAD:** `ConversationThreeRegionLayout.tsx` controla `leftExpanded`, `compact`, `rightOpen` de modo local; calcula `compact` com largura de `rootRef.current?.parentElement`, transição em `920px`; possui um único `NavigationActions action="toggle"` no header esquerdo e `leftToggle:null` no slot central.
3. **PROVEN no CSS:** `--delpi-ui-three-left:clamp(248px,19%,288px)`, rail de `64px` e `52px` no `@container delia-page (max-width:920px)`; painel esquerdo usa posicionamento `absolute`, largura `min(344px,88%)` em compact. Existe regra de backdrop em CSS, **mas o componente TSX consultado não o renderiza**: backdrop clicável/foco/semântica **não implementados nesse shell**.
4. **PROVEN no CSS:** `ContextPopover` `position:absolute; right:16px; top:66px; width:min(360px,calc(100% - 32px))`, compact `top:60px; right:8px; width:min(360px,calc(100% - 16px));max-height:70%`. É superfície flutuante, não terceira coluna; faltam provas de dimensões/scroll/foco em mobile.
5. **PROVEN no TSX:** Contexto tem Escape e pointerdown outside, botão de fechar e return-focus ao trigger; não há coordenação explícita com `leftExpanded` (podem coexistir). Esse fato **não comprova** que backdrop/drawer sejam acessíveis.
6. **EVIDÊNCIA EXTERNA fornecida pelo usuário:** capturas desktop/mobile no Portal com rail visível apenas no mobile recolhido, drawer amplo e popover grande; log de `git pull e7159c867→faecfd8a3`, `npm run build` do plugin-ui, `npx vite build` da DÉLIA e containers recriados. **Build/deploy PROVEN somente para essa execução relatada**, não para a task E01 nem para cada interação/viewport.
7. `git status` local, deployed asset SHA, estado real do runtime em navegador autenticado, Dock, zoom 200% e evidências por viewport: **TO_INVENTORY / TEST_NOT_RUN**. Os arquivos de projeto em outro container/host não foram inspecionados por esta leitura GitHub. A pesquisa pelo nome presumido `16-delia-roadmap.md` retornou 404; consultas search de `16`, `50` e ledger retornaram 0 resultados; **isso não prova inexistência**. Não foi possível concluir reancoragem canônica integral .cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura → product spec → ledger.

### 9.2 Decisão de reuse e boundaries para E02 (candidata, ainda não autorizada pelo gate)

```text
RESPONSIBILITY = COMPOSE_EXISTING_LEFT_RAIL_AND_CATEGORY_PANEL
UI_OWNER = plugin-ui
STATE_CONSUMER = plugins/delia
PORTAL_HOST = EXISTING
CORE_APP_ROUTE_RBAC_OWNER = EXISTING
DOMAIN_FINAL_AUTHORITY = UNCHANGED
EXISTING_EQUIVALENT_VISUAL = YES (source inspected)
REUSE_DECISION_VISUAL = EXTEND
NEW_SHELL_OR_REGISTRY = NOT_ALLOWED
PROJECT_AGENT_PLUGIN_CATALOGS = TO_INVENTORY (not in scope of visual E02)
```

Os componentes inspecionados confirmam o reuso em `plugin-ui`; o slot left e o CSS serão estendidos somente após E01 aceita com reanchor canônico. Nenhuma nova autorização é inferida de label visual, callback, JWT ou MCP.

### 9.3 Matriz de aceite congelada como hipóteses testáveis

| ID | Cenário verificável | Critério de saída |
|---|---|---|
| AC-D01 | Desktop host/container 1440/1280px | rail e painel adjacentes, um único controle de recolher, centro útil, card Contexto não vira coluna |
| AC-D02 | Resize desktop ~1024/768px | fallback inline→overlay quando `containerWidth - railWidth - panelWidth < minCenterWidth`; sem clipping ou composer estreito |
| AC-C01 | Trocar entre Conversas/Projetos/Agentes/Plugins | mudar conteúdo de painel mantendo rail disponível, sem remount de centro/draft, nenhum catálogo fictício ou ACT |
| AC-M01 | Mobile 420/375/320px + Dock | launcher/rail de acordo com espaço útil, drawer limitado pelo host, backdrop clicável, Escape e return-focus; nenhum elemento invisível acessível por Tab |
| AC-M02 | Contexto 420/375/320px | popover ou sheet visível e rolável, compositor acessível quando fecha, altura/largura sem ultrapassar container |
| AC-O01 | Drawer e Contexto em mobile | no máximo uma superfície sobreposta; abrir uma fecha a outra sem cancelar confirmação governada |
| AC-A01 | Teclado, a11y, zoom 200%, light/dark | labels/ARIA, foco previsível, contraste, reduced motion, sem rolagem horizontal indesejada |
| AC-R01 | Conversa ativa com draft/streaming/confirm | seleção, resize e overlays preservam estado central; nenhum reset de turns, nova sessão, send ou ACT |
| AC-B01 | Testes e integração no SHA/config final | Vitest, TypeScript, plugin-ui federation/export gate, DÉLIA build, Portal/Dock QA executados; resultados e screenshots documentados |

**Larguras em pixels são alvos de QA, não breakpoints congelados.** Confirmar largura do **container do Portal**, não apenas emulação de viewport. Prioridade: centro/composer → rail viável → painel inline ou overlay → launcher compacto. E02 não deve alterar este contrato sem registrar drift.

### 9.4 Checklist E01 — execução dirigida e bloqueios

- [x] Consultar HEAD GitHub main e documento 115.
- [x] Ler consumer DÉLIA, shell TSX/CSS, rail e panel existentes.
- [x] Confrontar os sintomas visuais recebidos e o log de deploy com a composição efetiva.
- [x] Definir critérios AC-D01…AC-B01 verificáveis, reuse e owners frontend.
- [ ] Reancorar **integralmente** HEAD/git status + Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura/product → temática → ledger; identificar CP/RQ/NEXT e conflitos.
- [ ] Executar e registrar baseline instrumental em Portal/Dock autenticados: screenshots por viewport + resize, teclado, light/dark/zoom; deployed SHA/asset config.
- [ ] Revisão da evidência E01 e aceite independente conforme regras do roadmap.

**Resultado E01 nesta execução: `INCONCLUSIVE` (baseline documental PARCIAL); checklist mestre E01 permanece `[ ]` e contador `0/10 ACCEPTED`.** Não escrever `PASS` ou avançar para E02 automaticamente. As lacunas acima são concretas e delimitadas, não autorização para inventário amplo. Uma continuação E01 em workspace Git + Portal browser pode fechar o gate; se revelar conflito, retornar à coordenação com `EXECUTION_DRIFT`.

```text
STAGE = E01
TASK_ID = DELIA-UX-NAV-REWORK-E01-BASELINE-01
BASE_HEAD = fe7df91879bca2957127833923f0ca80f2fb44ef
FILES_CHANGED = docs/12-roadmap-e-evolucao/delia/115-navigation-ux-rework-execution-roadmap.md
CODE_CHANGED = NO
REUSE_DECISION = EXTEND_VISUAL (pending full canonical reanchor)
CANONICAL_FULL_REANCHOR = INCONCLUSIVE
GIT_STATUS_WORKSPACE = NOT_VERIFIED
BROWSER_QA = TEST_NOT_RUN
DEPLOYED_SHA = TO_INVENTORY
STAGE_VERDICT = INCONCLUSIVE
CHECKLIST_CHANGED = NO
STAGES_ACCEPTED = 0
NEXT = E01_CANONICAL_AND_LIVE_BASELINE_RESIDUALS (E02 BLOCKED)
```

## 10. E01 continuação R1 — reancoragem canônica individual completada por fontes reais (2026-10-17)

**Solicitação do Product Master:** executar individualmente todas as verificações E01 possíveis neste chat, não parar no relatório anterior. Esta seção **corrige/supersede** a afirmação em §9.1 de que as autoridades 16/50/ledger não teriam caminhos descobertos. O índice oficial `docs/12-roadmap-e-evolucao/delia/README.md` publicou os caminhos exatos; buscas vazias anteriores eram um problema de discovery, **não ausência de documentos**.

### 10.1 Reancoragem por ordem: fontes efetivamente lidas do GitHub main

| Ordem | Fonte conferida | Resultado material |
|---|---|---|
| HEAD | `main` no início E01 `fe7df91879bca2957127833923f0ca80f2fb44ef`; `AGENTS.md` | Main direta/fast-forward; working tree do servidor ainda NÃO acessível por conector |
| Project Instructions/.cursor | `AGENTS.md`, `.cursor/rules/development-standards-index.mdc`, `delia-execution-protocol.mdc`, `evidence-driven-execution.mdc`, `centralized-rules-first.mdc`, `clean-code-architecture-guardrails.mdc`, `english-code-identifiers.mdc` | Exigem responsabilidade, evidence-first, owner, reuse, tests; não alterar fase; plano visual é bounded |
| 16 | `16-execution-master-plan.md` | Plano mestre vigente indica C3 `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`, `C3_EXECUTED=NO`, `RETURN_TO_ARCHITECTURE_COORDINATION`; nenhum C4/C5 liberado |
| 50 | `50-standalone-copilot-application-architecture.md` | Boundary standalone DÉLIA; evitar runtime Minha DELPI Chat |
| 17 | `17-component-and-contract-map.md` | Contratos/owners devem continuar nas fronteiras legítimas |
| 49 | `49-architecture-and-design-patterns-standard.md` | Reuse/Clean Architecture; mudanças UX não criam runtime ou authority |
| 51 | `51-platform-integration-baseline.md` | Baseline factual não implica integração de catálogos |
| 52 | `52-standalone-repository-and-bootstrap-plan.md` | Frontend DÉLIA próprio, no Portal, respeitando o plugin-ui |
| 21 | `21-data-and-state-model.md` | Nenhuma persistência sombra/histórico inventado |
| 20 | `20-testing-and-acceptance-matrix.md` | Evidência de SHA/config + testes e outcome; não confundir build com UX QA |
| 25 | `25-requirements-traceability.md` | CP-001 UX Portal/Companion Dock; CP-005 navegação/histórico (não liberado como sessão fake); CP-068 sem business action por DOM; CP-138 estado frontend; CP-181 acessibilidade/frontline; não promover CP por task visual |
| Temáticas | `103`, `113`, `115`; `22-cursor-execution-protocol.md` | Roadmap de navegação é bounded e **não** redefine NEXT global |
| Ledger | `evidence/execution-ledger.md` | `C3_AUTHORIZED/STARTED=YES`, `C3_EXECUTED=NO`, `C4/C5_LOCKED` phase-level; ledger volumoso contém registros históricos/superseded — não inferir fase nova de §115 |

**Ressalva:** os arquivos canônicos foram fetchados e seus cabeçalhos/trechos aplicáveis analisados. Esta execução não prova audit linha a linha dos documentos enormes nem estado de arquivos não listados no working tree. **Documentary authority paths identified = PROVEN; complete environment reanchor including git status = INCONCLUSIVE.** Não interpretar uma referência a CP como aceite de seu requisito.

### 10.2 Inventário técnico concluído para a mudança visual

`RESPONSIBILITY=UX_SHELL_AND_RESPONSIVENESS` → `OWNER=plugin-ui` → `CONSUMER=plugins/delia/DeliaConversationPage` → `CONTRACT=render-only props + callbacks` → `IMPLEMENTATION=ConversationThreeRegionLayout / NavigationRail / NavigationCategoryPanel / ConversationNavigation / ContextPopover` → `TEST=component/integration/browser` → `OUTCOME=not yet independently proven`.

- `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` para shell, rail, panel, sidebar e contexto; **não criar outro shell, controller ou domínio**.
- `NavigationRail` e categoria são reais em código; o consumer usa escolha `collapsed ? rail : panel`, prova de que composição lado-a-lado não está entregue.
- `ConversationThreeRegionLayout` tem `compact` a 920px por container pai, mas CSS do painel usa `width:min(344px,88%)`, sem JSX de backdrop. Testar overflow, foco, peso mobile e stacking antes de ajustar.
- O contexto é popover absoluto (width máximo 360px), com Escape/click-outside, mas sem mutual exclusion com a sidebar; validar overlay single-surface.
- A evidência screenshot+deploy trazida pelo usuário demonstra o problema em sessão própria, mas não substitui instrumentação e screenshot matricial de todos os breakpoints.
- **Não foi feito** import de runtime Minha DELPI Chat, nem design de API, catálogo, provider, ledger de fase ou autorização; dados não legitimados continuam indisponíveis.

### 10.3 Baseline observacional organizado (capturas da sessão do Product Master)

| ID | Captura recebida | Constatação observável | Veredicto baseline |
|---|---|---|---|
| B-DESKTOP | 2 capturas desktop, Contexto fechado/aberto | somente sidebar Conversas expandida, rail não simultâneo; Contexto flutuante | DEFECT_REPRODUCED_VISUALLY |
| B-MOBILE-RAIL | screenshot mobile ~375×667 | rail de quatro ícones visível e centro preservado | OBSERVED_ONLY |
| B-MOBILE-CONTEXT | screenshot mobile Contexto aberto | popover ocupa largura grande e se sobrepõe à conversa | DEFECT_REPRODUCED_VISUALLY |
| B-MOBILE-SIDEBAR | screenshot mobile menu expandido | painel ocupa quase toda a largura; centro aparece cortado/atrás; sem backdrop efetivo observado | DEFECT_REPRODUCED_VISUALLY |
| B-DEPLOY | transcrição do `git pull` e do build `up-prod-sequential.sh --build 'delia' plugin-ui` | pull até `faecfd8a3`, builds Docker plugin-ui e delia bem-sucedidos, containers recriados | BUILD_REPORTED_PASS_FOR_THAT_SHA_NOT_BROWSER_QA |

**Não se deve afirmar:** testes automatizados no SHA atual, deployed asset hash, ausência de bug em 320/420/768/1024, Chrome+Firefox, Dock, zoom 200%, foco e leitor de tela. Essas verificações permanecem `TEST_NOT_RUN`.

### 10.4 O que foi efetivamente executado neste chat

- [x] Índice oficial e caminhos reais das authorities identificados
- [x] AGENTS + regras `.cursor` relevantes recuperadas
- [x] Autoridades 16→50→17→49→51→52→21→20→25 e ledger recuperados e confrontados por responsabilidades
- [x] Baseline observacional das quatro situações visualmente diferentes organizado com screenshots já enviados
- [x] Owner/reuse/contrato/componentes e critérios AC-D01…AC-B01 mapeados
- [ ] `git status` **da máquina srv-api**: indisponível neste chat; GitHub HEAD não expõe working tree, e container local não contém clone nem DNS para clonar repositório
- [ ] Browser autenticado de produção **com QA instrumental e captura por breakpoint**: nenhuma ferramenta de browser interativo autenticado foi disponibilizada; screenshots do usuário são evidência pontual e não execução feita pelo assistente
- [ ] SHA do asset realmente servido e confirmação de qual commit cada container está executando: log confirma build/restart relatados, sem manifesto/asset hash verificado independentemente
- [ ] Revisão independente formal e reexecução de QA na configuração final

**Decisão de gate:** E01 agora possui baseline de fontes canônicas por caminho exato e inventário dirigido. Contudo, o roadmap 115 exige E01 **com baseline instrumental autenticado**. Portanto `E01=INCONCLUSIVE_WITH_PROVEN_DOCUMENTARY_BASELINE`; **não marcar [x] E01**, `STAGES_ACCEPTED=0/10`, `E02=BLOCKED_BY_E01_QA_GATES`. Resíduo técnico delimitado a acesso a working tree/deployed SHA/browser autenticado; não é justificativa para inventários novos.

```text
TASK_ID=DELIA-UX-NAV-REWORK-E01-BASELINE-01-R1
BASE_HEAD=fe7df91879bca2957127833923f0ca80f2fb44ef
CANONICAL_FILES_RETRIEVED=YES
DOCUMENTARY_AUTHORITY_PATHS=PROVEN
GIT_STATUS_SRV_API=TEST_NOT_RUN
AUTHORIZED_BROWSER_MATRIX=TEST_NOT_RUN
DEPLOYED_SHA=TO_VERIFY
EXISTING_EQUIVALENT_VISUAL=YES
REUSE_DECISION_VISUAL=EXTEND
CODE_CHANGED=NO
REVIEW_VERDICT=INCONCLUSIVE
E01_ACCEPTED=NO
STAGES_ACCEPTED=0
NEXT=E01_ENVIRONMENT_AND_BROWSER_EVIDENCE
```

## 11. E01-R2 — Fechamento de ambiente, SHA e baseline instrumental (2026-10-17)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E01-BASELINE-ENVIRONMENT-VALIDATION-R2`
**Evidence file:** [evidence/navigation-ux-rework-e01/e01-r2-environment-and-component-baseline.md](./evidence/navigation-ux-rework-e01/e01-r2-environment-and-component-baseline.md)
**MODE:** REANCHOR + ENVIRONMENT + CODE BASELINE + UNIT/BUILD — **zero** alteração React/CSS; **zero** deploy; **zero** E02.

### 11.1 Residuais R1 fechados nesta execução

| Residual R1 | Resultado R2 |
|---|---|
| `git status` workspace / srv-api | **PROVEN** — clean; `LOCAL=ORIGIN=REMOTE=8a194d4a8c3d5c1e1cb84ac0983b106238547d80` |
| Reancoragem canônica em workspace real | **PROVEN** — AGENTS/.cursor + 16→25 + 103/113/115 + ledger; `C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`; plano 115 não altera fase |
| Deployed / served assets | **PROVEN_PARTIAL** — containers healthy; HTTP 200; image digests + `remoteEntry` sha256 capturados; **sem** label git SHA na imagem (não inventado) |
| Baseline código rail/panel/backdrop/Escape/contexto | **PROVEN** — exclusive XOR left; backdrop CSS sem JSX; Escape só contexto; sem exclusividade overlays |
| Testes/builds/federation | **PASS** — plugin-ui nav 16 PASS; DeliaConversationPage 5 PASS; builds + host-exports + federation PASS; typecheck pré-existente kit |
| Browser autenticado Portal/Dock matriz | **TEST_NOT_RUN** — residual explícito → **E09** |

### 11.2 AC baseline (defeitos atuais = evidência válida de E01)

| ID | Baseline | Fix stage |
|---|---|---|
| AC-D01 | FAIL_CURRENT — rail XOR panel | E02 |
| AC-D02 | CODE_PARTIAL / live TEST_NOT_RUN | E04 / E09 |
| AC-C01 | FAIL_CURRENT — select chama `onExpand()` | E03 |
| AC-M01 | FAIL_CURRENT — sem backdrop JSX; Escape ignora left | E04 |
| AC-M02 | CODE_PROVEN / live TEST_NOT_RUN | E05 / E09 |
| AC-O01 | FAIL_CURRENT — overlays coexistentes | E06 |
| AC-A01 | UNIT_PARTIAL / live TEST_NOT_RUN | E06–E09 |
| AC-R01 | PASS_UNIT | E08 regressão |
| AC-B01 | PASS_PARTIAL (unit/build); browser TEST_NOT_RUN | E08 / E09 |

### 11.3 Reuse (confirmado)

```text
EXISTING_EQUIVALENT = YES
REUSE_DECISION = EXTEND
NEW_SHELL = NOT_ALLOWED
```

### 11.4 Parecer

```text
STAGE = E01
TASK_ID = DELIA-UX-NAV-REWORK-E01-BASELINE-ENVIRONMENT-VALIDATION-R2
BASE_HEAD = 8a194d4a8c3d5c1e1cb84ac0983b106238547d80
CODE_CHANGED = NO
CANONICAL_REANCHOR = PROVEN
GIT_STATUS = CLEAN_SYNCED
DEPLOYED_CORRELATION = HEAD_MATCHES_REMOTE + IMAGE_DIGESTS + REMOTEENTRY_SHA256 (no git label in image)
AUTHORIZED_BROWSER_MATRIX = TEST_NOT_RUN
REVIEW_VERDICT = ACCEPT_WITH_RESIDUAL
RESIDUAL_OWNER = E09 (Portal/Dock authenticated viewport matrix, light/dark, zoom200, reduced-motion)
INDEPENDENT_REVIEW = PENDING
CHECKLIST_CHANGED = YES (E01 [x]; 1/10)
E02_IMPLEMENTATION = NOT_STARTED (requires separate bounded task)
PHASE_PROGRESSION = NONE
NEXT = E02_DESKTOP_COMPOSITION_BOUNDED_TASK (after coordination/independent review as required)
```

**Não implementar E02 neste commit.** Coordenação pode exigir review independente antes da task E02; o residual de browser **não** bloqueia o desenho de E02, mas **bloqueia E10**.

## 12. E02 — Implementação bounded: rail persistente + painel desktop (2026-10-17)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E02-DESKTOP-COMPOSITION-01`  
**BASE_HEAD:** `1150735788b7b4c3e18b0c5f2e345647e4bb145c` (GitHub `main` consultada).  
**MODE:** implementação mínima de apresentação + regressões declaradas, sem E03/E04/E05/E06, nenhum backend/ACT e sem deploy. **Código publicado candidato, aceite PENDING.**

### 12.1 Gate de reuso/ownership

```text
RESPONSIBILITY = REUSE_AND_COMPOSE_LEFT_NAVIGATION
OWNER = plugins/plugin-ui (shell)
CONSUMER = plugins/delia (category state)
AUTHORITIES = 16/50/17/49/51/52/21/20/25 + 103/113/115 + ledger
EXISTING_EQUIVALENT = YES
REUSE_DECISION = EXTEND
NEW_SHELL = NO
SESSION_CATALOG_AUTHORITY_CHANGED = NO
PHASE_PROGRESSION = NONE
```

Reanchor canônico da E01-R2 §11 foi aceito com residual e não se presume NEXT de fase a partir deste documento. Fonte revisada por GitHub: código do `ConversationThreeRegionLayout`, CSS, `DeliaConversationPage`, suites de testes e roadmap. **Workspace `git status` e execução de testes nesta task via conector GitHub = não disponíveis;** não declarar PASS sem comando executado. E01 real instrumentado está no relatório `evidence/navigation-ux-rework-e01`.

### 12.2 Diferença de implementação

- `ConversationThreeRegionLayout` recebeu prop **opcional** `rail?: ReactNode | (({ onExpand }) => ReactNode)`. Ela mantém categoria persistentemente montada e cria o rail como irmão do `nav` do painel e do workspace central. Consumidores legados **sem `rail`** preservam o comportamento existente.
- `ConversationThreeRegionLayout.css` adiciona classes `--with-rail`, `__category-rail` e `__rail-heading`: rail 64px desktop e 52px no container compact (alvos da spec 113), painel atual de 248–288px desktop sem nova estrutura de domínio. Painel recolhido é desmontado do DOM visual, rail continua.
- **Toggle único por estado:** quando painel aberto, `NavigationActions action="toggle"` fica no header do painel; quando recolhido, aparece no rail. Composições antigas sem rail mantêm toggle prévio.
- `DeliaConversationPage` passou de `collapsed ? NavigationRail : NavigationCategoryPanel` para `rail={NavigationRail}` + `left={NavigationCategoryPanel}`, sem criar outro estado de categoria nem outro shell. `onSelectCategory` preserva intenção existente de expandir um painel recolhido; a evolução da interação direta entre categorias é a E03.
- `ConversationWorkspace` permanece em `center={conversation}`, sem depender do toggle; Projetos/Agentes/Plugins continuam como previews `contract_unavailable`, sem owner/Feed/ACT falsos.
- Nenhuma modificação em ContextPopover, backdrop mobile, autenticação, catálogos, buscas, sessão, Core ou Domain APIs.

### 12.3 Testes adicionados e evidência

- Teste no shell compartilhado para rail+painel concomitantes, rail persistente após recolher/expandir, um toggle acessível por estado e identidade do input central.
- Teste na DÉLIA para rail e painel simultâneos, regressão de estado central, painel recolhido com rail persistente, expansão e draft sem perda.
- Testes antigos de seleção de categoria preservados por callback `onExpand`, sem modificar a autoridade de estado ou criar navegação falsa.

**Nesta execução via GitHub API, nenhum runner local ou remoto autenticado foi disponibilizado.** Assim, `VITEST=TEST_NOT_RUN`, `TYPECHECK=TEST_NOT_RUN`, `BUILD=TEST_NOT_RUN`, `FEDERATION_GATE=TEST_NOT_RUN`, `PORTAL_BROWSER_QA=TEST_NOT_RUN`. Os testes E01-R2 se referiam ao SHA anterior e **não** cobrem o novo diff E02.

### 12.4 Acceptance gate

| Critério | Estado nesta execução |
|---|---|
| Rail e painel simultâneos no JSX | PROVEN_CODE |
| Rail persiste recolhido e centro não depende do toggle | PROVEN_CODE + TEST_WRITTEN |
| Um toggle por estado, acessível | PROVEN_CODE + TEST_WRITTEN |
| Responsive width real desktop/Dock 1440/1280/1024 | TEST_NOT_RUN |
| Plugin-ui Vitest/TypeScript/build/export gate | TEST_NOT_RUN |
| DÉLIA Vitest/typecheck/build/federation | TEST_NOT_RUN |
| Independent runtime acceptance | PENDING |

**E02_STATUS = IMPLEMENTATION_CANDIDATE / INCONCLUSIVE**, portanto a checklist mestre **continua `[ ] E02` e o progresso permanece `1/10 ACCEPTED`**. Após execução dos testes e revisão independente em SHA/config do candidato, atualizar E02 com `ACCEPT` ou `ACCEPT_WITH_RESIDUAL` e só então marcar `[x]`. E03 não é automaticamente autorizada. Residuais E04–E09 preservados.

```text
STAGE = E02
TASK_ID = DELIA-UX-NAV-REWORK-E02-DESKTOP-COMPOSITION-01
BASE_HEAD = 1150735788b7b4c3e18b0c5f2e345647e4bb145c
REUSE_DECISION = EXTEND
CODE_CHANGED = YES
TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
REVIEW_VERDICT = INCONCLUSIVE
E02_ACCEPTED = NO
CHECKLIST_CHANGED = NO
ROADMAP_PROGRESS = 1/10 ACCEPTED
NEXT = E02_INDEPENDENT_TEST_AND_VISUAL_REVIEW
```
