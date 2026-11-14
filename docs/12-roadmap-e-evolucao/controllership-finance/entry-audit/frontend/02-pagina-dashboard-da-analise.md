# Entry audit · Front-end · Página 02 — Dashboard da análise

| Campo | Valor |
|---|---|
| Rota | `/apps/controllership-finance/entry-audit/analyses/:analysisId` |
| Família visual | analítica / indicadores (padrão visual §9.3) |
| Permissão | `controllership-finance.access` (resolver e reabrir inclusos) |
| Wireframe | seção 1 do [HTML](./wireframes-auditoria-entradas.html) |

## 1. Objetivo

Mostrar o resultado de uma análise (período + filiais) e permitir o acompanhamento: o que pede ação, onde se concentra, como evoluiu, e marcar o que já foi resolvido. Tudo o que aparece aqui a CLARA também lê pelas mesmas rotas.

Dois grupos de filtro:
- **filtros da execução** (período, filiais, documentos): mostrados como resumo no PageHero; mudar algum leva à página 01 com os campos preenchidos (pede nova execução);
- **filtros da análise** (unidade, severidade, tema, fornecedor, TES, tipo, dia, status, busca): recortam o resultado sem reexecutar e ficam na URL.

## 2. Estado na URL

`branch`, `severity`, `theme`, `supplier`, `tes`, `docType`, `day`, `status`, `tab`, `q`, `page`, `sort`. Padrão: `branch=all` (se a análise tem mais de uma filial), `status=pending`, `tab=occurrences`. `Esc` limpa os filtros da análise (exceto `tab`).

## 3. Estrutura e dimensionamento

```text
PagePath: Auditoria de entradas › 01/10–31/10/2026
┌ PageHero (compact) ───────────────────────────────────────────────────────────────┐
│ Controladoria · Fiscal                                [⤓ Exportar] [▶ Reexecutar] │
│ h1 Auditoria de entradas                                                           │
│ Matriz e Filial · 01/10/2026 a 31/10/2026 (recebimento)                            │
│ Última execução 13/11 22:10 por Michael · 2 min 14 s · Fontes: SF1 SD1 SF4 SFT XML │
│ ┌ FilterBar: Unidade ▾ Severidade ▾ Tema ▾ Fornecedor ▾ TES ▾ Documento ▾  Limpar ┐ │
└───────────────────────────────────────────────────────────────────────────────────┘
ScopeChipBar ─ filtros ativos (removíveis) · Limpar tudo
[A] KPI │ KPI │ KPI │ KPI
[B] Divergências por dia (ComparativeAreaChart) 1.7fr │ Conformidade (Gauge) 1fr
[C] Top 8 fornecedores (HorizontalValueBars) 1fr      │ Ocorrências por tema (DistributionDonut) 1fr
[D] Por severidade │ TES com mais ocorrências │ Evolução entre análises
[E] SectionCard: UnderlineNav (5 abas) → SegmentToggle + busca → DataTableSection
[F] Pergunte à CLARA
```

| Linha | > 1100px | ≤ 1100px | ≤ 900px | ≤ 768px | ≤ 480px |
|---|---|---|---|---|---|
| A — KPIs | 4 colunas (`repeat(4, minmax(0,1fr))`) | 2 colunas | 2 colunas | 2 colunas | 1 coluna |
| B — dia + conformidade | `minmax(0,1.7fr) minmax(0,1fr)` | `1fr 1fr` | empilha | empilha | empilha |
| C — fornecedores + tema | `1fr 1fr` | `1fr 1fr` | empilha | empilha | empilha |
| D — três gráficos | `repeat(3, 1fr)` | `1fr 1fr` (o 3º desce) | empilha | empilha | empilha |
| E — tabela | largura total | largura total | largura total | cards | cards |

| Medida | Valor |
|---|---|
| Altura do gráfico por dia | 260px (desktop), 200px (≤ 768px) |
| Tamanho do medidor | `size={200}`; 168 no mobile |
| Altura do top fornecedores | 8 itens, ~32px cada (sem rolagem) |
| Rosca | 200px de diâmetro; lista ao lado (> 900px) ou abaixo |
| Gráficos da linha D | 220px |
| Página da tabela | 25 linhas (`pageSize`) |
| Gaps | `var(--cf-section-gap)` entre linhas; `var(--cf-grid-gap)` dentro de cada linha |

