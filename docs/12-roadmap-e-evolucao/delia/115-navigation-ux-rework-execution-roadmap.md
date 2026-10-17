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
| E02 | Composição Rail + Panel desktop | E01 | **IMPLEMENTED / VISUAL_OBSERVED_PASS / ACCEPTANCE_PENDING** | rail e painel simultâneos, centro sem remount, testes + screenshot |
| E03 | Troca direta das quatro categorias | E02 | **IMPLEMENTED / VISUAL_OBSERVED_PASS / ACCEPTANCE_PENDING** | troca no rail sem recolher, estados honestos, testes de navegação |
| E04 | Sidebar responsiva + drawer mobile | E03 | **IMPLEMENTED_R1 / VISUAL_OBSERVED_PASS / ACCEPTANCE_PENDING** | largura baseada no host; overlay, backdrop, Escape e foco sem corte |
| E05 | ContextPopover responsivo | E04 | **IMPLEMENTED / VISUAL_OBSERVED_PASS / ACCEPTANCE_PENDING** | limites, scroll, posicionamento, sem cobrir composer indevidamente |
| E06 | Convivência de painéis + acessibilidade | E04+E05 | **IMPLEMENTED / VISUAL_PARTIAL / INTERACTION_QA_PENDING** | exclusividade mobile, teclado/foco/ARIA, não cancelar fluxo governado |
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

## 13. E03 — Troca direta de categorias (2026-10-17)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E03-CATEGORY-SWITCH-01`  
**BASE_HEAD:** `0d4a647cf18c4fecaeae6313d820df4f549b5256` (GitHub `main`).  
**ESCOPO:** componente frontend consumer `DeliaConversationPage` e sua suíte de integração. Nenhum novo shell, backend, API, catálogo, permissão ou ACT.

### 13.1 Dependência da E02 e decisão de escopo

O registro §12 declara `E02=IMPLEMENTATION_CANDIDATE / INCONCLUSIVE` e o checklist mestre ainda registra `[ ] E02` e `1/10 ACCEPTED`. A captura desktop recebida do Product Master **prova visualmente** a presença de Rail + Panel lado-a-lado no Portal, porém **não** executa a suíte E02 no SHA implantado. O Product Master autorizou explicitamente a E03 nesta interação. Portanto esta mudança é registrada **como candidato E03**, sem promover/aceitar E02 e sem reivindicar liberação automática de etapas subsequentes. A aceitação E03 fica condicionada ao fechamento da dependência e à validação no seu SHA/config.

### 13.2 Reuse Gate

```text
RESPONSIBILITY = CHANGE_SELECTED_VISUAL_CATEGORY_ONLY
OWNER = plugins/delia (category state)
PRESENTATION_OWNER = plugins/plugin-ui (NavigationRail / NavigationCategoryPanel)
EXISTING_EQUIVALENT = YES
REUSE_DECISION = REUSE (existing props and onSelectCategory callback)
NEW_COMPONENT_OR_REGISTRY = NO
OWNER_AUTHZ_OR_DOMAIN_CHANGE = NO
PHASE_PROGRESSION = NONE
```

**Mudança no consumer:** `DeliaConversationPage` remove o uso do `rail` render-prop `onExpand` e passa `rail={<NavigationRail onSelectCategory={setCategory} .../>}`. Com painel expandido, clicar Conversas/Projetos/Agentes/Plugins modifica apenas `category`, seleciona `aria-current="page"` via `NavigationRail` e atualiza `NavigationCategoryPanel` existente no mesmo local, sem fechar/reabrir o painel. Com painel recolhido, a seleção de categoria persiste e o toggle existente pode expandir o painel com a categoria escolhida. Nenhuma categoria torna catálogo/provider autorizado: os previews permanecem `contract_unavailable/catalog_unavailable`.

**Sem alteração** de `ConversationThreeRegionLayout`, CSS, `NavigationRail`, `ConversationWorkspace`, ContextPopover, Portal/Core/Domain, sessão, history backend ou MCP. `REUSE_DECISION=REUSE` e menor diff.

