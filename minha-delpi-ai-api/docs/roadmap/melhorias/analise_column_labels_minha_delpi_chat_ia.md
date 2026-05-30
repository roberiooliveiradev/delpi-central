# Análise e sugestões — `column_labels.json`

Arquivo analisado:

`minha-delpi-ai-api/app/content/pt-BR/assistant/column_labels.json`

## Objetivo do arquivo

O `column_labels.json` funciona como um dicionário de apresentação dos dados retornados pela API.

Ele traduz nomes técnicos ou padronizados de campos para nomes amigáveis em português, por exemplo:

| Campo interno | Rótulo exibido |
|---|---|
| `code` | Código |
| `description` | Descrição |
| `product_code` | Produto |
| `product_description` | Descrição produto |
| `current_quantity` | Qtd. atual |
| `available_quantity` | Qtd. disponível |
| `supplier_name` | Fornecedor |
| `customer_name` | Cliente |
| `invoice_number` | Nº nota |
| `sale_number` | Nº OV |
| `production_order` | Ordem produção |
| `kpi_label` | Indicador |

Além disso, o arquivo define perfis de tabela para identificar automaticamente o tipo de resposta e escolher colunas preferenciais.

---

# Perfis encontrados

O arquivo possui uma lista de prioridade para perfis de tabela:

1. Estoque
2. Produção
3. LMP
4. Nota fiscal
5. Roteiro
6. Inspeção
7. Movimentação
8. Preço
9. Fornecedor
10. Cliente
11. KPI

Esses perfis ajudam o chat a entender o tipo de dado retornado e apresentar as colunas mais úteis para o usuário.

---

# 1. Perfil: Estoque

## Detecção

O perfil de estoque é identificado quando aparecem campos como:

- `current_quantity`
- `available_quantity`

## Colunas preferenciais

- Filial
- Armazém
- Produto
- Qtd. atual
- Qtd. disponível
- Qtd. empenhada
- Qtd. reservada
- Localização
- Centro de custo

## Perguntas ricas sugeridas

- Qual é o estoque atual do produto `10080001`?
- Mostre o saldo disponível por armazém.
- Esse produto tem quantidade empenhada?
- Existe quantidade reservada para esse item?
- Qual é o estoque físico versus estoque disponível?
- Mostre produtos com saldo disponível abaixo do mínimo.
- Liste produtos sem saldo no armazém principal.
- Quais produtos têm quantidade reservada maior que disponível?
- Mostre o estoque do produto por filial.
- Gere uma tabela com estoque atual, disponível, empenhado e reservado.

## Sugestões de resposta enriquecida

Quando o resultado for de estoque, o chat pode responder com:

- Resumo do saldo total.
- Tabela por filial e armazém.
- Destaque de quantidade disponível.
- Alerta quando a quantidade disponível for zero ou negativa.
- Alerta quando a quantidade empenhada for maior que a atual.
- Sugestão de consultar compras, fornecedores ou estruturas relacionadas.

## Perguntas combinadas

- Esse item tem estoque suficiente e quem fornece?
- Onde esse produto está armazenado e em quais estruturas é usado?
- O produto tem saldo disponível, vendas recentes e compras em aberto?
- Quais produtos vendidos recentemente estão sem estoque?
- Quais componentes críticos estão com estoque baixo?

---

# 2. Perfil: Nota fiscal

## Detecção

O perfil de nota fiscal é identificado por:

- `invoice_number`

## Colunas preferenciais

- Nº nota
- Série
- Fornecedor
- Cliente
- Data emissão
- Quantidade
- Preço unitário
- Valor total

## Perguntas ricas sugeridas

- Mostre as notas fiscais de entrada do produto `10080001`.
- Mostre as notas fiscais de saída desse item.
- Qual foi a última nota fiscal desse produto?
- Liste notas fiscais por cliente.
- Liste notas fiscais por fornecedor.
- Mostre nota, série, data, quantidade e valor total.
- Quais notas fiscais têm esse produto?
- Compare notas fiscais com pedidos de venda.
- Compare notas fiscais com compras.
- Liste notas fiscais emitidas em determinado período.

## Sugestões de resposta enriquecida

- Separar entrada e saída quando possível.
- Mostrar valor total por nota.
- Agrupar por cliente ou fornecedor.
- Destacar última emissão.
- Somar quantidade e valor no final.
- Permitir continuação com “mais linhas” ou “próxima página”.