## 4. Componentes

### 4.1 `CfPagePath` (← `PagePath`) — existe

`back={{label:"Auditoria de entradas", href:"…/entry-audit"}}`, `current="01/10–31/10/2026"`, `size="sm"`.

### 4.2 `CfPageHero` (← `PageHero`) — existe

| Prop | Valor |
|---|---|
| `density` | `"compact"` |
| `eyebrow` | `"Controladoria · Fiscal"` |
| `title` | `"Auditoria de entradas"` |
| `description` | «Matriz e Filial · 01/10/2026 a 31/10/2026 (recebimento)» |
| `badge` | `CfStatusBadge` do status da análise (`success` Concluída · `warning` Parcial — uma filial falhou · `info` Em andamento) |
| `actions` | `CfActionButton` «Exportar planilha» (secundário, `GET …/export`); `CfActionButton` «Reexecutar» (primário, `POST …/rerun`, confirmação em `CfDialog`: «Reexecutar substitui o resultado. O que já foi marcado como resolvido continua resolvido.») ; `CfActionButton` «Alterar período» (link para a página 01 com os filtros preenchidos) |
| `highlights` | não usa (os números ficam nos KPIs) |
| `children` | linha de metadados (texto `sm`: última execução, duração, quem pediu; chip «Fontes ao vivo: SF1 · SD1 · SF4 · SFT · XML») + `FilterBar` (4.3) |

### 4.3 `FilterBar` dos filtros da análise (← `createDashboardFiltersKit`) — existe

`ariaLabel="Filtros da análise"`, `variant="extended"`, `compact`, `trailing` = `ClearFiltersButton` («Limpar filtros», `disabled` sem filtro ativo).

| Campo | Componente | Props |
|---|---|---|
| Unidade | `CfSegmentToggle` | `options=[Consolidado, Matriz, Filial]` (só quando a análise tem mais de uma filial), `size="sm"`, `ariaLabel="Unidade"` |
| Severidade | `FilterSelectField` | `options` de `facets.severity` com contagem no rótulo («Alta (22)»), `placeholderOption="Todas"` |
| Tema | `FilterSelectField` | `options` de `facets.theme`, `placeholderOption="Todos"` |
| Fornecedor | `FilterSelectField` | `options` de `facets.supplier` (nome + UF), `searchable`, `placeholderOption="Todos"` |
| TES | `FilterSelectField` | `options` de `facets.tes` («036 — Frete s/ vendas»), `searchable` |
| Documento | `FilterSelectField` | `options=[NF-e, CT-e]` (só os tipos da análise) |

O dia e o status não estão na barra: o dia vem do clique no gráfico (4.6) e o status do `SegmentToggle` da tabela (4.12). Todos aparecem nos chips (4.4).

### 4.4 `CfScopeChipBar` (← `ScopeChipBar`) — **evoluir** (doc 04 §3)

| Prop | Valor |
|---|---|
| `label` | `"Filtros ativos"` |
| `chips` | um por filtro ativo: `{id:"severity", label:"Severidade: Alta", onRemove}` … e o dia: `{id:"day", label:"Dia: 14/10", onRemove}` |
| `onClearAll` (novo) | limpa os filtros da análise |
| `clearAllLabel` (novo) | `"Limpar tudo"` |

Sem filtro ativo: a barra mostra a dica «Clique num card, num dia, num fornecedor ou num tema para filtrar a página inteira.»

### 4.5 KPIs — `CfMetricKpiCard` (← `MetricKpiCard`) + `CfTrendDelta` — existem

Dados: `GET …/summary`. Os quatro cards aceitam clique (`onSelect`) e teclado.

