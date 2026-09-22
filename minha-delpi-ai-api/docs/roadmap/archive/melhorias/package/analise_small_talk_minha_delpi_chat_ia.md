# Análise e sugestões — `small_talk.json`

> **Status (31/05/2026):** [Concluído (referência arquivada)](./STATUS_ROADMAP_MELHORIAS.md).


Arquivo analisado:

`minha-delpi-ai-api/app/content/pt-BR/assistant/small_talk.json`

## Objetivo do arquivo

O `small_talk.json` controla respostas curtas para conversas simples do usuário, como cumprimentos, agradecimentos, desculpas, elogios, despedidas, confirmações e risadas.

Ele evita que mensagens simples acionem consultas pesadas, RAG, API ou agentes operacionais sem necessidade.

Também ajuda o chat a parecer mais natural, educado e rápido nas interações do dia a dia.

---

# Configurações principais

## `maxMessageLength`

O arquivo usa `maxMessageLength: 48`.

Isso indica que a detecção de small talk deve se aplicar principalmente a mensagens curtas.

Exemplos:

- “oi”
- “obrigado”
- “valeu”
- “tudo bem?”
- “até mais”
- “kkk”
- “ok”

## `exactMatchCategories`

A categoria `ack` aparece como correspondência exata.

Isso é importante porque palavras como “sim”, “não”, “ok” e “certo” podem ser respostas de continuidade em fluxos operacionais. Se não houver contexto, são small talk; se houver uma pergunta pendente, podem ser confirmação de ação.

## `categoryPriority`

A prioridade definida é:

1. `wellbeing`
2. `thanks`
3. `apology`
4. `praise`
5. `farewell`
6. `ack`
7. `laughter`
8. `greeting`

Essa prioridade ajuda em mensagens curtas que podem encaixar em mais de uma categoria, como “oi, tudo bem?”.

## `exclusions`

O arquivo evita classificar como small talk mensagens que contenham termos operacionais, como:

- estoque
- produto
- pedido
- SQL
- API
- relatório
- fornecedor
- cliente
- fatura
- produção
- consulta
- busque
- mostre
- liste
- abrir
- agente
- projeto

Isso é positivo, porque evita responder “Olá!” quando o usuário escreveu algo como “oi, mostre o estoque do produto”.

---

# Categorias encontradas

O arquivo possui estas categorias:

1. `greeting` — cumprimentos
2. `wellbeing` — perguntas de bem-estar
3. `thanks` — agradecimentos
4. `apology` — desculpas
5. `praise` — elogios
6. `farewell` — despedidas
7. `ack` — confirmações/entendimentos
8. `laughter` — risadas

Também há respostas separadas para:

- `platform` — chat geral.
- `agent` — agente ativo, usando `{agent_name}`.

---

# 1. Categoria `greeting`

## Finalidade

Detectar cumprimentos simples.

## Exemplos existentes

- oi
- olá
- opa
- e aí
- fala
- salve
- bom dia
- boa tarde
- boa noite
- hello
- hola

## Resposta atual no chat geral

> Olá! Como posso ajudar você hoje?

## Resposta atual com agente

> Olá! Sou o **{agent_name}**. Como posso ajudar?

## Perguntas/frases adicionais sugeridas

- bom dia, tudo certo?
- boa tarde, preciso de ajuda
- olá pessoal
- oi Delpi
- fala assistente
- bom dia, pode me ajudar?
- boa noite, tenho uma dúvida
- e aí, tudo certo?
- opa, consegue me ajudar?
- salve, preciso consultar uma coisa

## Sugestão de melhoria

Adicionar saudação com sugestão contextual:

```json
{
  "responses": {
    "platform": {
      "greetingWithHint": "Olá! Como posso ajudar hoje? Você pode perguntar *o que você pode fazer* para ver as opções."
    },
    "agent": {
      "greetingWithHint": "Olá! Sou o **{agent_name}**. Me diga o que deseja consultar ou pergunte *o que você pode fazer*."
    }
  }
}
```

---

# 2. Categoria `wellbeing`

## Finalidade

Responder perguntas como “tudo bem?” ou “como vai?”.

## Exemplos existentes

- tudo bem
- tudo bom
- como vai
- como você está
- tudo certo
- tudo joia
- blz
- e você?

## Resposta atual no chat geral

> Tudo certo por aqui! E com você — em que posso ajudar?

## Resposta atual com agente

> Tudo certo por aqui! Sou o **{agent_name}** — em que posso ajudar?

## Frases adicionais sugeridas

- como estão as coisas?
- tudo tranquilo?
- beleza por aí?
- como você tá hoje?
- tudo em ordem?
- tá tudo certo?
- firmeza?
- como anda?
- tudo ok?
- tudo suave?

