# Playbook — Ampliação de gráficos e visualizações no Minha DELPI Chat IA

> **Status (31/05/2026):** [Parcial](./STATUS_ROADMAP_MELHORIAS.md) — **Fase 1 em produção** (`chartPresentation`, toggles Texto/Tabela/Gráfico/Árvore, testes MFE). Fases 2–5 em backlog.

Projeto: **Minha DELPI Chat IA**

Objetivo: evoluir a camada de apresentação rica para suportar mais tipos de gráficos e escolher automaticamente a melhor visualização conforme o tipo de dado: temporal, categórico, participação, ranking, distribuição, comparação, meta, hierarquia e KPI.

---

## 1. Diagnóstico do estado atual

A plataforma já tem uma base forte de apresentação rica.

Hoje existem componentes para:

- texto/markdown;
- tabela;
- gráfico;
- KPI;
- árvore;
- expansão da visualização;
- alternância de formatos;
- drill-down;
- exportação de gráfico para PNG;
- exportação de tabela para CSV;
- navegação por paginação e profundidade.

No front, o componente `ChatRichPresentation` já centraliza a decisão entre texto, gráfico, árvore e tabela, além de usar `ChatRichChart`, `ChatRichTable`, `ChatRichKpi` e `ChatRichTree`.

O componente `ChatRichChart` já importa recursos do Recharts para `BarChart`, `LineChart`, `PieChart` e `AreaChart`. Isso indica que a base técnica para alguns gráficos além de barra já está presente no front.

O tipo `ChatPresentation` já aceita `type: "chart"` com `chartType: "bar" | "line" | "pie" | "area"`. Ou seja, a plataforma já tem no contrato atual suporte tipado para barra, linha, pizza e área. O que falta é organizar o uso, ampliar o contrato e criar critérios automáticos mais ricos.

---

# 2. Visão desejada

O chat deve conseguir responder perguntas como:

- “Mostre as vendas por mês em linha.”
- “Faça um gráfico de pizza por cliente.”
- “Mostre a participação por fornecedor em rosca.”
- “Mostre ranking horizontal dos produtos mais vendidos.”
- “Mostre evolução do estoque ao longo do tempo.”
- “Compare compra e venda por mês.”
- “Mostre meta versus realizado.”
- “Mostre distribuição por status.”
- “Transforme essa tabela em gráfico.”
- “Me mostre como dashboard.”

A resposta ideal não deve depender apenas do usuário pedir o tipo de gráfico. O sistema deve sugerir o melhor gráfico automaticamente.

---

# 3. Princípio central

> O tipo de gráfico deve ser escolhido pelo formato dos dados e pela pergunta do usuário.

A escolha não deve ser aleatória.

Exemplo:

- Dados por mês → linha ou área.
- Ranking de categorias → barra horizontal.
- Participação percentual → pizza ou rosca.
- Comparação com meta → barra agrupada ou KPI.
- Hierarquia → árvore.
- Lista detalhada → tabela.
- Um número principal → KPI.

---

# 4. Tipos de gráficos recomendados

## 4.1 Barra vertical

### Uso

Comparar categorias com nomes curtos.

### Exemplos

- Vendas por mês, se poucos meses.
- Compras por fornecedor.
- Quantidade por status.
- Produtos por grupo.

### Perguntas

- “Compare vendas por mês.”
- “Mostre compras por fornecedor.”
- “Quais grupos têm mais produtos?”

---

## 4.2 Barra horizontal

### Uso

Ranking com nomes longos.

### Exemplos

- Top clientes por faturamento.
- Top produtos vendidos.
- Fornecedores por volume de compra.
- Produtos com maior estoque.

### Por que é importante

Nomes de clientes, fornecedores e produtos costumam ser longos. Em barra vertical, os rótulos ficam ruins. Barra horizontal melhora leitura.

### Perguntas

- “Mostre ranking de clientes.”
- “Top 10 produtos mais vendidos.”
- “Fornecedores com maior compra.”
- “Produtos com maior saldo.”

---

## 4.3 Linha

### Uso

Séries temporais.

