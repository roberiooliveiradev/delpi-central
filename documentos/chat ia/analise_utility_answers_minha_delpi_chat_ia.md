# Análise e sugestões — `utility_answers.json`

Arquivo analisado:

`minha-delpi-ai-api/app/content/pt-BR/assistant/utility_answers.json`

## Objetivo do arquivo

O `utility_answers.json` controla respostas utilitárias simples relacionadas a data, hora, dia da semana e ano atual.

Ele evita que perguntas simples como “que horas são?” ou “que dia é hoje?” acionem consultas documentais, agentes ou APIs operacionais.

O arquivo também define exclusões para não confundir perguntas operacionais com perguntas utilitárias. Por exemplo, se o usuário perguntar “hora de setup”, “ordem de produção” ou “entrega do pedido”, o sistema não deve responder apenas com a hora atual.

---

# Configurações principais

## `maxMessageLength`

O arquivo usa:

```json
"maxMessageLength": 90
```

Isso indica que a detecção deve ser aplicada a mensagens curtas, geralmente perguntas diretas sobre data ou hora.

## `categoryPriority`

A prioridade das categorias é:

1. `current_datetime`
2. `current_time`
3. `tomorrow_date`
4. `yesterday_date`
5. `current_date`
6. `current_weekday`
7. `current_year`

Essa prioridade é importante porque uma pergunta como “qual a data e hora?” contém termos de data e hora. Nesse caso, `current_datetime` deve vencer.

---

# Categorias encontradas

O arquivo cobre sete categorias:

1. `current_time` — hora atual.
2. `current_date` — data de hoje.
3. `tomorrow_date` — data de amanhã.
4. `yesterday_date` — data de ontem.
5. `current_datetime` — data e hora atuais.
6. `current_weekday` — dia da semana atual.
7. `current_year` — ano atual.

Também define:

- `timezoneLabel`: horário de Brasília.
- `responses`: modelos de resposta com placeholders.

---

# 1. Categoria `current_time`

## Finalidade

Responder perguntas sobre a hora atual.

## Exemplos cobertos

- Que horas são?
- Qual é a hora?
- Me diga as horas.
- Horas agora.
- Hora atual.
- Horário agora.
- Quanto tá no relógio?
- Quantas horas são?

## Resposta atual

> Agora são **{time}** ({timezone_label}).

## Perguntas adicionais sugeridas

- Que horas temos agora?
- Qual horário de agora?
- Hora de Brasília agora?
- Que horas são em Brasília?
- Me passa o horário atual.
- Pode informar o horário?
- Que horário é agora?
- Estamos em que horário?
- Agora são quantas horas?
- Qual o horário exato?

## Sugestões de melhoria

Adicionar variações específicas para fuso:

```json
{
  "patterns": {
    "current_time": [
      "hora de brasilia",
      "horário de brasília",
      "que horas em brasilia",
      "que horas são em brasília"
    ]
  }
}
```

Adicionar suporte futuro para outras localidades:

```json
{
  "timezones": {
    "default": "America/Sao_Paulo",
    "labels": {
      "America/Sao_Paulo": "horário de Brasília",
      "UTC": "UTC"
    }
  }
}
```

---

# 2. Categoria `current_date`

## Finalidade

Responder perguntas sobre a data de hoje.

## Exemplos cobertos

- Que dia é hoje?
- Qual é a data?
- Data de hoje.
- Que data é hoje?
- Me diga a data.
- Hoje é que dia?
- Dia de hoje.
- Data atual.

## Resposta atual

> Hoje é **{weekday}**, **{date}** ({timezone_label}).

## Perguntas adicionais sugeridas

- Qual a data de hoje no Brasil?
- Hoje é qual data?
- Me passa a data atual.
- Em que data estamos?
- Qual a data corrente?
- Que dia estamos?
- Hoje é dia quanto?
- Me informe o dia de hoje.
- Qual o dia do mês hoje?
- Data de hoje em Brasília.

## Sugestões de melhoria

Adicionar resposta curta opcional:

```json
{
  "responsesShort": {
    "current_date": "**{date}**."
  }
}
```

Adicionar resposta com formato ISO para contexto técnico:

```json
{
  "responsesTechnical": {
    "current_date_iso": "Data atual: **{iso_date}** ({timezone_label})."
  }
}
```

---

# 3. Categoria `tomorrow_date`

## Finalidade

Responder perguntas sobre a data de amanhã.

## Exemplos cobertos

- Que dia é amanhã?
- Qual o dia de amanhã?
- Que data é amanhã?
- Amanhã é que dia?
- Dia de amanhã.
- Data de amanhã.

## Resposta atual