## Sugestão de melhoria

Permitir variação para evitar repetição:

```json
{
  "responseVariants": {
    "wellbeing": [
      "Tudo certo por aqui! Em que posso ajudar?",
      "Tudo bem por aqui. O que você precisa consultar?",
      "Tudo ótimo! Me diga como posso ajudar."
    ]
  }
}
```

---

# 3. Categoria `thanks`

## Finalidade

Responder agradecimentos.

## Exemplos existentes

- obrigado
- obrigada
- valeu
- vlw
- obg
- grato
- thanks
- thank you

## Resposta atual no chat geral

> Por nada! Se precisar de algo mais, é só chamar.

## Resposta atual com agente

> Por nada! Se precisar de mais alguma coisa neste agente, é só chamar.

## Frases adicionais sugeridas

- muito grato
- agradeço
- obrigado pela ajuda
- valeu mesmo
- perfeito, obrigado
- obrigado, resolveu
- show, obrigado
- muito obrigado mesmo
- brigadão pela força
- era isso, obrigado

## Sugestão de melhoria

Adicionar respostas que ofereçam continuação útil:

```json
{
  "responses": {
    "platform": {
      "thanksWithContinuation": "Por nada! Posso continuar com outra consulta, resumo ou explicação."
    },
    "agent": {
      "thanksWithContinuation": "Por nada! Posso consultar outro item ou detalhar mais algum resultado neste agente."
    }
  }
}
```

---

# 4. Categoria `apology`

## Finalidade

Responder desculpas simples.

## Exemplos existentes

- desculpa
- desculpe
- perdão
- foi mal
- peço desculpas

## Resposta atual no chat geral

> Sem problemas! Como posso ajudar agora?

## Resposta atual com agente

> Sem problemas! Me diga como posso ajudar neste agente.

## Frases adicionais sugeridas

- me confundi
- mandei errado
- escrevi errado
- perdão, não era isso
- desculpa, corrige aí
- foi mal, quis dizer outra coisa
- desculpa pela confusão
- errei o código
- ignore a mensagem anterior
- foi engano

## Sugestão de melhoria

Essas frases podem ser mais do que small talk; algumas indicam correção de contexto. Exemplo: “errei o código” deve permitir o usuário enviar o código correto.

```json
{
  "apologyContextual": {
    "wrongCode": "Sem problemas. Envie o código correto e eu refaço a consulta.",
    "wrongMessage": "Sem problemas. Pode reformular a pergunta.",
    "ignorePrevious": "Tudo bem. Vou considerar sua próxima mensagem como novo pedido."
  }
}
```

---

# 5. Categoria `praise`

## Finalidade

Responder elogios ou feedback positivo.

## Exemplos existentes

- show
- show de bola
- massa
- top
- legal
- muito bom
- ótimo
- excelente
- perfeito
- incrível
- parabéns
- arrasou
- mandou bem
- sensacional

## Resposta atual no chat geral

> Que bom! Posso ajudar em mais alguma coisa?

## Resposta atual com agente

> Que bom! Posso ajudar em mais alguma coisa por aqui?

## Frases adicionais sugeridas

- ficou ótimo
- era isso
- resolveu
- ajudou bastante
- boa
- excelente trabalho
- ficou perfeito
- resposta boa
- gostei
- funcionou

## Sugestão de melhoria

Aproveitar elogio como oportunidade para continuidade:

```json
{
  "responses": {
    "platform": {
      "praiseWithNext": "Que bom que ajudou! Posso resumir, comparar ou transformar isso em uma tabela."
    },
    "agent": {
      "praiseWithNext": "Que bom! Posso detalhar, buscar mais linhas ou cruzar com outra consulta."
    }
  }
}
```

---

# 6. Categoria `farewell`

## Finalidade

Responder despedidas.

## Exemplos existentes

- até mais
- até logo
- até já
- até amanhã
- até breve
- tchau
- flw
- falou
- fui
- abraço
- beijo

## Resposta atual no chat geral

> Até logo! Estou por aqui quando precisar.

## Resposta atual com agente

> Até logo! Volte quando quiser continuar por aqui.

## Frases adicionais sugeridas

- bom descanso
- tenha um bom dia
- até depois
- até outra hora
- nos falamos
- vou sair
- encerrar por aqui
- valeu, até
- obrigado, tchau
- finalizamos

## Sugestão de melhoria

Adicionar fechamento de sessão/contexto:

```json
{
  "responses": {
    "farewellWithClosure": "Até logo! Quando voltar, posso continuar ajudando com consultas, resumos ou dúvidas da Minha DELPI."
  }
}
```