### 13.3 Tests and acceptance evidence

- `plugins/delia/src/ui/DeliaConversationPage.test.tsx` foi atualizado para expectativas de seleção sem expansão automática; acrescentados testes para troca direta nas quatro categorias com painel expandido, rail estável, toggle único, seleção `aria-current`, conteúdo unavailable veraz, draft DOM/input intacto; e seleção do rail recolhido que só abre o painel após toggle explícito.
- Testes **escritos, não executados** nesta sessão. Workspace do clone Git, runner local e navegador autenticado de produção não estavam disponíveis (conector GitHub só para arquivos). Portanto `VITEST=TEST_NOT_RUN`, `TYPECHECK=TEST_NOT_RUN`, `BUILD=TEST_NOT_RUN`, `FEDERATION=TEST_NOT_RUN`, `PORTAL_QA=TEST_NOT_RUN`, `INDEPENDENT_REVIEW=PENDING`.
- **Proven code:** um `setCategory` como única alteração em clique; `onExpand` não é mais invocado. **Pending runtime:** screenshot da troca entre categorias e preservação do rascunho/stream em browser; reexecução da suíte E02/E03 sobre o mesmo HEAD/config.

### 13.4 Veredicto e contagem

```text
STAGE = E03
TASK_ID = DELIA-UX-NAV-REWORK-E03-CATEGORY-SWITCH-01
BASE_HEAD = 0d4a647cf18c4fecaeae6313d820df4f549b5256
CODE_CHANGED = YES
EXISTING_EQUIVALENT = YES
REUSE_DECISION = REUSE
E02_ACCEPTED = NO (upstream acceptance outstanding)
TESTS = TEST_NOT_RUN
BROWSER_QA = TEST_NOT_RUN
REVIEW_VERDICT = INCONCLUSIVE
E03_ACCEPTED = NO
CHECKLIST_CHANGED = NO
ROADMAP_PROGRESS = 1/10 ACCEPTED
NEXT = E02_E03_TEST_AND_INDEPENDENT_REVIEW
```

Não marcar `[x] E03` antes de E02 aceita e testes/evidências da própria E03. E04 não inicia automaticamente.

## 14. E02/E03 — Consolidação de evidência visual apresentada pelo Product Master (2026-10-17)

**Evidência externa da sessão:** o Product Master enviou duas capturas reais de `https://minhadelpi.com.br/apps/delia` com desktop dark-mode: (a) rail de Conversas/Projetos/Agentes/Plugins persistente à esquerda e painel **Agentes** expandido, selecionado, com texto de indisponibilidade autorizada e `ConversationWorkspace` visível; (b) rail com **Projetos** selecionado e painel recolhido, liberando espaço horizontal ao centro. São **screenshots fornecidos pelo usuário**, não browser QA executado pelo assistente. Identificação de SHA exato dos assets dessas capturas = `TO_VERIFY`.

| Stage | Evidência | Resultado documental |
|---|---|---|
| E02 | rail e painel simultâneos na captura desktop + centro visível; painel recolhido conserva rail | `VISUAL_OBSERVED_PASS` no recorte capturado, não `ACCEPT` de teste/QA |
| E03 | seleção Agentes abre painel existente; seleção Projetos permanece destacada com painel fechado | `VISUAL_OBSERVED_PASS` no recorte capturado; não prova fluxo completo de quatro categorias, streaming nem draft |
| E02/E03 | unit/TypeScript/build/federation atualizados nos SHAs após código | `TEST_NOT_RUN` neste chat |
| E02/E03 | revisão independente de runtime/config e matriz responsive | `PENDING`; QA amplo pertence à E09 |