### Exemplos

- Vendas por mês.
- Faturamento por semana.
- Estoque ao longo do tempo.
- Preço médio por período.
- OEE por dia.
- Produção por semana.

### Perguntas

- “Mostre evolução das vendas.”
- “Faça gráfico de linha do faturamento mensal.”
- “Compare este mês com o mês passado.”
- “Mostre tendência do indicador.”

---

## 4.4 Área

### Uso

Série temporal com volume/acumulado.

### Exemplos

- Faturamento acumulado.
- Produção acumulada.
- Consumo de material ao longo do tempo.
- Volume mensal de compras.

### Perguntas

- “Mostre evolução acumulada.”
- “Mostre o volume ao longo do tempo.”
- “Faça gráfico de área das compras mensais.”

---

## 4.5 Pizza

### Uso

Participação percentual com poucas categorias.

### Exemplos

- Participação de clientes no faturamento.
- Distribuição de vendas por grupo.
- Compras por fornecedor.
- Status de pedidos.

### Regra

Usar pizza apenas com poucas categorias, preferencialmente até 6.

### Evitar

- Muitas fatias.
- Valores muito parecidos.
- Série temporal.
- Ranking longo.

---

## 4.6 Rosca

### Uso

Mesma lógica da pizza, mas com melhor leitura visual e espaço central para total ou indicador.

### Exemplos

- Participação por status.
- Distribuição por departamento.
- Share de compras por fornecedor.
- Mix de produtos vendidos.

### Vantagem

Permite exibir no centro:

- total;
- valor principal;
- percentual dominante;
- legenda curta.

---

## 4.7 Barra agrupada

### Uso

Comparar duas ou mais séries por categoria.

### Exemplos

- Compra x venda por mês.
- Programado x produzido.
- Meta x realizado.
- Quantidade vendida x entregue.
- Ano atual x ano anterior.

### Perguntas

- “Compare venda e compra por mês.”
- “Mostre meta versus realizado.”
- “Compare produzido e programado.”
- “Compare 2025 com 2026.”

---

## 4.8 Barra empilhada

### Uso

Mostrar composição dentro de cada categoria.

### Exemplos

- Vendas por mês separadas por cliente.
- Produção por status por semana.
- Compras por tipo de fornecedor.
- Estoque por armazém e status.

### Cuidados

Funciona melhor com poucas séries. Muitas cores poluem.

---

## 4.9 Linha múltipla

### Uso

Comparar tendências de várias séries ao longo do tempo.

### Exemplos

- Vendas de dois produtos.
- Faturamento por cliente ao longo dos meses.
- Indicadores por departamento.
- Preço médio de fornecedores.

### Regra

Limitar número de linhas. Acima de 5 séries, sugerir filtro.

---

## 4.10 Dispersão

### Uso futuro

Relação entre duas medidas numéricas.

### Exemplos

- Preço x quantidade.
- Lead time x valor de compra.
- Estoque x vendas.
- Refugo x produção.

### Perguntas

- “Existe relação entre preço e quantidade?”
- “Compare lead time e volume comprado.”
- “Mostre dispersão de estoque versus venda.”

---

## 4.11 Histograma

### Uso futuro

Distribuição de valores numéricos.

### Exemplos

- Distribuição de prazos de entrega.
- Distribuição de preços.
- Distribuição de lead time.
- Distribuição de tempos de produção.

### Perguntas

- “Como estão distribuídos os prazos?”
- “A maioria dos preços está em qual faixa?”
- “Mostre distribuição de lead time.”

---

## 4.12 Heatmap

### Uso futuro

Matriz de intensidade.

### Exemplos

- Vendas por mês e cliente.
- Produção por dia e turno.
- Ocorrências por setor e status.
- Faturamento por região e período.

### Perguntas

- “Mostre mapa de calor das vendas por mês e cliente.”
- “Quais dias têm maior produção?”
- “Onde estão concentradas as ocorrências?”

---

## 4.13 Gauge / velocímetro

### Uso futuro

Indicador com meta/faixas.

### Exemplos