| Card | `label` | `value` | `hint` | `tone` / `status` | `onSelect` |
|---|---|---|---|---|---|
| Valor conferido | «Valor conferido» | `money(summary.checked_amount)` | «612 notas casadas» + `CfTrendDelta value={delta_pct}` | `default` | aba Notas casadas, `status=all` |
| Notas sem divergência | «Notas sem divergência» | `548` | «89,5% das casadas» + delta em p.p. | `positive` | aba Notas casadas, filtro «sem divergência» |
| Ocorrências pendentes | «Ocorrências pendentes» (ou «Pendentes (alta)» com severidade filtrada) | `97` | «31 resolvidas» + delta (queda = bom) | `warning` se > 0 | aba Ocorrências, `status=pending` |
| Diferença nas altas | «Diferença nas altas» | `money(summary.high_amount)` | «22 ocorrências altas» | `negative` se > 0 | `severity=high` |

`titleHint` de cada card explica a conta (ex.: «Soma das diferenças em R$ das ocorrências de severidade Alta, pendentes, no recorte atual.»). `fitValue` ligado. Erro ou indisponível vira «—» com `status={label:"Indisponível", tone:"neutral"}`, nunca zero.

### 4.6 Divergências por dia — `CfChartCard` + `CfComparativeAreaChart` — existe, **evoluir** o gráfico (doc 04 §6)

`CfChartCard`: `title="Notas com divergência por dia"`, `hint="Período selecionado × período anterior de mesmo tamanho, pela data de emissão. Clique num dia para filtrar."`, `titleLevel={2}`.

`CfComparativeAreaChart` (dados `GET …/daily`):

| Prop | Valor |
|---|---|
| `data` | `[{name:"01", current: 3, previous: 5}, …]` um ponto por dia do período |
| `series` | `[{dataKey:"current", name:"01/10–31/10", color: token primário}, {dataKey:"previous", name:"Período anterior", color: token secundário, fillOpacity:0}]` |
| `height` | 260 / 200 |
| `valueFormatter` | inteiro pt-BR |
| `smooth` | `true` |
| `emptyMessage` | «Sem notas no período.» |
| `onPointSelect` (novo) | `(point) => setFilter("day", point.name)` |
| `selectedName` (novo) | o dia filtrado, destacado |

### 4.7 Conformidade — `CfSemicircleProgressGauge` — existe, **evoluir** (doc 04 §4)

| Prop | Valor |
|---|---|
| `value` | `summary.no_divergence_pct` |
| `max` | 100 |
| `unit` | `"%"` |
| `centerLabel` | `"sem divergência"` |
| `tone` | `success` ≥ 90 · `warning` 70–90 · `danger` < 70 |
| `size` | 200 / 168 |
| `legend` | `[{id:"ok",label:"Sem divergência",count:548,tone:"success"}, {id:"div",label:"Com divergência",count:64,tone:"warning"}, {id:"unmatched_action",label:"Sem par a resolver",count:11,tone:"danger"}, {id:"unmatched_info",label:"Sem par explicadas",count:37,tone:"neutral"}]` |
| `onLegendSelect` (novo) | abre a aba correspondente (Notas casadas com filtro, ou Notas sem par «a resolver»/«explicadas») |

Dentro de `CfChartCard title="Conformidade" hint="Notas casadas entre Protheus e XML"`.

### 4.8 Top 8 fornecedores — `CfHorizontalValueBars` — existe, **evoluir** (doc 04 §5)

`CfChartCard`: `title="Top 8 fornecedores"`, `hint="Por número de ocorrências. A cor indica a parte das notas do fornecedor com divergência."`, `headerActions` = legenda curta («até 20% · 20–50% · acima de 50%»).

| Prop | Valor |
|---|---|
| `items` | `breakdowns.suppliers.slice(0,8)` → `{id: código, label: nome, meta: UF, value: ocorrências, valueLabel:"14 · 3 altas", tone}` |
| `tone` por item (novo) | `success` ≤ 20% · `warning` 20–50% · `danger` > 50% das notas com divergência |
| `selectedId` (novo) | fornecedor filtrado |
| `onItemClick` | `setFilter("supplier", item.id)` (clique de novo tira o filtro) |
| `layout` | `"stacked"` |
| `emptyMessage` | «Nenhuma ocorrência nesta seleção.» |

### 4.9 Ocorrências por tema — **`CfDistributionDonut`** — novo (doc 04 §1)

`CfChartCard`: `title="Ocorrências por tema"`, `hint="Clique para filtrar."`.

