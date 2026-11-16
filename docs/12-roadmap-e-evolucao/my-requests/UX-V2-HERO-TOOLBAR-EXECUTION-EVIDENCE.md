# UX-V2 Hero × Tabela × Header-Sort — evidência de execução (HML)

> **TASK_ID:** `MYREQ-UX-V2-HERO-TOOLBAR-HEADER-SORT-PARITY-HML-01`
> **Data:** 15/11/2026 · **Branch:** `main` · **Ambiente:** HML (`delpi-hml`, srv-api `https://192.168.1.237:18443`)
> **Plano canônico:** `UX-V2-HERO-TABLE-HELPDESK-PARITY-CORRECTION-PLAN.md` (AC01–AC14)
> **BASE_HEAD:** `31efa88ba2` · **IMPLEMENTATION_SHA:** `96e9b5bf30` + `9488209013`

## 1. Causa raiz

**Layout.** Os controles de listagem eram passados como props de
`DataTableSection` (`serverSearch`, `toolbarExtra`, `toolbarLeading`,
chips, Tabela|Cards, itens/página) e renderizados dentro do card da
seção, **abaixo** do hero — nunca dentro dele. O bug de composição era
de ownership: o hero (`PageHero`) não recebia os controles.

**Header-sort.** Duas falhas encadeadas:
1. Nenhuma coluna tinha `sortable: true` — `DataTable` não renderizava
   botão/seta/`aria-sort` nos cabeçalhos (affordance inexistente, não
   quebrado).
2. O handler fazia `sort.onChange([{field,direction}])` seguido de
   `sort.onApply()` no mesmo tick — `applySort` fechava sobre
   `sortLevels` do estado anterior (React setState assíncrono), então o
   commit serializava o nível **anterior** (um clique de atraso).

## 2. Solução

**Plugin UI (owner):**
- `DataTableSection`: novo `toolbarLayout="hero"` — a mesma toolbar é
  reordenada visualmente via CSS `order` (busca dominante em linha
  cheia → extras + itens/página → chips | Tabela|Cards), sem mudar
  instância nem estado. Prop `embedded` remove o card externo da seção.
- `toolbarPortalTarget` (API já existente, usada por
  controllership-finance) porta a toolbar real para um host dentro do
  `PageHero.children` — uma única toolbar no documento.
- CSS novo apenas no kit (`data-table.css`): `.delpi-ui-list-toolbar-host`,
  `.delpi-ui-table-toolbar--hero`, `.delpi-ui-table-section--embedded`,
  `.delpi-ui-table-wrap--embedded`.

**My Requests (consumidor):**
- `RequestListShell`: host `data-testid="request-list-toolbar-host"`
  dentro do hero; seção `embedded` logo abaixo; `PagePath` clicável
  (Início / módulo / página) substitui o eyebrow textual duplicado.
- Colunas ganham `sortable` somente quando presentes em `columnSortMap`
  — matriz honesta de capacidade.
- Header-sort aplica `sort.onApply([{field, direction}])`
  **atomicamente** — o novo nível vai por extenso ao commit de URL/API
  (regressão `UX-V2-HEADER-01` coberta por teste estrutural).
- `page_size` vira estado de URL real (default 20 omitido; opções
  10/20/50/100 espelhando `TABLE_PAGE_SIZE_OPTIONS` do kit; reset de
  página em mudança).

**Catálogo de ordenação por fonte (matriz AC06):**

| Lista | Fonte efetiva | Colunas sortáveis | Níveis |
|---|---|---|---|
| Minhas (merged) | Requests+PRC | **Data** (`created_at`) | 1 |
| Minhas (Tipo=outro) | Requests API | Número, Tipo, Status, Filial, Data | 3 |
| Minhas (Tipo=PRC) | merged | **Data** (`created_at`) | 1 |
| Fila de trabalho | Requests API | Número, Tipo, Status, Filial, Data | 3 |

Assunto, Solicitante e Concluída por **não** são ordenáveis (fora do
contrato/merge) e não exibem affordance — sem fake sort. Direção
inicial segue convenção Helpdesk: `*_at` → desc, demais → asc.

## 3. Testes locais

| Suíte | Resultado |
|---|---|
| plugin-ui vitest | **2643/2643** |
| plugin-ui build + verify-host-exports | OK |
| my-requests vitest | **230/232** — 2 falhas pré-existentes em `ProcessIssuePayloadPanel` (arquivos intocados, já registradas) |
| my-requests typecheck | 0 erros |
| my-requests build | OK |
| helpdesk build | OK (sem mudança de fonte) |

Novos testes: `ux-v2-hero-sort.spec.ts` (E2E), structural ampliado em
`MyRequestsListUx.structural.test.ts` (portal no hero, embedded, sort
atômico, page_size, matriz sortável) e `useRequestListUrlState.test.ts`
(page_size parse/serialize/whitelist).

## 4. Deploy HML

```
BASE_HEAD local:      31efa88ba2 → 96e9b5bf30 (+9488209013 spec fix)
HML checkout:         pull --ff-only → 96e9b5bf30
Ordem:                plugin-ui → my-requests (requests-api inalterada)
plugin-ui digest:     aff11127e23b  (style-CzMxkvuk.css — mesmo hash local)
my-requests digest:   9612c8cb0899  (App-_H4aJ3uz.js contém toolbarPortalTarget)
Health:               ambos healthy; remoteEntry 200/200
Rollback tags:        delpi-hml/plugin-ui:rollback-ux-v2b-20261115
                      delpi-hml/my-requests:rollback-ux-v2b-20261115
PRD_DEPLOY=NOT_EXECUTED
```