- OEE.
- OTD.
- Atingimento de meta.
- SLA.
- Eficiência.

### Observação

Pode ser substituído por KPI card com barra de progresso se quiser evitar visual poluído.

---

## 4.14 Combo chart

### Uso futuro

Combinar barra e linha.

### Exemplos

- Vendas em barra e margem em linha.
- Quantidade em barra e ticket médio em linha.
- Faturamento em barra e meta em linha.

### Perguntas

- “Mostre faturamento e margem.”
- “Compare volume e preço médio.”
- “Mostre realizado e meta.”

---

# 5. Contrato de dados recomendado

Hoje o tipo `chart` aceita:

```ts
{
  type: "chart";
  title: string;
  chartType: "bar" | "line" | "pie" | "area";
  data: Record<string, unknown>[];
  config?: {
    xAxis?: string;
    yAxis?: string | string[];
    colors?: string[];
    legend?: boolean;
  };
}
```

## Evolução sugerida

Ampliar `chartType` para:

```ts
type ChartType =
  | "bar"
  | "horizontal_bar"
  | "stacked_bar"
  | "grouped_bar"
  | "line"
  | "multi_line"
  | "area"
  | "stacked_area"
  | "pie"
  | "donut"
  | "scatter"
  | "histogram"
  | "heatmap"
  | "combo"
  | "gauge";
```

## Novo contrato

```ts
export type ChartPresentation = {
  type: "chart";
  title: string;
  chartType: ChartType;
  data: Record<string, unknown>[];
  config?: {
    xAxis?: string;
    yAxis?: string | string[];
    series?: {
      key: string;
      label?: string;
      type?: "bar" | "line" | "area";
      axis?: "left" | "right";
      stackId?: string;
    }[];
    categoryKey?: string;
    valueKey?: string;
    dateKey?: string;
    groupKey?: string;
    colors?: string[];
    legend?: boolean;
    stacked?: boolean;
    orientation?: "vertical" | "horizontal";
    showDataLabels?: boolean;
    percent?: boolean;
    unit?: string;
    currency?: string;
    maxSlices?: number;
    aggregation?: "sum" | "avg" | "count" | "min" | "max";
  };
};
```

---

# 6. Critérios automáticos de escolha

Criar serviço:

`ChatChartRecommendationService`

## Entrada

- colunas da tabela;
- tipos de dados;
- quantidade de linhas;
- cardinalidade das categorias;
- presença de datas;
- presença de valores numéricos;
- intenção do usuário;
- preferência explícita;
- tipo de rota/action;
- metadados da apresentação.

## Saída

```json
{
  "chartType": "line",
  "reason": "dados temporais com valor numérico",
  "xAxis": "month",
  "yAxis": ["total_value"],
  "fallback": "table"
}
```

---

# 7. Regras de decisão

## Dados com data + número

Usar linha.

Exemplo:

| mês | faturamento |
|---|---:|
| Jan | 100 |
| Fev | 120 |

Recomendação:

```json
{
  "chartType": "line",
  "xAxis": "month",
  "yAxis": "faturamento"
}
```

---

## Dados com data + número acumulado

Usar área.

---

## Categoria curta + valor

Usar barra vertical.

---

## Categoria longa + valor

Usar barra horizontal.

Exemplos de categoria longa:

- cliente;
- fornecedor;
- descrição de produto;
- nome de item.

---

## Categoria + percentual ou participação

Usar donut ou pizza.

Regra:

- até 6 categorias: donut/pizza;
- acima de 6: barra horizontal com “Outros”.

---

## Duas séries por categoria

Usar barra agrupada.

Exemplo:

- vendido x entregue;
- meta x realizado;
- comprado x vendido.

---

## Séries empilháveis

Usar barra empilhada.

Exemplo:

- status por mês;
- cliente por mês;
- armazém por produto.

---

## Hierarquia

Usar árvore, não gráfico.

---

## Indicador único

Usar KPI.

---

## Muitos dados detalhados

Usar tabela e sugerir gráfico.

---

# 8. Como lidar com dados temporais

## Normalização de datas

