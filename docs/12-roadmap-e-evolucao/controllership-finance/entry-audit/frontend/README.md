# Entry audit · Front-end — índice e convenções

| Campo | Valor |
|---|---|
| Status | **READY** (reconciliado com o contrato publicado da BFF, T9R5 — T10.0) |
| Data | 2026-11-14 |
| Plano | [../plan.md](../plan.md) · back-end [../backend/README.md](../backend/README.md) · MCP [../mcp/README.md](../mcp/README.md) |
| Contrato | rotas `/entry-audit/*` de `controllership-finance-api` (back-end fechado); o que o doc usa e a BFF não entrega foi ajustado no doc — ver «Reconciliação T10.0» |
| Wireframes | [wireframes-auditoria-entradas.html](./wireframes-auditoria-entradas.html) |
| Baseline do kit | `@delpi/plugin-ui` no HEAD `08825074` (props lidas do código) |
| Padrões | [padrão visual dos Portais](../../../../11-padroes-de-desenvolvimento/padrao-visual-portais-minha-delpi.md) · [30 — mapa de reuso do plugin-ui](../../30-plugin-ui-reuse-map.md) |

## Visão geral do dashboard

Wireframes completos: [wireframes-auditoria-entradas.html](./wireframes-auditoria-entradas.html).

```text
TopBar do Portal
PageHero compact ─ título, período, última execução, fontes   [Exportar] [Executar / Reexecutar]
└─ FilterBar
   ├─ Filtros da execução: De, Até, Tipos de documento (NF-e, CT-e), Filiais — os dois filtros de hoje: período e tipo de documento
   └─ Filtros da análise: Severidade, Tema, Fornecedor, TES, Status, Limpar   (na URL; não reexecutam)
ScopeChipBar ─ filtros ativos removíveis
KPIs ×4 ─ Valor conferido (`gross_checked`) · Notas sem divergência (`conformity.clean`) · Ocorrências pendentes (`pending`) · Diferença nas altas (`high_difference`) (Δ vs `previous` quando existe)
Linha: Ocorrências por dia (período × anterior)             |   Conformidade (medidor + legenda clicável)
Linha: Top 8 fornecedores                                    |   Ocorrências por tema (rosca + lista)
Linha: Por severidade | TES com mais ocorrências | Evolução entre análises
SectionCard ─ abas: Ocorrências | Notas casadas | Notas sem par | CT-e | TES usadas
   └─ Pendentes / Resolvidas / Todas · busca · colunas · tabela com Resolver/Reabrir · progresso · paginação
Pergunte à CLARA ─ sugestões prontas
Detalhe da ocorrência ─ painel lateral: valores, por quê, o que fazer, regra, documento (XML; DANFE/DACTE só com LNF), histórico, Resolver
```

Estados: primeiro acesso (sem análise, com «Análises anteriores»), execução em andamento (etapa e contadores de XML por filial, sem percentual), falha parcial (uma filial falhou, a outra concluiu), vazio por filtro. Mobile: KPIs em 2 colunas, gráficos empilhados, filtros num painel, tabela em cards.

Filtros da execução = os dois que o usuário aplica hoje: **período (De/Até, livre)** e **tipos de documento**, mais as filiais (a skill roda uma filial por vez). Filtros da análise = os do painel Raio-X: unidade, severidade, tema, fornecedor, dia (clique no gráfico), status e busca, mais documento (NF-e/CT-e) e TES. Os parâmetros fixos da skill (TES 004 do presumido, final 352 do CFOP de frete) viram configuração da BFF, fora da tela.

### Componentes do `@delpi/plugin-ui` (resumo; parâmetros no doc 04)

Regra: componente novo nasce no `@delpi/plugin-ui`, genérico (sem «auditoria» no nome nem na API), e é importado pelo MFE. Evoluções são aditivas, com os padrões atuais preservados e testes de caracterização antes da mudança.

