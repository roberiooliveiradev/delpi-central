# Análise e sugestões — `identity.json`

Arquivo analisado:

`minha-delpi-ai-api/app/content/pt-BR/assistant/identity.json`

## Objetivo do arquivo

O `identity.json` define como o assistente da **Minha DELPI** deve se apresentar, explicar sua função, seus limites, sua origem e como o usuário pode utilizá-lo.

Ele também contém padrões de detecção para perguntas como:

- Quem é você?
- O que é esse chat?
- Para que você serve?
- Quais são seus limites?
- Como você funciona?
- Como usar o chat?

O arquivo também evita confundir perguntas sobre a identidade do assistente com perguntas sobre a identidade do usuário. Por isso há uma lista de exclusões como “quem sou eu”, “meu perfil”, “meus dados”, “meu e-mail”, “minhas permissões” e semelhantes.

---

# Estrutura principal encontrada

## Configurações gerais

- `platformName`: Minha DELPI
- `maxMessageLength`: 260
- `categoryPriority`: prioridade das categorias de resposta
- `userIdentityExclusions`: perguntas que são sobre o usuário, não sobre o assistente
- `patterns`: padrões de identificação de intenção
- `placeholders`: textos de fallback
- `responses`: respostas padrão da plataforma
- `followUps`: sugestões de continuidade

---

# Categorias de intenção

O arquivo trabalha com seis categorias principais:

1. `who` — Quem é você?
2. `what` — O que é você / o que é esse chat?
3. `role` — Qual sua função?
4. `limits` — Quais seus limites?
5. `origin` — Como você funciona / como foi feito?
6. `usage` — Como usar?

A prioridade definida é:

1. `who`
2. `limits`
3. `origin`
4. `usage`
5. `role`
6. `what`

Essa prioridade é importante quando uma pergunta pode cair em mais de uma categoria.

---

# 1. Categoria `who`

## Finalidade

Detectar perguntas em que o usuário quer saber quem é o assistente.

## Exemplos já cobertos

- Quem é você?
- Quem é vc?
- Quem é o assistente?
- Quem é o agente?
- Quem é o bot?
- Quem é a IA?
- Se apresente.
- Qual seu nome?
- Como você se chama?
- Me fale de você.

## Perguntas ricas sugeridas

- Quem é você dentro da Minha DELPI?
- Você é um assistente geral ou especializado?
- Qual é o seu nome aqui na plataforma?
- Você representa a DELPI ou é só um chat?
- Você é o mesmo assistente em todos os módulos?
- Você muda quando eu escolho outro agente?
- Você sabe quem eu sou?
- Você consegue se apresentar de forma curta?
- Você pode se apresentar para um novo funcionário?
- Você pode explicar seu papel em uma frase?

## Sugestão de resposta enriquecida

> Sou o assistente da Minha DELPI. Ajudo usuários a consultar informações autorizadas, entender dados, navegar por recursos da plataforma e, quando um agente especialista está ativo, acessar consultas específicas como produtos, estoque, LMP, vendas, compras e indicadores.

## Possível melhoria no JSON

Adicionar variações por contexto:

```json
{
  "responses": {
    "agent": {
      "who": "Sou o agente **{agent_name}** dentro da Minha DELPI, especializado em {agent_description}."
    },
    "platform": {
      "whoShort": "Sou o assistente da Minha DELPI, pronto para ajudar com informações autorizadas e agentes especialistas."
    }
  }
}
```

---

# 2. Categoria `what`

## Finalidade

Detectar perguntas em que o usuário quer entender o que é o chat, a plataforma ou a própria Minha DELPI.

## Exemplos já cobertos

- O que é você?
- O que é esse chat?
- O que é Minha DELPI?
- O que é a Minha DELPI?
- Para que serve esse chat?
- Para que serve Minha DELPI?

## Perguntas ricas sugeridas