O backend deve converter datas para formato consistente.

Campos possíveis:

- `date`;
- `month`;
- `year_month`;
- `period`;
- `emission_date`;
- `delivery_date`;
- `created_at`.

## Formatos recomendados

Para gráfico mensal:

```json
{
  "period": "2026-05",
  "label": "mai/2026",
  "total": 12345.67
}
```

Para gráfico diário:

```json
{
  "date": "2026-05-30",
  "label": "30/05",
  "total": 120
}
```

## Ordenação

Sempre ordenar datas cronologicamente, não alfabeticamente.

Errado:

```text
abr, ago, dez, fev
```

Certo:

```text
jan, fev, mar, abr
```

---

# 9. Pie e donut

## Quando usar

- participação por cliente;
- mix de produto;
- status de pedidos;
- compras por fornecedor;
- ocorrências por categoria.

## Regras

1. Máximo recomendado: 6 fatias.
2. Se passar de 6, agrupar menores em “Outros”.
3. Mostrar percentual e valor no tooltip.
4. Evitar quando todos valores são muito parecidos.
5. Não usar para série temporal.

## Donut recomendado como padrão

Preferir `donut` sobre `pie`, porque:

- visualmente mais moderno;
- permite total no centro;
- funciona melhor em dashboards;
- reduz poluição visual.

---

# 10. Barra horizontal

## Quando usar

- nomes longos;
- ranking;
- top N;
- produtos;
- clientes;
- fornecedores;
- descrições.

## Exemplo de pergunta

> Top 10 clientes por faturamento.

Contrato:

```json
{
  "type": "chart",
  "title": "Top 10 clientes por faturamento",
  "chartType": "horizontal_bar",
  "data": [
    { "cliente": "Cliente A", "faturamento": 100000 },
    { "cliente": "Cliente B", "faturamento": 85000 }
  ],
  "config": {
    "xAxis": "faturamento",
    "yAxis": "cliente",
    "orientation": "horizontal"
  }
}
```

---

# 11. Barra agrupada

## Quando usar

- vendido x entregue;
- programado x produzido;
- meta x realizado;
- compras x vendas;
- ano atual x ano anterior.

Contrato:

```json
{
  "type": "chart",
  "title": "Vendido x Entregue por mês",
  "chartType": "grouped_bar",
  "data": [
    { "mes": "jan/2026", "vendido": 100, "entregue": 90 },
    { "mes": "fev/2026", "vendido": 120, "entregue": 110 }
  ],
  "config": {
    "xAxis": "mes",
    "yAxis": ["vendido", "entregue"],
    "legend": true
  }
}
```

---

# 12. Combo chart

## Quando usar

Combinar medidas com naturezas diferentes.

Exemplo:

- faturamento em barra;
- margem em linha.

Contrato:

```json
{
  "type": "chart",
  "title": "Faturamento e margem por mês",
  "chartType": "combo",
  "data": [
    { "mes": "jan/2026", "faturamento": 100000, "margem": 18.5 }
  ],
  "config": {
    "xAxis": "mes",
    "series": [
      { "key": "faturamento", "label": "Faturamento", "type": "bar", "axis": "left" },
      { "key": "margem", "label": "Margem %", "type": "line", "axis": "right" }
    ]
  }
}
```

---

# 13. Heatmap

## Quando usar

Para matriz de intensidade.

Exemplo:

- mês x cliente;
- dia x turno;
- departamento x status.

Contrato:

```json
{
  "type": "chart",
  "title": "Vendas por cliente e mês",
  "chartType": "heatmap",
  "data": [
    { "cliente": "Cliente A", "mes": "jan/2026", "valor": 10000 },
    { "cliente": "Cliente A", "mes": "fev/2026", "valor": 12000 }
  ],
  "config": {
    "xAxis": "mes",
    "yAxis": "cliente",
    "valueKey": "valor"
  }
}
```

---

# 14. Histogramas

## Quando usar

Para distribuição de uma métrica.

Exemplo:

- lead time;
- preço unitário;
- tempo de produção;
- atraso em dias.

