# UI review — revisão 2 do owner (15/11/2026)

Origem: o owner abriu em HML (`192.168.1.237:18443`) a entrada da Auditoria de Entradas e a análise 01/11–15/11 depois da U10 e pediu os ajustes abaixo. O Claude conferiu cada ponto no código (`origin/main` `d2aaaae2`) e acrescentou o que viu nos mesmos prints. Execução: [track.md §10 (U12)](./track.md) · prompt [prompts/U12-cursor.md](./prompts/U12-cursor.md).

Legenda de origem: **OW** = pedido do owner · **CL** = achado do Claude nos prints/código.

## 1. Padrão de tabela do Portal (todas as tabelas)

| # | Orig. | Problema | Evidência no código | Correção |
|---|---|---|---|---|
| T1 | OW | Nenhuma coluna ordena; a tabela já vem com a ordem pronta | O kit tem `sortable`/`sortValue` (cliente) e `serverSort` (servidor) em `DataTableSection`; só 4 páginas do MFE usam (`ChecklistAdmin`, `ChecklistVersion`, `MonthlyClosing`, `ProductionOrderConsumption`). Nenhuma tabela da auditoria | Toda coluna de dado ordenável. Tabela paginada no servidor ordena **no servidor** (`serverSort`; ordenar só a página atual é proibido pelo kit). Tabela local usa `sortValue` tipado (número, data ISO, texto), nunca o texto renderizado |
| T2 | OW | Não dá para escolher colunas | O kit exibe o menu «Colunas» quando recebe `columnPreferencesKey` (com `defaultColumnVisibility`); as tabelas da auditoria não passam | `columnPreferencesKey="controllership-finance:<página>:<tabela>:columns:v1"` em todas; `fontSizePreferencesKey` junto, como no Comercial |
| T3 | OW | Coluna «Ação / Abrir» em tabela cuja linha já abre o detalhe | `EntryAuditHomePage.tsx` coluna `open` + `onRowClick` | Linha clicável (mouse, Enter e Espaço pelo kit); sem coluna «Abrir». Ação na linha só quando é outra ação (ex.: Resolver) |
| T4 | CL | Paginação com quatro ícones «?» (anterior, ir para, próxima, resumo) | `cfDataTableUi.tsx` passa `hints` ao `createDashboardPaginationKit`; o Comercial não passa | Remover os `hints` da paginação; manter só os rótulos acessíveis |
| T5 | CL | Valores crus na tabela: `408.00`, `2800.00`, `2.05` | `occurrenceColumns` usa `displayValue(row.protheus_value)` / `xml_value` | Formatar pelo tipo do campo: dinheiro `R$ 408,00`, alíquota `%`, data `dd/mm/aaaa`; CFOP/CST/TES/NCM/CNPJ como texto. Um formatador em `entryAuditPresentation.ts`, com teste |
| T6 | CL | Termo técnico na tela: coluna Campo mostra `field` (regra «Data de emissão divergente») | `field_label ?? field` cai no nome técnico | Mapa de rótulos completo para todos os campos das regras; teste que falha se algum campo do catálogo de regras não tiver rótulo |
| T7 | CL | Seis tabelas em HTML local fora do kit | `<table className="cf-p3-table">` (P3, matriz R01–R15, conciliação, compartilhada) e `cf-pend-table` (Pacotes, Pendências) | Lista de registros → `DataTableSection`. Matriz (linhas × colunas fixas) pode ficar, registrada como exceção com motivo |
| T8 | CL | Celular: tabela larga com rolagem horizontal | Sem `viewLayoutPreferencesKey`/`renderCard` | Em listas de registros, Tabela/Cards como no Comercial (`renderCard` com o cartão interativo do kit); cards por padrão no celular |
| T9 | CL | Leitor de tela anuncia «Filtros das baixas financeiras» em qualquer página | `cfFiltersUi.ts` fixa `filtersAriaLabel` | Rótulo por uso (prop da linha de filtros) ou genérico «Filtros» |

## 2. Auditoria de Entradas — entrada

| # | Orig. | Problema | Correção |
|---|---|---|---|
| E1 | OW | Hero e card «Nova análise» separados gastam espaço vertical | Filtros (De, Até, Filiais, Tipos) e «Executar auditoria» **dentro do hero**, no `FilterBarShell` do kit (regra «uma moldura», padrão §14), como em `plugins/commercial/src/features/customers/pages/CustomersPage.tsx`. O texto «a auditoria confere…» vai para a ajuda do título. Card «Nova análise» removido |
| E2 | OW | Coluna «Ação» | T3 |
| E3 | CL | Filiais aparecem como «DELPI COMPONENTES LTDA, DELPI COMPONENTES LTDA» (mesma razão social) | Rótulo de filial pelo código: «Filial 01 · SC»; razão social só no `title`/ajuda. Lista compacta: «Filiais 01 e 02» |
| E4 | CL | Lista carrega 50 análises sem paginação no servidor (a BFF aceita `page`) | Paginação e ordenação no servidor (T1) |

## 3. Auditoria de Entradas — resultado da análise