## Perguntas combinadas

- Esse produto foi faturado recentemente?
- Mostre notas de saída e clientes relacionados.
- Compare vendas com notas fiscais de saída.
- Compare compras com notas fiscais de entrada.
- Quais produtos tiveram nota fiscal, mas não têm estoque atual?

---

# 3. Perfil: Roteiro de produção

## Detecção

O perfil de roteiro é identificado por grupos de campos como:

- `operation_code` + `operation_description`
- `step` + `sequence`

## Colunas preferenciais

- Filial
- Cód. roteiro
- Produto
- Cód. operação
- Descrição operação
- Cód. recurso
- Centro de trabalho
- Setup
- Tempo padrão
- Tipo operação
- Operação obrigatória
- Sequência obrigatória
- Apontamento obrigatório
- Componente
- Nível BOM
- Máquina
- Tempo operação

## Perguntas ricas sugeridas

- Mostre o roteiro de produção do produto `10080001`.
- Quais etapas fazem parte desse roteiro?
- Quais operações são obrigatórias?
- Qual é o tempo padrão por peça?
- Quais máquinas são usadas nesse roteiro?
- Quais centros de trabalho aparecem?
- Mostre setup e tempo de operação.
- Compare o roteiro de dois produtos.
- Quais componentes aparecem no roteiro?
- Explique esse roteiro em linguagem simples.

## Sugestões de resposta enriquecida

- Apresentar em ordem de sequência.
- Separar operação, recurso, centro de trabalho e tempo.
- Destacar operações obrigatórias.
- Somar tempos quando fizer sentido.
- Indicar possíveis gargalos por maior tempo de operação.
- Oferecer comparação com estrutura/BOM.

## Perguntas combinadas

- Mostre roteiro, estrutura e estoque dos componentes.
- O produto tem roteiro e LMP cadastrados?
- Compare roteiro e estrutura entre dois produtos.
- Quais operações podem impactar o prazo de produção?
- Existe componente da BOM que não aparece no roteiro?

---

# 4. Perfil: Inspeção

## Detecção

O perfil de inspeção é identificado por:

- `inspection_type`
- ou conjunto `characteristic` + `specification`

## Colunas preferenciais

- Tipo inspeção
- Sequência
- Característica
- Especificação
- Método
- Frequência
- Resultado

## Perguntas ricas sugeridas

- Mostre o plano de inspeção do produto `10080001`.
- Quais características são inspecionadas?
- Qual é a especificação esperada?
- Qual método de inspeção deve ser usado?
- Qual é a frequência de inspeção?
- Esse produto tem inspeção cadastrada?
- Liste produtos sem plano de inspeção.
- Compare inspeção de dois produtos.
- Mostre resultados de inspeção por lote.
- Explique o plano de inspeção em linguagem simples.

## Sugestões de resposta enriquecida

- Mostrar característica, especificação e método juntos.
- Destacar resultados reprovados.
- Destacar frequência de inspeção.
- Agrupar por tipo de inspeção.
- Sugerir verificar qualidade ou lote quando houver reprovação.

## Perguntas combinadas

- Esse produto tem inspeção e roteiro cadastrados?
- A inspeção está coerente com o tipo de produto?
- Quais lotes foram rejeitados?
- Mostre inspeção, nota fiscal e fornecedor do item.
- Existe inspeção para produtos críticos sem fornecedor alternativo?

---

# 5. Perfil: Movimentação

## Detecção

O perfil de movimentação é identificado por:

- `origin_warehouse`
- `destination_warehouse`

## Colunas preferenciais

- Data
- Operação
- Armazém origem
- Armazém destino
- Quantidade
- Documento
- Lote

## Perguntas ricas sugeridas

- Mostre movimentações internas do produto `10080001`.
- Esse item teve transferência entre armazéns?
- Qual foi a última movimentação interna?
- Mostre origem, destino e quantidade.
- Liste movimentações por período.
- Mostre movimentações por lote.
- Quais documentos geraram movimentações?
- Compare movimentações com estoque atual.
- Quais produtos tiveram transferência recente?
- Identifique movimentações atípicas.

## Sugestões de resposta enriquecida