> Amanhã será **{weekday}**, **{date}** ({timezone_label}).

## Perguntas adicionais sugeridas

- Amanhã cai em que dia?
- Amanhã é qual data?
- Amanhã é qual dia da semana?
- Qual será a data de amanhã?
- Me diga o dia de amanhã.
- Amanhã é dia quanto?
- Amanhã é útil?
- Amanhã é fim de semana?
- Que dia da semana será amanhã?
- Data de amanhã em Brasília.

## Sugestão de melhoria

Adicionar suporte a perguntas sobre dias úteis:

```json
{
  "patterns": {
    "tomorrow_business_day": [
      "amanhã é dia útil",
      "amanha e dia util",
      "amanhã é feriado",
      "amanha e feriado",
      "amanhã é fim de semana"
    ]
  }
}
```

Observação: para responder feriados corretamente, seria necessário calendário de feriados. Sem esse dado, o sistema deve deixar claro quando só consegue dizer o dia da semana.

---

# 4. Categoria `yesterday_date`

## Finalidade

Responder perguntas sobre a data de ontem.

## Exemplos cobertos

- Que dia foi ontem?
- Qual o dia de ontem?
- Que data foi ontem?
- Ontem foi que dia?
- Dia de ontem.
- Data de ontem.

## Resposta atual

> Ontem foi **{weekday}**, **{date}** ({timezone_label}).

## Perguntas adicionais sugeridas

- Ontem caiu em que dia?
- Ontem foi qual data?
- Ontem foi qual dia da semana?
- Qual foi a data de ontem?
- Me diga o dia de ontem.
- Ontem foi dia quanto?
- Ontem era dia útil?
- Ontem foi fim de semana?
- Que dia da semana foi ontem?
- Data de ontem em Brasília.

## Sugestão de melhoria

Adicionar resposta com formato técnico:

```json
{
  "responsesTechnical": {
    "yesterday_date_iso": "Ontem foi **{iso_date}** ({timezone_label})."
  }
}
```

---

# 5. Categoria `current_datetime`

## Finalidade

Responder perguntas sobre data e hora atuais.

## Exemplos cobertos

- Que dia e hora?
- Qual a data e hora?
- Data e hora.
- Dia e hora.
- Data e horário.
- Me diga data e hora.

## Resposta atual

> Agora são **{time}** de **{weekday}**, **{date}** ({timezone_label}).

## Perguntas adicionais sugeridas

- Me diga a data e hora atual.
- Qual a data e horário agora?
- Hoje é que dia e que horas são?
- Em que data e hora estamos?
- Data, hora e dia da semana.
- Me passa data e horário.
- Qual o timestamp atual?
- Data e hora em Brasília.
- Agora é quando?
- Que dia é hoje e que horas são?

## Sugestão de melhoria

Adicionar respostas técnicas:

```json
{
  "responsesTechnical": {
    "current_datetime_iso": "Data/hora atual: **{iso_datetime}** ({timezone_label})."
  }
}
```

---

# 6. Categoria `current_weekday`

## Finalidade

Responder perguntas sobre o dia da semana atual.

## Exemplos cobertos

- Que dia da semana?
- Qual dia da semana?
- Que dia da semana é hoje?
- Hoje é que dia da semana?
- Qual o dia da semana hoje?

## Resposta atual

> Hoje é **{weekday}** ({timezone_label}).

## Perguntas adicionais sugeridas

- Hoje cai em qual dia?
- Hoje é segunda?
- Hoje é dia útil?
- Hoje é fim de semana?
- Em que dia da semana estamos?
- Qual o dia semanal de hoje?
- Que dia útil é hoje?
- Hoje é sexta-feira?
- Hoje é qual dia da semana em Brasília?
- Hoje é útil ou fim de semana?

## Sugestão de melhoria

Adicionar categorias para dia útil/fim de semana:

```json
{
  "patterns": {
    "is_weekend": [
      "hoje é fim de semana",
      "hoje e fim de semana",
      "hoje é sábado",
      "hoje é domingo"
    ],
    "is_business_day": [
      "hoje é dia útil",
      "hoje e dia util",
      "hoje é dia de trabalho"
    ]
  }
}
```

Sem calendário de feriados, “dia útil” só pode considerar segunda a sexta, salvo integração com calendário oficial.

---

# 7. Categoria `current_year`

## Finalidade

Responder perguntas sobre o ano atual.

## Exemplos cobertos

- Qual o ano?
- Qual é o ano?
- Que ano estamos?
- Em que ano estamos?
- Ano atual.

## Resposta atual

> Estamos em **{year}** ({timezone_label}).

## Perguntas adicionais sugeridas