Contrato:

```json
{
  "type": "chart",
  "title": "Distribuição do lead time",
  "chartType": "histogram",
  "data": [
    { "faixa": "0-5 dias", "quantidade": 10 },
    { "faixa": "6-10 dias", "quantidade": 22 }
  ],
  "config": {
    "xAxis": "faixa",
    "yAxis": "quantidade"
  }
}
```

---

# 15. UX recomendada

## Toolbar de gráfico

Adicionar botões:

- Baixar PNG.
- Expandir.
- Ver como tabela.
- Trocar tipo de gráfico.
- Explicar gráfico.
- Filtrar período.
- Comparar período anterior.

## Alternância de visualização

Hoje existe alternância entre Texto, Gráfico, Árvore e Tabela.

Evolução:

- dentro da aba “Gráfico”, permitir trocar:
  - barra;
  - linha;
  - área;
  - pizza;
  - rosca;
  - barra horizontal.

## Menu “Alterar visualização”

Botão:

> Alterar gráfico

Opções:

- Linha.
- Barra.
- Barra horizontal.
- Pizza.
- Rosca.
- Área.
- Tabela.

---

# 16. Drill-down em gráficos

O projeto já possui menu de ações em pontos do gráfico.

Ampliar ações por tipo:

## Linha/área

Clique no mês:

- Ver registros do mês.
- Comparar mês anterior.
- Ver clientes do mês.
- Ver produtos do mês.

## Barra

Clique na categoria:

- Detalhar categoria.
- Ver registros.
- Comparar com outras.
- Filtrar por categoria.

## Pizza/rosca

Clique na fatia:

- Detalhar fatia.
- Ver registros da categoria.
- Comparar participação.
- Filtrar por categoria.

## Heatmap

Clique na célula:

- Ver registros da célula.
- Comparar linha.
- Comparar coluna.

---

# 17. Texto explicativo junto ao gráfico

Todo gráfico deve vir com uma leitura automática curta.

Exemplo:

```md
O faturamento cresceu entre janeiro e março, com queda em abril.
O maior valor ocorreu em março.
```

Para pizza/rosca:

```md
O cliente A concentra 42% do valor total.
```

Para ranking:

```md
Os 3 primeiros clientes representam 68% do total.
```

---

# 18. Fallbacks

## Sem dados suficientes

```md
Não há dados suficientes para gerar um gráfico útil. Organizei em tabela.
```

## Muitas categorias

```md
Há muitas categorias para pizza/rosca. Usei barra horizontal para melhorar a leitura.
```

## Dados sem número

```md
Não encontrei coluna numérica para montar gráfico. Mostrei em tabela.
```

## Datas não ordenáveis

```md
Não consegui identificar uma sequência temporal confiável. Mostrei os dados em tabela.
```

---

# 19. Backend: presenter

Criar ou evoluir:

`ChatChartPresentationService`

Funções:

- detectar colunas temporais;
- detectar colunas categóricas;
- detectar colunas numéricas;
- agregar dados;
- ordenar;
- limitar top N;
- agrupar “Outros”;
- recomendar chartType;
- criar `tablePresentation` de fallback;
- criar texto explicativo.

---

# 20. Backend: metadados úteis

Adicionar em `metadata`:

```json
{
  "presentation": {
    "type": "chart",
    "chartType": "line"
  },
  "tablePresentation": {},
  "chartRecommendation": {
    "reason": "Série temporal detectada",
    "alternatives": ["area", "bar"],
    "fallback": "table"
  },
  "availableChartTypes": ["line", "area", "bar", "table"]
}
```

---

# 21. Frontend: componentes

## Evoluir `ChatRichChart`

Adicionar renderização para:

- `horizontal_bar`;
- `donut`;
- `grouped_bar`;
- `stacked_bar`;
- `multi_line`;
- `stacked_area`;
- `combo`;
- `scatter`;
- `histogram`;
- `heatmap`;
- `gauge`.

## Componentes auxiliares

- `ChatChartTypeSwitcher`.
- `ChatChartInsight`.
- `ChatChartLegend`.
- `ChatChartEmptyState`.
- `ChatChartConfigMenu`.

