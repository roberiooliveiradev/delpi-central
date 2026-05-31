# Análise e sugestões — `operational_parameters.json`

> **Status (31/05/2026):** [Concluído (referência arquivada)](./STATUS_ROADMAP_MELHORIAS.md).


Arquivo analisado:

`minha-delpi-ai-api/app/content/pt-BR/assistant/operational_parameters.json`

## Objetivo do arquivo

O `operational_parameters.json` centraliza mensagens de solicitação de parâmetros obrigatórios para consultas operacionais.

Ele é usado quando o usuário pede algo que depende de uma informação mínima, mas não fornece essa informação na pergunta.

Exemplos:

- Consulta de estoque sem código de produto.
- Consulta de estrutura/BOM sem código de produto.
- Consulta de onde o item é usado sem código de produto.
- Consulta de LMP ou ordem de venda sem número da OV.
- Consulta por período sem período informado.
- Consulta por filial sem filial informada.
- Período ambíguo, como mês sem ano.

O arquivo ajuda o assistente a fazer uma pergunta curta e objetiva, evitando inventar dados ou executar consultas incompletas.

---

# Estrutura encontrada

O arquivo possui estes blocos principais:

| Chave | Finalidade |
|---|---|
| `missingProductCode` | Mensagens quando falta código do produto |
| `missingSaleNumber` | Mensagem quando falta número da OV |
| `missingPeriod` | Mensagem quando falta período |
| `missingBranch` | Mensagem quando falta filial |
| `ambiguousPeriodYear` | Mensagem quando o mês foi informado sem ano claro |
| `ambiguousPeriodRange` | Mensagem quando há mais de uma interpretação de período |

---

# 1. Bloco `missingProductCode`

## Finalidade

Esse bloco orienta o usuário a informar o código do produto quando a consulta depende dele.

## Contextos existentes

- `stock` — estoque.
- `structure` — estrutura/BOM.
- `parents` — onde o produto é usado.
- `description` — descrição ou ficha do produto.
- `analyser` — ficha completa.
- `summary` — resumo consolidado.
- `default` — dados operacionais do produto.

## Perguntas que acionam esse bloco

- Qual o estoque desse produto?
- Mostre a estrutura.
- Onde esse item é usado?
- Abra a ficha completa.
- Faça o resumo consolidado do produto.
- Me fale desse item.
- Veja os fornecedores desse produto.
- Mostre as vendas desse item.
- Consulte o preço desse produto.
- Compare estoque e vendas desse item.

## Sugestões de melhoria

O bloco já cobre os principais casos, mas pode ser expandido para outros endpoints e intenções do `capabilities.json`.

### Novas chaves sugeridas

```json
{
  "missingProductCode": {
    "suppliers": "Para consultar os **fornecedores**, informe o **código do produto** (ex.: 10080099).",
    "customers": "Para consultar os **clientes que compram o produto**, informe o **código do produto** (ex.: 10080099).",
    "purchases": "Para consultar o **histórico de compras**, informe o **código do produto** (ex.: 10080099).",
    "sales": "Para consultar as **vendas do produto**, informe o **código do produto** (ex.: 10080099).",
    "prices": "Para consultar **preços ou tabelas de preço**, informe o **código do produto** (ex.: 10080099).",
    "guide": "Para consultar o **roteiro de produção**, informe o **código do produto** (ex.: 10080099).",
    "inspection": "Para consultar o **plano de inspeção**, informe o **código do produto** (ex.: 10080099).",
    "internalMovements": "Para consultar **movimentações internas**, informe o **código do produto** (ex.: 10080099).",
    "inboundInvoice": "Para consultar **notas fiscais de entrada**, informe o **código do produto** (ex.: 10080099).",
    "outboundInvoice": "Para consultar **notas fiscais de saída**, informe o **código do produto** (ex.: 10080099)."
  }
}
```

## Respostas mais ricas sugeridas

### Estoque sem código

> Para consultar o **estoque**, informe o **código do produto**.  
> Exemplo: `estoque do produto 10080099`.

### Estrutura sem código

> Para abrir a **estrutura/BOM**, preciso do **código do produto**.  
> Exemplo: `estrutura do produto 10080099`.

### Fornecedor sem código

> Para consultar **fornecedores**, informe o **código do produto**.  
> Exemplo: `quem fornece o produto 10080099`.

### Vendas sem código

> Para consultar **vendas**, informe o **código do produto** e, se quiser, um período.  
> Exemplo: `vendas do produto 10080099 nos últimos 30 dias`.

---

# 2. Chave `missingSaleNumber`

## Finalidade

Solicitar o número da OV quando a consulta envolve LMP ou ordem de venda.

## Perguntas que acionam esse bloco