- Estamos em qual ano?
- Que ano é hoje?
- Ano corrente.
- Qual ano vigente?
- Qual é o ano atual no Brasil?
- Em que ano estamos agora?
- Me diga o ano atual.
- Ano de hoje.
- Que ano é?
- Qual o exercício atual?

## Sugestão de melhoria

Adicionar suporte para mês atual e trimestre atual:

```json
{
  "patterns": {
    "current_month": [
      "qual o mês atual",
      "qual o mes atual",
      "em que mês estamos",
      "em que mes estamos",
      "mês atual",
      "mes atual"
    ],
    "current_quarter": [
      "qual o trimestre atual",
      "em que trimestre estamos",
      "trimestre atual"
    ]
  }
}
```

---

# Exclusões existentes

O arquivo exclui termos que poderiam gerar falso positivo, como:

- produção
- setup
- hora mil
- início
- fim
- encerramento
- ordem
- OP
- TOTVS
- Protheus
- SQL
- produto
- estoque
- entrega
- pedido
- venda
- compra
- faturamento

Isso é importante porque palavras como “hora”, “data”, “início” e “fim” aparecem em contextos operacionais.

Exemplos que não devem cair em resposta utilitária:

- Hora de setup do produto.
- Data de entrega do pedido.
- Início da produção.
- Fim da OP.
- Data de faturamento.
- Hora-mil no roteiro.
- Data da compra.
- Data de venda.
- Encerramento da ordem.
- Consulta SQL por data.

---

# Melhorias sugeridas para exclusões

Adicionar mais termos operacionais:

```json
{
  "exclusionsExtra": [
    "ov",
    "lmp",
    "bom",
    "estrutura",
    "roteiro",
    "inspecao",
    "inspeção",
    "nota",
    "nf",
    "nfe",
    "emissao",
    "emissão",
    "vencimento",
    "validade",
    "prazo",
    "lead time",
    "programada",
    "programado",
    "agenda",
    "cronograma",
    "apontamento",
    "movimentacao",
    "movimentação",
    "kpi",
    "indicador",
    "competencia",
    "competência",
    "periodo",
    "período"
  ]
}
```

---

# Novas categorias recomendadas

## 1. Mês atual

```json
{
  "current_month": {
    "patterns": [
      "qual o mês atual",
      "qual o mes atual",
      "em que mês estamos",
      "em que mes estamos",
      "mês atual",
      "mes atual"
    ],
    "response": "Estamos em **{month} de {year}** ({timezone_label})."
  }
}
```

## 2. Trimestre atual

```json
{
  "current_quarter": {
    "patterns": [
      "qual o trimestre atual",
      "em que trimestre estamos",
      "trimestre atual"
    ],
    "response": "Estamos no **{quarter}º trimestre de {year}** ({timezone_label})."
  }
}
```

## 3. Semana do ano

```json
{
  "current_week_number": {
    "patterns": [
      "qual a semana do ano",
      "semana atual do ano",
      "em que semana estamos"
    ],
    "response": "Estamos na **semana {week_number}** de **{year}** ({timezone_label})."
  }
}
```

## 4. Dia útil / fim de semana

```json
{
  "business_day": {
    "patterns": [
      "hoje é dia útil",
      "hoje e dia util",
      "amanhã é dia útil",
      "amanha e dia util"
    ],
    "response": "**{date}** cai em **{weekday}**. Sem calendário de feriados, considero apenas segunda a sexta como dias úteis."
  }
}
```

## 5. Formato ISO

```json
{
  "iso_date": {
    "patterns": [
      "data em formato iso",
      "data iso",
      "qual a data yyyy-mm-dd"
    ],
    "response": "Data atual em formato ISO: **{iso_date}**."
  }
}
```

---

# Perguntas sugeridas para teste

## Hora

- Que horas são?
- Qual é a hora?
- Me diga as horas.
- Hora agora.
- Horário de Brasília agora.
- Quanto tá no relógio?
- Pode me dizer a hora?
- Estamos em que horário?
- Qual o horário atual?
- Agora são quantas horas?

## Data

- Que dia é hoje?
- Qual é a data?
- Data de hoje.
- Hoje é que dia?
- Qual o dia de hoje?
- Em que data estamos?
- Hoje é dia quanto?
- Data atual.
- Me diga a data.
- Data de hoje em Brasília.

## Amanhã

- Que dia é amanhã?
- Qual a data de amanhã?
- Amanhã é que dia?
- Amanhã cai em qual dia?
- Amanhã será qual dia da semana?
- Amanhã é dia quanto?
- Data de amanhã.
- Amanhã é fim de semana?
- Amanhã é dia útil?
- Qual o dia de amanhã?

## Ontem