---

# 22. Recharts: mapeamento sugerido

| Tipo | Recharts |
|---|---|
| bar | `BarChart` |
| horizontal_bar | `BarChart layout="vertical"` |
| grouped_bar | `BarChart` com várias `Bar` |
| stacked_bar | `BarChart` com `stackId` |
| line | `LineChart` |
| multi_line | `LineChart` com várias `Line` |
| area | `AreaChart` |
| stacked_area | `AreaChart` com `stackId` |
| pie | `PieChart` + `Pie` |
| donut | `PieChart` + `Pie innerRadius` |
| scatter | `ScatterChart` |
| combo | `ComposedChart` |
| heatmap | componente custom ou grade SVG |
| gauge | `RadialBarChart` ou KPI custom |
| histogram | `BarChart` com bins |

---

# 23. Tabelas continuam essenciais

Todo gráfico deve ter fallback de tabela.

Por quê?

- auditoria;
- exportação;
- detalhes;
- acessibilidade;
- conferência dos valores;
- drill-down.

Regra:

> Se houver gráfico, mantenha tabela disponível como visualização alternativa.

---

# 24. Acessibilidade

Gráficos devem ter:

- título;
- descrição curta;
- tabela alternativa;
- tooltip legível;
- contraste adequado;
- não depender só de cor;
- labels quando necessário;
- navegação por teclado, se possível.

---

# 25. Performance

Cuidados:

- limitar pontos exibidos;
- agrupar por período;
- usar top N;
- paginar tabela;
- não renderizar 500 categorias;
- usar expansão para gráficos grandes;
- calcular agregação no backend quando possível.

---

# 26. Boas práticas visuais

## Linha

- usar para tempo;
- evitar muitas séries;
- ordenar datas;
- mostrar pontos apenas se útil.

## Barra

- começar eixo em zero;
- ordenar rankings;
- usar horizontal para nomes longos.

## Pizza/rosca

- máximo 6 fatias;
- agrupar “Outros”;
- mostrar total;
- evitar categorias similares demais.

## Área

- usar para volume/acumulado;
- cuidado com sobreposição.

## KPI

- usar para números principais;
- incluir delta e tendência;
- indicar meta.

---

# 27. Exemplos por área DELPI

## Comercial

- Faturamento por mês → linha.
- Top clientes → barra horizontal.
- Participação por cliente → donut.
- Vendas por produto → barra.
- Ano atual x anterior → barra agrupada.

## Compras

- Compras por fornecedor → barra horizontal.
- Evolução de preço → linha.
- Participação por fornecedor → donut.
- Lead time por fornecedor → barra.
- Distribuição de lead time → histograma.

## Estoque

- Saldo por armazém → barra.
- Produtos com maior saldo → barra horizontal.
- Evolução do estoque → linha.
- Composição por depósito → donut.
- Itens críticos → KPI + tabela.

## Produção

- Programado x produzido → barra agrupada.
- Produção por dia → linha.
- Refugo por motivo → barra.
- OEE → KPI/gauge.
- Produção por turno → heatmap.

## Qualidade

- Não conformidades por mês → linha.
- Motivos de rejeição → barra.
- Distribuição por status → donut.
- Indicadores de qualidade → KPI.

## Financeiro

- Receita por mês → linha/área.
- Despesas por categoria → donut.
- Fluxo mensal → combo.
- Atingimento de meta → KPI/gauge.

---

# 28. Interação por linguagem natural

O chat deve entender:

- “em linha”;
- “em pizza”;
- “em rosca”;
- “barra horizontal”;
- “ranking”;
- “evolução”;
- “tendência”;
- “participação”;
- “distribuição”;
- “meta versus realizado”;
- “comparar períodos”.

## Mapeamento

| Termo do usuário | Tipo |
|---|---|
| evolução | line |
| tendência | line |
| acumulado | area |
| participação | donut/pie |
| fatia | pie/donut |
| ranking | horizontal_bar |
| top 10 | horizontal_bar |
| meta x realizado | grouped_bar/kpi |
| distribuição | histogram |
| mapa de calor | heatmap |