- O que é a Minha DELPI?
- Esse chat faz parte de qual sistema?
- O que diferencia o chat comum de um agente?
- O que é um agente especialista?
- Esse chat consulta dados reais?
- Esse chat usa documentação interna?
- Esse chat substitui o ERP?
- O que consigo resolver por aqui?
- A Minha DELPI é só chat ou também tem módulos?
- Como esse chat se conecta aos dados da empresa?

## Sugestão de resposta enriquecida

> A Minha DELPI é uma plataforma corporativa com chat, agentes e recursos autorizados por perfil. O chat geral ajuda com documentação e dúvidas amplas. Já os agentes especialistas podem ter ferramentas específicas para consultar dados reais, como produtos, estoque, fornecedores, LMP, vendas ou indicadores.

## Possível melhoria no JSON

Adicionar explicação separada para:

- Chat geral.
- Agente especialista.
- Actions/API.
- RAG/documentação.
- Permissões/RBAC.

```json
{
  "responses": {
    "platform": {
      "whatDetailed": "A Minha DELPI combina chat corporativo, documentação autorizada, agentes especialistas e integrações com APIs internas, respeitando permissões do usuário."
    }
  }
}
```

---

# 3. Categoria `role`

## Finalidade

Responder perguntas sobre o papel ou função do assistente.

## Exemplos já cobertos

- O que você faz?
- Para que você serve?
- Qual sua função?
- Qual seu papel?
- No que você ajuda?
- Como você pode me ajudar?
- Qual sua especialidade?

## Perguntas ricas sugeridas

- Em que situações você pode me ajudar?
- O que você faz no chat geral?
- O que você faz quando uso um agente?
- Você consegue ajudar com produto?
- Você consegue ajudar com estoque?
- Você consegue ajudar com indicadores?
- Você consegue interpretar tabelas?
- Você consegue resumir resultados?
- Você consegue transformar perguntas em consultas?
- Você pode me orientar no uso da plataforma?

## Sugestão de resposta enriquecida

> Meu papel é entender sua pergunta, identificar se ela pode ser respondida com conhecimento autorizado, documentação, contexto da conversa ou uma action de agente. Quando houver dados reais envolvidos, uso apenas ferramentas autorizadas e aviso se faltar permissão ou informação.

## Possível melhoria no JSON

Adicionar respostas por área:

```json
{
  "roleByContext": {
    "general": "No chat geral, ajudo com documentação, explicações, textos, resumos e orientação.",
    "operational": "Com agente operacional, posso consultar dados reais autorizados, como produto, estoque, fornecedores e vendas.",
    "analytics": "Com agente de indicadores, posso resumir KPIs, comparar metas e sugerir análises."
  }
}
```

---

# 4. Categoria `limits`

## Finalidade

Explicar limites e cuidados do assistente.

## Exemplos já cobertos

- O que você não faz?
- Quais suas limitações?
- O que você não pode fazer?
- Você inventa dados?
- Posso confiar em tudo?
- Você alucina?
- Você erra?
- Quais são seus limites?

## Pontos importantes já comunicados

- Não inventar dados de produto, estoque, preço ou indicadores.
- Só acessar o que o perfil e o agente autorizam.
- Não substituir sistemas oficiais.
- Não executar ações críticas sem confirmação.
- Pode errar em interpretação.
- Em dúvida, o usuário deve pedir reformulação ou conferir na fonte.

## Perguntas ricas sugeridas

- Você pode errar?
- Quando devo conferir no sistema oficial?
- Você acessa tudo da empresa?
- Você pode alterar dados?
- Você pode criar produto no ERP?
- Você pode aprovar pedido?
- Você pode consultar dados sem permissão?
- O que acontece se faltar contexto?
- Você inventa estoque se a API falhar?
- Você pode executar ações críticas sozinho?

## Sugestão de resposta enriquecida

> Tenho limites importantes: não invento dados operacionais, não acesso informações fora da sua permissão, não altero registros sem autorização explícita e não substituo sistemas oficiais. Quando os dados não aparecem ou a pergunta é ambígua, devo explicar a limitação e pedir mais contexto.