**Conclusão:** observação visual positiva, porém critérios de aceite do roadmap continuam condicionados à reexecução dos testes e revisão com SHA/config. **Checklist E02 e E03 continuam [ ] e progresso 1/10**, preservando rastreabilidade. A autorização explícita subsequente do Product Master para consolidar evidência e executar E04 é **bounded**, sem autoaceitar E02/E03. Residual extra notado ao reexaminar o HEAD: `ConversationThreeRegionLayout` continha `left && (!rail || !collapsed)` (invertia condição de painel quando rail presente); E04 faz correção mínima de regressão para `leftExpanded`. Nenhum diagnóstico de deploy é inferido da diferença código/captura sem provenance suficiente.

## 15. E04 — Implementação bounded de drawer mobile (2026-10-17)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E04-MOBILE-DRAWER-01`  
**BASE_HEAD:** `756bee731df106288c4b0e25281e10276fa2bd2d`; execução autorizada explicitamente pelo Product Master após screenshots desktop.  
**OWNER:** `plugins/plugin-ui`; consumer DÉLIA permanece sem diff na E04. `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` (shell e CSS atuais). **Nenhum novo componente/engine/provider/regra de RBAC.** E04 não modifica ContextPopover responsivo (E05) nem faz coordenação drawer↔contexto (E06).

**Diferença no shell:**
- corrigido o predicado anterior de renderização do painel quando `rail` está presente para `leftExpanded`; elimina drift entre estado e existência do painel e torna o drawer testável em estado compacto
- `drawerOpen` é derivado de `compact && leftExpanded && !!left`, com `compact` medido por `ResizeObserver` sobre container pai, não `window.innerWidth`
- quando drawer aberto, renderiza `button` de backdrop nomeado **Fechar navegação**; click fecha drawer; Escape fecha e devolve o foco ao botão de expansão no rail; o botão existente de recolher utiliza o mesmo close path
- CSS `--compact` adiciona posicionamento absoluto ao painel sobre o centro, começando **após o rail**, largura `min(288px, calc(100% - rail - 8px))`; z-index rail>drawer>backdrop, sem ocupar 100vw/100vh; centro permanece montado
- esta task não implementa launcher-only extremo nem foco modal completo/trap do drawer; esses requisitos permanecem associados a E06/QA E09. Se o drawer atrapalhar controles do Dock em QA, `REWORK` antes do aceite.

**Teste escrito:** `ConversationThreeRegionLayout.test.tsx` passou a incluir simulação de host compacto com `ResizeObserver` em 375px, estado inicialmente recolhido, abrir drawer/backdrop, fechar Escape com retorno de foco, fechar por backdrop, verificar input central intacto. Também permanece a suíte desktop de E02/E03 como regressão. **Teste escrito != PASS executado.**

**Evidência operacional nesta execução:** código CSS/TSX e teste publicados no GitHub. Não houve clone local de todo o monorepo nem comando Vitest/npm/build/autenticado Portal; portanto `VITEST=TEST_NOT_RUN`, `TYPECHECK=TEST_NOT_RUN`, `FEDERATION_BUILD=TEST_NOT_RUN`, `BROWSER_QA=TEST_NOT_RUN`, `INDEPENDENT_REVIEW=PENDING`. A E04 não é considerada concluída com base em compilação presumida ou no screenshot desktop anterior.

```text
E02_VISUAL_EVIDENCE = USER_SCREENSHOT_OBSERVED
E03_VISUAL_EVIDENCE = USER_SCREENSHOT_OBSERVED
E02_ACCEPTED = NO (test/review pending)
E03_ACCEPTED = NO (test/review pending)
E04_IMPLEMENTATION = CODE_COMMITTED_CANDIDATE
E04_ACCEPTED = NO
E04_TESTS = TEST_NOT_RUN
E04_LIVE_QA = TEST_NOT_RUN
ROADMAP_PROGRESS = 1/10 ACCEPTED
CHECKLIST_E02_E03_E04 = UNCHECKED
NEXT = E02_E03_E04_SAME_SHA_TEST_AND_INDEPENDENT_REVIEW
PHASE_PROGRESSION = NONE
```

