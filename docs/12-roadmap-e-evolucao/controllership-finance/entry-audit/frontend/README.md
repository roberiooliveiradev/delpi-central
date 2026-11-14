# Entry audit · Front-end — índice e convenções

| Campo | Valor |
|---|---|
| Status | **DESIGN_DRAFT** (aguarda aprovação do owner) |
| Data | 2026-11-13 |
| Plano | [../plan.md](../plan.md) · back-end [../backend/README.md](../backend/README.md) · MCP [../mcp/README.md](../mcp/README.md) |
| Wireframes | [wireframes-auditoria-entradas.html](./wireframes-auditoria-entradas.html) |
| Baseline do kit | `@delpi/plugin-ui` no HEAD `08825074` (props lidas do código) |
| Padrões | [padrão visual dos Portais](../../../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md) · [30 — mapa de reuso do plugin-ui](../../30-plugin-ui-reuse-map.md) |

## Visão geral do dashboard

Wireframes completos: [wireframes-auditoria-entradas.html](./wireframes-auditoria-entradas.html).

```text
TopBar do Portal
PageHero compact ─ título, período, última execução, fontes   [Exportar] [Executar / Reexecutar]
└─ FilterBar
   ├─ Filtros da execução: Período (preset + De/Até), Data de referência, Filiais, Documentos, Parâmetros avançados
   └─ Filtros da análise: Severidade, Tema, Fornecedor, TES, Status, Limpar   (na URL; não reexecutam)
ScopeChipBar ─ filtros ativos removíveis
KPIs ×4 ─ Valor conferido · Notas sem divergência · Ocorrências pendentes · Diferença nas altas (com Δ vs período anterior)
Linha: Notas com divergência por dia (período × anterior)   |   Conformidade (medidor + legenda clicável)
Linha: Top 8 fornecedores                                    |   Ocorrências por tema (rosca + lista)
Linha: Por severidade | TES com mais ocorrências | Evolução entre análises
SectionCard ─ abas: Ocorrências | Notas casadas | Notas sem par | CT-e | TES usadas
   └─ Pendentes / Resolvidas / Todas · busca · colunas · tabela com Resolver/Reabrir · progresso · paginação
Pergunte à CLARA ─ sugestões prontas
Detalhe da ocorrência ─ painel lateral: valores, por quê, o que fazer, regra, documentos, Resolver
```

Estados: primeiro acesso (sem análise, com «Análises anteriores»), execução em andamento (etapas e progresso por filial), falha parcial (uma filial falhou, a outra concluiu), vazio por filtro. Mobile: KPIs em 2 colunas, gráficos empilhados, filtros num painel, tabela em cards.

Filtros vindos da skill e do painel: período (no lugar da competência fixa), filiais (matriz/filial, consolidado), severidade, tema, fornecedor, dia (clique no gráfico), status (pendente/resolvida), busca, mais tipo de documento e TES. Os parâmetros da skill (`--tes-presumido 004`, `--cfop-frete 352`) ficam em «Parâmetros avançados» com o padrão preenchido. `--cnpj`, `--uf` e `--filial` deixam de existir para o usuário: vêm do cadastro das filiais.

### Componentes do `@delpi/plugin-ui` (resumo; parâmetros no doc 04)

Regra: componente novo nasce no `@delpi/plugin-ui`, genérico (sem «auditoria» no nome nem na API), e é importado pelo MFE. Evoluções são aditivas, com os padrões atuais preservados e testes de caracterização antes da mudança.