## Possível melhoria no JSON

Adicionar limites por tipo de risco:

```json
{
  "limitsByRisk": {
    "data": "Não invento números de estoque, preço, produto, pedido ou indicador.",
    "permission": "Só acesso dados autorizados pelo perfil do usuário e pelo agente ativo.",
    "criticalActions": "Não executo ações críticas sem confirmação clara.",
    "interpretation": "Posso interpretar errado perguntas ambíguas; nesses casos, peço confirmação."
  }
}
```

---

# 5. Categoria `origin`

## Finalidade

Explicar como o assistente funciona e sua origem técnica.

## Exemplos já cobertos

- Como você foi feito?
- Como funciona?
- Você é IA?
- Você é um bot?
- Você é inteligência artificial?
- Você é LLM?
- Quem te criou?
- Qual modelo você usa?
- Você usa ChatGPT?
- Você usa GPT?

## Perguntas ricas sugeridas

- Você é uma IA generativa?
- Você usa modelo de linguagem?
- Você consulta banco de dados diretamente?
- Você usa APIs?
- O que é RAG?
- Você aprende com minhas conversas?
- Suas respostas são gravadas?
- Como você decide qual action usar?
- Como você sabe o que eu posso acessar?
- Como o SSO/RBAC entra nisso?

## Sugestão de resposta enriquecida

> Funciono com IA generativa orquestrada pela Minha DELPI, usando documentação autorizada, regras de segurança e, quando disponível, actions para consultar APIs reais. Eu não sou uma pessoa; gero respostas em tempo real e devo respeitar permissões do usuário e do agente ativo.

## Possível melhoria no JSON

Adicionar respostas para dúvidas sensíveis:

```json
{
  "originDetails": {
    "rag": "RAG é o uso de documentação autorizada como base para respostas, reduzindo respostas inventadas.",
    "actions": "Actions são chamadas a APIs reais configuradas no agente.",
    "rbac": "RBAC controla o que cada usuário pode acessar conforme seu perfil.",
    "history": "O histórico da conversa pode ser usado para manter contexto dentro da sessão."
  }
}
```

---

# 6. Categoria `usage`

## Finalidade

Ensinar o usuário a usar o chat.

## Exemplos já cobertos

- Como usar?
- Como te usar?
- Como usar esse chat?
- Como começar?
- Como conversar?
- Como perguntar?
- Dicas de uso.
- Primeiros passos.
- Tutorial do chat.

## Dicas já existentes

- Escrever em português.
- Ser direto.
- Informar código de produto, OV ou período quando souber.
- Selecionar agente adequado para números da operação.
- Pedir formato: tabela, gráfico ou só texto.
- Perguntar “o que você pode fazer?” para ver ferramentas.
- Não é necessário informar nome/e-mail só para conversar.

## Perguntas ricas sugeridas

- Como faço uma boa pergunta?
- Que dados devo informar para consultar produto?
- Como peço uma resposta em tabela?
- Como peço um gráfico?
- Como continuo uma tabela truncada?
- Como uso um agente especialista?
- Quando devo escolher outro agente?
- Como pergunto sobre estoque?
- Como pergunto sobre uma OV?
- Como faço uma pergunta com período?

## Sugestão de resposta enriquecida

> Para usar melhor: diga o que quer, informe código, OV, cliente, fornecedor ou período quando tiver, escolha o agente certo para dados operacionais e peça o formato desejado. Exemplo: “Mostre o estoque do produto 10080001 em tabela” ou “Compare vendas deste mês com o mês passado em gráfico”.

## Possível melhoria no JSON

Adicionar exemplos por intenção:

```json
{
  "usageExamples": {
    "product": "Me fale do produto 10080001",
    "stock": "Mostre o estoque do produto 10080001 por armazém",
    "sales": "Mostre vendas do produto 10080001 nos últimos 30 dias",
    "chart": "Faça um gráfico de vendas por mês",
    "table": "Mostre em tabela com código, descrição e quantidade",
    "followUp": "Mostre mais linhas"
  }
}
```