- Mostre a LMP.
- Consulte a ordem de venda.
- Abra a OV.
- Quais itens estão na LMP?
- A OV está pendente?
- Mostre os itens dessa ordem.
- Compare a OV com nota fiscal.
- Quais itens da OV ainda não foram entregues?
- Mostre a LMP em tabela.
- Consulte os dados da ordem.

## Sugestões de melhoria

Adicionar variações para contextos diferentes:

```json
{
  "missingSaleNumberByContext": {
    "lmp": "Para consultar a **LMP**, informe o **número da OV** (ex.: 123456).",
    "saleOrder": "Para consultar a **ordem de venda**, informe o **número da OV** (ex.: 123456).",
    "delivery": "Para verificar **entregas da OV**, informe o **número da OV**.",
    "invoiceComparison": "Para comparar **OV e nota fiscal**, informe o **número da OV** e, se souber, o número da nota."
  }
}
```

## Resposta ideal

> Para consultar a **LMP** ou **ordem de venda**, informe o **número da OV**.  
> Exemplo: `consulte a OV 123456`.

---

# 3. Chave `missingPeriod`

## Finalidade

Solicitar período quando a consulta depende de datas.

## Perguntas que acionam esse bloco

- Mostre vendas.
- Mostre compras.
- Liste notas fiscais.
- Traga indicadores.
- Mostre produção.
- Quais produtos foram vendidos?
- Quais produtos foram comprados?
- Mostre movimentações.
- Gere gráfico de faturamento.
- Compare vendas por mês.

## Exemplos de períodos aceitos

- março de 2026
- últimos 30 dias
- 01/03/2026 a 31/03/2026
- hoje
- ontem
- esta semana
- semana passada
- este mês
- mês passado
- ano atual
- último trimestre

## Sugestões de melhoria

Adicionar mensagens por tipo de consulta:

```json
{
  "missingPeriodByContext": {
    "sales": "Para consultar **vendas**, informe o período (ex.: últimos 30 dias, março de 2026 ou 01/03/2026 a 31/03/2026).",
    "purchases": "Para consultar **compras**, informe o período desejado.",
    "invoices": "Para consultar **notas fiscais**, informe o período de emissão.",
    "movements": "Para consultar **movimentações**, informe o período.",
    "kpi": "Para consultar **indicadores**, informe o período ou competência.",
    "production": "Para consultar **produção programada**, informe o período."
  }
}
```

## Resposta ideal

> Para essa consulta, informe o **período desejado**.  
> Exemplos: `últimos 30 dias`, `março de 2026` ou `01/03/2026 a 31/03/2026`.

---

# 4. Chave `missingBranch`

## Finalidade

Solicitar filial quando o resultado precisa ser filtrado por filial.

## Perguntas que acionam esse bloco

- Mostre estoque da filial.
- Consulte vendas da matriz.
- Mostre produção da filial 01.
- Traga notas fiscais por filial.
- Liste compras da unidade.
- Mostre movimentos do armazém da filial.
- Compare filiais.
- Mostre indicadores da filial.
- Liste produtos sem estoque na filial.
- Mostre OPs da filial.

## Sugestões de melhoria

Adicionar exemplos mais completos:

```json
{
  "missingBranch": "Informe a **filial** desejada (ex.: `01`, `matriz`, `filial 02`) para eu filtrar o resultado."
}
```

Adicionar também:

```json
{
  "missingBranchByContext": {
    "stock": "Para consultar o **estoque por filial**, informe a filial desejada (ex.: 01 ou matriz).",
    "sales": "Para consultar **vendas por filial**, informe a filial desejada.",
    "production": "Para consultar **produção por filial**, informe a filial desejada.",
    "invoice": "Para consultar **notas por filial**, informe a filial desejada."
  }
}
```

## Resposta ideal

> Informe a **filial** desejada para filtrar o resultado.  
> Exemplo: `filial 01`, `matriz` ou `filial 02`.

---

# 5. Chave `ambiguousPeriodYear`

## Finalidade

Pedir confirmação do ano quando o usuário menciona um mês sem especificar o ano.

## Exemplo

Usuário:

> Mostre vendas de março.

Resposta:

> Para **março**, preciso confirmar o ano: você quer os dados de **2026** ou de **2025**?

## Perguntas que acionam esse bloco

- Mostre vendas de março.
- Traga compras de abril.
- Liste notas de janeiro.
- Mostre produção de maio.
- Indicadores de fevereiro.
- Faturamento de dezembro.
- Movimentações de junho.
- Compras de outubro.
- Vendas de novembro.
- Notas de julho.

## Sugestões de melhoria

Adicionar opção de padrão configurável:

```json
{
  "periodDefaults": {
    "monthWithoutYear": "ask_confirmation",
    "defaultYear": "current_year",
    "showAssumption": true
  }
}
```

Opções possíveis:

- `ask_confirmation`: pergunta antes de consultar.
- `current_year`: assume ano atual e informa a suposição.
- `last_occurrence`: assume a última ocorrência daquele mês.
- `business_rule`: segue regra da empresa.

## Resposta ideal

> Para **março**, preciso confirmar o ano. Você quer **março de 2026** ou **março de 2025**?

---

# 6. Chave `ambiguousPeriodRange`

## Finalidade

Pedir confirmação quando uma expressão de período pode ter mais de uma interpretação.

## Exemplos de ambiguidade

- “Semana passada” pode significar:
  - semana calendário anterior;
  - últimos 7 dias.

- “Último mês” pode significar:
  - mês calendário anterior;
  - últimos 30 dias.

- “Trimestre passado” pode significar:
  - trimestre calendário anterior;
  - últimos 3 meses.

## Perguntas que acionam esse bloco

- Mostre vendas da última semana.
- Traga compras do último mês.
- Mostre indicadores do trimestre passado.
- Liste produção do próximo período.
- Mostre notas recentes.
- Traga dados do fim do mês.
- Mostre movimentos da semana.
- Compare mês anterior.
- Mostre o acumulado recente.
- Consulte dados do período passado.

## Sugestões de melhoria

Adicionar exemplos de resolução:

```json
{
  "ambiguousPeriodRangeExamples": {
    "lastWeek": {
      "optionA": "semana passada (segunda a domingo)",
      "optionB": "últimos 7 dias"
    },
    "lastMonth": {
      "optionA": "mês passado fechado",
      "optionB": "últimos 30 dias"
    },
    "lastQuarter": {
      "optionA": "trimestre calendário anterior",
      "optionB": "últimos 3 meses"
    }
  }
}
```

## Resposta ideal

> Encontrei mais de uma interpretação de período. Você quer **semana passada (segunda a domingo)** ou **últimos 7 dias**?

---

# Perguntas ricas sugeridas por falta de parâmetro

## Quando falta código do produto

- Qual produto você quer consultar?
- Informe o código do produto.
- Você quer buscar por código ou descrição?
- Não tenho o código. Posso buscar por descrição?
- Quer procurar produtos parecidos?
- Você sabe o grupo do produto?
- Quer listar produtos de um grupo?
- Quer consultar por termo da descrição?
- O produto é matéria-prima, intermediário ou acabado?
- Quer usar um exemplo de código para testar?

## Quando falta OV

- Qual é o número da OV?
- Informe a OV para consultar a LMP.
- Você quer buscar por cliente em vez de OV?
- Você quer listar OVs de um período?
- Você tem o número do pedido?
- A consulta é de OV, LMP ou entrega?
- Quer consultar uma OV específica?
- Quer buscar OVs por produto?
- Quer buscar OVs por cliente?
- Quer buscar OVs pendentes?

## Quando falta período

- Qual período deseja consultar?
- Você quer este mês ou mês passado?
- Quer consultar os últimos 30 dias?
- Quer consultar por competência?
- Quer informar data inicial e final?
- O período é por emissão, entrega ou movimentação?
- Quer comparar com período anterior?
- Quer o acumulado do ano?
- Quer consultar apenas hoje?
- Quer consultar a semana atual?

## Quando falta filial

- Qual filial deseja consultar?
- Quer consultar a matriz?
- Quer consultar todas as filiais?
- Quer comparar filiais?
- A filial é 01, 02 ou outra?
- Quer filtrar por armazém também?
- Quer consolidado geral ou por filial?
- Quer separar filial por tabela?
- Quer incluir nome da filial?
- Quer filtrar por unidade?

---

# Sugestão de perguntas de fallback inteligentes

Essas mensagens podem ser usadas quando o assistente percebe a intenção, mas falta algum dado.

## Produto

> Entendi que você quer consultar dados de produto. Informe o **código do produto** ou uma **descrição** para eu localizar.

## Estoque

> Para consultar estoque, preciso do **código do produto**. Exemplo: `estoque do produto 10080099`.

## Estrutura

> Para abrir a estrutura/BOM, informe o **código do produto**. Exemplo: `estrutura do produto 10080099`.

## Onde é usado

> Para ver onde um componente é usado, informe o **código do produto**. Exemplo: `onde o produto 10080099 é usado`.

## Compras ou vendas

> Para consultar compras ou vendas, informe o **produto** e, se possível, um **período**. Exemplo: `vendas do produto 10080099 nos últimos 30 dias`.

## Indicadores

> Para consultar indicadores, informe o **departamento** e o **período**. Exemplo: `KPIs da produção deste mês`.