## 16. E04-R1 — Hotfix bounded de isolamento visual e interativo do drawer (2026-10-17)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E04-MOBILE-DRAWER-OVERLAY-ISOLATION-R1`. **BASE_HEAD:** `5b2f764cc3f44b43a719ca0e862e35be9ee6fd68`. O Product Master enviou três screenshots de Chrome responsivo iPhone SE 375×667: rail recolhido satisfatório, drawer aberto com uma faixa da conversa/compositor exposta à direita, Contexto alto/largo no mobile. Estes screenshots são **evidência visual fornecida pelo usuário**: `E04_DRAWER_BACKGROUND=REWORK` e `E05_CONTEXT_SIZE=PENDING` — não são prova automatizada de teclado/estado.

**RESPONSIBILITY:** UI compact drawer / background isolation; **OWNER:** plugin-ui shell; **CONSUMER:** DÉLIA. `EXISTING_EQUIVALENT=YES` para `ConversationThreeRegionLayout`/CSS/NavigationActions; `REUSE_DECISION=EXTEND`; nenhum componente/registry/provider/route/authorization novo. Escopo não inclui ajustar ContextPopover E05 nem implementar exclusividade simultânea E06.

**Correção E04-R1:**
- Reutiliza o backdrop de botão existente e torna perceptível sua camada visual na área exposta do compositor: no shell `--compact --with-rail`, backdrop `rgba(0,0,0,.66)` + blur 2px, stacking isolado `center:0 < backdrop:40 < drawer:41 < rail:42`. Fica restrito ao container do Portal, com rail interativo por cima.
- O centro recebe `inert={drawerOpen}` e o popover Contexto também fica `inert` enquanto o drawer estiver aberto; o DOM central não é desmontado nem se perde o rascunho. Esse gate previne foco/tab/click por input legítimo no compositor atrás do drawer. O isolamento de context e central **não é permissão de negócio**.
- O botão de recolher existente no drawer compacto é apresentado por um botão visual local com ícone X e mesmo label `Recolher conversas`, vinculado ao mesmo `closeDrawer`; foco inicial no botão de fechamento após abrir; Escape/backdrop/fechar restauram foco ao toggle de rail já existente. O shell sem rail e o modo desktop mantêm o controle anterior.
- Teste `ConversationThreeRegionLayout.test.tsx` ampliado para checar `inert` enquanto aberto e sua remoção ao fechar, foco inicial no botão, rail disponível, fechamento Escape e backdrop e input com valor preservado.

**LIMITES E EVIDÊNCIA:** código/estilos/testes escritos e publicados em GitHub; `VITEST=TEST_NOT_RUN`, `TSC=TEST_NOT_RUN`, `BUILD=TEST_NOT_RUN`, `FEDERATION=TEST_NOT_RUN`, `MOBILE_BROWSER_QA=TEST_NOT_RUN` nesta execução (sem clone/runner/browser autenticado no conector). Revisão independente **PENDING**. Não marcar E04 como concluída ainda; roadmap permanece `1/10 ACCEPTED` até testes e review material em SHA/config final. A E05 continua pendente, tal como coordenação entre Contexto e drawer em E06.

```text
E04_R1_STATUS = CODE_COMMITTED_CANDIDATE
VISUAL_USER_EVIDENCE = DEFECT_REPRODUCED_IN_375PX_DRAWER
EXISTING_EQUIVALENT = YES
REUSE_DECISION = EXTEND
CODE_FILES = ConversationThreeRegionLayout.tsx, ConversationThreeRegionLayout.css
TEST_FILE = ConversationThreeRegionLayout.test.tsx
TESTS = TEST_NOT_RUN
DEPLOYED_SHA = TO_VERIFY
E04_ACCEPTED = NO
CHECKLIST = UNCHANGED
ROADMAP_PROGRESS = 1/10 ACCEPTED
NEXT = E04_R1_VITEST_BUILD_FEDERATION_AND_MOBILE_QA
```

