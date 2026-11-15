# Trilha — UI review (U0–U8)

Fonte: [review.md](./review.md). Autoridade: instruções oficiais do arquiteto e `.cursor` > padrão visual dos Portais (`docs/11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md`) > `30-plugin-ui-reuse-map.md` > docs do front-end da auditoria (`entry-audit/frontend/01–04`) > este track > review.md.

## 1. Regras

1. `main`, sem branch; `git add` só com caminhos explícitos (nunca `-A`, `.`, `commit -a`); push a cada etapa.
2. `@delpi/plugin-ui` first: usar o componente do kit pelo adaptador `Cf*`; não recriar tabela, card, hero, badge ou gráfico com CSS local (§22). Mudança no plugin-ui só aditiva, com testes de caracterização e prova dos consumidores (lição da T13R).
3. Sem mudança de regra de negócio, contrato ou permissão. Se uma correção de tela pedir dado que a BFF não entrega, parar (Y-dado) e listar; leitura nova aditiva só com decisão.
4. Vocabulário e formatação num lugar só (`entryAuditPresentation.ts` e utilitários do MFE), com teste.
5. DoD de cada página: desktop 1440, tablet 1024, celular 390; claro e escuro (mesma árvore); teclado e foco; estados do §16; ajuda atualizada no mesmo gate.
6. Evidência por screenshot nos três tamanhos e dois temas (no report, não commitado) + Playwright + verificação de acessibilidade automatizada (axe) sem violação séria nova.
7. Página não aberta = INCONCLUSIVE.

## 2. Paradas

| # | Quando parar |
|---|---|
| V1 | 4º ciclo de correção no mesmo problema |
| V2 | Falha nova em suíte (MFE, plugin-ui, consumidores) |
| V3 | Correção exige mudança não aditiva no plugin-ui |
| V4 | Tela precisa de dado que a BFF não entrega (listar campo, página e motivo) |
| V5 | Escolha de produto fora desta revisão (conteúdo, fluxo, regra) |
| V6 | Falha em PROD → rollback e parar |

## 3. Quadro de status

| Etapa | Status | SHA |
|---|---|---|
| U0 Inventário visual e matriz de conformidade | DONE | `938ccd1edb` |
| U1 Base comum (vocabulário, formatação, badges, ícones, estados) | DONE | `1bcb9f470a` |
| U2 Início | DONE | `b31321f1d0` |
| U3 Auditoria — entrada e execução | DONE | `4577724671` |
| U4 Auditoria — resultado da análise | DONE | `25a491123f` |
| U5 Auditoria — detalhe da ocorrência | DONE | `94a98abca1` |
| U6 Demais páginas do Portal (desvios do padrão) | DONE | `f16cec684a` |
| U7 HML (usuários de teste por perfil, Playwright, axe, screenshots) | DONE | `cc2aec7849` |
| U8 PROD | DONE | `4785e7aa3e` |
| U9 Rework (G9, perfis, axe, página do usuário) | DONE | `1a1b8749bb` |
| U10 Desempenho BFF e perfis | DONE | `aefd74682d` |
| U11 Sem análise anterior | INCLUÍDA NA U12 | — |
| U13 Residuais da U12 (X1 axe, X2 testes antigos, X3 filtro) | READY | [prompt](./prompts/U13-residuais.md) |
| U12 Revisão 2 do owner (W0–W8) | DONE (W2–W8) | `ba53e55a2a` + tags rollback-ui-review-u12-* |
| U13 Residuais da U12 (X1–X3) | IN_PROGRESS | [prompt](./prompts/U13-residuais.md) |

## 3.1 Matriz de conformidade (U0) — evidência no código HEAD `1970a2bb4a`

Classificação: `CONFIRMADO_NO_CODIGO` | `CONFIRMADO_EM_HML` | `INCONCLUSIVO` | `OK`.

