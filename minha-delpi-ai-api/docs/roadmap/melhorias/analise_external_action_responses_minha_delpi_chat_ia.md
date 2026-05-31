# Análise e sugestões — `external_action_responses.json`

> **Status (31/05/2026):** [Concluído (referência arquivada)](./STATUS_ROADMAP_MELHORIAS.md).


Arquivo analisado:

`minha-delpi-ai-api/app/content/pt-BR/assistant/external_action_responses.json`

## Objetivo do arquivo

O `external_action_responses.json` centraliza textos prontos usados pelo assistente quando uma action/API externa é executada ou quando o sistema precisa explicar o resultado de uma consulta.

Ele cobre principalmente:

- Respostas de SQL.
- Consultas de programação de produção.
- Motivos de seleção de actions.
- Execuções compostas, com múltiplas consultas.
- Mensagens de erro e ausência de dados.
- Termos temporais em português.
- Razões para interpretação de intervalos de datas.

Esse arquivo é importante para manter respostas consistentes, amigáveis e padronizadas quando o Minha DELPI Chat IA interage com a API DELPI.

---

# 1. Bloco `sql`

## O que existe

O bloco `sql` define mensagens para consultas SQL:

- Título padrão da consulta.
- Título do resultado.
- Mensagem quando não há registros.
- Contagem de registros retornados.
- Indicação de linhas/produtos adicionais.
- Aviso de resultado parcial.
- Dica para pedir “mais linhas” ou “próxima página”.

## Exemplos de situações cobertas

- A consulta não retornou registros.
- A consulta retornou uma quantidade específica de linhas.
- O resultado foi truncado.
- Há mais linhas disponíveis.
- Há mais produtos disponíveis.

## Perguntas que acionam esse tipo de resposta

- Execute essa consulta SQL.
- Rode essa query.
- Traga os dados dessa consulta.
- Mostre o resultado dessa query.
- Execute a consulta dos produtos ativos.
- Rode novamente, mas com mais linhas.
- Mostre a próxima página.
- Refaça essa SQL com filtro de grupo.
- Execute a consulta e mostre em tabela.
- Essa query não retornou dados, o que pode estar errado?

## Sugestões de melhoria

Adicionar mensagens mais orientadas à ação:

```json
{
  "sql": {
    "emptyWithSuggestions": "A consulta não retornou registros. Verifique filtros de data, código, filial ou exclusão lógica.",
    "unsafeQueryBlocked": "Não executei a consulta porque ela não parece ser somente leitura.",
    "syntaxErrorHint": "A consulta retornou erro de sintaxe. Posso revisar e sugerir uma versão corrigida.",
    "permissionHint": "A consulta exige permissão ou tabela não liberada para este agente.",
    "largeResultHint": "O resultado parece grande. Posso resumir, paginar ou agrupar os dados."
  }
}
```

## Respostas mais úteis para o usuário

Em vez de apenas dizer:

> A consulta não retornou registros.

Responder:

> A consulta não retornou registros. Pode ser por filtro muito restrito, período sem movimento, código incorreto ou filial diferente. Posso tentar ampliar o período ou remover alguns filtros.

---

# 2. Bloco `productionSchedule`

## O que existe

Esse bloco padroniza respostas sobre produtos programados para produção.

Ele contempla:

- Título com período.
- Título fallback para hoje.
- Mensagem vazia.
- Resumo com quantidade de produtos programados.
- Introdução para SQL sugerida.
- Dica para executar no Protheus.

## Perguntas que acionam esse contexto

- Quais produtos estão programados para produção hoje?
- O que está programado para amanhã?
- Mostre a produção da próxima semana.
- Quais produtos serão produzidos em maio?
- Liste produtos programados para produção.
- Tem produção programada para hoje?
- Quais OPs estão programadas esta semana?
- Mostre a programação de produção por data.
- Existe produção para depois de amanhã?
- Gere uma consulta SQL para produção programada.

## Sugestões de melhoria

Adicionar mensagens para agrupamento e risco:

