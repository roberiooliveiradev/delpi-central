# My Requests — correção de composição Hero/Tabela e ordenação por cabeçalho

**TASK_ID:** `MYREQ-UX-V2-HERO-TOOLBAR-HEADER-SORT-PARITY-HML-01`  
**Origem:** revisão visual do Product Owner (15/11/2026), prints HML Minhas/Fila e referência Meus Chamados de TI  
**Estado:** `TARGET / APPROVED_FOR_IMPLEMENTATION_PLANNING` — documentação aprovada; **não** implementado nesta task de registro.  
**Branch:** `main` exclusivamente. **Ambiente alvo:** HML. **Produção:** `NOT_AUTHORIZED`.

## 1. Evidências visuais e diagnóstico

Screenshots fornecidas pelo PO:
- `/apps/my-requests/mine`: topbar com quatro abas acima do hero, hero próprio com título/contagem/Atualizar/Nova; **toolbar fora do hero** dentro de card escuro duplicado: Tabela|Cards, itens/página, busca, Colunas, Filtros, Data ↓ e chips status. Grade segue abaixo, com cabeçalhos sem interação de ordenação perceptível.
- `/apps/my-requests/work-queue`: mesmo problema; tabela possui Número/Tipo/Assunto/Solicitante/Status/Filial/Concluída por/Data, footer de paginação interno e grande espaço ocioso de container.
- `/apps/helpdesk`: referência aprovada: hero contém título+ações, busca dominante, botões Filtros/Ordenação/Colunas e chips + modos adjacentes; grade independente, compacta, com ordenação visível nos headers; paginação fora do scroll.

**Inventário canônico em `main` (lido no GitHub):**
- `plugins/my-requests/src/components/RequestListShell.tsx` monta `MyRequestsPageHero` e **separadamente** `MyRequestsDataTableSection` com `serverSearch`, `toolbarExtra` (Filters+Sort), `toolbarFilters`, `columnPreferencesKey`, `viewLayoutPreferencesKey`, `serverPagination` e `serverSort`. Causa comprovada do posicionamento incorreto: ownership de render/layout dos controles sob `DataTableSection`, não hero.
- `MinePage.tsx` e `WorkQueuePage.tsx` montam `columnSortMap`, `sortKey`, `sortDirection` e contratos de URL/sort, mas o uso concreto deve ser corrigido/validado.
- `RequestListShell.tsx` no clique de header chama `sort.onChange([{field,direction}])` **seguido imediatamente** de `sort.onApply()`. Como as páginas usam state React para draft, há risco de `onApply` observar `sort.levels` anterior por closure. **TO_VERIFY** com teste reproduzível; não afirmar defeito sem teste.
- `plugins/plugin-ui` já provê `DataTable`, `TableColumnVisibilityMenu`, `useTableColumnVisibility`, `createDashboardFilterRulesBuilder`, `createDashboardSortLevelsBuilder`, `createDashboardToolbarPopover`, `ScopeChipBar` e primitivas de Hero; não criar duplicatas locais.
- Resultado anterior `HML_DEPLOY_PASS` do pacote UX V2 **não** comprova os novos AC visuais. Documentação: [Especificação](./UX-PARITY-HELPDESK-PLUGIN-UI-TWO-MFES.md), [Execução anterior](./UX-PARITY-EXECUTION-EVIDENCE.md).

## 2. Wireframe contratual aprovado

```text
MY REQUESTS TOPBAR (fora do hero, inalterada)
[Minhas solicitações] [Fila de trabalho] [Nova solicitação] [Administração]
PagePath compacto: Início / Minhas Solicitações / {Minhas solicitações|Fila de trabalho}

┌ HERO ÚNICO (owner visual: Plugin UI) ─────────────────────────────────────┐
│ MINHAS SOLICITAÇÕES / FILA DE TRABALHO    [N resultados] [Atualizar] [Nova*]│
│ Descrição breve                                                            │
│ Buscar                                                                     │
│ [_____________________________________________________________________]   │
│ [Filtros] [Ordenar: Data ↓] [Colunas] [Itens/página 20]                     │
│ [Todas] [Enviadas] [Em atendimento] [...]     [Tabela] [Cards]             │
└────────────────────────────────────────────────────────────────────────────┘
┌ TABELA SEM CARD EXTERNO DUPLICADO ─────────────────────────────────────────┐
│ NÚMERO ↕  TIPO ↕  ASSUNTO ↕  STATUS ↕  FILIAL ↕  DATA ↓ (campos permitidos)│
│ linhas de dados autorizados                                                │
└────────────────────────────────────────────────────────────────────────────┘
PAGINAÇÃO (um rodapé): Itens/página · mostrando x–y de N · página a de b
```

