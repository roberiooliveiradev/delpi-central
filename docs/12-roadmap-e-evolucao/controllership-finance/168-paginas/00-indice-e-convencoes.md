# 168 · Páginas da Auditoria de entradas — índice e convenções

| Campo | Valor |
|---|---|
| Status | **DESIGN_DRAFT** (aguarda aprovação do owner) |
| Data | 2026-11-13 |
| Plano | [168 — Auditoria de entradas](../168-auditoria-entradas-protheus-xml-portal-clara.md) |
| Wireframes | [168-anexos/wireframes-auditoria-entradas.html](../168-anexos/wireframes-auditoria-entradas.html) |
| Baseline do kit | `@delpi/plugin-ui` no HEAD `08825074` (props lidas do código) |
| Padrões | [padrão visual dos Portais](../../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md) · [30 — mapa de reuso do plugin-ui](../30-plugin-ui-reuse-map.md) |

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
5. O MFE não calcula regra fiscal nem agrega número: KPIs, gráficos e contagens chegam prontos da BFF ([§4A.4 do plano](../168-auditoria-entradas-protheus-xml-portal-clara.md)).

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
