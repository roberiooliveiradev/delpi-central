# ENGINEERING.LMP.G5.V — Native Portal UX & Visual Validation Evidence

**Gate:** G5.V — Native Portal Visual Design, Dashboard & Detail UX Alignment
**Escopo:** redesenho visual/UX das páginas `Acompanhamento de LMPs` (geral) e
`Detalhe da LMP` em `plugins/engineering` para a identidade nativa do Portal
Engenharia, sem copiar o visual do MFE legado `dashboard-lmps`.
**Baseline (`BASE_HEAD`):** `acb80117fd` (`origin/main` na reancoragem; G5 +
G5.R1 ancestrais)
**Status:** evidência real de navegador executada; veredicto no relatório EVA.

---

## 1. Baseline e reancoragem

| Item | Valor |
|---|---|
| `BASE_HEAD` | `acb80117fd` |
| Branch | `main` (working tree com alterações concorrentes de outras sessões preservadas) |
| G5 presente no HEAD? | Sim (`plugins/engineering/src/features/lmps/**`) |
| G5.R1 presente no HEAD? | Sim (doc 42; registro do plugin na Core dev ativo) |
| Alterações concorrentes preservadas | `controllership-finance-api/**`, `plugins/controllership-finance/**` e untracked de terceiros — nenhum arquivo compartilhado com o escopo G5.V |

## 2. Authorities lidas

- `AGENTS.md`, constituição mínima (`development-standards-index`,
  `evidence-driven-execution`, `centralized-rules-first`,
  `clean-code-architecture-guardrails`, `english-code-identifiers`).
- `platform-frontend-mfe-experience.mdc` (design system, temas, a11y,
  responsividade) — responsabilidade transversal material nº 5.
- `platform-security-identity-authorization.mdc` (backend-first AuthZ).
- `platform-architecture-boundaries.mdc` + `mfe-own-api-no-direct-api-delpi.mdc`
  (boundary MFE → Engineering API, zero bypass api-delpi).
- `platform-quality-testing.mdc` + `test-and-commit.mdc` + `plan-execution.mdc`.
- `platform-delivery-runtime-operations.mdc` +
  `infra-sequential-container-startup.mdc` (rebuild/restart do container).
- `contract-evolution-backward-compatibility.mdc`, `feature-help-sync.mdc`,
  `mf-federation-patch-safety.mdc`, `root-cause-generalized-fix.mdc`.
- Docs Engenharia 32–42 (G2→G5.R1).

## 3. Inventário de design system (Abstraction Gate)

Primeira autoridade visual: Home (`HomePage.tsx`) e Visão Geral
(`OverviewPage.tsx`) do próprio plugin, compostas sobre o kit canônico
`@delpi/plugin-ui` (fonte `@delpi/ui-kit`), tipografia/raios/sombras vindos dos
tokens `--en-*`/tokens globais do Portal e escopo `.portal-engineering`.

Padrões canônicos inventariados e reutilizados:

| Elemento | Componente oficial (kit) | Wrapper Engineering | Uso em LMPs |
|---|---|---|---|
| Breadcrumb/caminho | `createDashboardPagePath` | `EngineeringPagePath` | ambas as páginas |
| Hero + eyebrow + ações | `createDashboardPageHero` | `EngineeringPageHero` | ambas |
| Card KPI | `createDashboardKpiCard` | `EngineeringKpiCard` | ambas |
| Card de detalhe | `createDashboardDetailCard` (`detailCardRichBemClasses`) | `EngineeringDetailCard*` | detalhe |
| Grid de campos | `createDashboardDetailFieldGrid` | `EngineeringDetailFieldGrid` | detalhe |
| Card de gráfico | `chartCardBemClasses` / `ChartCard` | `EngineeringChartCard*` | dashboard |
| Toolbar de gráfico | `createDashboardChartToolbarKit` | `EngineeringChartToolbar*` | dashboard |
| Tabela | `dataTableBemClasses` / `dataTableSectionBemClasses` | `EngineeringDataTable*` | ambas |
| Paginação | `createCompactPagination` | `EngineeringCompactPagination` | ambas |
| Badge de status | `createDashboardStatusBadge` | `EngineeringStatusBadge` | ambas |
| Filtros (data/multi) | `createDashboardDateField` / `createDashboardMultiSelectField` | `EngineeringDateField` / `EngineeringMultiSelectField` | dashboard |
| Estados (loading/vazio/erro) | `stateChrome` kit + `EngineeringStateBox`/`ghostChrome` | wrappers locais → canônico | ambas |