```json
{
  "productionSchedule": {
    "groupByDateSummary": "Agrupei os produtos por data programada.",
    "lateItemsWarning": "Há itens com data programada vencida ou próxima.",
    "stockCheckSuggestion": "Posso verificar o estoque dos componentes desses produtos.",
    "routeCheckSuggestion": "Posso consultar o roteiro de produção dos itens programados.",
    "bomCheckSuggestion": "Posso abrir a estrutura/BOM dos produtos programados."
  }
}
```

## Perguntas combinadas recomendadas

- Quais produtos estão programados para hoje e têm estoque suficiente?
- Mostre produção da semana e componentes críticos.
- Quais produtos programados têm fornecedor único?
- A produção de amanhã tem itens sem saldo?
- Mostre programação de produção e roteiro dos produtos.

---

# 3. Bloco `selectionReasons`

## O que existe

Esse bloco explica por que o sistema escolheu uma action ou caminho de execução.

Motivos existentes:

- Consulta SQL de produção reconhecida.
- Refinamento de SQL anterior.
- Consulta SQL genérica.
- Consulta de estoque reconhecida.
- Busca de produtos.
- Detalhe de LMP por número de OV.
- Indicador departamental.

## Utilidade

Esse bloco é útil para debug, logs, explicabilidade e transparência interna.

Ele pode ajudar a responder perguntas como:

- Por que você chamou essa action?
- Por que você usou SQL?
- Por que você entendeu minha pergunta como estoque?
- Por que você buscou por produto?
- Por que você usou a OV?
- Como você escolheu a consulta?

## Sugestões de melhoria

Adicionar mais motivos para cobrir todos os caminhos do `capabilities.json`:

```json
{
  "selectionReasons": {
    "supplierLookup": "Consulta de fornecedores reconhecida pelo código do produto.",
    "customerLookup": "Consulta de clientes reconhecida pelo código do produto.",
    "structureLookup": "Consulta de estrutura/BOM reconhecida pelo código do produto.",
    "parentsLookup": "Consulta de onde o item é usado reconhecida pelo contexto.",
    "purchaseHistory": "Consulta de compras reconhecida pelo produto e período.",
    "salesHistory": "Consulta de vendas reconhecida pelo produto, cliente ou período.",
    "priceLookup": "Consulta de preço/tabela reconhecida pelo produto.",
    "invoiceInboundLookup": "Consulta de notas fiscais de entrada reconhecida.",
    "invoiceOutboundLookup": "Consulta de notas fiscais de saída reconhecida.",
    "inspectionLookup": "Consulta de inspeção/qualidade reconhecida.",
    "guideLookup": "Consulta de roteiro de produção reconhecida.",
    "movementLookup": "Consulta de movimentações internas reconhecida.",
    "kpiLookup": "Consulta de indicadores reconhecida pelo departamento ou período."
  }
}
```

## Perguntas que se beneficiam desse bloco

- Por que você consultou estoque?
- Essa pergunta foi entendida como produto ou produção?
- Qual action você usou?
- Você usou SQL ou endpoint específico?
- Você está refinando a consulta anterior?

---

# 4. Bloco `composite`

## O que existe

Esse bloco padroniza respostas quando o assistente executa mais de uma consulta para responder a uma pergunta.

Ele cobre:

- Resumo de múltiplas consultas.
- Cabeçalho de atenção.
- Resultado vazio.
- Falha de formatação.
- Rótulo da consulta.
- Rótulo da action.
- Erro 404.
- Erro de permissão.
- Erro temporário de servidor.
- Status HTTP genérico.
- Consulta não concluída.
- Timeout.
- Sucesso parcial.

## Perguntas que exigem resposta composta

- Me traga uma visão 360° do produto.
- Mostre cadastro, estoque, fornecedores e vendas do produto.
- Esse item está sem estoque. Onde ele é usado e quem fornece?
- Compare compra, venda e estoque desse produto.
- Mostre produção programada e estoque dos componentes.
- Compare dois produtos em estrutura, estoque e vendas.
- Quais itens da LMP têm estoque insuficiente?
- Mostre cliente, notas fiscais e vendas desse produto.
- Faça uma análise de impacto desse componente.
- Esse produto está pronto para produção?