## 5. E2E HML — Chromium real (36/36)

Runner `~/myreq-e2e-run` na VM (Playwright 1.65.x), usuário `hml-tester`,
`PLAYWRIGHT_INSECURE=1` (TLS self-signed HML).

**Spec nova `ux-v2-hero-sort.spec.ts` (5 × 4 projetos = 20):**
- Containment DOM: `request-list-toolbar-host` dentro de
  `.delpi-ui-page-hero` por bounding rect; **uma única**
  `.delpi-ui-table-toolbar` no documento; busca/Filtros/Ordenar/
  Colunas/Itens-por-página/Tabela-Cards visíveis dentro do hero.
- Grade `.delpi-ui-table-section--embedded` começa após o fim do hero;
  breadcrumb `PagePath` acima do hero.
- AC06: `th[aria-sort]` = 1 em Minhas merged; = 5 na Fila; Assunto/
  Solicitante/Concluída por sem botão.
- Header Data (mine): clique → `sort=created_at:asc`,
  `aria-sort=ascending`, seta ↑; segundo clique → desc/↓; popup Ordenar
  mostra "Data" selecionada; **F5 preserva** via URL.
- Header Número (fila): asc → números `REQ-2026-000001→4` monotônicos;
  desc → `000004→1` — **conjuntos diferentes na página 1**, prova de
  ordenação global no backend (não só da página carregada).
- Itens por página: seleção 10 → `page_size=10` na URL e ≤10 linhas.
- Sem overflow horizontal (scrollWidth == clientWidth) em todos os
  viewports — incluindo 320px.

**Regressão `ux-v2.spec.ts` (4 × 4 = 16):** todas PASS — hero/toolbar,
busca→URL, sort popup, new/admin sem barras de filtro, forbidden
honesto. (1 flake transitório de SSO em mobile/tablet, PASS no rerun.)

## 6. Evidência visual inspecionada

Screenshots versionados em `evidence/ux-v2-hero-toolbar-hml-01/`:

- **Desktop mine:** hero azul único contendo título + "20 solicitações"
  + Atualizar + Nova solicitação + descrição + busca + Filtros/"Data ↓"/
  Colunas + chips Status; grade navy logo abaixo — paridade com
  Helpdesk. `01-desktop-mine-hero.png`
- **Desktop fila:** header "Número ↓" destacado + trigger "Número ↓"
  sincronizado + REQ-004→001 real. `02-desktop-wq-header-sort-desc.png`
- **Itens por página:** controle real na toolbar do hero.
  `03-desktop-mine-page-size.png`
- **Mobile 320:** hero completo empilhado (título/badge/ações/busca/
  Filtros/sort/Colunas/itens/chips/Tabela-Cards), cards abaixo, sem
  overflow. `04-mobile320-mine-cards.png`
- **Dark theme:** composição idêntica em dark (hero, toolbar, chips,
  grade). `05-dark-mine.png`
- **Zoom 200%:** sidebar colapsa, breadcrumb + hero legíveis, conteúdo
  reflow sem quebra. `06-zoom200-mine.png`
- **Tablet:** hero completo + cards 2 col + footer "1–4 de 4 · página
  1 de 1". `07-tablet-wq-list.png`

## 7. delpi-verifier (verificação independente)

Motor `cursor` (Composer), executor `swe-2-high` — independência OK.

| Rodada | Escopo | Veredito |
|---|---|---|
| 1 | `31efa88ba2..3a36472864` | `ACCEPT_WITH_RESIDUAL` |

Rodada 1: **zero ordens de correção**. AC01–AC08, AC10, AC12–AC14 PASS
em verificação estática (código, diffs, testes alvo 40/40, builds 3/3).
AC09 `INCONCLUSIVE` e AC11 `TEST_NOT_RUN` **apenas no verificador** —
seu contrato proíbe SSH/deploy/E2E; o E2E HML 36/36 e os screenshots
foram executados e inspecionados pelo executor (§5–§6, artefatos
versionados). O verificador reproduziu plugin-ui com 2639/2643 (4
timeouts flake em `RichTextEditor`/`ColorPickerPopover`, arquivos fora
do diff; a suíte rodou 2643/2643 no ambiente do executor). Registro:
`registro: OK`.

## 8. Riscos residuais

- **Helpdesk HML `TEST_NOT_RUN` (bloqueio real, evidenciado):** o
  serviço existe no HML (`delpi-helpdesk`, remoteEntry 200), mas o
  usuário `hml-tester` não tem o plugin liberado — `/apps/helpdesk`
  renderiza "Aplicação indisponível" (gate de permissão do portal
  funcionando). Sem credencial autorizada com grant Helpdesk, a
  comparação visual side-by-side fica indisponível; a paridade foi
  validada por composição compartilhada (mesmo `PageHero`,
  `DataTableSection`, popovers e CSS do kit servindo os dois MFEs) e
  pela regressão da spec `ux-v2.spec.ts`.
- 403 real negativo não exercitado (sem usuário de teste negado nesta
  rodada) — fail-closed 401 já comprovado no pacote anterior.
- Merge multi-fonte segue bounded (≤100) — honesto por contrato.
- Breadcrumb trunca o item corrente em 320px ("Minhas solicitaçõ") —
  cosmético do PagePath do kit, sem perda de navegação.
- WIP concorrente (delia-api, controllership-finance, docs) preservado;
  o plano canônico estava **deletado no working tree** por trabalho
  concorrente — restaurado de HEAD para registrar a execução (G10).