Prefixo BEM canônico: `engineering` (`ENG_UI_PREFIX`), escopo
`.portal-engineering`. Wrappers centralizados em
`plugins/engineering/src/ui/engineeringUi.ts` — o mesmo módulo já usado por
Home/Overview. **Nenhuma segunda biblioteca visual** foi criada dentro de
`features/lmps`: os componentes locais viraram wrappers finos que delegam às
fábricas `Engineering*`; `features/lmps/styles/lmps.css` foi reduzido a layout
da feature e widgets especializados (timeline/Gantt/árvore/produto), com paleta
de domínio mínima sobre tokens `--en-*` e variante
`:root[data-theme="dark"] .portal-engineering`.

Componentes de domínio preservados (sem mover para `shared/` por não ter
consumer adicional): `LmpsHistoryTimeline`, `LmpsGantt`, árvore de estrutura
BOM, `LmpsExportButtons` (dispatch de exportação), `FilterBar` → substituído
pela composição nativa de filtros dentro do PageHero.

## 4. Mudanças — página geral (Acompanhamento de LMPs)

Arquivo: `features/lmps/pages/DashboardLmpsPage.tsx`.

- **Cabeçalho:** `EngineeringPagePath` (`← Início / LMPs`, navegação interna
  ao Portal) + `EngineeringPageHero` com eyebrow `PORTAL ENGENHARIA`, título
  `Acompanhamento de LMPs`, descrição funcional com período ativo, badge IDD
  (`IDD 10.0 · Excelência Integrada` via `department-idd`) e ações
  CSV/Excel/PDF/Atualizar — mesmo padrão da Visão Geral.
- **Filtros:** 6 campos (Competência, Data inicial, Data final, Unidade, Tipo,
  Status) agora renderizados **dentro do hero**, usando
  `EngineeringDateField`/`EngineeringMultiSelectField` — semântica
  intocada: query params, multi-seleção, defaults, persistência, deep links e
  round-trip continuam idênticos (prova: navegação preservou
  `?start_date&end_date&competence&branch`).
- **Tabs:** pill `Dashboard` ativo + `Registro de não conformidades` (link
  legado governado `/apps/dashboard-lmps/nonconformities`).
- **KPIs:** grid `engineering-lmps-kpi-grid` com 4 cards nativos:
  `Dias sem NC` (2551 dias · `Recorde: 2.551 dias` — harmonizado com o legado),
  `% LMP Dentro do Prazo` (valor + `META PARCIAL`/`META MÊS`/`NOTA IDD` +
  badges `Meta consolidada`/`Dentro da meta`/`Quanto maior, melhor`),
  `Lead Time Médio Útil`, `Total de Propostas`.
- **Gráficos:** 4 blocos (Contagem por Nível, Contagem por Status, Lead Time por
  Nível, Evolução) sobre `EngineeringChartCard`/`EngineeringChartToolbar*`.
  Novo hook `useLmpsChartTheme` resolve texto/eixos/grid/tooltip/legenda a
  partir dos tokens CSS do tema vigente (`data-theme`) e re-resolve na troca
  light↔dark — elimina cores hardcoded light-only. Pizza filtra categorias
  zeradas para evitar labels sobrepostos (sem falsificar dados).
- **Tabela:** `Registros filtrados` sobre `EngineeringDataTable*` +
  `EngineeringCompactPagination`; busca, sort, seleção de colunas, exports,
  scroll interno e deep link por linha preservados.