## 17. E05 — ContextPopover responsivo, rail-safe (2026-10-17)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E05-CONTEXT-RESPONSIVE-01`. **BASE_HEAD:** `8b86356763ef45301d6d04c0d28b253fbdd3de0b` em GitHub `main`. **Autorização:** Product Master solicitou avanço e implementação da E05 após fornecer três capturas mobile 375×667. O conteúdo Contexto aparecia encoberto pelo rail na faixa esquerda; screenshot = `VISUAL_DEFECT_OBSERVED` e **não** mede geometria programaticamente nem prova SHA de assets.

**Reuse Gate:** `RESPONSIBILITY=COMPACT_CONTEXT_POSITION_AND_SCROLL`, `OWNER=plugin-ui`, `CONSUMER=plugins/delia`, `EXISTING_EQUIVALENT=YES` (`ConversationThreeRegionLayout__context-popover` com animação, CSS e close button existentes), `REUSE_DECISION=EXTEND`, `NEW_COMPONENT=NO`, `NEW_COLUMN=NO`. Portal mantém host; Core/domain/identity/permission sem alterações. Respeita 103, 113, 115 e baseline da E01; não representa liberação de fase C3/C4.

**Alteração mínima:** `plugins/plugin-ui/src/components/conversation/ConversationThreeRegionLayout.css`. Dentro da `@container delia-page (max-width:920px)` apenas para `--with-rail`, ContextPopover usa `left:calc(var(--delpi-ui-three-rail) + 8px)`, `right:8px`, `width:auto` e `max-width:calc(100% - rail - 16px)`, com `box-sizing:border-box`. Resultado esperado: nenhum título/ícone começa atrás do rail, e largura fica dentro do próprio container do Portal inclusive a 320/375/420px; a regra desktop não muda. `max-height:min(70%,calc(100% - 72px))` e body `overflow-y:auto`, `overscroll-behavior:contain`, `overflow-x:hidden`, padding compacto: evitar corte do conteúdo vertical, sem interferir no composer após fechar. A regra considera o tamanho efetivo do container em CSS, não usa `100vw/100vh`. A query de altura de container foi removida, pois o container pode ser `inline-size` e não suportar tal eixo.

**Teste criado:** `ConversationThreeRegionLayout.test.tsx` cobre ambiente compacto simulado 375px, rail persistente, contexto aberto/fechado dentro do mesmo shell, sem terceira coluna, e input central preservado. **Limite:** JSDOM não prova coordenadas de CSS container queries; validar em navegador real durante E05 QA e E09. Nenhuma alteração no React para a E05, no Portal, na API ou na governança das categorias.

**Resultado factual nesta task:** alterações CSS/teste publicadas em GitHub. Não houve runner Git/Node nem navegador autenticado acessíveis pelo conector: `VITEST=TEST_NOT_RUN`, `TSC=TEST_NOT_RUN`, `BUILD=TEST_NOT_RUN`, `FEDERATION=TEST_NOT_RUN`, `PORTAL_QA=TEST_NOT_RUN`, `INDEPENDENT_REVIEW=PENDING`. Não promover screenshots anteriores do defeito a validação do fix. A exclusividade de Contexto e drawer e os controles de foco pertencem à E06.

```text
STAGE = E05
TASK_ID = DELIA-UX-NAV-REWORK-E05-CONTEXT-RESPONSIVE-01
BASE_HEAD = 8b86356763ef45301d6d04c0d28b253fbdd3de0b
EXISTING_EQUIVALENT = YES
REUSE_DECISION = EXTEND
CODE_CHANGED = CSS + UNIT_TEST
BROWSER_QA = TEST_NOT_RUN
AUTOMATED_TESTS = TEST_NOT_RUN
REVIEW_VERDICT = INCONCLUSIVE
E05_IMPLEMENTATION = CODE_COMMITTED_CANDIDATE
E05_ACCEPTED = NO
ROADMAP_PROGRESS = 1/10 ACCEPTED
CHECKLIST_CHANGED = NO
NEXT = E05_TESTS_AND_REAL_CONTAINER_QA; E06_NOT_AUTO_AUTHORIZED
```