---

# 7. Categoria `ack`

## Finalidade

Responder confirmações e reconhecimentos curtos.

## Exemplos existentes

- ok
- sim
- não
- entendi
- certo
- claro
- pode ser
- tá bom
- combinado
- fechado
- beleza
- de acordo
- isso mesmo
- exatamente
- de nada
- disponha

## Resposta atual no chat geral

> Certo! Me diga o que você precisa.

## Resposta atual com agente

> Certo! Me diga o que você precisa neste agente.

## Atenção importante

Essa categoria é delicada.

Palavras como “sim” e “não” podem ser:

1. Small talk.
2. Resposta a uma pergunta de confirmação.
3. Autorização para executar uma action.
4. Escolha entre duas opções.
5. Resposta a uma pergunta de período, filial ou código.

Por isso, `ack` deve ser tratado com contexto. A regra de correspondência exata ajuda, mas o ideal é:

- Se houver pergunta pendente, interpretar como resposta à pergunta.
- Se não houver pergunta pendente, responder como small talk.
- Se houver ação crítica, exigir confirmação explícita mais completa.

## Frases adicionais sugeridas

- pode
- pode sim
- isso aí
- correto
- confirmo
- confirmado
- manda
- segue
- prossiga
- continuar

## Sugestão de melhoria

Adicionar subcategorias:

```json
{
  "ackSubtypes": {
    "positive": ["sim", "pode", "confirmo", "correto", "isso mesmo", "prossiga"],
    "negative": ["não", "nao", "negativo", "cancela", "não precisa"],
    "neutral": ["ok", "entendi", "certo", "beleza", "combinado"]
  }
}
```

## Respostas contextuais sugeridas

```json
{
  "ackContextual": {
    "noPendingAction": "Certo! Me diga o que você precisa.",
    "pendingClarification": "Perfeito, vou considerar essa opção.",
    "pendingExecution": "Confirmado. Vou executar a consulta autorizada.",
    "negativePendingExecution": "Tudo bem, não vou executar."
  }
}
```

---

# 8. Categoria `laughter`

## Finalidade

Responder risadas ou reações descontraídas.

## Exemplos existentes

- kkk
- kkkk
- haha
- hahaha
- rs
- rsrs
- hehe
- huehue

## Resposta atual no chat geral

> 😊 Posso ajudar em algo?

## Resposta atual com agente

> 😊 Em que posso ajudar neste agente?

## Frases adicionais sugeridas

- kkkkkk
- haha boa
- rsrs boa
- kkk verdade
- hehe
- hahaha entendi
- kkkk show
- rsrsrsrs
- kkk beleza
- haha perfeito

## Sugestão de melhoria

Evitar acionar small talk quando a risada vier junto de pedido operacional.

Exemplo:

- “kkk agora mostra o estoque do produto 10080001”

Nesse caso, deve consultar estoque, não responder apenas à risada.

Sugestão de regra:

```json
{
  "laughterRules": {
    "ignoreIfContainsOperationalTerm": true,
    "ignoreIfMessageLengthAbove": 48,
    "stripLaughterAndContinue": true
  }
}
```

---

# Melhorias nas exclusões

O arquivo já exclui termos operacionais importantes. Sugiro adicionar:

```json
{
  "exclusionsExtra": [
    "ov",
    "lmp",
    "bom",
    "estrutura",
    "saldo",
    "preço",
    "preco",
    "nota",
    "nfe",
    "nf",
    "op",
    "ordem",
    "venda",
    "compra",
    "compras",
    "vendas",
    "roteiro",
    "inspecao",
    "inspeção",
    "qualidade",
    "kpi",
    "indicador",
    "dashboard",
    "grafico",
    "gráfico",
    "tabela",
    "linha",
    "mais linhas",
    "proxima pagina",
    "próxima página",
    "fornecedores",
    "clientes",
    "movimentacao",
    "movimentação",
    "armazem",
    "armazém",
    "filial"
  ]
}
```

Essas exclusões reduzem o risco de uma mensagem operacional ser tratada como conversa casual.

---

# Sugestão de novas seções para o `small_talk.json`

## 1. Variações de resposta

Para evitar respostas repetitivas:

```json
{
  "responseVariants": {
    "platform": {
      "greeting": [
        "Olá! Como posso ajudar você hoje?",
        "Oi! Me diga o que você precisa.",
        "Olá! Posso ajudar com dúvidas, consultas ou orientações."
      ],
      "thanks": [
        "Por nada! Se precisar de algo mais, é só chamar.",
        "Disponha! Posso ajudar com mais alguma coisa.",
        "De nada! Estou por aqui."
      ]
    }
  }
}
```