- Que dia foi ontem?
- Qual a data de ontem?
- Ontem foi que dia?
- Ontem caiu em qual dia?
- Ontem foi qual dia da semana?
- Ontem foi dia quanto?
- Data de ontem.
- Ontem foi fim de semana?
- Ontem era dia útil?
- Qual o dia de ontem?

## Data e hora

- Qual a data e hora?
- Data e hora.
- Que dia e hora são agora?
- Me diga data e hora.
- Hoje é que dia e que horas são?
- Data e horário agora.
- Me passa data e horário.
- Agora é quando?
- Data, hora e dia da semana.
- Qual o timestamp atual?

## Dia da semana

- Que dia da semana é hoje?
- Qual o dia da semana hoje?
- Hoje é que dia da semana?
- Hoje cai em qual dia?
- Em que dia da semana estamos?
- Hoje é sexta?
- Hoje é fim de semana?
- Hoje é dia útil?
- Qual dia semanal de hoje?
- Hoje é qual dia?

## Ano

- Qual o ano?
- Em que ano estamos?
- Ano atual.
- Que ano é?
- Qual é o ano vigente?
- Estamos em qual ano?
- Qual o exercício atual?
- Ano de hoje.
- Me diga o ano atual.
- Que ano estamos agora?

---

# Casos de teste importantes

## Caso 1 — pergunta simples de hora

Usuário:

> Que horas são?

Resposta esperada:

> Agora são **{time}** (horário de Brasília).

## Caso 2 — pergunta operacional com palavra “hora”

Usuário:

> Qual a hora de setup do produto 10080001?

Resposta esperada:

> Não deve responder a hora atual. Deve encaminhar para roteiro/produção ou pedir código/contexto se necessário.

## Caso 3 — pergunta simples de data

Usuário:

> Que dia é hoje?

Resposta esperada:

> Hoje é **{weekday}**, **{date}** (horário de Brasília).

## Caso 4 — pergunta operacional com “data”

Usuário:

> Qual a data de entrega do pedido 123456?

Resposta esperada:

> Não deve responder a data de hoje. Deve tratar como consulta de pedido/entrega.

## Caso 5 — pergunta de mês sem contexto operacional

Usuário:

> Em que mês estamos?

Resposta esperada sugerida:

> Estamos em **{month} de {year}** (horário de Brasília).

## Caso 6 — pergunta sobre período operacional

Usuário:

> Mostre vendas deste mês.

Resposta esperada:

> Não deve responder apenas o mês atual. Deve tratar como consulta de vendas por período.

---

# Proposta de extensão JSON

```json
{
  "patterns": {
    "current_month": [
      "qual o mês atual",
      "qual o mes atual",
      "em que mês estamos",
      "em que mes estamos",
      "mês atual",
      "mes atual"
    ],
    "current_quarter": [
      "qual o trimestre atual",
      "em que trimestre estamos",
      "trimestre atual"
    ],
    "current_week_number": [
      "qual a semana do ano",
      "semana atual do ano",
      "em que semana estamos"
    ],
    "current_date_iso": [
      "data iso",
      "data em formato iso",
      "data yyyy-mm-dd",
      "qual a data iso"
    ]
  },
  "responses": {
    "current_month": "Estamos em **{month} de {year}** ({timezone_label}).",
    "current_quarter": "Estamos no **{quarter}º trimestre de {year}** ({timezone_label}).",
    "current_week_number": "Estamos na **semana {week_number}** de **{year}** ({timezone_label}).",
    "current_date_iso": "Data atual em formato ISO: **{iso_date}** ({timezone_label})."
  },
  "exclusionsExtra": [
    "ov",
    "lmp",
    "bom",
    "estrutura",
    "roteiro",
    "nota",
    "nf",
    "nfe",
    "emissão",
    "vencimento",
    "validade",
    "prazo",
    "lead time",
    "programado",
    "programada",
    "kpi",
    "indicador",
    "competência",
    "período"
  ]
}
```

---

# Recomendações finais

O `utility_answers.json` está bem focado em perguntas utilitárias de data e hora.

As principais melhorias recomendadas são:

- Adicionar mês atual, trimestre atual e semana do ano.
- Adicionar resposta em formato ISO para uso técnico.
- Expandir exclusões operacionais para evitar falso positivo.
- Diferenciar perguntas simples de data/hora de perguntas sobre datas de pedidos, entregas, produção, notas ou estoque.
- Considerar suporte futuro a outros fusos horários.
- Adicionar suporte limitado a dia útil/fim de semana, com aviso quando não houver calendário de feriados.

Com esses ajustes, o Minha DELPI Chat IA responde rapidamente perguntas simples sem atrapalhar consultas operacionais mais importantes.
