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

---

# Anexo — Correção P1 `CROSS-MFE-UXV3-CLEAR-FILTERS-BUTTON-REGRESSION-HML-01`

## A. Causa raiz

**Geometria (botão deformado/estreito):** a regra de overflow do V3
`.delpi-ui-table-toolbar--hero > .delpi-ui-table-toolbar__controls .delpi-ui-help-tooltip--wrap > * { min-width: 0 }`
(especificidade 0,3,1) sobrescrevia o `min-width: 36px` do `IconButton` (0,1,0).
Sem largura mínima, o botão dimensionava para o conteúdo (~largura do SVG 16px)
mantendo `min-height: 36px` → retângulo estreito e alto. Probe mediu e confirmou.

**Visibilidade:** os consumidores usavam `disabled={!filtersActive}` — o botão
continuava renderizado e reservando largura sem filtros. Corrigido para
renderização condicional (o botão deixa de existir no DOM no estado limpo).

**Achado colateral (AC09):** `.delpi-ui-page-hero__actions { flex: 0 0 auto }`
impedia o shrink; em 320px os botões «Atualizar» + «Nova solicitação» (317px)
estouravam os 242px úteis e eram clippados pelo `overflow:hidden` do hero
(scrollW 374 × clientW 284). Corrigido para `flex: 0 1 auto; min-width: 0` —
tamanho natural preservado em desktop, wrap interno empilha em telas estreitas.

## B. Correções (owner: Plugin UI)

| Arquivo | Mudança |
|---|---|
| `plugin-ui/styles/data-table.css` | wrap `> *:not(.delpi-ui-icon-btn)` — icon buttons excluídos do `min-width: 0` nas faixas chips e controls |
| `plugin-ui/styles/action-controls.css` | `.delpi-ui-icon-btn { flex-shrink: 0 }` |
| `plugin-ui/styles/page-hero.css` | `__actions` `flex: 0 1 auto; min-width: 0` |
| `my-requests/RequestListShell.tsx` | FilterX renderizado só quando há filtro removível ativo |
| `helpdesk/HelpdeskPage.tsx` | mesma condicional sobre `filterActive` |

Zero CSS/componente duplicado nos MFEs — apenas bindings e condicionais.

## C. Prova geométrica HML (320px, probe autenticado)

| Estado | clearBtn | docOverflow |
|---|---|---|
| Limpo | `null` (não existe no DOM) | 0 |
| Filtrado | `{w:36, h:36}` — quadrado, âmbar | 0 |

Hero actions após fix: «Nova solicitação» empilha abaixo de «Atualizar»,
sem clipping (screenshot versionado).

## D. Testes

- Plugin UI: typecheck + build OK; ClearFiltersButton/IconButton 17/17.
- My Requests: estrutural 26/26; suíte focada 44/44.
- Helpdesk: estrutural 18/18; build OK.
- E2E HML autenticado (`https://192.168.1.237:18443`): **36/36** em
  desktop, tablet, mobile-390 e mobile-320 — incluindo estado limpo sem
  FilterX, aparição com filtro, geometria 36×36, cor âmbar, posição à
  esquerda de Filtros, desaparecimento após limpar, preservação de
  sort/page-size/layout e zero overflow.

### Flake de medição E2E corrigido

Rects viewport-relative dessincronizavam quando o scroll anchoring
atuava entre chamadas `boundingBox` separadas (remount pós-filtro e
encolhimento do hero pós-clear). Compares verticais migraram para
`page.evaluate` atômico + `expect.poll` até estabilizar. Nenhuma
asserção enfraquecida — tolerância `-2`/`+2` preservada.

## E. Deploy HML

| Item | Valor |
|---|---|
| SHA | `1fbea4178d` (impl) → `a7218deeca` (hero actions) → `c176dac339` |
| plugin-ui image | `delpi-hml/plugin-ui:local` → `f10f0d2cdc2b` (healthy) |
| my-requests image | `delpi-hml/my-requests:local` → `a15b3aded778` (healthy) |
| Helpdesk | ausente do compose HML — E2E `TEST_NOT_RUN` (mesmo bloqueio do ciclo anterior; grant/inventário pendentes do owner) |
| Rollback | imagens `rollback-ux-v3-20261116` + redeploy por SHA anterior |
| PRD | `NOT_EXECUTED` — sem autorização nesta task |

## F. Verificação independente

Pedido `.git/delpi-verifier/requests/ux-v3-clear-filters-regression-r1.md`.
Veredito: `INCONCLUSIVE` por restrição de ambiente (engine devin sem auth,
cursor sem quota — mesmo bloqueio do ciclo anterior). Registrado em
`verdicts.jsonl`. Evidência primária: E2E HML 36/36 + probes geométricos +
estruturais + builds.

---

# Anexo — Deploy controlado PRD `CROSS-MFE-UXV3-P1-PRODUCTION-CONTROLLED-DEPLOY-01`

## A. Isolamento do release