- Ordenar por data mais recente.
- Separar entradas, saídas e transferências.
- Mostrar origem e destino.
- Somar quantidade movimentada.
- Destacar lote quando houver rastreabilidade.
- Sugerir consultar estoque atual após movimentos relevantes.

## Perguntas combinadas

- Esse produto teve transferência e qual o saldo atual?
- Movimentações recentes explicam a queda de estoque?
- Quais produtos foram transferidos para o armazém principal?
- Mostre estoque atual e últimas movimentações.
- Quais lotes foram movimentados recentemente?

---

# 6. Perfil: Preço

## Detecção

O perfil de preço é identificado por:

- `table_code`
- `sale_price`

## Colunas preferenciais

- Cód. tabela
- Tabela
- Preço venda
- Preço máx.
- Desconto
- % Desconto

## Perguntas ricas sugeridas

- Qual é o preço do produto `10080001`?
- Mostre a tabela de preço desse produto.
- Existe preço cadastrado?
- Qual é o preço máximo?
- Existe desconto cadastrado?
- Compare preço de venda com custo médio.
- Mostre preços por tabela.
- Qual foi o último preço de venda?
- Liste produtos sem preço cadastrado.
- Compare preços entre produtos similares.

## Sugestões de resposta enriquecida

- Mostrar preço por tabela.
- Destacar descontos.
- Comparar preço de venda com custo, se houver.
- Sinalizar ausência de preço.
- Sugerir consulta de vendas para verificar preço praticado.

## Perguntas combinadas

- Esse produto tem preço, estoque e vendas recentes?
- O preço de venda cobre o custo médio?
- Compare preço de compra, custo e preço de venda.
- Produtos sem preço têm estoque disponível?
- Quais produtos têm margem abaixo da meta?

---

# 7. Perfil: Fornecedor

## Detecção

O perfil de fornecedor é identificado por:

- `supplier_name`
- `supplier_code`

Desde que não seja uma resposta de nota fiscal.

## Colunas preferenciais

- Cód. fornecedor
- Fornecedor
- Part number
- Últ. preço
- Data últ. preço
- Lead time médio
- Lead time cadastrado
- Amostras

## Perguntas ricas sugeridas

- Quem fornece o produto `10080001`?
- Esse item tem fornecedor cadastrado?
- Qual é o part number do fornecedor?
- Qual foi o último preço do fornecedor?
- Qual é o lead time cadastrado?
- Qual é o lead time real médio?
- Compare lead time cadastrado e real.
- O fornecedor está atrasando em relação ao cadastro?
- Quais produtos têm fornecedor único?
- Liste fornecedores com maior lead time.

## Sugestões de resposta enriquecida

- Mostrar fornecedor, part number, último preço e lead time.
- Destacar diferença entre lead time cadastrado e real.
- Indicar número de amostras usadas no cálculo.
- Alertar quando não houver fornecedor.
- Sugerir consulta de compras ou notas de entrada.

## Perguntas combinadas

- Esse item tem fornecedor e estoque suficiente?
- O lead time real é maior que o cadastrado?
- Quem fornece os componentes críticos da estrutura?
- Produtos sem estoque têm fornecedor cadastrado?
- Quais itens dependem de fornecedor único e têm vendas recentes?

---

# 8. Perfil: Cliente

## Detecção

O perfil de cliente é identificado por:

- `customer_name`
- `customer_code`

Desde que não seja uma resposta de nota fiscal.

## Colunas preferenciais

- Cód. cliente
- Cliente
- Loja
- Data últ. venda
- Últ. preço venda
- Qtd. total
- Valor total

## Perguntas ricas sugeridas

- Quem compra o produto `10080001`?
- Quais clientes compraram esse item?
- Qual cliente mais comprou?
- Qual foi a última venda por cliente?
- Mostre valor total vendido por cliente.
- Mostre quantidade total por cliente.
- Quais clientes compraram produtos do grupo `1008`?
- Liste clientes sem venda recente.
- Compare clientes por faturamento.
- Mostre os clientes em tabela.

## Sugestões de resposta enriquecida

- Ordenar por valor total ou data da última venda.
- Mostrar quantidade e valor.
- Destacar último preço de venda.
- Agrupar por cliente e loja.
- Sugerir consulta de vendas ou notas de saída.

## Perguntas combinadas

- Esse produto tem clientes ativos e estoque disponível?
- Quais clientes compram itens sem estoque?
- Mostre clientes, vendas e notas fiscais de saída.
- Compare preço praticado por cliente.
- Quais clientes compraram componentes de um mesmo grupo?