## 2. Continuação inteligente

```json
{
  "continuationHints": {
    "afterGreeting": [
      "Você pode perguntar: o que você pode fazer?",
      "Se tiver um código de produto, posso ajudar a consultar.",
      "Você pode pedir resposta em tabela, gráfico ou texto."
    ],
    "afterThanks": [
      "Posso continuar com outra consulta.",
      "Posso resumir o resultado.",
      "Posso transformar os dados em tabela."
    ]
  }
}
```

## 3. Small talk com contexto pendente

```json
{
  "pendingContextRules": {
    "ackAsAnswer": true,
    "thanksKeepsContext": true,
    "farewellEndsSoftly": true,
    "apologyAllowsCorrection": true
  }
}
```

## 4. Intensidade do tom

```json
{
  "tone": {
    "default": "amigável, breve e profissional",
    "avoid": [
      "respostas longas para small talk",
      "excesso de emojis",
      "brincadeiras fora do contexto corporativo",
      "tom informal demais em assuntos operacionais"
    ]
  }
}
```

---

# Perguntas e mensagens sugeridas para teste

## Cumprimentos

- oi
- olá
- bom dia
- boa tarde
- boa noite
- opa
- e aí
- fala
- salve
- hello

## Bem-estar

- tudo bem?
- tudo certo?
- como vai?
- como você está?
- blz?
- tudo de boa?
- e você?
- tudo tranquilo?
- beleza por aí?
- como estão as coisas?

## Agradecimentos

- obrigado
- obrigada
- valeu
- vlw
- obg
- muito obrigado
- grato
- agradeço
- obrigado pela ajuda
- era isso, obrigado

## Desculpas

- desculpa
- foi mal
- perdão
- me confundi
- escrevi errado
- mandei errado
- ignore a mensagem anterior
- errei o código
- desculpa pela confusão
- quis dizer outra coisa

## Elogios

- show
- top
- perfeito
- excelente
- muito bom
- mandou bem
- sensacional
- resolveu
- ficou ótimo
- gostei

## Despedidas

- tchau
- até mais
- até amanhã
- falou
- flw
- abraço
- nos vemos
- até breve
- finalizamos
- obrigado, tchau

## Confirmações

- ok
- sim
- não
- certo
- combinado
- fechado
- pode ser
- entendi
- isso mesmo
- prosseguir

## Risadas

- kkk
- kkkkk
- haha
- rsrs
- hehe
- kkk boa
- hahaha
- rsrsrs
- kkk verdade
- haha perfeito

---

# Casos de teste importantes

## Caso 1 — Small talk puro

Usuário:

> oi

Resposta esperada:

> Olá! Como posso ajudar você hoje?

## Caso 2 — Cumprimento com pedido operacional

Usuário:

> oi, mostre o estoque do produto 10080001

Resposta esperada:

> Não deve responder apenas “Olá”. Deve seguir para consulta de estoque.

## Caso 3 — Agradecimento após resultado

Usuário:

> obrigado

Resposta esperada:

> Por nada! Se precisar de algo mais, é só chamar.

## Caso 4 — “sim” após pergunta de confirmação

Assistente:

> Você quer março de 2026?

Usuário:

> sim

Resposta esperada:

> Interpretar como confirmação do período, não como small talk isolado.

## Caso 5 — “não” sem contexto

Usuário:

> não

Resposta esperada:

> Certo! Me diga o que você precisa.

## Caso 6 — Desculpa com correção

Usuário:

> desculpa, errei o código

Resposta esperada:

> Sem problemas. Envie o código correto e eu refaço a consulta.

## Caso 7 — Risada com pedido

Usuário:

> kkk agora mostra as vendas do produto 10080001

Resposta esperada:

> Ignorar a risada como ruído e seguir para consulta de vendas.

---

# Recomendações finais

O `small_talk.json` está bem estruturado para manter respostas curtas, naturais e seguras em mensagens simples.

As principais melhorias recomendadas são:

- Expandir exclusões operacionais para termos como OV, LMP, BOM, saldo, preço, nota, OP, roteiro, inspeção, KPI e gráfico.
- Criar variações de respostas para reduzir repetição.
- Tratar `ack` com contexto pendente para evitar erros com “sim” e “não”.
- Permitir small talk com continuação inteligente.
- Diferenciar desculpa simples de correção operacional.
- Ignorar risadas quando houver pedido operacional na mesma mensagem.
- Manter tom profissional, breve e amigável.

Com esses ajustes, o Minha DELPI Chat IA fica mais natural sem perder precisão operacional.