---

# Proposta de extensão JSON

Abaixo uma sugestão de estrutura complementar para tornar o arquivo mais robusto:

```json
{
  "missingRequiredParams": {
    "productAndPeriod": "Para essa consulta, informe o **código do produto** e o **período** desejado.",
    "productAndBranch": "Para essa consulta, informe o **código do produto** e a **filial**.",
    "productPeriodBranch": "Para essa consulta, informe **produto**, **período** e **filial**.",
    "customerAndPeriod": "Informe o **cliente** e o **período** desejado.",
    "supplierAndPeriod": "Informe o **fornecedor** e o **período** desejado.",
    "kpiDepartmentPeriod": "Informe o **departamento** e o **período** do indicador."
  },
  "optionalParamHints": {
    "period": "Se quiser, também posso filtrar por período.",
    "branch": "Se quiser, posso filtrar por filial.",
    "format": "Você pode pedir o resultado em tabela, gráfico ou texto.",
    "limit": "Você pode pedir uma quantidade de linhas, como 10, 50 ou 100."
  },
  "paramExamples": {
    "productCode": ["10080099", "10010001", "10130005"],
    "saleNumber": ["123456", "000123", "789012"],
    "period": ["hoje", "últimos 30 dias", "março de 2026", "01/03/2026 a 31/03/2026"],
    "branch": ["01", "matriz", "filial 02"]
  },
  "clarificationStrategy": {
    "maxQuestionsAtOnce": 1,
    "preferMostImportantParam": true,
    "askOnlyMissingRequired": true,
    "avoidLongExplanations": true
  }
}
```

---

# Sugestão de fluxo de esclarecimento

## Caso 1 — Usuário pede “estoque”

Usuário:

> Mostre estoque.

Resposta ideal:

> Para consultar o **estoque**, informe o **código do produto**.  
> Exemplo: `estoque do produto 10080099`.

## Caso 2 — Usuário pede “vendas”

Usuário:

> Mostre vendas.

Resposta ideal:

> Para consultar **vendas**, informe pelo menos o **produto, cliente ou período**.  
> Exemplo: `vendas do produto 10080099 nos últimos 30 dias`.

## Caso 3 — Usuário pede “produção de março”

Resposta ideal:

> Para **março**, preciso confirmar o ano: você quer **março de 2026** ou **março de 2025**?

## Caso 4 — Usuário pede “última semana”

Resposta ideal:

> Você quer **semana passada (segunda a domingo)** ou **últimos 7 dias**?

## Caso 5 — Usuário pede “filial”

Usuário:

> Mostre estoque da filial.

Resposta ideal:

> Informe a **filial** desejada, por exemplo `01`, `matriz` ou `filial 02`.

---

# Melhorias recomendadas para experiência do usuário

## 1. Perguntar apenas o dado que falta

Evitar:

> Informe código do produto, período, filial, cliente e fornecedor.

Preferir:

> Para consultar o estoque, informe o código do produto.

## 2. Dar exemplo no mesmo formato que o usuário deve enviar

Sempre que pedir código, mostrar um exemplo prático:

> Exemplo: `estoque do produto 10080099`.

## 3. Permitir busca alternativa

Quando faltar código do produto, oferecer busca por descrição:

> Se não souber o código, posso buscar por descrição. Exemplo: `buscar produtos com descrição cabo pp`.

## 4. Diferenciar obrigatório de opcional

Exemplo:

> Para consultar vendas, preciso de um produto ou período. Se quiser, também posso filtrar por filial.

## 5. Resolver ambiguidades antes de consultar

Quando o período for ambíguo, confirmar antes de executar a API.

## 6. Manter as perguntas curtas

O arquivo já usa mensagens curtas. Isso é bom para não travar o fluxo da conversa.

---

# Recomendações finais

O `operational_parameters.json` é pequeno, mas muito importante para a qualidade da conversa.

Ele evita que o assistente:

- Execute consultas incompletas.
- Invente códigos, períodos ou filiais.
- Use filtros errados.
- Responda com dados fora do contexto.
- Interprete datas ambíguas de forma silenciosa.

As principais melhorias sugeridas são:

- Expandir `missingProductCode` para todos os contextos operacionais.
- Criar mensagens para múltiplos parâmetros ausentes.
- Adicionar exemplos padronizados de produto, OV, período e filial.
- Permitir orientação alternativa quando o usuário não souber o código.
- Definir estratégia de esclarecimento com apenas uma pergunta por vez.
- Diferenciar período calendário de período móvel.
- Criar dicas opcionais de formato, limite e agrupamento.

Com isso, o Minha DELPI Chat IA fica mais natural, mais seguro e mais eficiente em consultas operacionais.