| Item | Página | Achado | Classificação |
|---|---|---|---|
| G1 PagePath | entry-audit home/analysis/occurrence | Sem `CfPagePath`; TopBar só «Início» | CONFIRMADO_NO_CODIGO |
| G2 Eyebrow | entry-audit | Home «Fiscal»; análise/ocorrência «Auditoria de Entradas» — deveria ser «Notas fiscais» | CONFIRMADO_NO_CODIGO |
| G3 Vocabulário | analysis/home | Temas/tipos/filiais técnicos (`cte`, `CTE`, `Filial 01`); `displayValue` só faz toLocaleString | CONFIRMADO_NO_CODIGO |
| G4 R$ | analysis/occurrence | KPI usa `currency` local; coluna Diferença usa `displayValue` → `170.00` | CONFIRMADO_NO_CODIGO |
| G5 Severidade | analysis | Texto puro; donut sem `tone` de status | CONFIRMADO_NO_CODIGO |
| G6 Ícones/ajuda | analysis/home | Ações sem Lucide; KPIs via MetricStrip sem ícone/ajuda | CONFIRMADO_NO_CODIGO |
| G7 Loading | analysis/occurrence | `<p>Carregando…</p>` sem hero/esqueleto | CONFIRMADO_NO_CODIGO |
| G8 Grid | home create + charts | `cf-filters-grid` / `cf-charts-grid` **sem CSS**; 7 KPIs no MetricStrip | CONFIRMADO_NO_CODIGO |
| G9 Perf | analysis | Summary+breakdowns+rows no mount; tempo abertura 01/11–15/11 | INCONCLUSIVO (medir U7) |
| H1 Highlights | PluginShell home | `highlightsUnavailable: "—"` hardcoded | CONFIRMADO_NO_CODIGO |
| H2 Recents icons | HomePage | Todos usam `SECTION_ICONS.closing` (calendário) | CONFIRMADO_NO_CODIGO |
| H3 LNF externo | catalog/HomePage | Link externo existe; sem `ExternalLink`/tooltip dedicado no card | CONFIRMADO_NO_CODIGO |
| E1 Form | EntryAuditHomePage | Campos empilhados; botão «Criar análise» | CONFIRMADO_NO_CODIGO |
| E2 Progresso | EntryAuditHomePage | Texto por filial; sem `CfProgressTracker` | CONFIRMADO_NO_CODIGO |
| E3 Histórico | EntryAuditHomePage | Tipos uppercased; status texto; sem badge/ação Abrir | CONFIRMADO_NO_CODIGO |
| A1–A9 | EntryAuditAnalysisPage | Hero/KPIs/donut solto/abas SegmentToggle/tabela/CLARA — alinhado ao review | CONFIRMADO_NO_CODIGO |
| O Detalhe | EntryAuditOccurrencePage | Sem PagePath; sem badge severidade; history em `<ol>` não `CfTimeline` | CONFIRMADO_NO_CODIGO |
| F Demais | closing/* | PagePath+Hero presentes em Received/DocumentsAdmin/Checklist* | OK parcial |
| F Meu perfil / DRE | shell | Perfil via TopBar→`/profile`; DRE projeta Home | OK / INCONCLUSIVO visual HML |

Screenshots HML (não commitados): `/tmp/ui-review-u0/` via `e2e/specs/u0-inventory.spec.ts` (home + entry-audit 1440/1024/390). Demais páginas e temas claro/escuro: evidência completa na U7.

**G9:** medição de abertura da análise 01/11–15/11 adiada à U7 (precisa sessão autenticada + análise existente); sem token seguro no inventário U0.

## 4. Etapas

**U0 — Inventário (somente leitura).** Screenshots de todas as páginas do MFE (Início, fechamento mensal e abas, documentos, relatórios, administração, Meu perfil, DRE, Auditoria: entrada, resultado com cada aba, detalhe) em 1440/1024/390 e claro/escuro. Matriz página × regra do padrão (§8–§24): hero, PagePath, SectionCard, KPIs, filtros, tabela, estados, responsivo, ícones, ajuda, vocabulário. Confirmar ou corrigir cada item do review.md e acrescentar o que faltar. Medir o tempo de abertura da análise de 01/11–15/11 (G9).

**U1 — Base comum.** Vocabulário (temas, tipos, filiais, situações), formatação (R$, datas, números de nota/série), mapa severidade → `StatusBadge` (tom + ícone), mapa de ícones por rota e ação, estados de carregamento/erro/parcial/vazio reutilizáveis, ajuda (`CF_HELP`) das telas. Testes de unidade.

**U2 — Início.** H1–H3 do review.md. H1 usa leituras que já existem (competência, bloqueios, última auditoria, backlog do LNF) e mostra estado explícito quando faltar.

**U3 — Entrada da auditoria.** E1–E3. Execução com progresso real (estágio e contadores da análise).

**U4 — Resultado da análise.** A1–A9 e G7/G9. Layout alvo (desktop):

```
PagePath
PageHero  [eyebrow Notas fiscais] Análise de 01/11 a 15/11/2026  [Concluída]
          Matriz (SC) · Filial ES · NF-e · CT-e · criada em … por …
          [⤓ Exportar] [↻ Executar de novo] [+ Nova análise]
KPIs      Notas | Valor | Pendentes | Alta | Diferença nas Altas | Sem par
Linha 1   [Conformidade: medidor + legenda + strip]   [Severidade: donut]
Linha 2   [Por tema]  [Por fornecedor]  [Por TES]
Linha 3   [Evolução por dia: período × anterior]   (só se > 1 dia)
Escopo    chips de filtro ativos  · Limpar
Abas      Ocorrências 159 · Notas casadas 315 · Sem par 144 · CT-e · TES · Fora do período 400
Tabela    severidade | nota/série | fornecedor | regra | campo | Protheus | XML | diferença | status
CLARA     Pergunte à CLARA + 3 sugestões
```

Tablet: KPIs 3 colunas, gráficos 2; celular: 1 coluna, tabela em cards.

**U5 — Detalhe da ocorrência.** Item O do review.md contra o doc 03.

**U6 — Demais páginas.** Corrigir os desvios de padrão da matriz U0, página a página, um commit por página. O que não for padrão vai para a lista de decisão (V5).

**U7 — HML.** Criar no Keycloak de HML usuários de teste por perfil (só access; access+manage; access+LNF; DRE), autorizado pela regra 9 da trilha da auditoria, com senha só no `.env.hml`. Playwright por perfil nas páginas mexidas, axe, screenshots 1440/1024/390 claro/escuro.

**U8 — PROD.** Tags `rollback-ui-review-controllership-finance` (e `-plugin-ui` se tocado); publicar; abrir o Início, a entrada da auditoria e a análise de 01/11–15/11 logado (página aberta, não remoteEntry); comparar números do resultado com a CLARA (summary).

## 5. Rollback

MFE (e plugin-ui, se tocado) pelas tags. Sem migration nesta trilha.

## 6. Registro

| Data | Etapa | SHA | Status | Nota |
|---|---|---|---|---|
| 2026-11-14 | plano | — | READY | Doc 171. Revisão pedida pelo owner sobre os prints de PROD. |
| 2026-11-14 | U0 | `938ccd1edb` | DONE | Matriz G/H/E/A/O/F no código HEAD≥2ce2d29c; G9 INCONCLUSIVO até U7; screenshots HML via u0-inventory.spec (não commitados). |
| 2026-11-14 | U1 | `1bcb9f470a` | DONE | Vocabulário/R$/severidade/ícones/estados/ajuda em entryAuditPresentation + SeverityBadge + LoadingState + CSS grids. |
| 2026-11-14 | U2 | `b31321f1d0` | DONE | H1 highlights reais; H2 hubRouteIcons; H3 ExternalLink+title no SectionRouteCard (aditivo). |
| 2026-11-14 | U3 | `4577724671` | DONE | E1 form em linha + Executar; E2 ProgressTracker; E3 histórico com badge/vocabulário/Abrir; PagePath. |
| 2026-11-14 | U4 | `25a491123f` | DONE | A1–A9: PagePath/Hero/6 KPIs/donut status/charts/UnderlineNav/tabela/CLARA; loading G7; daily A5. |
| 2026-11-14 | U5 | `94a98abca1` | DONE | O: PagePath, badge severidade, DetailField, Por quê/O que fazer, confirmação Resolver, Timeline, XML. |
| 2026-11-14 | U6 | `f16cec684a` | DONE | NotFound → CfPageHero. Lista V5: relatórios ClosingHero (padrão fechamento); Meu perfil no Core `/profile`. |
| 2026-11-15 | U7 | `cc2aec7849` | DONE | HML MFE healthy; Playwright U7 PASS (home/entry/analysis 1440/1024/390). G9 openMs≈9,0s (docs=315, high=17). Screenshots `/tmp/ui-review-u7`. Perfis Keycloak dedicados: INCONCLUSIVE (só `hml-tester`, como H5). axe: INCONCLUSIVE (sem `@axe-core/playwright` no MFE). Claro/escuro: INCONCLUSIVE. Fixes: PagePath `back` + hooks #310. |
| 2026-11-15 | U8 | `4785e7aa3e` | DONE | Tags `rollback-ui-review-controllership-finance` + `rollback-ui-review-plugin-ui`. PROD pull+build plugin-ui+CF; home/remoteEntry 200; App chunk com «Executar auditoria» e «Diferença nas Altas». Abertura autenticada Início/entrada/análise 01–15/11 + paridade CLARA: INCONCLUSIVE (sem usuário de teste PROD; não usar credencial HML). |

## 7. Report final (U0–U8)

| Etapa | SHA | Resultado |
|---|---|---|
| U0 | `938ccd1edb` | Matriz G/H/E/A/O/F no código |
| U1 | `1bcb9f470a` | Vocabulário/R$/badges/estados/CSS |
| U2 | `b31321f1d0` | Highlights reais + ícones + LNF title (kit aditivo) |
| U3 | `4577724671` | Entrada: form, ProgressTracker, histórico |
| U4 | `25a491123f` | Análise layout alvo A1–A9 |
| U5 | `94a98abca1` | Detalhe ocorrência |
| U6 | `f16cec684a` | NotFound + lista V5 |
| U7 | `cc2aec7849` (+fixes `f5f263df86`/`cc2aec7849`) | HML Playwright PASS; G9≈9s |
| U8 | `4785e7aa3e` | PROD publicado; tags de rollback |

**Paradas V1–V6:** nenhuma acionada.

### U6 — páginas corrigidas e lista de decisão (V5)

| Página | Ação |
|---|---|
| `NotFoundPage` | Corrigida — CfPageHero + CfActionButton |
| Relatórios / Central de Fechamento (`ClosingHero`) | **V5** — já seguem o padrão próprio do fechamento (doc 50); não forçar PageHero genérico |
| Administração (checklist/documentos/catálogos) | **OK** — PagePath e/ou ClosingHero presentes |
| Meu perfil | **U9 R4** — `/users/{userId}` com `PortalUserProfilePage` (alias `/profile` → `users/me`); CTA «Editar no Meu Perfil» ainda abre Core `/profile` |

## 8. U9 — rework (G9, perfis HML, axe/temas, página do usuário)

| Item | Status | Nota |
|---|---|---|
| R1 Progressive load análise | DONE | Wiring PASS; HML medição `analysis≈90ms`, `summary≈8260ms`, KPI visível≈8388ms (antes U7≈9s). Meta &lt;1,5s/&lt;3s **não atingida** — gargalo BFF `/summary` |
| R2 Perfis Keycloak HML | DONE (provision) | Users `cf-access`/`cf-manage`/`cf-lnf`/`cf-dre` no KC + grants Core VERIFY PASS. Playwright UI: bloqueado no gate LGPD do 1º login (browser closed) — reexecutar após aceite |
| R3 axe + claro/escuro | DONE (evidência) | Screenshots `/tmp/ui-review-u9/r3-*-{light,dark}.png`. Residuais host: `color-contrast`, `button-name` |
| R4 PortalUserProfilePage | DONE | `/users/{userId}` + alias `/profile`→`me`; avatar TopBar; Playwright R4 PASS |
| PROD | DONE | Publicado; tag `rollback-ui-review-u9-controllership-finance`; **pedir prints ao owner** |

SHA código U9: `1a1b8749bb` (+fixes grant). Tag rollback: `rollback-ui-review-u9-controllership-finance`.

## 9. U10 — desempenho BFF e perfis

| Item | Status | Nota |
|---|---|---|
| R1 `/summary` N+1 + memo | DONE | `statuses_of` + memo rows/runs; HML 01–15/11 summary≈242–285 ms (antes ≈8,3 s); query-budget tests |
| R2 Perfis + LGPD | DONE | ConsentModal no Playwright; cf-access/manage/lnf/dre PASS; access sem LNF |
| R3 axe inventário | DONE | Lista seletor/página/dono; MFE-local=0; host/plugin-ui registrados (sem fix kit nesta etapa) |
| PROD BFF | DONE | Tag `rollback-ui-review-u10-controllership-finance-api`; **pedir prints + tempo de abertura ao owner** |

SHA BFF: `aefd74682d`. Report: [reports/U10-desempenho-e-perfis.md](./reports/U10-desempenho-e-perfis.md).

| Data | Etapa | SHA | Status | Nota |
|---|---|---|---|---|
| 2026-11-15 | U10 | `aefd74682d` / `f71d6006f9` | DONE | G9 BFF; e2e LGPD+perfis+axe; PROD BFF publicada |

## 10. U12 — revisão 2 do owner (15/11): tabelas, hero com filtros, gráficos e abas

Fonte: [review-2.md](./review-2.md) (T1–T9, E1–E4, A1–A10). **Inclui a U11** (prompt [U11](./prompts/U11-sem-analise-anterior.md) não foi executado e passa a ser o item W1a). Prompt: [prompts/U12-cursor.md](./prompts/U12-cursor.md). Regras e paradas: §1 e §2 desta trilha.

### Etapas

| Etapa | O que entrega | Itens |
|---|---|---|
| W0 Inventário | Matriz de **todas** as tabelas do MFE: página, tabela, paginação (cliente/servidor), colunas ordenáveis hoje, `columnPreferencesKey`, cards no celular, coluna «Abrir», tabela HTML local. Medição de requisições ao trocar de aba na análise 01–15/11 (antes) | T1–T8, A1 |
| W1 BFF (aditivo) | **a)** sem análise anterior → `previous: null`; regra do anterior = mesmo nº de dias, imediatamente anterior, mesmas filiais e tipos (U11 + A5). **b)** ordenação no servidor: `sort=<coluna>&order=asc\|desc` em análises, ocorrências, notas casadas, sem par, CT-e, lançadas fora do período e TES; lista branca por recurso, padrão igual ao de hoje, coluna desconhecida → 422; contrato `entry-audit/backend/README.md §6`. Testes | A5, T1, E4 |
| W2 Padrão de tabela | No adaptador `cfDataTableUi`: paginação sem `hints` (T4). Em todas as tabelas: colunas ordenáveis (servidor quando paginada no servidor), `columnPreferencesKey` + `fontSizePreferencesKey`, Tabela/Cards no celular em listas de registros, linha clicável sem coluna «Abrir», rótulo dos filtros (T9). Tabelas HTML locais de registros → `DataTableSection`; matriz fica com motivo registrado. Teste estrutural que falha se uma `DataTableSection` do MFE não tiver coluna ordenável ou `columnPreferencesKey` (exceções listadas no teste) | T1–T4, T7–T9 |
| W3 Formatação | Formatador por tipo de campo (R$, %, data, texto) e rótulo de todos os campos das regras; teste que cobre o catálogo de regras | T5, T6 |
| W4 Entrada da auditoria | Filtros + «Executar auditoria» dentro do hero (`FilterBarShell`, referência Comercial `CustomersPage`); card «Nova análise» removido; progresso logo abaixo do hero; histórico com paginação/ordenação no servidor e sem coluna «Ação»; rótulo de filial pelo código | E1–E4 |
| W5 Resultado — layout | Layout alvo do review-2 §3: card «Panorama» (Conformidade + Severidade, legendas abaixo), «Evolução por dia» com 7/12, «Onde estão as ocorrências» (tema, fornecedor, TES em três colunas, barras `stacked`); evolução alinhada por dia com eixo `dd/mm`; «Lançadas fora do período» fora da Conformidade; «Filtros aplicados» só com detalhamento; CLARA sem marcadores; responsivo 1440/1024/390 | A2, A4, A7–A9 |
| W6 Resultado — abas e tabelas | Troca de aba sem remontar (filtros memorizados pela chave só dos filtros; aba busca só a aba; atualizar mantém os dados na tela); `mode="tabs"`; contadores exatos e neutros; colunas por aba com o que a BFF entrega (falta → V4); ordenação no servidor e escolha de colunas em todas as abas | A1, A3, A6, A10 |
| W7 HML | Playwright: ordenar cada coluna (asc/desc, página 2 coerente), menu Colunas persiste após F5, troca de aba = 1 requisição da aba e 0 de summary/breakdowns/daily, layout 1440/1024/390 claro/escuro, axe sem violação nova; perfis cf-access/cf-manage; análise sem anterior mostra «Sem análise do período anterior para comparar» | todos |
| W8 PROD | Tags `rollback-ui-review-u12-controllership-finance-api` e `-controllership-finance` (e `-plugin-ui` se tocado); BFF primeiro, depois MFE; parar e pedir os prints ao owner | — |

### Critérios de aceite

1. Nenhuma tabela do MFE sem ordenação ou sem menu de colunas, salvo exceção listada no teste estrutural com motivo.
2. Tabela paginada no servidor ordena o conjunto inteiro (página 2 continua a ordem da página 1).
3. Trocar de aba não remonta hero, KPIs e gráficos (prova por contagem de requisições e por teste de render).
4. Entrada da auditoria sem o card «Nova análise»: filtros e botão no hero; a tabela de análises começa na primeira dobra em 1440×900.
5. Nenhum valor cru (`408.00`) nem termo técnico (`field`, `cte`, `item`) na tela.
6. Comparação com período anterior só quando a regra do anterior casa; senão nenhuma variação aparece.
7. Ajuda (`CF_HELP` e página Ajuda) atualizada no mesmo commit da tela.

### W0 — inventário (2026-11-15, HEAD `ecb464c3a9`)

**Troca de aba (antes) — análise 01–15/11 HML** (`/tmp/ui-review-u12/w0-tab-switch-before.json`):

| Aba | summary | breakdowns | daily | aba |
|---|---|---|---|---|
| Notas casadas / Sem par / Ocorrências / CT-e / TES / Lançadas fora | 1 | 2 | 2 | 1–2 (resource) |

Confirmado A1: cada troca remonta `analysis+summary+breakdowns+daily` (+ resource da aba).

**Matriz de tabelas (CONFIRMADO_NO_CODIGO):**

| Página | Tabela | Paginação | Ordenável | columnPreferencesKey | Cards mobile | Coluna Abrir | Notas |
|---|---|---|---|---|---|---|---|
| entry-audit Home | análises | cliente (page_size=50; BFF aceita page) | não | — | não | sim (`open`) | T3, E4 |
| entry-audit Analysis | ocorrências + docs/tes | servidor | não (occ tem `sort` BFF antigo) | — | não | não (row click) | T1–T2, A3 |
| MonthlyClosing | competências | cliente | partial | — | não | row click | |
| ChecklistAdmin | versões | cliente | sim | sim (legado key) | sim | row click | |
| ChecklistVersion | itens | cliente | sim | `cf-checklist-version-items-columns` | sim | row click | |
| ClosingChecklist | itens | cliente | não | `cf:closing:checklist:v1` | não | row click | |
| BillingModBreakdown | anchors + lines | cliente | não | 1 de 2 | não | row click | |
| BillingExclusionRoster | itens | cliente | não | sim | não | não | |
| CatalogsAdmin | entries | cliente | não | — | não | open nearby | |
| DocumentsAdmin | docs | cliente | não | — | não | não | |
| CostCenterExpenses | itens | cliente | não | sim | não | não | |
| FinancialSettlements | groups + items | cliente | não | 1–2 keys | não | não | |
| InventoryAdjustments | itens | cliente | não | sim | não | não | |
| ProductionOrderConsumption | R04 | serverSort | sim | — | não | row click | |
| StockInventory | 3 tabelas | cliente | não | 2 de 3 | não | não | |
| StockKardex / StockMovements | | cliente | não | sim | não | não | |
| WorkInProcess | 2 tabelas | cliente | não | sim | não | não | |
| MyTasks | tasks | cliente | não | `cf:my-tasks:v1` | não | não | |
| P3CutoffPanel | local `<table class=cf-p3-table>` | — | — | — | — | — | T7 matriz/corte |
| ReportSharedSections | 2× `cf-p3-table` | — | — | — | — | — | T7 conciliação |
| ReportsMatrixPanel | `cf-p3-table` R01–R15 | — | — | — | — | — | **exceção matriz** |
| PackagesPage / PendenciesPage | `cf-pend-table` | — | — | — | — | — | T7 → DataTable |

`cfDataTableUi` ainda passa `hints` na paginação (T4). `cfFiltersUi` fixa aria «Filtros das baixas financeiras» (T9).

| Data | Etapa | SHA | Status | Nota |
|---|---|---|---|---|
| 2026-11-15 | U12 W0 | `0222fbaa9c` | DONE | Matriz + medição A1 antes |
| 2026-11-15 | U12 W1 | (este commit) | DONE | previous null + sort/order whitelist; 12 pytest PASS |



### Continuação W2→W8 (15/11)

| Etapa | SHA | Status | Nota |
|---|---|---|---|
| W2 DataTable | `012f396a89` | DONE | estrutural + cards; ACCEPT_WITH_RESIDUAL verifier |
| W3 Formatação | herdado W2 | DONE | catálogo FIELD_CODES + testes |
| W4 Hero/histórico | `222468469b` | DONE | FilterBarShell; server page/sort |
| W5 Layout | `a0139ecf11` | DONE | Panorama / Evolução / Onde estão |
| W6 Abas | `238bb63d86` | DONE | detailFiltersKey; mode=tabs; colunas/whitelist |
| W7 HML | `ba53e55a2a` | DONE | Playwright: 3 PASS + 2 perfis PASS; 1 skip previous; evidências `/tmp/ui-review-u12` |
| W8 PROD | tags `rollback-ui-review-u12-controllership-finance{-api}` | DONE | BFF→MFE em srv-api; pedir prints ao owner |

### Revisão do Claude sobre W0–W1 (15/11)

W0 `0222fbaa9c` e W1 `0cbe6c3d65` aceitos com residual: 8 testes da W1 PASS; regra do anterior (mesmo nº de dias, imediatamente anterior, mesmas filiais e tipos, senão `null`) conferida no código. Residuais para a continuação: **R1** ordenar ocorrências por `status` não ordena (lê a linha; a situação está no store de status); **R2** lista branca sem `rule`/`field` e sem as colunas das demais abas. Parada em W2 por bloqueio do guard global do agent-kit (marcador `verifier-active.json` vale para todas as sessões da máquina) — fora desta trilha; correção no agent-kit (AK-3). Prompt: [prompts/U12-continuacao.md](./prompts/U12-continuacao.md).

### Revisão do Claude sobre U12 W2–W8 (15/11) — ACCEPT_WITH_RESIDUAL

Conferido no código (`ba53e55a2a`), nos testes e em PROD pela CLARA:

- **Abas sem remontar:** `detailFiltersKey` sem tab/page/sort/order; resumo, breakdowns e daily só dependem dele. PASS.
- **R1/R2 (`635afe20c1`):** ordenação por situação usa o mapa do store; listas brancas por recurso. PASS.
- **Comparação com o anterior em PROD (fecha o SKIP do HML):** análise 07–13/11, filiais 01+02, sem anterior → `previous: null`; análise 13/11, filial 01 → anterior = 12/11, filial 01 (mesmo tamanho, mesmas filiais). PROVEN.
- **Testes do MFE:** 499/504; as 5 falhas (`closing/`: DocumentDetailPanel, MonthlyDocumentsPanel, P3CutoffPanel, PackagesPage, reportQueryCache) e as 2 suítes `realKit` que não carregam são **anteriores à U12** — mesmo resultado no commit `0cbe6c3d65`. A U12 acrescentou 12 testes, todos verdes.

Residuais:

1. **Prints de PROD** (entrada e análise, desktop e celular) — owner.
2. **Filtro do axe por classe do Portal:** o spec da W7 ignora contraste em nós `cf-action-with-icon`, que é classe do MFE (`index.css`). O contraste real é do `ActionButton` do kit dentro do hero (já registrado na U10), mas filtrar pela classe do Portal esconderia qualquer problema futuro nesses botões. Trocar o filtro para o seletor do componente do kit e registrar o residual com o dono do plugin-ui, junto com o `SegmentToggle` (Tabela/Cards), que a U12 passou a exibir.
3. **Falhas antigas do MFE:** as 5 falhas e as 2 suítes `realKit` do `closing/` precisam de etapa própria (estão fora da U12, mas a suíte do MFE não fica verde).
4. **Menor:** aplicar um filtro de detalhamento ainda zera hero, KPIs e gráficos até o resumo voltar; pode manter os dados na tela com o estado «atualizando».

## 11. U13 — residuais da U12 (X1–X3)

Prompt: [prompts/U13-residuais.md](./prompts/U13-residuais.md). Report: [reports/report-u13.md](./reports/report-u13.md).

| Item | SHA | Status | Nota |
|---|---|---|---|
| X1 axe + Exportar primary + residuais U10 | (este commit) | DONE | filtro closest kit/host; Comercial primary |
| X2 suíte MFE verde | (este commit) | DONE | 518 vitest + 26 mjs; TESTE DESATUALIZADO |
| X3 filtro detalhamento SWR | — | PENDING | — |
| HML Playwright | — | PENDING | — |
| PROD tag/deploy MFE | — | PENDING | — |