## Sugestões de melhoria

Adicionar textos para respostas compostas mais ricas:

```json
{
  "composite": {
    "allSuccessful": "Todas as consultas foram concluídas com sucesso.",
    "someEmpty": "Algumas consultas não retornaram dados.",
    "nextStepSuggestions": "Próximos passos sugeridos:",
    "dataFreshnessUnknown": "Não consegui confirmar a atualização dos dados retornados.",
    "crossCheckSuggestion": "Posso cruzar esses dados com estoque, compras ou vendas.",
    "insufficientDataForConclusion": "Os dados retornados não são suficientes para uma conclusão segura.",
    "summaryUnavailable": "Não consegui gerar um resumo consolidado com os dados disponíveis."
  }
}
```

## Exemplo de resposta composta ideal

> Resumo: realizei 4 consultas para o produto `10080001`: cadastro, estoque, fornecedores e vendas.  
> Encontrei saldo disponível, fornecedor cadastrado e vendas recentes.  
> Atenção: a consulta de estrutura não retornou componentes.  
> Próximos passos: posso verificar onde esse item é usado ou consultar compras recentes.

---

# 5. Bloco `temporal`

## O que existe

Esse bloco contém termos temporais em português:

- hoje
- amanhã
- depois de amanhã
- ontem
- antes de ontem
- esta semana
- semana passada
- próxima semana
- este mês
- mês passado
- próximo mês
- dias da semana
- meses completos
- meses abreviados

## Perguntas que dependem desse bloco

- O que está programado para hoje?
- Mostre vendas de ontem.
- Quais produtos serão produzidos amanhã?
- Mostre compras da semana passada.
- Liste notas fiscais deste mês.
- Mostre produção da próxima semana.
- Quais vendas ocorreram em março?
- Mostre indicadores de abril de 2026.
- Traga dados do último mês.
- Liste movimentos de sexta-feira.

## Sugestões de melhoria

Adicionar expressões comuns usadas por usuários:

```json
{
  "temporalAliases": {
    "ultimos7Dias": ["últimos 7 dias", "última semana móvel", "de 7 dias pra cá"],
    "ultimos30Dias": ["últimos 30 dias", "último mês móvel", "de 30 dias pra cá"],
    "inicioDoMes": ["começo do mês", "início do mês"],
    "fimDoMes": ["fim do mês", "final do mês"],
    "anoAteAgora": ["ano até agora", "YTD", "acumulado do ano"],
    "mesAteAgora": ["mês até agora", "MTD", "acumulado do mês"]
  }
}
```

## Melhorias de resposta

Quando o usuário pergunta “semana passada”, o chat poderia informar:

> Interpretei “semana passada” como o intervalo de segunda a domingo da semana anterior.

Quando o usuário pergunta “últimos 7 dias”, o chat poderia informar:

> Interpretei como período móvel dos últimos 7 dias até hoje.

Isso evita ambiguidade entre semana calendário e janela móvel.

---

# 6. Bloco `dateRangeReasons`

## O que existe

Esse bloco explica por que um intervalo de datas foi escolhido.

Razões existentes:

- Intervalo explícito.
- Competência explícita.
- Últimos N dias.
- Última semana.
- Semana passada.
- Semana que vem.
- Mês passado.
- Mês que vem.
- Mês atual.
- Ano passado.
- Ano atual.
- Mês e ano nomeados.
- Período ano-mês.
- Data pontual como intervalo.
- Confirmação do ano pelo usuário.
- Referência a dia da semana.
- Trimestre.

## Perguntas que usam esse bloco

- Mostre vendas de 01/05/2026 a 15/05/2026.
- Traga compras dos últimos 30 dias.
- Mostre produção da semana que vem.
- Liste notas fiscais do mês passado.
- Mostre KPIs do trimestre.
- Traga dados de março de 2026.
- Mostre faturamento do ano atual.
- Consulte movimentos de ontem.
- Liste entregas da próxima semana.
- Mostre pedidos do 2º trimestre.