| Prop | Valor |
|---|---|
| `items` | `breakdowns.themes` → `{id:"cte", label:"CT-e (frete)", value: 31, tone:"chart-3"}` |
| `selectedId` | tema filtrado |
| `onSelect` | `setFilter("theme", id)` |
| `centerValue` / `centerLabel` | total ou o do tema selecionado; «ocorrências» |
| `size` | 200 |
| `legendPlacement` | `"side"` (> 900px) / `"below"` |
| `showPercent` | `true` |

### 4.10 Linha D — três gráficos — existem

| Card (`CfChartCard`) | Componente | Props |
|---|---|---|
| «Por severidade» | `CfHorizontalValueBars` (não `BarSeriesChart`: precisa de clique) | `items` = 4 severidades com `tone` do mapa de cores, `onItemClick` → `severity`, `selectedId` |
| «TES com mais ocorrências» | `CfHorizontalValueBars` | `items` = top 6 TES `{label:"036 — Frete s/ vendas", meta:"crédito × livro desencontrados" quando houver alerta}`, `onItemClick` → `tes` |
| «Evolução entre análises» | `CfLineSeriesChart` | `points` de `GET /entry-audit/trend` (pendentes e altas por mês das análises anteriores do mesmo recorte de filiais), `seriesList` = [Pendentes, Altas], sem interação; `emptyMessage="Precisa de pelo menos duas análises para mostrar a evolução."` |

### 4.11 Abas — `CfSectionCard` + `CfUnderlineNav` — existem

`CfSectionCard`: `title` oculto (as abas são o título), `fill`.

`CfUnderlineNav`: `mode="tabs"`, `activeId={tab}`, `items`:

| `id` | `label` | `count` |
|---|---|---|
| `occurrences` | Ocorrências | pendentes no recorte |
| `documents` | Notas casadas | total |
| `unmatched` | Notas sem par | a resolver |
| `cte` | CT-e | total |
| `tes` | TES usadas | total |

### 4.12 Tabela — `DataTableSection` (cfDataTableUi) + `CfSegmentToggle` + **`CfResolutionStatusCell`** — existe / novo (doc 04 §2)

Comum às abas:

| Prop | Valor |
|---|---|
| `toolbarLeading` | `CfSegmentToggle` de status: aba Ocorrências [Pendentes · Resolvidas (n) · Todas]; Notas casadas [Todas · Sem divergência · Com divergência]; Notas sem par [A resolver · Resolvidas (n) · Explicadas · Todas]. `size="sm"` |
| `serverPagination` | `{page, pageSize: 25, total, onPageChange}` |
| `serverSort` | `{sortKey, sortDirection, onSortChange}` |
| `serverSearch` | `{value: q, onChange}` com `searchPlaceholder="Buscar NF, fornecedor, ocorrência…"` |
| `columnPreferencesKey` | `"cf-entry-audit-<aba>"` |
| `fontSizePreferencesKey` | `"cf-entry-audit"` |
| `onRowClick` | abre o detalhe (doc 03) — aba Ocorrências e Notas sem par |
| `tableLayout` | `"scroll"` |

Rodapé (abas com status): `CfProgressSummaryBar` `value={resolvidas/total*100}`, `label="Resolvidas"`, `summary="31 de 128 resolvidas"`.

**Aba Ocorrências** (`GET …/occurrences`)

| `key` | `header` | `render` | Observação |
|---|---|---|---|
| `status` | Status | `CfResolutionStatusCell` (`interactive`) | resolve/reabre sem abrir o detalhe |
| `branch` | Unidade | «Matriz» | só no consolidado |
| `severity` | Severidade | `CfStatusBadge` com o mapa de cores | ordenável |
| `occurrence` | Ocorrência | texto | |
| `document` | NF | número/série | |
| `supplier` | Fornecedor | nome | |
| `issueDate` | Emissão | data | ordenável |
| `tes` | TES | código | |
| `field` | Campo | «ICMS» | |
| `difference` | Diferença | moeda ou número | `align="right"`, ordenável |
| `action` | O que fazer | texto curto | |

**Aba Notas casadas** (`GET …/documents`): Situação (badge) · Unidade · NF · Fornecedor · UF · Emissão · Total XML · Ocorrências. Clique leva à aba Ocorrências filtrada pela NF (`q=<nf>`).