| Bloco | Componente | Situação | O que falta |
|---|---|---|---|
| Cabeçalho | `PageHero` (compact) | existe | — |
| Período | `DateField` ×2 (De/Até) | existe | — |
| Tipos de documento, filiais | `MultiSelectField` | existe | — |
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
3. Os componentes do kit usados aqui que **ainda não têm adapter** no Portal ganham um, no mesmo arquivo, com prefixo `cf` e `CF_PORTAL_SCOPE`: `CfChartCard`, `CfComparativeAreaChart`, `CfSemicircleProgressGauge`, `CfHorizontalValueBars`, `CfBarSeriesChart`, `CfLineSeriesChart`, `CfScopeChipBar`, `CfUnderlineNav`, `CfTrendDelta`, `CfMultiSelectField`, `CfProgressTracker`, `CfInlineLoadingProgress`, `CfProgressSummaryBar`, `CfDrawerShell`, `CfDetailCard`, `CfEmptyGuidance`, `CfHelpTooltip`, `CfTablePaginationNav`, e os novos do [doc 04](./04-componentes-plugin-ui-novos-e-evolucoes.md). O adapter só injeta `classNames`/`prefix`/`portalScopeClassName`; não muda comportamento.
4. Componente que não existe nasce no `@delpi/plugin-ui`, genérico (sem «auditoria», «NF» ou «Protheus» no nome nem na API), com testes e entrada no catálogo do kit. Evolução de componente existente é **aditiva**: props novas opcionais, padrão igual ao de hoje, testes de caracterização antes.
5. O MFE não calcula regra fiscal nem agrega número de negócio: KPIs, gráficos e contagens chegam prontos da BFF ([back-end §3.4](../backend/README.md)). Só é derivado na UI o que é aritmética de apresentação sobre campos do contrato (lista em «Campos derivados na UI», abaixo). Campo que o contrato não traz **não** é inventado nem calculado no MFE: a coluna/bloco sai do desenho.

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

Filtros que mudam o que se vê ficam na query string, para F5 e link compartilhável (padrão visual §14). Nomes em inglês, valores simples. Os filtros da análise usam os **mesmos nomes dos query params da BFF** (`document_type`, `situation`, …), exceto `severity` (ver mapeamento abaixo):

| Parâmetro (URL do MFE) | Exemplo | Query param da BFF | Página |
|---|---|---|---|
| `from`, `to` | `2026-10-01`, `2026-10-31` | `date_from`, `date_to` (corpo do `POST`) | 01 |
| `branches` | `01,02` | `branches` (corpo do `POST`) | 01 |
| `docs` | `nfe,cte` | `document_types` (corpo do `POST`) | 01 |
| `branch` | `01` \| `all` | `branch` (omitido quando `all`) | 02 |
| `severity` | `high` | `severity` = valor da API em PT (`Alta`) — o MFE mapeia | 02 |
| `theme` | `cte` | `theme` = prefixo do `rule_id` (igual ao da URL) | 02 |
| `supplier` | nome do fornecedor (como em `facets.suppliers[].name`) | `supplier` (busca por trecho no nome) | 02 |
| `tes` | `036` | `tes` | 02 |
| `document_type` | `nfe` \| `cte` | `document_type` | 02 |
| `situation` | `clean` \| `divergent` \| `posted_outside_period` \| `xml_unavailable` (só aba Notas casadas; vazio = recebidas no período) | `situation` | 02 |
| `day` | `2026-10-14` (dia de **recebimento**) | `day` | 02 |
| `status` | `pending` \| `resolved` \| `all` (`all` = sem param) | `status` | 02 |
| `tab` | `occurrences` \| `documents` \| `unmatched` \| `cte` \| `tes` | — (escolhe a rota) | 02 |
| `q`, `page`, `sort` | busca, página e ordenação da tabela; `sort` ∈ `severity` \| `supplier` \| `document` \| `day` (só ascendente) | `q`, `page`, `sort` | 02 |

**Filtro × aba (o servidor ignora o que não se aplica à coleção):** ocorrências aceitam todos; Notas casadas: `branch`, `supplier`, `document_type`, `day`, `situation`, `q`; Notas sem par: `branch`, `severity`, `theme`, `supplier`, `document_type`, `day`, `status`, `situation`, `q`; CT-e: `branch`, `document_type`, `q`; TES usadas: `branch`, `tes`, `document_type`. Na aba em que um filtro não se aplica, o controle fica desabilitado com `hint` («não se aplica a esta aba») e não vira chip. Os KPIs de notas (`gross_checked`, `conformity.clean/divergent`) também só respondem a esses filtros de documento.

### Vocabulário (UX em PT-BR; identificadores em inglês)