## Sugestões de melhoria

Adicionar mensagens para ambiguidade:

```json
{
  "dateRangeReasons": {
    "ambiguousMonthNoYear": "Mês informado sem ano; usei o ano atual.",
    "ambiguousWeekday": "Dia da semana informado sem data; usei a próxima ocorrência.",
    "businessDaysOnly": "Intervalo calculado considerando apenas dias úteis.",
    "calendarDays": "Intervalo calculado em dias corridos.",
    "fiscalPeriod": "Período fiscal/competência informado na pergunta."
  }
}
```

## Perguntas combinadas recomendadas

- Mostre vendas do mês passado e compare com este mês.
- Mostre produção da próxima semana e estoque dos componentes.
- Traga notas fiscais do trimestre por cliente.
- Compare compras dos últimos 30 dias com os 30 dias anteriores.
- Mostre KPIs do ano atual por departamento.

---

# Oportunidades gerais de melhoria

## 1. Criar respostas de recuperação

Quando algo falhar, o chat pode sugerir ações práticas.

```json
{
  "recoverySuggestions": {
    "notFoundProduct": [
      "Verifique se o código foi digitado corretamente.",
      "Posso tentar buscar por parte da descrição.",
      "Posso procurar produtos parecidos."
    ],
    "emptyStock": [
      "Posso verificar compras recentes.",
      "Posso consultar fornecedores.",
      "Posso verificar onde o item é usado."
    ],
    "timeout": [
      "Tente reduzir o período.",
      "Tente informar um produto, cliente ou fornecedor.",
      "Posso buscar em páginas menores."
    ]
  }
}
```

## 2. Criar mensagens para sucesso parcial por tipo

```json
{
  "partialSuccessByContext": {
    "product360": "Consegui consultar parte da visão 360° do produto, mas algumas fontes não retornaram dados.",
    "comparison": "A comparação foi parcialmente concluída; alguns dados não estavam disponíveis para todos os itens.",
    "dateRange": "Parte do período retornou dados; outra parte não teve registros."
  }
}
```

## 3. Adicionar sugestões de continuação

```json
{
  "followUpSuggestions": {
    "afterStock": [
      "Ver fornecedores",
      "Ver compras recentes",
      "Ver onde é usado",
      "Ver vendas recentes"
    ],
    "afterSupplier": [
      "Ver último preço de compra",
      "Comparar lead time",
      "Ver notas de entrada",
      "Ver produtos do mesmo fornecedor"
    ],
    "afterProduction": [
      "Ver estoque dos componentes",
      "Ver roteiro",
      "Ver estrutura",
      "Ver OPs pendentes"
    ]
  }
}
```

## 4. Adicionar mensagens para gráficos

```json
{
  "chartResponses": {
    "notEnoughData": "Não há dados suficientes para gerar um gráfico útil.",
    "chartSuggested": "Há dados numéricos por período; posso apresentar em gráfico.",
    "chartFallbackTable": "Não foi possível gerar gráfico, então organizei os dados em tabela."
  }
}
```

## 5. Padronizar tom de erro

Sugestão de tom:

- Claro.
- Sem culpar o usuário.
- Explicando o que aconteceu.
- Sugerindo o próximo passo.

Exemplo:

> Não encontrei registros para esse filtro. O código pode estar incorreto, o período pode estar muito restrito ou os dados podem não existir nessa fonte. Posso tentar buscar por descrição ou ampliar o período.

---

# Sugestão de novas perguntas para enriquecer a experiência

## SQL e execução

- Execute essa consulta e mostre só as 20 primeiras linhas.
- A consulta não retornou dados; ajuste os filtros.
- Reexecute a consulta anterior com mais linhas.
- Mostre a próxima página do resultado.
- Transforme essa pergunta em SQL somente leitura.
- Corrija essa query e explique o erro.
- Execute e depois resuma o resultado.
- Agrupe esse resultado por cliente.
- Some o valor total por mês.
- Mostre os dados em tabela e depois em gráfico.