- **Estados:** loading card/inline, stale, erro, vazio e forbidden via chrome
  canônico.

## 5. Mudanças — página de detalhe (`lmps/ov/{sale}`)

Arquivo: `features/lmps/pages/LmpDetailPage.tsx`.

- `EngineeringPagePath` (`← LMPs / Proposta 003696`) + `EngineeringPageHero`
  com eyebrow `PORTAL ENGENHARIA • LMPS`, título `Proposta {sale}`, badge de
  status oficial `EngineeringStatusBadge`, descrição `Tipo · produto` e ações
  `Atualizar`/`← Voltar` (back preservando filtros via `navigateLmpsBack` +
  `appendFiltersToPath`).
- KPIs `Status`, `Lead time útil`, `Tempo engenharia` em cards nativos.
- `Proposta`, `Engenharia`, `Cliente e vendedor` como `EngineeringDetailCard`
  + `EngineeringDetailFieldGrid` (48 elementos de detail-card medidos).
- `Produtos`/`BOM`: tabela nativa + visualização de estrutura mantida com seus
  estados loading/forbidden/unavailable.
- `Histórico`: timeline/Gantt/filtros preservados em `.lmps-history-section`
  (apenas re-scoped ao CSS da feature).

## 6. Temas, responsividade, acessibilidade

- Tema herdado do host via `localStorage["theme"]` + `data-theme`; CSS dark
  escopado em `:root[data-theme="dark"] .portal-engineering`. Charts
  re-resolvem tokens na troca.
- Breakpoints: filtros empilham e KPIs vão a 2→1 col em tablet/mobile; tabela e
  Gantt mantêm scroll **interno** (nenhum overflow de página — medido).
- A11y auditado em browser (light desktop-xl):
  `h1` único por página, hierarquia h2/h3 coerente, `unlabelledInputs: 0`,
  `pageOverflowX: false`. Tooltips/help (`?`) preservados nos cards.

## 7. NC streak — investigação (G5V-20)

Chamadas reais lado a lado: legado `/apps/api-delpi/.../nonconformities/streak`
e `/apps/engineering-api/v1/lmps/nonconformities/streak` retornam **o mesmo
contrato e os mesmos valores oficiais**: `current_days_without_nc: 2551`,
`record_days_without_nc: 2551`, `last_nc_date: null`,
`reference_start_date: "2019-11-04"`, `as_of_date: "2026-10-29"`,
`nc_count: 0`. A divergência observada nas capturas era **de apresentação**,
não de fonte/período/semântica: o card do Portal exibia subtítulo diferente do
legado (`Recorde: N dias`). Harmonizado: o card agora mostra
`2551 dias` + `Sem NC em LMP's · Recorde: 2.551 dias`. Nenhum valor foi
inventado nem regra alterada.

## 8. Evidência de browser (Playwright real)

Ambiente: Chromium headless (Playwright), login real via Portal → SSO →
Keycloak `delpi`, credenciais de `infra/.env.local` (não emitidas). Matriz
2 páginas × 2 temas × 4 viewports = **16 screenshots**
(`/tmp/g5v-evidence/{dashboard,detail}-{light,dark}-{desktop-xl,desktop-md,tablet,mobile}.png`)
+ `evidence.json` + `evidence-nav.json`.

| Métrica (light desktop-xl) | Dashboard | Detalhe |
|---|---|---|
| Filtros renderizados | 6 | — |
| Elementos KPI | 43 | 22 |
| `recharts-surface` | 9 | — |
| Linhas na tabela | 14 | — |
| Detail cards | — | 48 |
| `h1` | 1 (`Acompanhamento de LMPs`) | 1 (`Proposta 003696`) |
| Inputs sem label | 0 | 0 |
| Overflow de página X | false | false |

Navegação (browser real): clique na linha →
`/apps/engineering/lmps/ov/003696?start_date=…&competence=2026-10&branch=01`
(h1 `Proposta 003696`); `goBack` → `/apps/engineering/lmps?start_date=…`
(filtros preservados); deep link direto renderiza o detalhe. `goBack` retorna
à listagem com query intacta.