---

# 9. Perfil: Produção

## Detecção

O perfil de produção é identificado por:

- `production_order`
- `scheduled_quantity`
- `produced_quantity`

## Colunas preferenciais

- Ordem produção
- Produto
- Data programada
- Qtd. programada
- Qtd. produzida
- Qtd. refugo
- Filial
- Status

## Perguntas ricas sugeridas

- Mostre ordens de produção do produto `10080001`.
- Quais OPs estão em aberto?
- Qual quantidade foi programada?
- Qual quantidade foi produzida?
- Houve refugo?
- Mostre produção por período.
- Compare quantidade programada e produzida.
- Liste OPs atrasadas.
- Quais produtos têm maior refugo?
- Mostre status das ordens de produção.

## Sugestões de resposta enriquecida

- Destacar diferença entre programado e produzido.
- Mostrar percentual de atendimento.
- Sinalizar refugo.
- Agrupar por status.
- Ordenar por data programada.
- Sugerir consultar roteiro, estrutura e estoque dos componentes.

## Perguntas combinadas

- Essa OP tem componentes com estoque suficiente?
- Compare produção programada e venda pendente.
- Quais produtos têm OP aberta e estoque baixo?
- Mostre OP, roteiro e estrutura do produto.
- Quais OPs têm refugo acima do normal?

---

# 10. Perfil: LMP

## Detecção

O perfil de LMP é identificado por:

- `sale_number`
- `sale_order`

## Colunas preferenciais

- Nº OV
- Produto
- Descrição
- Filial
- Status
- Data entrega
- Quantidade

## Perguntas ricas sugeridas

- Mostre a LMP da OV `123456`.
- Quais itens estão na LMP?
- Qual é o status da LMP?
- Quais produtos têm entrega próxima?
- Liste LMPs por data de entrega.
- Mostre quantidade por item.
- Quais LMPs estão pendentes?
- Compare LMP com estoque disponível.
- Quais itens da LMP não têm saldo?
- Explique a LMP em linguagem simples.

## Sugestões de resposta enriquecida

- Ordenar por data de entrega.
- Destacar status.
- Mostrar quantidade e produto.
- Sugerir consulta de estoque para itens pendentes.
- Sugerir consulta de estrutura para produtos fabricados.

## Perguntas combinadas

- Essa LMP tem estoque suficiente para atender?
- Quais itens da OV estão em risco?
- Mostre LMP, estoque e estrutura dos produtos.
- Quais produtos da LMP têm fornecedor crítico?
- Compare LMP com produção programada.

---

# 11. Perfil: KPI

## Detecção

O perfil de KPI é identificado por:

- `kpi_label`
- `kpi_value`

## Colunas preferenciais

- Indicador
- Valor
- Meta
- Variação
- Período
- Departamento

## Perguntas ricas sugeridas

- Mostre os KPIs do período.
- Quais indicadores estão abaixo da meta?
- Compare valor realizado com meta.
- Mostre variação por departamento.
- Faça um gráfico dos KPIs.
- Mostre indicadores por período.
- Quais departamentos estão fora da meta?
- Liste KPIs com maior variação negativa.
- Explique esse indicador.
- Resuma os principais KPIs em linguagem simples.

## Sugestões de resposta enriquecida

- Destacar indicadores abaixo da meta.
- Calcular variação percentual quando possível.
- Agrupar por departamento.
- Mostrar tendência por período.
- Sugerir gráfico quando houver série temporal.
- Separar indicadores bons, atenção e críticos.

## Perguntas combinadas

- Quais KPIs pioraram no mês?
- Quais departamentos estão abaixo da meta?
- Faça um resumo executivo dos indicadores.
- Mostre KPIs em gráfico.
- Explique a variação dos principais indicadores.

---

# Melhorias sugeridas para o `column_labels.json`

## 1. Adicionar descrições de negócio por campo

Além do rótulo curto, cada campo poderia ter uma descrição para tooltip ou explicação automática.

Exemplo:

```json
{
  "fieldDescriptions": {
    "available_quantity": "Quantidade disponível para uso, descontando reservas e empenhos quando aplicável.",
    "committed_quantity": "Quantidade já comprometida para pedidos, produção ou outras necessidades.",
    "reserved_quantity": "Quantidade reservada e ainda não liberada para uso geral."
  }
}
```

