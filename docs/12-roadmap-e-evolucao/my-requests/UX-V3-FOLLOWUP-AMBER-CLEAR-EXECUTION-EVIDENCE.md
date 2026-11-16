# Evidência de execução — UX V3 Follow-up: FilterX âmbar compartilhado + header sort

**TASK_ID:** `CROSS-MFE-LIST-UXV3-HEADER-SORT-AMBER-CLEAR-PLUGIN-UI-HML-01`
**Data:** 16/11/2026
**BASE_SHA:** `139b1eab2c` (origin/main no início do G0)
**IMPLEMENTATION_SHA:** `30fba42e82` (código) + `929291374a` (seletores E2E)
**FINAL_MAIN_SHA:** `929291374a`

## 1. Plugin UI (owner compartilhado)

| Item | Evidência |
|------|-----------|
| Componente público | `ClearFiltersButton variant="icon"` — quadrado só-ícone `FilterX` sobre `IconButton tone="amber"` (`src/components/actions/ClearFiltersButton.tsx`) |
| Export | `ClearFiltersButtonVariant` adicionado em `src/components/actions/index.ts`; presente no remoteEntry (`ClearFiltersButton` já federado) |
| Token âmbar | `var(--delpi-ui-warning, #f59e0b)` + `color-mix` em `.delpi-ui-icon-btn--amber` (`styles/action-controls.css`) — sem cor hardcoded nos MFEs |
| Estados | normal / hover / focus-visible / disabled (herda muted do base); dark excluído do override genérico para preservar a tinta âmbar |
| Acessibilidade | `aria-label` («Limpar filtros»), tamanho 16px ícone; tooltip via `HintAction` do consumidor |
| Testes | `ClearFiltersButton.test.tsx`: 4/4 (labeled, compact, icon+amber class+click, icon disabled+aria-label custom) |

## 2. Consumidores (bindings, sem duplicação)

| MFE | Binding | Uso |
|-----|---------|-----|
| my-requests | `MyRequestsClearFiltersButton = ClearFiltersButton` (`ui/mrUi.tsx`) | `RequestListShell.toolbarExtra`, primeiro elemento — antes do popover Filtros |
| helpdesk | `HelpdeskClearFiltersButton` (`ui/helpdeskUi.tsx`) | `helpdesk-list-controls-row`, primeiro filho — antes de `TicketListFilterPopover` |

Nenhum `FilterX` importado direto nos MFEs (`grep` limpo). Shims `plugin-ui.d.ts` atualizados nos dois.

## 3. Semântica de limpeza (consumidor)

- **Mine:** `clearAllFilters` → `q,typeCode,status,branch=""`, `page=1`, `setFilterRules([])`. Preserva `sort`, `pageSize`, colunas e Tabela/Cards.
- **Work Queue:** idem + `mineScope=""` (escopo Minhas é filtro avançado).
- **Helpdesk:** `clearListFilters` existente preservado — limpa `q/status/urgency/category/assignee/requester*/date-ranges`, `page=1`, preserva `sort` e `page_size`.
- `filtersActive`/`isTicketFilterActive` controlam o `disabled`.

## 4. Correções colaterais provadas

- **«Limpar tudo» removido** (My Requests): `onClearAll`/`onClearChips` fora do shell; teste estrutural asserta ausência.
- **«Meus chamados» duplicado** (Helpdesk): chip de escopo + label `activeFilterLabels` renderizavam o mesmo estado duas vezes; removido o label (regra `requester_mine` preservada para o builder).
- **Ordem canônica** `[FilterX] [Filtros] [Ordenar] [Colunas] [Tabela|Cards]` verificada por teste estrutural (índice no JSX) e E2E (bounding box row-major).

## 5. Header sort — matriz por fonte (auditada, inalterada)