## 18. E06 — Coordenação de overlays e acessibilidade (2026-10-17)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E06-OVERLAYS-A11Y-01`. **BASE_HEAD (GitHub main):** `767465bf2d9fcf55d5ca149f8b26e840e9dee24e`. **Autorização:** solicitação explícita do Product Master para implementar E06 após screenshot mostrando o ContextPopover ajustado em 375px. A captura é evidência visual pontual da E05, **não prova de QA E06**.

**Owner/consumers/reuse:** `RESPONSIBILITY=COMPACT_OVERLAY_COORDINATION`; `OWNER=plugin-ui/ConversationThreeRegionLayout`; `CONSUMER=plugins/delia`; Portal host, Core/AuthZ, Domain authorities inalterados. `EXISTING_EQUIVALENT=YES` (estados `leftExpanded/rightOpen/compact`, backdrop, close e focus refs no shell); `REUSE_DECISION=EXTEND` — nenhum engine, provider, overlay manager ou componente paralelo.

**Implementado no shell:**
- `openDrawer` fecha o Contexto em modo compacto antes de expandir a navegação; `toggleContext` recolhe o drawer ao abrir o Contexto no compacto. `useEffect` de convergência fecha drawer caso ambos acabem abertos por resize/estado transitório. A regra não interfere na coexistência permitida no desktop.
- Ao abrir Contexto compacto, foco é direcionado ao botão existente **Fechar painel de contexto**; não houve alteração no contrato `IconButton` (que não aceita `ref`). Escape fecha a superfície ativa e retorna foco ao acionador de Contexto, respeitando `defaultPrevented`. Drawer continua com foco inicial no X e retorno ao botão de expansão do rail, Escape e backdrop como no E04-R1.
- Enquanto drawer aberto, centro e Contexto permanecem `inert`, como definido na E04-R1. A navegação Tab/Shift+Tab no drawer tenta permanecer entre elementos focáveis do rail e painel, sem mover foco para o compositor oculto. Os candidates são coletados sob o próprio shell, não no documento global; sem alteração na autorização de negócios.
- `ConversationWorkspace` é mantido montado; a seleção/expansão não cria sessão, não envia mensagem nem dispara ACT.

**Teste escrito:** `ConversationThreeRegionLayout.test.tsx` cobre em container simulado 375px: abrir Contexto, verificar foco no fechamento; abrir navegação, verificar fechamento de Contexto, drawer/backdrop e centro inert; Escape fecha drawer, input central mantém valor; reabrir Contexto e Escape restaura foco ao gatilho. Regressões anteriores E02-E05 preservadas.

**Evidência e limites:** diff publicado no GitHub. **Nesta sessão não houve execução de Vitest, TypeScript, build federado, nem browser QA autenticado:** `VITEST=TEST_NOT_RUN`, `TYPECHECK=TEST_NOT_RUN`, `PLUGIN_UI_BUILD=TEST_NOT_RUN`, `DELIA_BUILD=TEST_NOT_RUN`, `PORTAL_DOCK_QA=TEST_NOT_RUN`, `INDEPENDENT_REVIEW=PENDING`. O teste criado não demonstra foco real do navegador, zoom 200%, resize, leitor de tela ou teclado completo; estes permanecem gates de E06/E09. Não marcar `[x] E06` nem alterar o contador apenas pela publicação.

```text
E06_IMPLEMENTATION=CODE_COMMITTED_CANDIDATE
BASE_HEAD=767465bf2d9fcf55d5ca149f8b26e840e9dee24e
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
CODE_CHANGED=ConversationThreeRegionLayout.tsx
TEST_CHANGED=ConversationThreeRegionLayout.test.tsx
TESTS=TEST_NOT_RUN
BROWSER_QA=TEST_NOT_RUN
REVIEW_VERDICT=INCONCLUSIVE
E06_ACCEPTED=NO
ROADMAP_PROGRESS=1/10 ACCEPTED
CHECKLIST_CHANGED=NO
NEXT=E06_SAME_SHA_TEST_BUILD_AND_LIVE_KEYBOARD_QA
```

## 19. Consolidação incremental das evidências E02–E06 (2026-10-17)