## Produção

- O que está programado para hoje?
- Quais produtos serão produzidos amanhã?
- Mostre produção da próxima semana.
- Quais OPs estão programadas este mês?
- A produção de hoje tem componentes com estoque suficiente?
- Mostre programação por data.
- Liste produtos programados e seus roteiros.
- Quais produtos programados têm fornecedor único?
- Existe produção atrasada?
- Mostre programação e destaque riscos.

## Consultas compostas

- Faça uma visão 360° do produto.
- Mostre cadastro, estoque, fornecedores, vendas e compras.
- Esse produto tem risco de falta?
- Onde esse componente é usado e quem fornece?
- Compare dois produtos em estoque, vendas e preço.
- Quais itens da LMP estão em risco?
- Mostre produção da semana e estoque dos componentes.
- Quais produtos têm venda recente, mas estão sem estoque?
- Quais produtos têm fornecedor único e aparecem em muitas estruturas?
- Resuma os principais problemas encontrados.

## Datas e períodos

- Mostre dados dos últimos 7 dias.
- Mostre dados dos últimos 30 dias.
- Compare este mês com o mês passado.
- Compare este trimestre com o anterior.
- Traga o acumulado do ano.
- Mostre a semana passada.
- Mostre a próxima semana.
- Liste dados de março de 2026.
- Mostre dados de ontem.
- Mostre dados de segunda-feira.

---

# Proposta de extensão JSON

Abaixo uma proposta que poderia ser adicionada ao arquivo ou usada em arquivo complementar:

```json
{
  "followUpSuggestions": {
    "afterEmptyResult": [
      "Tentar buscar por descrição",
      "Ampliar o período",
      "Remover filtros opcionais",
      "Verificar código informado"
    ],
    "afterStock": [
      "Consultar fornecedores",
      "Ver compras recentes",
      "Ver onde o item é usado",
      "Ver vendas recentes"
    ],
    "afterProductionSchedule": [
      "Ver estoque dos componentes",
      "Abrir estrutura/BOM",
      "Consultar roteiro",
      "Ver fornecedores críticos"
    ],
    "afterSqlResult": [
      "Mostrar mais linhas",
      "Agrupar resultado",
      "Gerar gráfico",
      "Exportar tabela"
    ]
  },
  "actionFailureHints": {
    "404": [
      "Verifique se o código informado está correto.",
      "Posso tentar buscar por descrição.",
      "Posso procurar registros parecidos."
    ],
    "403": [
      "Seu perfil pode não ter permissão para esta consulta.",
      "Verifique se o agente está configurado com a action correta."
    ],
    "500": [
      "A API retornou erro temporário.",
      "Tente novamente em instantes ou reduza o filtro."
    ],
    "timeout": [
      "A consulta demorou além do esperado.",
      "Tente reduzir o período ou informar mais filtros."
    ]
  },
  "chartResponses": {
    "suggested": "Os dados retornados podem ser visualizados em gráfico.",
    "notEnoughData": "Não há pontos suficientes para um gráfico útil.",
    "fallbackTable": "Organizei em tabela porque o gráfico não seria informativo."
  }
}
```

---

# Recomendações finais

O `external_action_responses.json` já está bem estruturado para padronizar mensagens de execução, erro, ausência de dados e interpretação temporal.

A principal oportunidade é evoluir o arquivo para incluir:

- Sugestões de continuação após cada consulta.
- Mensagens específicas por tipo de falha.
- Recuperação automática quando não há resultado.
- Explicação de datas interpretadas.
- Mensagens para gráficos e exportações.
- Respostas compostas mais orientadas a negócio.
- Dicas práticas quando a consulta falha.

Com isso, o Minha DELPI Chat IA fica mais útil porque não apenas informa “não encontrei dados”, mas orienta o usuário sobre o que fazer em seguida.