| Na tela | No contrato |
|---|---|
| Análise | `analysis` |
| Execução (por filial) | `run` |
| Ocorrência | `occurrence` |
| Notas casadas | `documents` |
| Notas sem par | `unmatched` |
| Severidade: Alta · Depende da TES · Média · Baixa · Info (nota sem par explicada) | **valor da API em PT**: `Alta` · `Depende da TES` · `Média` · `Baixa` · `Info` (`severity` da ocorrência, de `facets.severities[].name` e de `breakdowns.by_severity[].name`) |
| Tema: Cabeçalho · Itens · Coerência fiscal · Simples e presumido · Livro fiscal · CT-e (frete) · Chave · Sem par | prefixo do `rule_id` (campo `theme`): `header` · `item` · `coherence` · `simples` · `fiscal_book` · `cte` · `key` · `unmatched` |
| Situação da nota casada: Sem divergência · Com divergência · Lançada fora do período · XML indisponível | `documents[].situation`: `clean` · `divergent` · `posted_outside_period` · `xml_unavailable` |
| Execução (etapa) | `runs[].stage`: `reading_protheus` · `reading_xml` · `auditing` · `saving` · `done` · `partial` · `failed`; vazio na fila e `reading` por instantes ao iniciar — o MFE trata estágio desconhecido como «Preparando» |

**Mapeamento de severidade (MFE).** A URL do MFE pode continuar em inglês (`severity=high`), mas a BFF só entende o valor em PT. O MFE traduz nos dois sentidos com **uma tabela única** (`high`↔`Alta`, `tes_dependent`↔`Depende da TES`, `medium`↔`Média`, `low`↔`Baixa`, `info`↔`Info`) antes de montar o query param e ao ler `facets`/`breakdowns`. Valor desconhecido → exibido como veio, tom `neutral`. **Tema** não tem tabela de contrato: o `name` de `facets.themes`/`breakdowns.by_theme` é o prefixo do `rule_id`; o rótulo em PT-BR é conteúdo/locale do MFE e prefixo novo cai no próprio prefixo como rótulo.

Mapa de cores de severidade (tokens do kit, nunca hex no MFE): Alta → `danger`; Depende da TES → `info`; Média → `warning`; Baixa → `neutral`; Info → `neutral`; sem divergência → `success`. A severidade sempre aparece com texto, nunca só com cor.

### Campos derivados na UI (únicos permitidos)

| Derivado | Fórmula (sobre campos do contrato) | Observação |
|---|---|---|
| % do medidor de conformidade | `conformity.clean / (clean + divergent)` | `unmatched_*` e `posted_outside_period` ficam fora do denominador; sem notas → «—» |
| Δ dos KPIs | `kpis.x` vs `previous.x` (valor e %) | `previous` vem zerado quando não há análise anterior: com `previous.documents = 0` e `previous.occurrences = 0` o delta não é exibido. «Notas sem divergência» não tem delta (`previous` não traz `clean`) |
| Dias sem ocorrência no gráfico | preencher com 0 os dias de `daily.period` ausentes em `series` | `series`/`previous` só trazem dias com `count > 0`; o anterior alinha por posição do dia no período |
| % de resolvidas (barra) | `kpis.resolved / (kpis.pending + kpis.resolved)` | no recorte atual |
| Texto de andamento | `counts.xml_read` de `counts.xml_expected` | sem percentual da BFF; barra só indeterminada ou razão lida/esperada |
| Rótulo de tema, severidade e evento | tabelas de locale do MFE | ver mapeamento acima |
| Navegar anterior/próxima no detalhe | ordem da página de `occurrences` já carregada | a BFF não devolve `prev_key`/`next_key` |
| «Onde está» (sem par) | lista: `side` (`xml` → «Só no XML», `protheus` → «Só no Protheus»); detalhe: `rule_id` `unmatched.xml_only` / `unmatched.protheus_only` | só rótulo; sem regra |

### Acessibilidade (todas as páginas)

Headings em ordem (`h1` no PageHero; `h2` nos cards); todo controle com rótulo; tudo operável por teclado com foco visível; filtros cruzados também acessíveis por teclado (Enter/Espaço); `Esc` limpa os filtros da análise; anúncios de estado em `aria-live="polite"`; gráficos com `aria-label` descrevendo o dado e a tabela como alternativa textual; contraste nos temas claro e escuro.

## Reconciliação T10.0