| Superfície | Colunas clicáveis | Contrato |
|------------|-------------------|----------|
| Mine (merged Requests+PRC) | Data → `created_at` | `MERGED_SORT_FIELDS` — único campo semanticamente comparável nas duas fontes |
| Mine (fonte=Requests) | + Número, Tipo, Status, Filial | `REQUESTS_SORT_FIELDS` |
| Work Queue | Número, Tipo, Status, Filial, Data | requests-api: `created_at,updated_at,request_number,status,type_code,branch` (max 3 níveis) |
| Helpdesk | 11 colunas (`id,title,status,category,urgency,assigned,requester,created_at,updated_at,solved_at,closed_at`) | `TICKET_LIST_SORTABLE_COLUMNS`; `entity`,`last_editor` não ordenáveis; `nextTicketSort` alterna ASC/DESC |

Sem afordância em coluna fora do contrato; sem re-sort local de página.

## 6. Testes executados

| Suíte | Resultado |
|-------|-----------|
| plugin-ui actions | 17/17 |
| my-requests | 235 passed; 2 falhas pré-existentes `ProcessIssuePayloadPanel` (fora do diff) |
| helpdesk | 282 passed; 1 falha pré-existente `helpTooltips budget listUi.myTickets` (fora do diff) |
| Estruturais | my-requests 26/26 (+caso FilterX/«Limpar tudo»); helpdesk 18/18 (nova ordem) |
| Typecheck | my-requests 0 erros; helpdesk 0 erros |
| Builds | plugin-ui, my-requests, helpdesk — 3/3 |

## 7. E2E HML autenticado (Chromium real)

Identidade `hml-tester` em `https://192.168.1.237:18443` — spec `ux-v2-hero-sort.spec.ts` + `ux-v2.spec.ts`:

- **36/36** em 4 projetos (desktop 1440, tablet 768, mobile 390, mobile-320).
- Ordem geométrica: FilterX primeiro da linha (row-major com wrap mobile).
- `delpi-ui-icon-btn--amber` presente; cor computada real `srgb(0.79,0.55,0.11)` ≈ `#c98c1b` (warning × texto) sobre fundo tint `#fdf3e1`.
- Header sort `Data`/`Número` alterna dir + `aria-sort` + URL `sort=` (prova server-side REQ-2026-000001↔4).
- `disabled` com zero filtros ativos; zoom 200% sem overflow (`scrollWidth-clientWidth=0`).
- Screenshots: `evidence/ux-v3-followup-amber-clear-hml-01/` (`amber-mine`, `amber-dark`, `amber-zoom200`).

**Helpdesk E2E visual: TEST_NOT_RUN** — serviço ausente de `docker-compose.hml.yml` e RBAC do `hml-tester` sem grant ao plugin. Paridade provada por estrutural+build; visual autenticado depende de decisão do owner (grant + inventário HML).

## 8. HML deploy

| Item | Valor |
|------|-------|
| SHA | `929291374a` (FF em `~/projetos-teste/delpi-central`) |
| Ordem | `up-hml-sequential.sh --build plugin-ui my-requests` |
| Digests | plugin-ui `236faeb98152`; my-requests `5cda269028f3` |
| Health | `delpi-hml-plugin-ui` healthy; `delpi-hml-my-requests` healthy |
| Código no bundle | `delpi-ui-icon-btn--amber` em `style-DAZ1Zguc.css`; `variant:"icon"` no bundle my-requests |
| Rollback | imagens `delpi-hml/*:rollback-ux-v3-20261116` (pré-V3) + redeploy por SHA anterior (bundles estáticos) |

## 9. Verificação independente

| Rodada | Motor | Veredito |
|--------|-------|----------|
| r1 | devin | INCONCLUSIVE — `devin auth login` ausente |
| r1 | cursor | INCONCLUSIVE — quota esgotada |

Verificador indisponível por restrição de ambiente nas duas engines — declarado, não fabricado. Evidência primária (E2E autenticado + estrutural + probe de cor computada) acima.

## 10. PRD — gate

**PRD_DEPLOY: NOT_AUTHORIZED_THIS_PACKAGE.** Nenhuma mutação em produção executada. Delta HML×PRD = 2 commits frontend-only (`30fba42e82`, `929291374a`), zero contrato/API/RBAC/migration. Relatório GO/NO-GO devolvido à Coordination para autorização explícita.