- Baseline PRD: `5782cd10dd` (imagens anteriores construídas desse SHA).
- Branch `release/uxv3-p1-prd` @ `c656ec3ca4` = baseline + cherry-picks
  do pacote (`30fba42e82`, `929291374a`, `1fbea4178d`, `7c0e308131`,
  `a7218deeca`, `53c670eb05`, `c176dac339` + docs link).
- Commits docs-only `8e0754988c`/`dec43da0ea` pulados (conflitos em
  arquivos `.md` editados por outros tracks — sem impacto de runtime).
- **Prova de isolamento:** `git diff origin/main -- plugins/plugin-ui
  plugins/my-requests plugins/helpdesk` = 0 arquivos não-md. As três
  árvores são byte-idênticas ao código homologado em HML.
- Checkout PRD restaurado a `main` após o build (preserva o fluxo
  FF-pull dos outros tracks).

## B. Ordem e resultado do deploy

| Etapa | Imagem nova | Container | Verificação |
|---|---|---|---|
| 1. plugin-ui | `infra-plugin-ui` `3e247e0c127c` | Up, 0 erros | `icon-btn--amber` + `flex:0 1 auto` no CSS |
| 2. my-requests | `infra-my-requests` `830882f7f285` | Up, 0 erros | `Limpar filtros` + remoteEntry 200 |
| 3. helpdesk | `infra-helpdesk` `35a90b2192d9` | Up, 0 erros | `Limpar filtros`/`filterActive` + remoteEntry 200 |

Imagens anteriores: plugin-ui `70b89d6ce531`, my-requests `882dcf2025c0`,
helpdesk `6e2c3a1a4930` — tags `rollback-pre-uxv3-p1-prd-202611161518`.

## C. Monitoramento

- remoteEntry ×3 = 200 via gateway; portal login 200; engineering
  remoteEntry 200 (consumidor cruzado íntegro).
- Gateway: 0 5xx no período; logs nginx dos MFEs limpos.
- Atividade concorrente observada (restarts de supplies, api-delpi,
  engineering-api por outros tracks — saudáveis, fora do escopo).

## D. Smoke autenticado

`INCONCLUSIVE` — não há identidade de teste autorizada no realm PRD
(`HML_TEST_*` existe só no realm HML; o submit no realm `delpi` de
minhadelpi.com.br não progride). Sem criação de credencial artificial,
conforme política. Evidência não-autenticada: bundles, remoteEntry,
CSS/tokens, federation e logs comprovados acima. Fluxo funcional
autenticado permanece **não comprovado** até o owner executar o smoke
com identidade legítima — checklist em §G7 do prompt da task.

## E. Verificação independente

Pedido `ux-v3-p1-prd-deploy-r1.md`; veredito `INCONCLUSIVE` nas duas
engines (devin sem auth, cursor sem quota) — restrição de ambiente,
registrada em `verdicts.jsonl`.

## F. Regressão residual HELPDESK-UXV3-FILTERX-GEOMETRY (16/11/2026 — `a85c6522b9`)

PO reportou FilterX deformado só no Helpdesk em PRD (My Requests ok).
Diagnóstico provado com CSS real de PRD: a regra do MFE
`.helpdesk-list-controls-row > .delpi-ui-help-tooltip--wrap > * { min-width: 0 }`
zerava o `min-width` do `IconButton` (18×36 medidos; `flex-shrink` irrelevante —
a largura intrínseca era 16 px de SVG + borda). Fix no Plugin UI:
`width/height` fixas 36 px no `.delpi-ui-icon-btn` (consumidor não consegue
zerar largura explícita). Dedup G4: `Status:` sai de `activeFilterLabels`
quando o valor tem chip rápido (sempre redundante — o filtro avançado usa
`TICKET_STATUS_FILTERS`); mantido para status sem chip.

| gate | resultado |
|---|---|
| reprodução (harness CSS PRD) | antes 18×36 `minWidth:0` → depois 36×36 |
| plugin-ui testes | 2653/2653 (+ contrato `iconButtonGeometry`) |
| helpdesk testes | verde (1 falha pré-existente helpTooltips budget) |
| my-requests vitest | 235/237 (2 falhas pré-existentes ProcessIssue — fora do diff) |
| tsc | limpo nos arquivos do diff (3 erros pré-existentes de outros tracks) |
| builds | plugin-ui + helpdesk OK |
| verificador | `INCONCLUSIVE` (devin sem auth) — `helpdesk-filterx-geometry-r1.md` |
| HML deploy | plugin-ui `95bc6045fe40`, rollback `rollback-pre-filterx-fix-202611161245` |
| HML E2E autenticado | 20/20 (ux-v2-hero-sort × viewports, FilterX 36×36/âmbar/ordem/clear) |
| PRD deploy | plugin-ui `d0a4438c8f91` + helpdesk `3746301be434`, remoteEntry 200 ×4 |
| PRD rollback tags | `rollback-pre-filterx-fix-202611161245` (plugin-ui 3e247e0c127c, helpdesk 35a90b2192d9) |
| PRD smoke autenticado | `INCONCLUSIVE` — sem identidade autorizada no realm `delpi` |
| writes TOTVS/negócio/RBAC/migrations | 0 |