Doc de 13/11 × contrato publicado da BFF em 14/11 (pós T9R5; back-end fechado, sem `DECISION_REQUIRED`). Fonte: rotas `/entry-audit/*` (`router.py` + `EntryAuditService`). **MATCH** = o doc já refletia o contrato; **DOC_DRIFT** = o doc foi ajustado ao contrato (a BFF não muda).

| # | Tema | Contrato publicado | Decisão |
|---|---|---|---|
| 1 | KPIs | `kpis.gross_checked`, `high_difference`, `pending`, `resolved`, `high`, `documents`; «sem divergência» = `conformity.clean`; `previous` com os mesmos campos de `kpis` | DOC_DRIFT (`checked_amount`/`high_amount` renomeados; sem delta em «sem divergência») |
| 2 | Conformidade | `clean`, `divergent`, `unmatched_open`, `unmatched_explained`, `posted_outside_period {count, by_date[{date,count}]}`; sem `no_divergence_pct` | DOC_DRIFT (% derivado no MFE; fora do período = informação `neutral`, fora de «a resolver») |
| 3 | Notas casadas | `situation`: `clean` \| `divergent` \| `posted_outside_period` (+ `xml_unavailable`); padrão = recebidas no período; `comparison.gross` é valor Protheus | DOC_DRIFT («Total XML» → «Total»; sem UF) |
| 4 | Sem par | linha com `side`, `severity`, `reason`, `party_*`, `amount`, ICMS/IPI, `cfop`, `cst`, `nature`, `lnf_request_id`, `links`; sem `status` na linha; sem `GET unmatched/{key}` | DOC_DRIFT (detalhe via `occurrences/{key}`; toggle sem «Todas») |
| 5 | Ocorrência (lista) | `stable_key`, `rule_id`, `rule_name`, `severity`, `theme`, `title`, `document_number`, `series`, `supplier_name`, `item`, `field`, `field_label`, `*_value`, `difference` (null em campo de código), `tes`, `why`, `action`, `access_key`, `status`; sem `issue_date`/`branch` | DOC_DRIFT (colunas Emissão e Unidade saem; `reason` → `why`) |
| 6 | Ocorrência (detalhe) | forma plana + `history[{event,at,actor}]` + `links{xml,danfe,dacte}`; sem `values[]`, `rule`, `document`, `prev_key`/`next_key` | DOC_DRIFT |
| 7 | Andamento | `runs[].stage`, `documents_read`, `xml_downloaded`, `counts.xml_read`/`xml_expected`; sem `progress.percent` | DOC_DRIFT (percentual removido) |
| 8 | Criar análise | `POST` → 202 `{id, status, created}`; `options` com `label` | DOC_DRIFT (`{analysis}` → `{id,status,created}`) |
| 9 | Por dia e tendência | `daily {series, previous, period}` com `{name,count}`; `trend {points[], months[]}` por análise (`date_from`,`date_to`,`branches`,`documents`,`occurrences`,`high`,`pending`,`resolved`) | DOC_DRIFT (conta ocorrências por dia de **recebimento**, não notas por emissão) |
| 10 | Breakdowns e facets | `by_severity`, `by_theme`, `suppliers`, `tes` (`{name,count}`); facets `suppliers`, `themes`, `tes`, `severities` | DOC_DRIFT (`severity`→`severities`; fornecedor só nome; TES só código) |
| 11 | Severidade/tema | severidade em PT (`Alta`…); tema = prefixo do `rule_id` | DOC_DRIFT (URL do MFE pode ficar EN com mapeamento) |
| 12 | CT-e e TES | CT-e: `comparison` com emitente, tomador, CFOP, CST, base, alíquota, ICMS, `tes`, `linked_documents` (sem `fiscal_code`); TES: campos em `sf4.*`, sem alerta | DOC_DRIFT (colunas «Direito ao crédito», «Emissão» e «Alerta» saem) |
| 13 | Ordenação e export | `sort` ∈ `severity`\|`supplier`\|`document`\|`day`, só ascendente; export `.xlsx`; XML em `/entry-audit/xml/{chave}` | MATCH (export) · DOC_DRIFT (`sort`, sem direção) |
| 14 | Autorização e endpoints | `controllership-finance.access` (manage herda); `resolve`/`reopen` em `/occurrences/{key}` e `/unmatched/{key}`; envelope `meta.branches_unavailable` | MATCH |