`*` Botão Nova solicitação somente em Minhas quando permitido; Fila tem Atualizar e contagem, não CTA de criação duplicado.

A ordem exata entre botões, chips e layout deve imitar o Helpdesk nos mesmos breakpoints, priorizando busca dominante, alinhamento, densidade e legibilidade. Hero agrega os controles; DataTable apresenta apenas linhas/header, card view e footer. Nenhum título/section card redundante. Usar composição e props de Plugin UI; não copiar CSS Helpdesk/MyRequests.

## 3. Plano de execução ordenado (gates)

### G0 — Reanchor/evidência
- `git fetch`, conferir `HEAD == origin/main` ou fast-forward; `git status`, WIP, SHA efetivo, autoridades/docs existentes, shims, testes e convenções.
- Não criar branch. Não usar reset --hard, force-push ou descartar trabalho alheio. Registrar `BASE_HEAD`, alterações externas, RQ/AC.
- Inventariar `DataTableSection` / `DataTable` toolbar/search/filter/pagination APIs, `PageHero`, `ScopeChipBar`, `SegmentToggle`, `ToolbarPopover`, preferences hooks. Aplicar Abstraction Gate e localizar composição equivalente no Helpdesk. Resolver por primitivos públicos existentes antes de ampliar o kit.

### G1 — Plugin UI como owner (primeiro)
- Evoluir, **se necessário**, apresentação neutra do Hero/toolbar e DataTableSection em props/slots públicas para mover busca e controles para dentro do Hero sem duplicação visual ou lógica.
- Garantir que DataTable canônica possa renderizar grade desprovida de toolbar/card externo redundante mantendo sort/columns/preferences/cards/pagination. Se necessidade de `unframed`/slots, implementar no kit, não no CSS MFE.
- Manter Helpdesk consumindo export compartilhado e sem regressões; o domínio Helpdesk mantém seu modelo de tickets. Garantir popovers com portal, tokens dark/light, clamp/flip/esc.
- Evitar modificar Plugin UI se as APIs existentes já forem suficientes. Não inventar primitivo novo apenas por conveniência.

### G2 — My Requests: reorganizar componentes
- Nas duas listas, mover a busca (com Enter + debounce URL), chips, popovers Filtros/Ordenar/Colunas, modo Tabela|Cards e itens/página para **dentro do hero**, com posição análoga ao Helpdesk.
- Contagem/Atualizar/CTA existentes permanecem coerentes e sem duplicação.
- Remover card externo e espaçamento excessivo que envolve apenas a tabela (sem perder border/table overflow ou estados empty/error). A grade deve ocupar largura disponível e aparecer imediatamente após o Hero, com gap visual curto.
- Manter quatro abas `MyRequestsTopBar` **acima** do hero e breadcrumb/PagePath canônico (evitar apenas eyebrow em caixa alta quando breadcrumb clicável existe).
- Diminuir ruído de ícones `?` duplicados sem remover help acessível. Texto de estados e botões PT-BR.
- Responsivo: busca linha própria em telas menores; chips quebram linha ou rolam controladamente no próprio grupo; controles alcançáveis.