---

# 29. Chips pós-gráfico

Após gráfico, oferecer:

- Ver tabela.
- Explicar gráfico.
- Comparar período anterior.
- Baixar PNG.
- Filtrar período.
- Agrupar por cliente.
- Trocar para linha.
- Trocar para barra.
- Colocar na lousa.

---

# 30. Testes

## Frontend

- Render bar.
- Render line.
- Render pie.
- Render area.
- Render donut.
- Render horizontal bar.
- Render grouped bar.
- Render stacked bar.
- Render empty chart.
- Export PNG.
- Expand modal.
- Drill-down por ponto.

## Backend

- Detecta data + número → line.
- Detecta ranking → horizontal_bar.
- Detecta participação → donut.
- Detecta muitas categorias → horizontal_bar.
- Detecta indicador único → KPI.
- Ordena datas.
- Agrupa “Outros”.
- Gera fallback table.

## Integração

- “mostre vendas por mês em linha”.
- “faça pizza por cliente”.
- “top 10 produtos em barra horizontal”.
- “compare meta e realizado”.
- “transforme essa tabela em gráfico”.
- “explique esse gráfico”.

---

# 31. Roadmap

## Fase 1 — Consolidar o que já existe

- Garantir uso real de `line`, `pie` e `area`.
- Criar exemplos de payload.
- Criar testes.
- Ajustar seleção automática.
- Melhorar texto explicativo.

## Fase 2 — Novos tipos simples

- `horizontal_bar`.
- `donut`.
- `grouped_bar`.
- `stacked_bar`.
- `multi_line`.

## Fase 3 — Tipos analíticos

- `scatter`.
- `histogram`.
- `combo`.
- `gauge`.

## Fase 4 — Visualizações avançadas

- `heatmap`.
- dashboard multi-card.
- mini dashboards por agente.
- recomendações automáticas.

## Fase 5 — UX avançada

- alternar tipo de gráfico no front;
- filtros interativos;
- zoom temporal;
- comparação de períodos;
- salvar gráfico na lousa;
- exportar dashboard.

---

# 32. Métricas

- gráficos gerados por tipo;
- taxa de troca para tabela;
- exportações PNG;
- cliques em pontos;
- feedback “formato ruim”;
- uso de gráfico sugerido;
- taxa de fallback para tabela;
- tempo de renderização;
- número de categorias por gráfico;
- uso de chips pós-gráfico.

---

# 33. Anti-padrões

Evitar:

1. Pizza com 20 fatias.
2. Linha para categorias sem tempo.
3. Barra vertical com rótulos enormes.
4. Gráfico sem tabela alternativa.
5. Gráfico sem título.
6. Dados temporais fora de ordem.
7. Usar cores demais.
8. Usar gráfico quando tabela é melhor.
9. Misturar unidades incompatíveis no mesmo eixo.
10. Não explicar o insight principal.

---

# 34. Exemplo de resposta ideal

Usuário:

> Mostre vendas por mês em gráfico.

Resposta:

```md
Montei a evolução mensal das vendas.

O maior valor ocorreu em março, e houve queda em abril.
```

Visualização:

- gráfico de linha;
- tabela alternativa;
- chips:
  - Ver tabela;
  - Comparar mês anterior;
  - Baixar PNG;
  - Agrupar por cliente;
  - Colocar na lousa.

---

# 35. Resumo executivo

A plataforma já tem uma boa base: tabela, KPI, árvore e gráfico, além de suporte técnico inicial para barra, linha, pizza e área no front. A evolução recomendada é ampliar o contrato de `chartType`, criar um serviço de recomendação automática de gráficos, suportar novos tipos como rosca e barra horizontal, e melhorar a UX com troca de visualização, drill-down e explicação automática.

A regra principal é simples:

> Temporal vira linha ou área; ranking vira barra horizontal; participação vira rosca; comparação vira barra agrupada; hierarquia vira árvore; número único vira KPI; detalhe vira tabela.