| # | Orig. | Problema | Correção |
|---|---|---|---|
| A1 | OW | Trocar a aba (Ocorrências, Notas casadas, Sem par…) remonta a página inteira | Causa no código: `navigateWith` → `popstate` → `routeEpoch` → `params` novo → `filtersFromUrl` devolve objeto novo → o efeito do resumo (dependência `filters`) zera `summary`, `breakdowns`, `daily`, `rows` e busca tudo de novo. Corrigir: filtros memorizados pela chave serializada **só dos filtros** (sem `tab`, `page`, `page_size`, `sort`, `order`); troca de aba busca só a aba; atualizar não zera o que já está na tela (estado «atualizando» do kit). `CfUnderlineNav` em `mode="tabs"`. Teste: trocar de aba não chama summary/breakdowns/daily de novo |
| A2 | OW | Gráficos de rosca com legenda maior que o gráfico; barras (tema, fornecedor, TES) com metade do card vazia; Evolução por dia espremida | Layout alvo abaixo. Juntar Conformidade e Severidade num card «Panorama»; as três barras num card «Onde estão as ocorrências» em três colunas com barras na largura toda (`layout="stacked"`); Evolução por dia com mais largura |
| A3 | OW | Tabela de ocorrências sem ordenação e sem escolha de colunas | T1, T2 (ordenação no servidor) |
| A4 | CL | Evolução por dia mistura datas de outubro e novembro no mesmo eixo (o período anterior é desenhado nas próprias datas) e usa `2026-10-01` | Alinhar o anterior pela posição do dia (dia 1 com dia 1); eixo `dd/mm`; tooltip «05/11: 12 · anterior 21/10: 8»; legenda «Este período» e «Período anterior (17/10–31/10)». Sem análise anterior → só a série do período |
| A5 | CL | Comparação com período de tamanho diferente: 01–15/11 comparado com 01–31/10 dá «−48,1%» | `_previous_analysis()` pega qualquer análise concluída que caia na janela. Regra: mesmo número de dias, imediatamente anterior, mesmas filiais e tipos; senão `previous: null` (inclui a U11) |
| A6 | CL | Contadores das abas em vermelho e «99+» | Contagem exata e neutra (`159`, `1.234`); cor só para alerta real |
| A7 | CL | «Escopo» repete filiais e tipos (já estão no hero) e «Limpar tudo» parece desfazer a análise | Faixa só com os filtros de detalhamento (severidade, tema, fornecedor, TES, dia, situação), escondida quando vazia, rótulo «Filtros aplicados» |
| A8 | CL | «Lançadas fora do período 400» dentro de Conformidade, maior que as 315 notas conferidas | Sai da faixa de Conformidade; fica na aba e numa linha de nota com ajuda que diz o que essa contagem é, pela regra de `posted_outside_period` no código, e por que não entra nas notas conferidas |
| A9 | CL | «Pergunte à CLARA» com marcadores de lista (•) antes dos botões | Botões em linha, sem lista com marcador (`ul` sem `list-style` ou grupo de chips do kit) |
| A10 | CL | Abas Notas casadas, Sem par, CT-e e Lançadas fora do período com 4 colunas genéricas | Colunas por aba com o que a BFF já entrega (nota/série, emissão, entrada, valor, chave, situação…). Faltou dado → V4 com a lista |

### Layout alvo do resultado (desktop 1440)

```text
PagePath
PageHero  [Análise de 01/11/2026 a 15/11/2026] [Concluída]      [Exportar] [Executar de novo] [Nova análise]
          Filiais 01 e 02 · NF-e e CT-e
KPIs (6)  Notas conferidas · Valor conferido · Pendentes · Alta · Diferença nas Altas · Sem par em aberto
┌ Panorama (5/12) ───────────────────┐ ┌ Evolução por dia (7/12) ─────────────────────────┐
│ Conformidade (meia-lua) │ Severidade │ │ este período × período anterior (alinhado por dia) │
│ legenda abaixo           │ rosca, leg. │ │ eixo dd/mm                                          │
│ Sem par · Explicadas      │ abaixo      │ │                                                     │
└─────────────────────────────────────┘ └─────────────────────────────────────────────────┘
┌ Onde estão as ocorrências (12/12) ──────────────────────────────────────────────────────┐
│ Por tema            │ Por fornecedor (top 8)        │ Por TES (top 8)                      │
│ barras na largura toda, clique filtra a tabela                                            │
└──────────────────────────────────────────────────────────────────────────────────────────┘
Filtros aplicados (só quando houver)
Abas  Ocorrências 159 · Notas casadas 215 · Sem par 144 · CT-e · TES utilizadas · Lançadas fora do período 400
Tabela da aba (ordenação, colunas, busca, paginação no servidor; cards no celular)
Pergunte à CLARA (botões em linha)
```

Tablet 1024: Panorama e Evolução empilhados em 12/12; «Onde estão» em três colunas. Celular 390: tudo empilhado, «Onde estão» vira abas internas ou uma coluna, tabela em cards.

## 4. Fora desta revisão

- Residuais de acessibilidade do host e do plugin-ui (U10 R3) seguem com os donos.
- Prints de PROD pelo owner continuam pendentes (o que o owner viu foi HML).