## 2. Adicionar agrupamentos por área

Isso facilitaria menus e respostas por contexto.

```json
{
  "fieldGroups": {
    "estoque": ["current_quantity", "available_quantity", "committed_quantity", "reserved_quantity"],
    "comercial": ["sale_price", "last_sale_price", "customer_name", "total_value"],
    "compras": ["supplier_name", "last_purchase_price", "lead_time_days"],
    "engenharia": ["route_code", "operation_code", "component_code", "bom_level"],
    "qualidade": ["inspection_type", "characteristic", "specification", "result"]
  }
}
```

## 3. Adicionar regras de destaque visual

```json
{
  "highlightRules": {
    "available_quantity": {
      "zero": "Sem saldo disponível",
      "negative": "Saldo disponível negativo",
      "low": "Saldo baixo"
    },
    "kpi_variance": {
      "negative": "Abaixo da meta",
      "positive": "Acima da meta"
    },
    "scrap_quantity": {
      "positive": "Houve refugo"
    }
  }
}
```

## 4. Adicionar perguntas sugeridas por perfil

```json
{
  "suggestedQuestionsByProfile": {
    "stock": [
      "Esse produto tem saldo disponível?",
      "Mostre estoque por armazém",
      "Compare estoque atual e reservado"
    ],
    "supplier": [
      "Quem fornece esse produto?",
      "Qual o lead time real do fornecedor?",
      "Esse item tem fornecedor alternativo?"
    ],
    "production": [
      "Quais OPs estão em aberto?",
      "Compare quantidade programada e produzida",
      "Houve refugo nessa produção?"
    ]
  }
}
```

## 5. Adicionar formatos de resposta recomendados

```json
{
  "recommendedOutputByProfile": {
    "stock": "table_with_summary",
    "kpi": "summary_plus_chart",
    "guide": "ordered_steps",
    "inspection": "checklist_table",
    "movement": "timeline_table"
  }
}
```

---

# Sugestão de menus baseados no `column_labels.json`

## Menu Estoque

- Consultar saldo
- Ver saldo por armazém
- Ver quantidade reservada
- Ver quantidade empenhada
- Comparar estoque de produtos
- Identificar produtos sem saldo

## Menu Fiscal

- Notas fiscais de entrada
- Notas fiscais de saída
- Última nota do produto
- Notas por cliente
- Notas por fornecedor
- Total por período

## Menu Engenharia

- Estrutura/BOM
- Roteiro de produção
- Componentes
- Operações
- Centro de trabalho
- Tempos padrão

## Menu Qualidade

- Plano de inspeção
- Características inspecionadas
- Especificações
- Métodos
- Frequência
- Resultados

## Menu Comercial

- Clientes do produto
- Última venda
- Preço de venda
- Tabela de preço
- Valor total vendido
- Comparativo por cliente

## Menu Compras

- Fornecedores
- Último preço de compra
- Lead time cadastrado
- Lead time real
- Part number
- Histórico de compras

## Menu Produção

- Ordens de produção
- Quantidade programada
- Quantidade produzida
- Refugo
- Status da OP
- Data programada

## Menu Indicadores

- KPIs do período
- Indicadores abaixo da meta
- Variação
- Meta versus realizado
- Indicadores por departamento
- Gráficos executivos

---

# Recomendações finais

O `column_labels.json` é essencial para transformar retornos técnicos da API em respostas compreensíveis para usuários finais.

A principal oportunidade é evoluir o arquivo de um simples dicionário de rótulos para um arquivo de inteligência de apresentação, contendo:

- Rótulos amigáveis.
- Descrições dos campos.
- Perfis de tabela.
- Colunas preferenciais.
- Perguntas sugeridas.
- Regras de destaque.
- Formato de saída recomendado.
- Alertas automáticos por tipo de dado.

Com isso, o Minha DELPI Chat IA pode entregar respostas mais úteis, como:

- “Saldo disponível baixo.”
- “Produto sem fornecedor cadastrado.”
- “Lead time real maior que o cadastrado.”
- “OP com refugo.”
- “KPI abaixo da meta.”
- “Produto vendido recentemente, mas sem estoque.”

Essas mensagens são mais valiosas para o usuário do que apenas mostrar a tabela bruta.