---

# Exclusões de identidade do usuário

## O que existe

O arquivo possui `userIdentityExclusions`, que evitam que o assistente responda como se a pergunta fosse sobre ele quando, na verdade, o usuário quer saber sobre seu próprio perfil.

Exemplos:

- Quem sou eu?
- Meu perfil.
- Meus dados.
- Meu nome.
- Meu e-mail.
- Minhas permissões.
- Meus acessos.
- Meu login.
- Meu usuário.

## Sugestões de melhoria

Adicionar mais variações:

```json
{
  "userIdentityExclusionsExtra": [
    "qual meu cargo",
    "qual meu setor",
    "qual meu departamento",
    "quais grupos eu pertenço",
    "quais apps posso acessar",
    "quais módulos tenho acesso",
    "qual minha função na empresa",
    "minha conta",
    "dados da minha conta",
    "minhas credenciais"
  ]
}
```

## Resposta ideal para identidade do usuário

Quando o usuário perguntar “quem sou eu?”, a resposta não deve usar o `identity.json` do assistente. Deve acionar uma ferramenta de perfil, se disponível, ou responder:

> Para responder sobre seu perfil, preciso consultar seus dados autorizados na plataforma. Posso mostrar apenas informações liberadas pelo seu acesso.

---

# Sugestão de novas seções para o `identity.json`

## 1. `tone`

Para padronizar estilo:

```json
{
  "tone": {
    "default": "claro, direto, corporativo e amigável",
    "avoid": [
      "respostas longas demais em perguntas simples",
      "termos técnicos sem explicação",
      "promessas fora do escopo",
      "afirmações sem fonte quando envolver dados reais"
    ]
  }
}
```

## 2. `firstRunIntro`

Para primeira interação do usuário:

```json
{
  "firstRunIntro": {
    "short": "Olá! Sou o assistente da Minha DELPI. Posso ajudar com documentação, dúvidas e agentes especializados.",
    "withExamples": [
      "Pergunte: o que você pode fazer?",
      "Informe um código de produto para consultar dados.",
      "Escolha um agente para consultas operacionais."
    ]
  }
}
```

## 3. `agentSwitchExplanation`

Para explicar mudança de agente:

```json
{
  "agentSwitchExplanation": {
    "body": "Cada agente pode ter ferramentas, permissões e conhecimentos específicos. Se sua pergunta envolve dados operacionais, escolha o agente especializado adequado."
  }
}
```

## 4. `trustAndSafety`

Para reforçar confiabilidade:

```json
{
  "trustAndSafety": {
    "noGuessing": "Não devo inventar dados operacionais. Se a API não retornar informação, explico a limitação.",
    "sourceBound": "Quando possível, baseio respostas em fontes autorizadas, documentação ou actions configuradas.",
    "permissionBound": "Meu acesso respeita permissões do usuário e do agente ativo."
  }
}
```

## 5. `shortAnswers`

Para perguntas rápidas:

```json
{
  "shortAnswers": {
    "who": "Sou o assistente da Minha DELPI, um chat corporativo para ajudar com informações autorizadas e agentes especialistas.",
    "limits": "Não invento dados, não acesso o que seu perfil não permite e não substituo sistemas oficiais.",
    "usage": "Pergunte em português, informe código/OV/período quando souber e peça o formato desejado."
  }
}
```

---

# Perguntas sugeridas para enriquecer a experiência

## Sobre identidade

- Quem é você?
- Qual seu nome?
- Você é o assistente da Minha DELPI?
- Você é uma IA?
- Você é um agente ou chat geral?
- Você muda conforme o agente selecionado?
- Você pode se apresentar em uma frase?
- Você pode se apresentar para novos usuários?
- O que é a Minha DELPI?
- O que é esse chat corporativo?

## Sobre função