Rede capturada durante toda a matriz + navegação: **77 chamadas
`engineering-api`, 0 chamadas `api-delpi`, 0 `401` inesperados, 0 erros de
página**.

Estado visual confirmado por inspeção dos screenshots: hero nativo com filtros
embutidos, KPIs carregados (100,00% · metas 88,87%/95,00% · IDD 10,00 · 2,50
dias · 14 propostas · 2551 dias sem NC), pizzas com labels legíveis nos dois
temas, detalhe com cards agrupados, chrome mobile nativo (hambúrguer + nav
inferior) em 390px.

## 9. Testes técnicos

| Comando | Resultado |
|---|---|
| `npm run typecheck` (plugins/engineering) | PASS — 0 erros |
| `npm run lint` | 0 erros, 11 warnings (efeitos `setState` pré-existentes do G5 + dep warning em `loadingProgress.ts` — não introduzidos pelo redesign) |
| `npm test` (vitest) | **119/119 PASS** (14 arquivos) |
| `npm run build` | PASS (único warning de chunk grande já existente) |
| Rebuild + recreate `delpi-engineering` | `infra-engineering:latest`, `remoteEntry: 200`, rota lmps 200 |
| Residual search | 0 chamada funcional api-delpi no MFE; 0 escopo `dashboard-lmps` na feature migrada; única permissão `engineering.access` |

## 10. Segurança e compatibilidade

- AuthZ backend-first intocada (Core `engineering.access`/`engineering.manage`);
  nenhuma decisão de permissão no frontend, nenhum token S2S no browser.
- Nenhum contrato alterado; nenhum backend modificado (diff restrito a
  `plugins/engineering`).
- MFE legado `dashboard-lmps` intacto e registrado; nenhum cutover.
- `NcLegacyRedirectNotice` preservado com chrome nativo (redirect governado).

## 11. Arquivos alterados (escopo)

`plugins/engineering/src/ui/engineeringUi.ts` (+83 linhas: wrappers
Engineering* para detail/chart/table/pagination/state/filter);
`features/lmps/pages/{DashboardLmpsPage,LmpDetailPage}.tsx`;
`features/lmps/hooks/useLmpsChartTheme.ts` (novo);
`features/lmps/components/{KpiCard,ChartCard,Pagination,chartUi,dataTableUi,DetailCard,DetailFieldGrid,LoadingActivityCard,DataTableSection}.tsx`;
`features/lmps/ui/{ghostChrome,stateChrome}.ts`;
`features/lmps/{LmpsFeature,export/LmpsExportButtons,constants/filterOptions}.tsx/ts`;
`features/lmps/styles/lmps.css` (reescrito — design system delegado ao Portal);
removidos `components/{FilterBar,LoadingActivityInline,MultiSelectField,dashboardFiltersUi}` (substituídos por composições canônicas).

## 12. Drift documental observado

- O script sequencial de startup (`infra-sequential-container-startup`) não
  inclui `engineering` em seu inventário de fases, embora o serviço exista no
  Compose — `Nenhum serviço bate com: engineering`. O rebuild foi feito
  diretamente pelo profile Compose do plugin. Drift registrado para correção
  futura (não silenciado).
- Residual visual menor: label da pizza `Contagem por Status` encosta na borda
  esquerda do card em 1920px (clipping de label Recharts, não de dados).
- Warnings de lint pré-existentes (não introduzidos pelo redesign).

## 13. Riscos e residuais

- Negativo AuthZ em browser com usuário comum sem grant: `TEST_NOT_RUN` (sem
  segunda credencial dev); código fail-closed verificado em G5.R1.
- Evidência em ambiente dev local; produção depende do registro Core (doc 42
  §10) — já tratado como ACT operacional do G5.R1.
- Pie label clipping (§12) — cosmético.

## 14. Próximo gate

Não avançar automaticamente. Retornar à EVA — Architecture / Coordination. O
gate de Não Conformidades permanece separado e pendente de autorização.