| Bloco | Componente | Situação | O que falta |
|---|---|---|---|
| Cabeçalho | `PageHero` (compact) | existe | — |
| Período | **`PeriodRangeFilter`** = `QuickPeriodSelector` + `DateField` ×2 | **novo** | composto genérico: preset + De/Até + rótulo da data de referência |
| Filtros | `FilterBar`, `FiltersRow`, `FilterSelectField`, `MultiSelectField`, `ClearFiltersButton` | existe | — |
| Filtros ativos | `ScopeChipBar` | evoluir | `onRemove` por chip e «Limpar tudo» |
| KPIs | `MetricKpiCard` + `TrendDelta` | existe | — |
| Por dia | `ChartCard` + `ComparativeAreaChart` | evoluir | `onPointSelect` e `selectedName` (clique no dia) |
| Conformidade | `SemicircleProgressGauge` | evoluir | legenda clicável |
| Top fornecedores / TES | `HorizontalValueBars` | evoluir | `tone` por item e item selecionado |
| Por tema | **`DistributionDonut`** (sobre `ChartSeriesPie`) | **novo** | rosca + lista com contagem/% e seleção |
| Severidade | `HorizontalValueBars` | evoluir | mesma evolução (tom e seleção), para filtrar por clique |
| Evolução | `LineSeriesChart` | existe | — |
| Abas e status | `UnderlineNav`, `SegmentToggle` | existe | — |
| Tabelas | `DataTableSection`, `StatusBadge`, `TablePaginationNav`, `DataRecordCard` (mobile) | existe | — |
| Resolver na linha | **`ResolutionStatusCell`** | **novo** | Resolver / «✓ data» / Reabrir, acessível, com estado de envio |
| Progresso resolvido | `ProgressSummaryBar` | existe | — |
| Execução | `StateBanner`, `ProgressTracker`, `InlineLoadingProgress` | existe | — |
| Detalhe | `DrawerShell`, `DetailCard`, `HelpTooltip` | existe | — |
| Vazio | `EmptyGuidance` | existe | — |

## Documentos

| Doc | Página | Rota no MFE (`/apps/controllership-finance/…`) |
|---|---|---|
| [01](./01-pagina-entrada-e-execucao.md) | Entrada e execução | `entry-audit` |
| [02](./02-pagina-dashboard-da-analise.md) | Dashboard da análise | `entry-audit/analyses/:analysisId` |
| [03](./03-pagina-detalhe-da-ocorrencia.md) | Detalhe da ocorrência (painel lateral; página inteira no mobile) | `entry-audit/analyses/:analysisId/occurrences/:occurrenceKey` |
| [04](./04-componentes-plugin-ui-novos-e-evolucoes.md) | Componentes novos e evoluções no `@delpi/plugin-ui` (parâmetros) | — |

Cada documento de página traz: objetivo, rota e estado na URL, dimensionamento por faixa de largura, a árvore de componentes, cada componente com as props que serão passadas, a origem dos dados (rota da BFF), os estados (carregando, vazio, erro, parcial) e a acessibilidade.

## Regras comuns

### Componentes

1. Tudo vem do `@delpi/plugin-ui`. Nenhum componente visual é recriado no MFE.
2. O MFE usa os **adapters `Cf*`** de `plugins/controllership-finance/src/app/controllershipFinanceUi.ts` quando existem (`CfPageHero`, `CfMetricKpiCard`, `CfSectionCard`, `CfStateBanner`, `CfStatusBadge`, `CfSegmentToggle`, `CfDateField`, `CfSelectField`, `CfPagePath`, `CfEmptyState`, `CfDialog`) e o kit de filtros de `cfFiltersUi.ts` e de tabela de `cfDataTableUi.tsx`.
3. Os componentes do kit usados aqui que **ainda não têm adapter** no Portal ganham um, no mesmo arquivo, com prefixo `cf` e `CF_PORTAL_SCOPE`: `CfChartCard`, `CfComparativeAreaChart`, `CfSemicircleProgressGauge`, `CfHorizontalValueBars`, `CfBarSeriesChart`, `CfLineSeriesChart`, `CfScopeChipBar`, `CfUnderlineNav`, `CfTrendDelta`, `CfMultiSelectField`, `CfQuickPeriodSelector`, `CfProgressTracker`, `CfInlineLoadingProgress`, `CfProgressSummaryBar`, `CfDrawerShell`, `CfDetailCard`, `CfEmptyGuidance`, `CfHelpTooltip`, `CfTablePaginationNav`, e os novos do [doc 04](./04-componentes-plugin-ui-novos-e-evolucoes.md). O adapter só injeta `classNames`/`prefix`/`portalScopeClassName`; não muda comportamento.
4. Componente que não existe nasce no `@delpi/plugin-ui`, genérico (sem «auditoria», «NF» ou «Protheus» no nome nem na API), com testes e entrada no catálogo do kit. Evolução de componente existente é **aditiva**: props novas opcionais, padrão igual ao de hoje, testes de caracterização antes.
5. O MFE não calcula regra fiscal nem agrega número: KPIs, gráficos e contagens chegam prontos da BFF ([back-end §3.4](../backend/README.md)).

