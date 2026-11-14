# Entry audit · Front-end · Página 02 — Dashboard da análise

| Campo | Valor |
|---|---|
| Rota | `/apps/controllership-finance/entry-audit/analyses/:analysisId` |
| Família visual | analítica / indicadores (padrão visual §9.3) |
| Permissão | `controllership-finance.access` (resolver e reabrir inclusos) |
| Wireframe | seção 1 do [HTML](./wireframes-auditoria-entradas.html) |
| Contrato | reconciliado com a BFF publicada (T10.0, 2026-11-14) — [README](./README.md#reconciliação-t100); nomes de parâmetro e campo = os da BFF |

## 1. Objetivo

Mostrar o resultado de uma análise (período + filiais) e permitir o acompanhamento: o que pede ação, onde se concentra, como evoluiu, e marcar o que já foi resolvido. Tudo o que aparece aqui a CLARA também lê pelas mesmas rotas.

Dois grupos de filtro:
- **filtros da execução** (período, filiais, documentos): mostrados como resumo no PageHero; mudar algum leva à página 01 com os campos preenchidos (pede nova execução);
- **filtros da análise** (unidade, severidade, tema, fornecedor, TES, tipo, dia, status, busca): recortam o resultado sem reexecutar e ficam na URL.

## 2. Estado na URL

`branch`, `severity`, `theme`, `supplier`, `tes`, `document_type`, `situation`, `day`, `status`, `tab`, `q`, `page`, `sort` (tabela completa e mapeamento de `severity` PT↔EN no [README](./README.md)). Padrão: `branch=all` (se a análise tem mais de uma filial), `status=pending`, `tab=occurrences`. `Esc` limpa os filtros da análise (exceto `tab`). Filtro que não se aplica à aba corrente fica desabilitado (README, «Filtro × aba»).

## 3. Estrutura e dimensionamento

```text
PagePath: Auditoria de entradas › 01/10–31/10/2026
┌ PageHero (compact) ───────────────────────────────────────────────────────────────┐
│ Controladoria · Fiscal                                [⤓ Exportar] [▶ Reexecutar] │
│ h1 Auditoria de entradas                                                           │
│ Matriz e Filial · 01/10/2026 a 31/10/2026 (recebimento)                            │
│ Executada em 13/11 22:10 · Origem: Manual · Fontes: SF1 SD1 SF4 SFT XML           │
│ ┌ FilterBar: Unidade ▾ Severidade ▾ Tema ▾ Fornecedor ▾ TES ▾ Documento ▾  Limpar ┐ │
└───────────────────────────────────────────────────────────────────────────────────┘
ScopeChipBar ─ filtros ativos (removíveis) · Limpar tudo
[A] KPI │ KPI │ KPI │ KPI
[B] Ocorrências por dia (ComparativeAreaChart) 1.7fr │ Conformidade (Gauge) 1fr
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
| `children` | linha de metadados (texto `sm`: «Executada em» `created_at`, «concluída» `finished_at` e «Origem» `requested_via` — Manual/CLARA — lidos do item da análise em `GET /entry-audit/analyses?date_from&date_to` (casado por `id`; o `GET …/{id}` não traz esses campos); **sem nome de quem pediu** e sem duração calculada; chip estático «Fontes ao vivo: SF1 · SD1 · SF4 · SFT · XML») + `FilterBar` (4.3) |

### 4.3 `FilterBar` dos filtros da análise (← `createDashboardFiltersKit`) — existe

`ariaLabel="Filtros da análise"`, `variant="extended"`, `compact`, `trailing` = `ClearFiltersButton` («Limpar filtros», `disabled` sem filtro ativo).

| Campo | Componente | Props |
|---|---|---|
| Unidade | `CfSegmentToggle` | `options=[Consolidado, Matriz, Filial]` (só quando a análise tem mais de uma filial), `size="sm"`, `ariaLabel="Unidade"` |
| Severidade | `FilterSelectField` | `options` de `facets.severities[]` (`{name,count}`; `name` em PT, ex.: `Alta`) com contagem no rótulo («Alta (22)»); `value` do MFE traduzido pela tabela do README; `placeholderOption="Todas"` |
| Tema | `FilterSelectField` | `options` de `facets.themes[]` (`name` = prefixo do `rule_id`; rótulo PT-BR no locale), `placeholderOption="Todos"` |
| Fornecedor | `FilterSelectField` | `options` de `facets.suppliers[]` (`name` = nome do fornecedor; **sem UF nem código** no contrato), `value`=nome, `searchable`, `placeholderOption="Todos"` |
| TES | `FilterSelectField` | `options` de `facets.tes[]` (`name` = código da TES, ex.: «036»); a descrição só existe na aba «TES usadas» (`sf4.description`) — pode enriquecer o rótulo se essa aba já estiver em cache, nunca por chamada extra |
| Documento | `FilterSelectField` | `options=[NF-e, CT-e]` (só os `document_types` da análise) → `document_type` |

`facets` reflete o recorte das **ocorrências** com os filtros ativos (contagens de ocorrência, não de nota).

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

Dados: `GET …/summary` → `{kpis, previous, conformity}` (+ `meta.branches_unavailable`). Os quatro cards aceitam clique (`onSelect`) e teclado.

| Card | `label` | `value` | `hint` | `tone` / `status` | `onSelect` |
|---|---|---|---|---|---|
| Valor conferido | «Valor conferido» | `money(kpis.gross_checked)` | «`kpis.documents` notas» + `CfTrendDelta` (Δ% de `gross_checked` vs `previous.gross_checked`, derivado no MFE) | `default` | aba Notas casadas, `situation` vazio |
| Notas sem divergência | «Notas sem divergência» | `conformity.clean` | «X% das casadas» (X derivado: `clean/(clean+divergent)`); **sem delta** (`previous` não traz `clean`) | `positive` | aba Notas casadas, `situation=clean` |
| Ocorrências pendentes | «Ocorrências pendentes» (ou «Pendentes (alta)» com severidade filtrada) | `kpis.pending` | «`kpis.resolved` resolvidas» + delta vs `previous.pending` (queda = bom) | `warning` se > 0 | aba Ocorrências, `status=pending` |
| Diferença nas altas | «Diferença nas altas» | `money(kpis.high_difference)` | «`kpis.high` ocorrências altas» | `negative` se > 0 | `severity=high` (→ `Alta`) |

`titleHint` de cada card explica a conta: «Valor conferido» = soma do valor bruto (Protheus) das notas recebidas no período, sem «XML indisponível» nem «fora do período»; «Diferença nas altas» = soma do módulo da `difference` das ocorrências de severidade **Alta** no recorte (pendentes e resolvidas; ocorrência sem diferença numérica soma 0). `fitValue` ligado. Erro ou indisponível vira «—» com `status={label:"Indisponível", tone:"neutral"}`, nunca zero.

`previous` vem **zerado** (e não nulo) quando não há análise anterior de mesmo tamanho: com `previous.documents = 0` e `previous.occurrences = 0` o MFE não mostra `CfTrendDelta`. `kpis.xml_unavailable > 0` mostra um aviso discreto abaixo dos KPIs («N notas sem XML — fora da conferência»), com `onSelect` para a aba Notas casadas, `situation=xml_unavailable`. Filial que falhou: `meta.branches_unavailable` (ver §6).

### 4.6 Ocorrências por dia — `CfChartCard` + `CfComparativeAreaChart` — existe, **evoluir** o gráfico (doc 04 §6)

`CfChartCard`: `title="Ocorrências por dia"`, `hint="Período selecionado × período anterior de mesmo tamanho, pela data de recebimento. Clique num dia para filtrar."`, `titleLevel={2}`. (O contrato conta **ocorrências** por dia de recebimento; não conta notas distintas nem usa a emissão.)

`CfComparativeAreaChart` (dados `GET …/daily` → `{series, previous, period}`; `series` e `previous` são listas `{name:"2026-10-14", count: 3}` só com dias de `count > 0`; `period` = `[date_from, date_to]`):

| Prop | Valor |
|---|---|
| `data` | `[{name:"01", current: 3, previous: 5}, …]` um ponto por dia de `period`, montado no MFE: `current` = `series[].count` (0 nos dias ausentes); `previous` = `previous[].count` alinhado **por posição do dia** no período anterior (mesmo tamanho; `previous` vazio quando não há análise anterior → série omitida) |
| `series` | `[{dataKey:"current", name:"01/10–31/10", color: token primário}, {dataKey:"previous", name:"Período anterior", color: token secundário, fillOpacity:0}]` |
| `height` | 260 / 200 |
| `valueFormatter` | inteiro pt-BR |
| `smooth` | `true` |
| `emptyMessage` | «Sem notas no período.» |
| `onPointSelect` (novo) | `(point) => setFilter("day", <data ISO do dia clicado>)` (a BFF filtra `day=YYYY-MM-DD` pela data de recebimento) |
| `selectedName` (novo) | o dia filtrado, destacado |

### 4.7 Conformidade — `CfSemicircleProgressGauge` — existe, **evoluir** (doc 04 §4)

| Prop | Valor |
|---|---|
| `value` | **derivado no MFE**: `round(100 × conformity.clean / (conformity.clean + conformity.divergent), 1)` (o contrato não traz percentual); sem notas → «—» |
| `max` | 100 |
| `unit` | `"%"` |
| `centerLabel` | `"sem divergência"` |
| `tone` | `success` ≥ 90 · `warning` 70–90 · `danger` < 70 |
| `size` | 200 / 168 |
| `legend` | `[{id:"clean",label:"Sem divergência",count:conformity.clean,tone:"success"}, {id:"divergent",label:"Com divergência",count:conformity.divergent,tone:"warning"}, {id:"unmatched_open",label:"Sem par a resolver",count:conformity.unmatched_open,tone:"danger"}, {id:"unmatched_explained",label:"Sem par explicadas",count:conformity.unmatched_explained,tone:"neutral"}, {id:"posted_outside_period",label:"Lançadas fora do período",count:conformity.posted_outside_period.count,tone:"neutral"}]` |
| `onLegendSelect` (novo) | `clean`/`divergent` → aba Notas casadas com `situation=clean`/`divergent`; `unmatched_open` → aba Notas sem par, `status=pending`; `unmatched_explained` → aba Notas sem par, `severity=Info`; `posted_outside_period` → aba Notas casadas, `situation=posted_outside_period` |

«Lançadas fora do período» é **informação** (`tone` `neutral`): são XML da janela que já estão escriturados no Protheus em outra data de recebimento; **não** entram em «a resolver», nem no denominador do medidor, nem em `unmatched_*`. `conformity.posted_outside_period.by_date[{date,count}]` alimenta a lista de datas (só no `title`/tooltip do item da legenda).

Dentro de `CfChartCard title="Conformidade" hint="Notas casadas entre Protheus e XML"`.

### 4.8 Top 8 fornecedores — `CfHorizontalValueBars` — existe, **evoluir** (doc 04 §5)

`CfChartCard`: `title="Top 8 fornecedores"`, `hint="Por número de ocorrências."`. A cor por parte de notas com divergência **sai**: `breakdowns.suppliers` é `{name, count}` e não traz total de notas nem altas por fornecedor.

| Prop | Valor |
|---|---|
| `items` | `breakdowns.suppliers.slice(0,8)` (a BFF devolve até 10, já ordenado por `count`) → `{id: name, label: name, value: count, valueLabel: String(count), tone:"neutral"}`; sem UF, sem código, sem «altas» |
| `tone` por item (novo) | uniforme `neutral` nesta tela; a evolução aditiva de `tone` do doc 04 §5 continua usada em «Por severidade» |
| `selectedId` (novo) | fornecedor filtrado (`supplier` = nome) |
| `onItemClick` | `setFilter("supplier", item.id)` (nome; a BFF faz busca por trecho no nome; clique de novo tira o filtro) |
| `layout` | `"stacked"` |
| `emptyMessage` | «Nenhuma ocorrência nesta seleção.» |

### 4.9 Ocorrências por tema — **`CfDistributionDonut`** — novo (doc 04 §1)

`CfChartCard`: `title="Ocorrências por tema"`, `hint="Clique para filtrar."`.

| Prop | Valor |
|---|---|
| `items` | `breakdowns.by_theme[]` (`{name,count}`; `name` = prefixo do `rule_id`) → `{id: name, label: <rótulo PT-BR do locale>, value: count, tone:"chart-N"}` (tom por posição) |
| `selectedId` | tema filtrado |
| `onSelect` | `setFilter("theme", id)` |
| `centerValue` / `centerLabel` | total ou o do tema selecionado; «ocorrências» |
| `size` | 200 |
| `legendPlacement` | `"side"` (> 900px) / `"below"` |
| `showPercent` | `true` |

### 4.10 Linha D — três gráficos — existem

| Card (`CfChartCard`) | Componente | Props |
|---|---|---|
| «Por severidade» | `CfHorizontalValueBars` (não `BarSeriesChart`: precisa de clique) | `items` = `breakdowns.by_severity[]` (`{name,count}`, `name` em PT) com `tone` do mapa de cores (por `name`), `onItemClick` → `severity` (traduzido), `selectedId` |
| «TES com mais ocorrências» | `CfHorizontalValueBars` | `items` = `breakdowns.tes.slice(0,6)` → `{id: name, label: name (código da TES), value: count}`; sem `meta` de alerta (o contrato não traz alerta de TES; o sinal de «crédito × livro» já é ocorrência `fiscal_book.credit_against_tes`/`coherence.ipi_on_consumption`); `onItemClick` → `tes` |
| «Evolução entre análises» | `CfLineSeriesChart` | `points` de `GET /entry-audit/trend?branch&date_from&date_to` → `data.points[]`, **um ponto por análise concluída** (`status=done`): `{analysis_id, date_from, date_to, month, branches, documents, occurrences, high, pending, resolved}`; eixo X = «dd/MM–dd/MM» de `date_from`/`date_to`; `seriesList` = [Pendentes `pending`, Altas `high`], sem interação. Com `group=month` a BFF devolve também `months[]` agregado (`month`, somas e `analyses`) — usado quando há muitos pontos. `branch` = filial filtrada (omitido no consolidado). `emptyMessage="Precisa de pelo menos duas análises para mostrar a evolução."` |

### 4.11 Abas — `CfSectionCard` + `CfUnderlineNav` — existem

`CfSectionCard`: `title` oculto (as abas são o título), `fill`.

`CfUnderlineNav`: `mode="tabs"`, `activeId={tab}`, `items`:

| `id` | `label` | `count` |
|---|---|---|
| `occurrences` | Ocorrências | `kpis.pending` |
| `documents` | Notas casadas | `kpis.documents` |
| `unmatched` | Notas sem par | `conformity.unmatched_open` |
| `cte` | CT-e | `total` da última resposta da aba (sem número antes de abrir) |
| `tes` | TES usadas | `items.length` da última resposta da aba |

### 4.12 Tabela — `DataTableSection` (cfDataTableUi) + `CfSegmentToggle` + **`CfResolutionStatusCell`** — existe / novo (doc 04 §2)

Comum às abas:

| Prop | Valor |
|---|---|
| `toolbarLeading` | `CfSegmentToggle` de recorte, sempre por query param da BFF. **Ocorrências** [Pendentes `status=pending` · Resolvidas (n) `status=resolved` · Todas (sem `status`)]; **Notas casadas** [Todas (sem `situation` = recebidas no período) · Sem divergência `clean` · Com divergência `divergent`] e, à parte, as visões «Lançadas fora do período» (`situation=posted_outside_period`) e «XML indisponível» (`situation=xml_unavailable`); **Notas sem par** [Pendentes `status=pending` · Resolvidas `status=resolved` · Explicadas `severity=Info`] — **sem «Todas»** e sem contagem por opção (só o selo da aba). `size="sm"` |
| `serverPagination` | `{page, pageSize: 25, total, onPageChange}` (`page`/`page_size` da BFF; máx. 200) |
| `serverSort` | `{sortKey, onSortChange}` com `sortKey` ∈ `severity` \| `supplier` \| `document` \| `day`; **a BFF não tem direção**: ordenação ascendente fixa (sem `sortDirection`); só as colunas ordenáveis abaixo habilitam o cabeçalho |
| `serverSearch` | `{value: q, onChange}` com `searchPlaceholder="Buscar NF, fornecedor, ocorrência…"` |
| `columnPreferencesKey` | `"cf-entry-audit-<aba>"` |
| `fontSizePreferencesKey` | `"cf-entry-audit"` |
| `onRowClick` | abre o detalhe (doc 03) — aba Ocorrências e Notas sem par |
| `tableLayout` | `"scroll"` |

Rodapé (aba Ocorrências): `CfProgressSummaryBar` `value={kpis.resolved/(kpis.pending+kpis.resolved)*100}` (derivado no MFE), `label="Resolvidas"`, `summary="31 de 128 resolvidas"`. Notas sem par: sem barra (a linha da lista não traz `status`; ver aba).

**Aba Ocorrências** (`GET …/occurrences`)

| `key` | `header` | `render` | Observação |
|---|---|---|---|
Colunas **somente com campos de `_public_occurrence`** (`stable_key`, `rule_id`, `rule_name`, `severity`, `theme`, `title`, `document_number`, `series`, `supplier_name`, `item`, `field`, `field_label`, `protheus_value`, `xml_value`, `difference`, `tes`, `why`, `action`, `access_key`, `status`). Não há `issue_date`, `branch` nem `document_type` na linha: **Emissão e Unidade saem da tabela** (a unidade já está no filtro; o dia é filtro/ordenação, não coluna).

| `key` | `header` | Campo | `render` | Observação |
|---|---|---|---|---|
| `status` | Status | `status` (`pending`\|`resolved`) | `CfResolutionStatusCell` (`interactive`) | resolve/reabre sem abrir o detalhe |
| `severity` | Severidade | `severity` (PT) | `CfStatusBadge` com o mapa de cores | ordenável (`sort=severity`) |
| `occurrence` | Ocorrência | `title` | texto (o `rule_name` no `title` da célula) | |
| `document` | NF | `document_number`, `series` | número/série | ordenável (`sort=document`) |
| `supplier` | Fornecedor | `supplier_name` | nome | ordenável (`sort=supplier`) |
| `tes` | TES | `tes` | código(s) | |
| `field` | Campo | `field_label` | «ICMS», «CST (origem)» | |
| `difference` | Diferença | `difference` | moeda/número; **`null` → «—»** (campo de código: CST, CFOP, série, chave… não tem diferença numérica) | `align="right"`; não ordenável |
| `action` | O que fazer | `action` | texto curto | |

`sort=day` (recebimento) fica disponível como ordenação por menu/atalho, sem coluna própria.

**Aba Notas casadas** (`GET …/documents`, padrão = recebidas no período): `situation` (badge: `clean` Sem divergência `success` · `divergent` Com divergência `warning` · `posted_outside_period` Lançada fora do período `neutral` · `xml_unavailable` XML indisponível `neutral`) · `branch` (Unidade, só no consolidado) · `document_number`/`series` (NF) · `supplier_name` (Fornecedor) · `issue_date` (Emissão) · `received_date` (Recebimento) · `comparison.gross` (Valor bruto, Protheus) · `divergence_count` (Ocorrências). Sem UF e sem «Total XML» no contrato. Clique leva à aba Ocorrências filtrada pela NF (`q=<document_number>`). A visão «Lançadas fora do período» é separada (`situation=posted_outside_period`) e informativa: sem Resolver, sem contar como pendência.

**Aba Notas sem par** (`GET …/unmatched`; cada item traz `links`): `side` (Onde está: `xml` «Só no XML» · `protheus` «Só no Protheus») · `severity` + `situation` (texto do motor, ex.: «Em lançamento (LNF)», «em trânsito», «saída da própria filial», formulário próprio sem SF1 — severidade Alta, XML indisponível) · `document_number`/`series` · `party_name` (emitente) · `party_tax_id` (CNPJ) · `party_state` (UF) · `issue_date` · `amount` (Valor) · `nature` · `cfop` · `cst` · `icms_base`/`icms_amount`/`ipi_amount` · `lnf_request_id`/`lnf_status` (quando em lançamento: link para o app LNF pela solicitação) · `links.xml` (`/entry-audit/xml/{chave}?branch=…&document_type=…`). Colunas visíveis por padrão: Status · Situação · Onde está · NF · Emitente · Emissão · Valor; as demais no seletor de colunas.
- **Status**: a linha **não traz `status`**; o `CfResolutionStatusCell` deriva do recorte do toggle (`Pendentes` → pending; `Resolvidas` → resolved) e atualiza por otimismo após `resolve`/`reopen`. Linha com `severity = Info` (explicada) renderiza o selo «Explicada» **sem botão**.
- `Pendentes` (`status=pending`) pode incluir linhas explicadas (`Info`), pois o contrato não tem filtro de exclusão; o número do selo da aba é `conformity.unmatched_open` (a BFF), que pode ser menor que o `total` da lista. Esta diferença é intencional e documentada, não bug de UI.

**Aba CT-e** (`GET …/cte`; cada item = `{branch, access_key, document_number, comparison}`): CT-e (`document_number`) · Emitente (`comparison.issuer_name`/`issuer_state`) · Tomador (`comparison.taker_role`) · Valor (`comparison.gross`, Protheus) · CFOP (`comparison.cfop`, do XML) · CST (`comparison.cst`) · Base (`comparison.icms_base`) · Alíquota (`comparison.icms_rate`) · ICMS (`comparison.icms`, Protheus) · TES (`comparison.tes`) · Notas vinculadas (`comparison.linked_documents`) · Natureza (`comparison.operation_nature`). **Sem `fiscal_code`** (a leitura o remove), sem emissão, sem «direito ao crédito» e sem contagem de ocorrências por CT-e: o juízo de crédito/CFOP aparece como ocorrência `cte.*` na aba Ocorrências (`theme=cte`).

**Aba TES usadas** (`GET …/tes` → `data.items[]` sem paginação; cada item = `{branch, tes_code, document_type, sf4:{…}}`): TES (`tes_code`) · Descrição (`sf4.description`) · Tipo (`sf4.tes_type`) · CF (`sf4.fiscal_code`) · Calcula ICMS (`sf4.calculates_icms`) · Credita ICMS (`sf4.credits_icms`) · Livro ICMS (`sf4.icms_book`) · Calcula IPI (`sf4.calculates_ipi`) · Credita IPI (`sf4.credits_ipi`) · Livro IPI (`sf4.ipi_book`) · Mat. consumo (`sf4.consumption_material`) · Itens (`sf4.items`). Valores já vêm no vocabulário Sim/Nao e Tributado/Isento/Outros. **Sem coluna «Alerta»**: a BFF não entrega alerta de TES e o MFE não decide regra fiscal.

Mobile (≤ 768px): cards nativos do `DataTableSection` com `CfDataRecordCard` — `leading` = badge de severidade, `title` = ocorrência (`title`), `subtitle` = «NF 25655 · <fornecedor>», `fields` = Diferença (`—` se `null`), TES, Campo; `status` = `CfResolutionStatusCell` compacto.

### 4.13 Pergunte à CLARA — `CfSectionCard` + `CfHelpTooltip` — existem

`CfSectionCard`: `title="Pergunte à CLARA"`, `subtitle="A CLARA lê esta mesma análise"`, `collapsible`, `defaultOpen={false}` no mobile.

Conteúdo: lista de sugestões, cada uma com botão «Copiar» (`CfActionButton` variante ghost) que copia o texto já com o período: «Explique a auditoria de entradas de 01/10 a 31/10/2026», «O que pede ação na Matriz?», «Por que as CT-e da J.J. Sul deram alta?», «Compare com a análise anterior». Anúncio «Copiado» em `aria-live`.

## 5. Dados

| Bloco | Rota da BFF (todas com os filtros da análise; `…` = `/entry-audit/analyses/{id}`) |
|---|---|
| Cabeçalho, status | `GET …` → `status`, `runs[]`, `counts`, `config` |
| Opções dos filtros | `GET …/facets` → `suppliers`, `themes`, `tes`, `severities` (`{name,count}`) |
| KPIs, conformidade | `GET …/summary` → `kpis`, `previous`, `conformity` |
| Por dia | `GET …/daily` → `series`, `previous`, `period` |
| Fornecedores, temas, severidade, TES | `GET …/breakdowns` → `suppliers`, `by_theme`, `by_severity`, `tes` |
| Evolução | `GET /entry-audit/trend?branch&date_from&date_to&group` → `points` (+ `months` com `group=month`) |
| Abas | `GET …/occurrences` · `…/documents` · `…/unmatched` · `…/cte` · `…/tes` (paginadas `{items,page,page_size,total}`, exceto `tes`) |
| Resolver / reabrir | `POST /entry-audit/occurrences/{key}/resolve` · `/reopen`; na aba Notas sem par, `POST /entry-audit/unmatched/{key}/resolve` · `/reopen` (mesmo efeito, idempotente) → `{stable_key, kind, status, status_id}` |
| Exportar | `GET …/export` (`.xlsx`) |

Toda leitura de resultado devolve `meta.branches_unavailable` (filiais com `runs[].status = failed`); essas filiais **não entram como zero** nos números. `{key}` é a `stable_key` (contém `|`): sempre `encodeURIComponent` na rota do MFE e na URL da BFF; o MFE a trata como opaca (não faz parse).

Cache (React Query): chaves por `analysisId` + filtros. Resolver invalida `summary`, `breakdowns`, a aba atual e `facets`; a linha muda na hora (otimista) e volta se a BFF recusar.

## 6. Estados

| Estado | Comportamento |
|---|---|
| Carregando | `CfLoadingCard` por bloco (KPIs, gráficos e tabela carregam em paralelo; um bloco lento não segura os outros) |
| Atualizando (troca de filtro) | o bloco mantém o conteúdo e mostra `refreshing` (tabela) ou opacidade reduzida (gráfico) |
| Análise em andamento | redireciona para a página 01 acompanhando a análise |
| Análise parcial (uma filial falhou) | detectada por `meta.branches_unavailable` / `runs[].status = failed`: `CfStateBanner variant="error"` no topo: «A Filial não foi auditada: <motivo de `runs[].error`>. [Tentar de novo]»; os números mostram só a Matriz e o PageHero diz isso. Não confundir com `status = partial` (XML indisponível em notas), que é aviso informativo com `kpis.xml_unavailable` |
| Resultado ainda não pronto | 409 `ANALYSIS_NOT_READY` nas leituras: tratado como «Análise em andamento» |
| Filtro sem resultado | cada bloco com o seu `emptyMessage`; KPIs mostram 0 só quando a BFF devolve 0 |
| Erro de um bloco | `CfStateBanner variant="error"` dentro do card, com «Tentar de novo»; os demais blocos seguem |
| Sem permissão | página padrão de acesso negado do Portal |

## 7. Acessibilidade

`h1` no PageHero; `h2` em cada `ChartCard`/`SectionCard`. Cards, barras, fatias, pontos do gráfico e itens de legenda são focáveis e acionáveis por Enter/Espaço, com `aria-pressed` quando são filtro ativo. Cada gráfico tem `aria-label` com o resumo («22 ocorrências altas; maior concentração no dia 14») e a tabela como alternativa. Mudança de filtro anuncia o novo total em `aria-live="polite"`. Severidade sempre com texto.