### G3 — Ordenação de TODAS as colunas realmente suportadas
- Cabeçalhos de tabela de Minhas/Fila com affordance `↑↓`, cursor/foco/aria-sort; clique alterna `asc ↔ desc` para a **coluna clicada** quando houver campo no sort catalog efetivo. Ao escolher coluna diferente, nível 1 troca; estado refletido no popup e URL. Primeira direção conforme contrato; depois alterna.
- Validar com teste real o risco `onChange` + `onApply` com estado antigo. Corrigir com operação atômica `applySort(nextLevels)` ou mecanismo equivalente (sem `setTimeout` como gambiarra).
- Para colunas não ordenáveis por contrato, não mostrar interação/indicador enganoso; manter header sem clique e tooltip explicativo se útil. **Não prometer todos os campos se API multi-source não suportar.**
- `work-queue`: 3 níveis server-side conforme whitelist `requests-api`, antes de LIMIT/OFFSET; sort usado por header e popup deve ser o mesmo.
- `mine`: multi-source Requests+PRC, máximo 1 nível quando PRC contribui no escopo (conforme contrato atual); preservar sort global honesto dentro das limitações explicitadas. Não ordenar somente linhas da página. Não ampliar para 3 sem prova/contrato.
- Em ambos: persistência de sort na URL, reset page=1, back/forward/refresh, estado da seta e `aria-sort`, nulos e desempate estável.
- Confirmar se cada coluna exibida possui field sortável; inventariar mapeamento por tabela e publicar matriz resultado. Ordenação via click em Número, Tipo, Assunto, Status, Filial, Data, Solicitante, Concluída por somente onde API suportar, nunca fake sort.

### G4 — Demais controles e paridade
- Filtros avançados e chips refletem efetivamente a mesma query; aplicar/limpar, critérios AND, estado URL, popovers ancorados, sem clipping e sem fechar controles internos.
- `TableColumnVisibilityMenu` funciona em Tabela|Cards, persiste visibilidade/ordem por página, identidade obrigatória. Cards usam mesmo catálogo; sem fields perdidos e sem navegação quebrada.
- Itens por página acessíveis no Hero (se alteração de pageSize ainda não suportada por contrato, implementar corretamente ou marcar limitation, nunca controle decorativo); paginação footer simples fora de scroller, navegável.
- Diferenciar indisponível/403/vazio/partial; total autoritativo; preservar permissões, My Requests corporativo, PRC, protocolos, tipos, URLs e realtime.
- O Helpdesk permanece visualmente coerente; não mudar workflow GLPI para perseguir paridade.

### G5 — Testes e homologação
- Vitest/tsc/build do kit, Helpdesk e My Requests; regressões específicas de `RequestListShell` e comparador server-side.
- E2E Chromium HML com duas listagens, cliques **reais** nos headers: direção URL, ordenação das linhas, asc/desc e sincronização com popup após refresh; condições com ≥2 valores distintos, inclusive tie-break/nulos quando houver massa/fixture canônica.
- Testar toolbar **fisicamente dentro do Hero** por DOM containment/computed rectangles, não só presence; tabela fisicamente fora do Hero e sem wrapper de card duplicado; gap e densidade.
- E2E filtros, colunas, cards, paginação, deep-link, navegação, tema claro/escuro, zoom 200%, 1440/768/390/320px, teclado/Escape/foco/aria, no overflow horizontal.
- E2E Helpdesk HML obrigatório para paridade final: primeiro inventariar rota de serviço; se não existir no compose HML, procurar deployment oficial/rotas e estabelecer validação autorizada no ambiente correto **sem inventar ou provisionar infraestrutura não autorizada**. Se impossível, registrar TEST_NOT_RUN e **não** declarar full two-MFE parity PASS.
- Identidade negada real: testar quando disponível; nunca fabricar token/grant. Regressões requests-api/Engineering API/PRC/NF e My Requests.
- Usar agente **verificador independente** após implementação e após HML (mesmo contrato do verificador existente), com acesso aos diffs/código/tests/screenshots/HTTP permitido, e ordens de correção registradas. Repetir corrigir→testar→verificar até zero findings críticos e AC atendidos; separar findings preexistentes/concorrentes de forma honesta.