**Objetivo:** atualizar o quadro mestre com a implementação publicada e as capturas visuais fornecidas pelo Product Master, sem confundir implementação, observação visual e aceite técnico. Esta entrega é exclusivamente documental; nenhum teste, build ou deploy foi executado nesta interação.

| Etapa | Evidência visual fornecida pelo usuário | Classificação | Pendência |
|---|---|---|---|
| E02 | Desktop: rail e painel coexistem; painel recolhido preserva rail e workspace visível | VISUAL_OBSERVED_PASS | testes atualizados, SHA servido e aceite |
| E03 | Desktop: Agentes selecionado com painel aberto; Projetos selecionado com painel fechado | VISUAL_OBSERVED_PASS | fluxo completo, teclado, estado/draft e aceite |
| E04 | Mobile 375×667: rail recolhido, drawer Conversas/Projetos, X e backdrop escurecido | VISUAL_OBSERVED_PASS | Escape, foco, clique no backdrop, 320/420px e Dock |
| E05 | Mobile 375×667: Contexto começa após o rail, header e ações legíveis, compositor visível | VISUAL_OBSERVED_PASS | rolagem, tamanhos adicionais, QA instrumental |
| E06 | Mobile 375×667: conversa sem overlay e drawer Projetos aberto visualmente correto | VISUAL_PARTIAL | exclusividade Contexto/drawer, Tab/Shift+Tab, Escape, foco, inert e resize |

**Proveniência:** capturas do Portal minhadelpi.com.br/apps/delia em Chrome/DevTools fornecidas pelo Product Master nesta conversa, incluindo a largura simulada de 375px. Não existe vinculação verificada destas imagens ao SHA exato dos assets servidos. As capturas não comprovam comportamento não observado, testes automatizados ou QA de acessibilidade.

### Estado de implementação separado do aceite

- **E01:** ACCEPT_WITH_RESIDUAL, como anteriormente registrado.
- **E02:** IMPLEMENTED / VISUAL_OBSERVED_PASS / ACCEPTANCE_PENDING.
- **E03:** IMPLEMENTED / VISUAL_OBSERVED_PASS / ACCEPTANCE_PENDING.
- **E04:** IMPLEMENTED_R1 / VISUAL_OBSERVED_PASS / ACCEPTANCE_PENDING.
- **E05:** IMPLEMENTED / VISUAL_OBSERVED_PASS / ACCEPTANCE_PENDING.
- **E06:** IMPLEMENTED / VISUAL_PARTIAL / INTERACTION_QA_PENDING.
- **E07–E10:** PENDING.

**Aceite formal permanece 1/10.** Os checkboxes E02–E06 continuam desmarcados conforme o gate original do §4; evidência visual isolada e commit publicado não equivalem a testes/QA/review no SHA/config relevante. Este registro substitui somente o estado simplificado PENDING dessas linhas por uma representação fiel do progresso de implementação.

### Próximo passo verificável

Executar validação técnica acumulada E02–E06 no HEAD/ambiente correto: reanchor + Git status + Vitest plugin-ui/DÉLIA + TypeScript/dívida preexistente + builds/federation + QA de desktop, 320/375/420px, Dock, drawer e Contexto alternados, Escape, Tab/Shift+Tab, backdrop, foco, resize e preservação do composer. Registrar comandos, resultados, SHA/config e parecer por etapa. Somente após aceite independente atualizar as caixas e o contador. E07 segue como implementação temática separada, sem promoção automática de etapa ou fase canônica.

TASK_ID = DELIA-UX-NAV-REWORK-E02-E06-VISUAL-EVIDENCE-CONSOLIDATION-01
BASE_HEAD = af9cbf051ece988b71e4f775805870f5385c274b
CODE_CHANGED = NO
TESTS_THIS_TASK = TEST_NOT_RUN
BROWSER_QA_THIS_TASK = TEST_NOT_RUN
ROADMAP_PROGRESS = 1/10 ACCEPTED
PHASE_PROGRESSION = NONE