**Aba Notas sem par** (`GET …/unmatched`): Status (`CfResolutionStatusCell`; «explicada» sem botão quando a situação é Info) · Situação · Onde está (Só no XML / Só no Protheus) · NF · Fornecedor · Emissão · Valor · Motivo.

**Aba CT-e** (`GET …/cte`): CT-e · Transportadora · Emissão · Valor · Direito ao crédito (badge Sim/Não/Indefinido) · CFOP lançado × esperado · Base · Alíquota · ICMS Protheus × XML · CST · Ocorrências.

**Aba TES usadas** (`GET …/tes`): TES · Descrição · Credita ICMS · Livro ICMS · Credita IPI · Livro IPI · Mat. consumo · Itens · Alerta (badge `danger` «Crédito × livro desencontrados» ou «Consumo credita IPI»).

Mobile (≤ 768px): cards nativos do `DataTableSection` com `CfDataRecordCard` — `leading` = badge de severidade, `title` = ocorrência, `subtitle` = «NF 25655 · J.J. Sul», `fields` = Diferença, TES, Emissão; `status` = `CfResolutionStatusCell` compacto.

### 4.13 Pergunte à CLARA — `CfSectionCard` + `CfHelpTooltip` — existem

`CfSectionCard`: `title="Pergunte à CLARA"`, `subtitle="A CLARA lê esta mesma análise"`, `collapsible`, `defaultOpen={false}` no mobile.

Conteúdo: lista de sugestões, cada uma com botão «Copiar» (`CfActionButton` variante ghost) que copia o texto já com o período: «Explique a auditoria de entradas de 01/10 a 31/10/2026», «O que pede ação na Matriz?», «Por que as CT-e da J.J. Sul deram alta?», «Compare com a análise anterior». Anúncio «Copiado» em `aria-live`.

## 5. Dados

| Bloco | Rota da BFF (todas com os filtros da análise) |
|---|---|
| Cabeçalho, status | `GET /entry-audit/analyses/{id}` |
| Opções dos filtros | `GET …/facets` |
| KPIs, conformidade | `GET …/summary` |
| Por dia | `GET …/daily` |
| Fornecedores, temas, severidade, TES | `GET …/breakdowns` |
| Evolução | `GET /entry-audit/trend` |
| Abas | `GET …/occurrences` · `…/documents` · `…/unmatched` · `…/cte` · `…/tes` |
| Resolver / reabrir | `POST /entry-audit/occurrences/{key}/resolve` · `/reopen` (e `unmatched`) |
| Exportar | `GET …/export` |

Cache (React Query): chaves por `analysisId` + filtros. Resolver invalida `summary`, `breakdowns`, a aba atual e `facets`; a linha muda na hora (otimista) e volta se a BFF recusar.

## 6. Estados

| Estado | Comportamento |
|---|---|
| Carregando | `CfLoadingCard` por bloco (KPIs, gráficos e tabela carregam em paralelo; um bloco lento não segura os outros) |
| Atualizando (troca de filtro) | o bloco mantém o conteúdo e mostra `refreshing` (tabela) ou opacidade reduzida (gráfico) |
| Análise em andamento | redireciona para a página 01 acompanhando a análise |
| Análise parcial (uma filial falhou) | `CfStateBanner variant="error"` no topo: «A Filial não foi auditada: <motivo>. [Tentar de novo]»; os números mostram só a Matriz e o PageHero diz isso |
| Filtro sem resultado | cada bloco com o seu `emptyMessage`; KPIs mostram 0 só quando a BFF devolve 0 |
| Erro de um bloco | `CfStateBanner variant="error"` dentro do card, com «Tentar de novo»; os demais blocos seguem |
| Sem permissão | página padrão de acesso negado do Portal |

## 7. Acessibilidade

`h1` no PageHero; `h2` em cada `ChartCard`/`SectionCard`. Cards, barras, fatias, pontos do gráfico e itens de legenda são focáveis e acionáveis por Enter/Espaço, com `aria-pressed` quando são filtro ativo. Cada gráfico tem `aria-label` com o resumo («22 ocorrências altas; maior concentração no dia 14») e a tabela como alternativa. Mudança de filtro anuncia o novo total em `aria-live="polite"`. Severidade sempre com texto.