### G6 — Deploy e ledger HML
- Somente os serviços efetivamente modificados; ordem API → Plugin UI → consumidores (quando requerida). Backup/rollback de imagens, pre/post health, remoteEntry, assets e no 5xx.
- Trabalhar só em `main` com ff-only, preservar WIP concorrente e não usar force-push.
- Registrar commits de código, SHAs/digests de HML, resultados, screenshots, testes, matriz RQ/AC, findings do verificador, riscos e follow-ups na documentação/ledger.
- PRD_DEPLOY=NOT_EXECUTED; nenhuma alteração TOTVS ou escrita de negócio PRD.

## 4. Critérios de aceite (bloqueantes)

| ID | Critério medível |
|---|---|
| AC01 | Topbar de quatro abas acima do Hero, breadcrumbs sem triplicação |
| AC02 | Busca, Filtros, Ordenar, Colunas, chips, Tabela/Cards e page size estão **dentro da árvore/área visual do Hero** nas duas telas |
| AC03 | Grade diretamente após Hero, sem segundo card externo grande, com densidade e espaçamento equivalentes ao Helpdesk |
| AC04 | Clique em cada cabeçalho **sortável** muda a ordem real global no backend, direção alternada, seta+aria-sort+URL corretos |
| AC05 | Ao clicar header, popup Ordenar abre já com a nova seleção; não há stale state / double fetch incorreto |
| AC06 | Campos não-sortáveis não fingem interatividade; matriz de capacidade por coluna publicada |
| AC07 | Filters AND + chips combinam; URL e paginação corretas; contagens honestas |
| AC08 | Colunas, Cards, preferências independentes e navegação de origem intactas |
| AC09 | Popovers visíveis/ancorados em claro/escuro, zoom200/mobile, teclado |
| AC10 | Helpdesk mantém visual/funções atuais; primitivas neutras compartilhadas por Plugin UI |
| AC11 | E2E HML + agente verificador independente confirmam os AC com provas visuais reais |
| AC12 | My Requests PRC/NF/Requests API, segurança, isolamento, reatividade e APIs sem regressões |
| AC13 | Todos os findings desta task corrigidos ou bloqueios formalmente declarados, sem falsificar PASS |
| AC14 | PRD intocada, WIP concorrente preservado, ledger atualizado |

**Não encerrar apenas porque testes unitários passam**. Se um AC funcional ou visual falhar, corrigir e repetir até concluir. Se blocker real externo (permissão, massa, ambiente/authority) impossibilitar teste, registrar `BLOCKED/TEST_NOT_RUN` e trazer decisão explícita, não afirmar entrega completa.

## 5. Report exigido

```text
TASK_ID
BASE_HEAD / IMPLEMENTATION_SHA / FINAL_MAIN_SHA
G0_INVENTORY / PLUGIN_UI_ABSTRACTION_GATE
ROOT_CAUSE_LAYOUT / ROOT_CAUSE_HEADER_SORT
MY_REQUESTS_MINE_HERO / MY_REQUESTS_WORK_QUEUE_HERO
ALL_CONTROLS_INSIDE_HERO_DOM_PROOF
TABLE_UNFRAMED_AND_GAP_PROOF
HEADER_SORT_MATRIX / SERVER_ORDER_PROOF / STALE_STATE_FIX
FILTERS_AND_URL / COLUMNS / CARDS / PAGINATION
PLUGIN_UI_CHANGE / HELPDESK_PARITY_AND_REGRESSION
PLUGIN_UI_TESTS / MYREQ_TESTS / HELP_DESK_TESTS / BACKEND_TESTS
HML_E2E_HERO / HML_E2E_HEADER_SORT / VIEWPORTS / DARK / ZOOM
VERIFIER_ENGINE / VERIFIER_ROUNDS / VERIFIER_FINDINGS / FIXES
HML_DEPLOY_SHAS / DIGESTS / HEALTH / ROLLBACK
AUTHORIZATION / NO_TOTVS_WRITES / PRD_DEPLOY=NOT_EXECUTED
RQ_AC_MATRIX / TEST_NOT_RUN / EXECUTION_DRIFT / RESIDUAL_RISKS
FINAL_OUTCOME / NEXT_ACTION
```