- O que você faz?
- Qual sua função aqui?
- Como você pode me ajudar?
- Você consulta dados reais?
- Você entende documentação interna?
- Você pode interpretar tabelas?
- Você pode gerar resumo?
- Você pode me ajudar com produtos?
- Você pode me ajudar com indicadores?
- Você pode me ajudar com estoque?

## Sobre limites

- O que você não pode fazer?
- Você inventa dados?
- Posso confiar nos números?
- Você acessa tudo da empresa?
- Você pode alterar registros?
- Você pode aprovar pedidos?
- Você pode criar produto?
- Você pode consultar dados sem permissão?
- Quando devo conferir no sistema oficial?
- O que acontece se a API não responder?

## Sobre funcionamento

- Como você funciona?
- Você usa IA generativa?
- Você usa modelo de linguagem?
- Você usa documentação autorizada?
- Você usa APIs reais?
- Como você escolhe uma action?
- O que é RAG?
- O que é RBAC?
- Como as permissões funcionam?
- Você salva minhas conversas?

## Sobre uso

- Como usar esse chat?
- Como faço uma boa pergunta?
- Por onde começo?
- Como peço consulta de produto?
- Como peço consulta de estoque?
- Como peço resposta em tabela?
- Como peço gráfico?
- Como continuo uma resposta?
- Como vejo mais linhas?
- Como escolho o agente certo?

---

# Sugestão de menu de ajuda baseado no `identity.json`

## Começar

- Quem é você?
- O que é a Minha DELPI?
- Como usar esse chat?

## Usar melhor

- Como faço uma boa pergunta?
- Como peço resposta em tabela?
- Como peço gráfico?
- Como vejo mais linhas?

## Entender limites

- O que você não pode fazer?
- Você inventa dados?
- Quando devo conferir no sistema oficial?

## Entender funcionamento

- Você usa IA?
- Você consulta APIs reais?
- Como funcionam as permissões?

## Trocar de contexto

- O que muda quando escolho um agente?
- Como saber qual agente usar?
- O chat geral consulta dados operacionais?

---

# Exemplos de respostas prontas aprimoradas

## Quem é você?

> Sou o assistente da Minha DELPI, um chat corporativo em português que ajuda com documentação, dúvidas do dia a dia e agentes especialistas. Quando um agente está ativo, posso usar ferramentas autorizadas para consultar dados específicos, como produto, estoque, LMP, vendas, compras ou indicadores.

## O que você faz?

> Ajudo a transformar perguntas em respostas úteis. Posso explicar informações, resumir conteúdos, orientar o uso da plataforma e, com o agente certo, consultar dados reais autorizados. Para ver tudo que está disponível agora, pergunte: “o que você pode fazer?”.

## Quais são seus limites?

> Não invento dados operacionais, não acesso informações fora da sua permissão e não substituo sistemas oficiais. Se faltar código, período, contexto ou permissão, eu explico a limitação e posso sugerir o próximo passo.

## Como usar?

> Escreva em português e seja direto. Quando souber, informe código do produto, número da OV, cliente, fornecedor ou período. Você também pode pedir o formato: tabela, gráfico ou texto curto.

## Como funciona?

> Funciono com IA generativa, documentação autorizada e, quando configurado, actions/API de agentes especialistas. As respostas são geradas em tempo real e respeitam permissões do usuário e do agente ativo.

---

# Recomendações finais

O `identity.json` já cobre bem apresentação, função, limites, origem e uso do assistente.

As principais oportunidades de melhoria são:

- Criar respostas curtas e longas para cada categoria.
- Adicionar explicações específicas para chat geral versus agente especialista.
- Incluir exemplos práticos de perguntas por contexto.
- Expandir exclusões sobre identidade do usuário.
- Adicionar seção de tom e estilo.
- Criar mensagens de primeira utilização.
- Reforçar segurança, permissões e não invenção de dados.
- Explicar melhor termos como RAG, actions, RBAC e agentes.

Com isso, o Minha DELPI Chat IA pode receber usuários novos com mais clareza, reduzir dúvidas sobre o que o assistente faz e aumentar a confiança nas respostas.