### Dimensionamento

Valores do padrão visual (§18) e dos tokens já usados no Portal (`--cf-section-gap: 24px`, `--cf-grid-gap: 16px`).

| Faixa | Nome | Comportamento |
|---|---|---|
| `> 1100px` | desktop | grades completas |
| `≤ 1100px` | desktop estreito | grades de 4 viram 2; linhas 2:1 viram 1:1 |
| `≤ 900px` | tablet | gráficos e painéis lado a lado empilham |
| `≤ 768px` | mobile | filtros num painel (`DrawerShell`); tabelas em cards; detalhe em página inteira |
| `≤ 480px` | mobile estreito | uma coluna em tudo |

| Medida | Valor |
|---|---|
| Largura máxima do conteúdo | a do shell do Portal (sem `max-width` local) |
| Padding da página | `clamp(16px, 2vw, 28px)` (shell) |
| Espaço entre seções | `var(--cf-section-gap)` = 24px; 12px no mobile |
| Espaço na grade | `var(--cf-grid-gap)` = 16px; 8–10px no mobile |
| Alvo de toque | ≥ 44px |

### Estado na URL

Filtros que mudam o que se vê ficam na query string, para F5 e link compartilhável (padrão visual §14). Nomes em inglês, valores simples:

| Parâmetro | Exemplo | Página |
|---|---|---|
| `from`, `to` | `2026-10-01`, `2026-10-31` | 01 |
| `preset` | `last_month` | 01 |
| `basis` | `received` | 01 |
| `branches` | `01,02` | 01 |
| `docs` | `nfe,cte` | 01 |
| `branch` | `01` \| `all` | 02 |
| `severity` | `high` | 02 |
| `theme` | `cte` | 02 |
| `supplier` | código do fornecedor | 02 |
| `tes` | `036` | 02 |
| `docType` | `nfe` \| `cte` | 02 |
| `day` | `2026-10-14` | 02 |
| `status` | `pending` \| `resolved` \| `all` | 02 |
| `tab` | `occurrences` \| `documents` \| `unmatched` \| `cte` \| `tes` | 02 |
| `q`, `page`, `sort` | busca, página e ordenação da tabela | 02 |

### Vocabulário (UX em PT-BR; identificadores em inglês)

| Na tela | No contrato |
|---|---|
| Análise | `analysis` |
| Execução (por filial) | `run` |
| Ocorrência | `occurrence` |
| Notas casadas | `documents` |
| Notas sem par | `unmatched` |
| Severidade: Alta · Depende da TES · Média · Baixa | `high` · `tes_dependent` · `medium` · `low` |
| Tema: ICMS · IPI · CFOP · CST e origem · Simples e presumido · CT-e (frete) · Chave e cadastro · Valores e datas · Livro fiscal | `icms` · `ipi` · `cfop` · `cst_origin` · `simples` · `cte` · `key_registry` · `values_dates` · `fiscal_book` |

Mapa de cores de severidade (tokens do kit, nunca hex no MFE): Alta → `danger`; Depende da TES → `info`; Média → `warning`; Baixa → `neutral`; sem divergência → `success`. A severidade sempre aparece com texto, nunca só com cor.

### Acessibilidade (todas as páginas)

Headings em ordem (`h1` no PageHero; `h2` nos cards); todo controle com rótulo; tudo operável por teclado com foco visível; filtros cruzados também acessíveis por teclado (Enter/Espaço); `Esc` limpa os filtros da análise; anúncios de estado em `aria-live="polite"`; gráficos com `aria-label` descrevendo o dado e a tabela como alternativa textual; contraste nos temas claro e escuro.
