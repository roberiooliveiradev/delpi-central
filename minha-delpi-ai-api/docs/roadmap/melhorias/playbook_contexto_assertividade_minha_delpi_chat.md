# Playbook — Melhoria de contexto, memória conversacional e assertividade

Projeto: **Minha DELPI Chat IA**

Objetivo: melhorar a capacidade do chat de manter contexto entre perguntas, lembrar respostas anteriores, obedecer instruções de comportamento dadas pelo usuário e responder follow-ups sem se perder.

## Status de implementação (maio/2026)

| Fase | Escopo playbook | Status | Evidência |
|------|-----------------|--------|-----------|
| 1 | `contextSnapshot` em metadata, memória em `adminDebug` | **Concluída** | `ChatWorkingMemoryService`, `ChatContextMetadataService` |
| 2 | Follow-up operacional, reuso de entidade | **Concluída** | `ChatFollowUpIntentService`, `ChatReferenceResolutionService`, `workingMemory` |
| 3 | UI contextual (chips de contexto ativo) | **Concluída (MFE)** | `metadata.contextChips`, `ChatContextBar`, limpar contexto |
| 4 | Memória persistida (`ai_chat_session_memory`) | Backlog | — |
| 5 | Score de assertividade, smoke multi-turno, admin, feedback | **Concluída** | `ChatContextAssertivenessService`, `smoke_context_assertiveness_multiturn.py`, painel admin |

Detalhes e changelog: [`../../changelog/2026-05-contexto-memoria-assertividade.md`](../../changelog/2026-05-contexto-memoria-assertividade.md). Arquitetura: [`../../architecture/chat-intelligence-base.md`](../../architecture/chat-intelligence-base.md).

---

## 1. Diagnóstico resumido

O problema relatado é:

> “Muitas vezes o chat se perde no contexto entre perguntas. Eu gostaria de pedir algo específico de uma resposta anterior e ele lembrar, ou mandar ele se comportar de uma maneira e ele seguir agindo como pedi.”

Esse problema pode aparecer em cenários como:

- Usuário pergunta sobre um produto.
- O chat responde com tabela.
- Usuário diz: “agora mostre só os fornecedores”.
- O chat não entende qual produto era.
- Usuário diz: “daqui para frente responda sempre em tabela”.
- O chat obedece uma vez e depois esquece.
- Usuário diz: “use uma linguagem mais simples”.
- O chat volta ao estilo anterior.
- Usuário pede: “coloque essa resposta na lousa”.
- O chat não identifica qual foi a última resposta útil.
- Usuário diz: “compare com o anterior”.
- O chat não sabe qual item é “o anterior”.
- Usuário diz: “filtre pela filial 02”.
- O chat não reaplica o contexto da consulta anterior.

---

# 2. O que o projeto já tem de base

O projeto já tem elementos importantes para resolver isso.

## 2.1 Sessão e mensagem

O modelo conceitual define que uma conversa é uma sessão de chat com mensagens, fontes, anexos, artefatos e opcionalmente agente. Cada mensagem pode ter tool calls, fontes e apresentação rica.

Isso é essencial porque o contexto deve ser reconstruído a partir da sessão e das mensagens, não apenas do texto da última pergunta.

## 2.2 Metadata nas mensagens

As mensagens possuem `metadata`, e o projeto já usa esse campo para:

- `toolCalls`
- fontes
- RAG
- apresentação rica
- canvas/lousa
- diagnóstico admin
- feedback

A melhoria de contexto deve usar fortemente `metadata`, porque ela contém dados estruturados melhores que o texto renderizado.

## 2.3 Pipeline base

A arquitetura já define um pipeline com:

- Segurança.
- Workspace.
- Pipeline de inteligência.
- Contexto de conversa.
- Tools/actions.
- RAG.
- Prompt builder.
- LLM.

Também existem serviços já pensados para contexto, como:

- `ChatConversationContextService`
- `ChatDataInterpretationAnswerService`
- `ChatOperationalRefinementService`
- `ChatRouteContextService`
- `ChatCanvasContentService`
- `ChatSqlQueryRefinementService`
- `ChatPaginationConsolidationService`

Esses serviços devem ser a base para melhorar “memória” e assertividade.

## 2.4 Camadas pré-LLM

O projeto já documenta que chats maduros não mandam a pergunta crua direto ao modelo. Antes do LLM devem entrar regras, classificadores, APIs e RAG para reduzir custo, aumentar confiabilidade, proteger o sistema e enriquecer o prompt.

Isso confirma que a solução não deve ser apenas “melhorar o prompt”. A solução deve ser pipeline + contexto estruturado + regras determinísticas + prompt final enxuto.

---

# 3. Princípio central

## Não confiar só no histórico textual

Histórico textual é frágil. O modelo pode se perder.

O chat deve manter um **estado conversacional estruturado** por sessão.

Esse estado deve responder perguntas como:

- Qual foi o último produto consultado?
- Qual foi a última rota/action usada?
- Qual foi a última tabela exibida?
- Qual foi o último filtro de período?
- Qual foi a última filial?
- Qual foi o formato preferido pelo usuário?
- O usuário pediu para responder sempre em tabela?
- O usuário pediu linguagem simples?
- A última resposta útil tem canvas/lousa?
- A pergunta atual é um follow-up?
- “Esse item”, “isso”, “o anterior”, “essa tabela” apontam para quê?

---

# 4. Conceito proposto: Conversational Working Memory

Criar uma camada chamada:

`ChatWorkingMemoryService`

ou

`ChatConversationMemoryService`

## Função

Extrair, atualizar e injetar um resumo estruturado do contexto recente da sessão.

## Não é memória permanente

Essa memória é da conversa/sessão.

Não deve salvar preferências globais do usuário sem consentimento.

## Escopo

- Sessão atual.
- Projeto atual.
- Agente atual.
- Últimas mensagens relevantes.
- Últimos resultados de tools.
- Preferências temporárias dadas pelo usuário.

---

# 5. Estado estruturado recomendado

## Exemplo de `conversation_state`

```json
{
  "lastEntities": {
    "productCode": "10080001",
    "productDescription": "TERM. PINO ...",
    "saleNumber": "123456",
    "customerCode": null,
    "supplierCode": null,
    "branch": "01",
    "warehouse": "99",
    "period": {
      "label": "últimos 30 dias",
      "startDate": "01-05-2026",
      "endDate": "30-05-2026"
    }
  },
  "lastToolContext": {
    "actionId": "products.stock",
    "path": "/products/{code}/stock",
    "category": "Estoque de produto",
    "params": {
      "code": "10080001",
      "branch": "01"
    },
    "resultSummary": "Produto com saldo disponível em 2 armazéns.",
    "presentationType": "table"
  },
  "lastAnswer": {
    "messageId": "uuid",
    "kind": "operational_result",
    "title": "Estoque do produto 10080001",
    "hasTable": true,
    "hasChart": false,
    "hasCanvas": false
  },
  "userBehaviorInstructions": {
    "responseFormat": "table",
    "tone": "simple",
    "detailLevel": "short",
    "includeNextSteps": true,
    "validUntil": "session"
  },
  "pendingClarification": null
}
```

---

# 6. Tipos de memória

## 6.1 Memória de entidades

Guarda entidades mencionadas ou resultantes:

- Produto.
- OV.
- Cliente.
- Fornecedor.
- Filial.
- Armazém.
- Período.
- Grupo.
- Departamento.
- Indicador.
- Tabela SQL.
- Rota/action.

## 6.2 Memória de resultado

Guarda o último resultado útil:

- Tipo: produto, estoque, vendas, compras, KPI, SQL, RAG, lousa.
- Fonte: action, RAG, anexo, SQL.
- Resumo humano.
- Colunas da tabela.
- Número de linhas.
- IDs/códigos principais.
- Caminho da action.
- Parâmetros usados.

## 6.3 Memória de instrução comportamental

Guarda ordens como:

- “Responda sempre em tabela.”
- “Seja mais direto.”
- “Use linguagem simples.”
- “Não use gráfico.”
- “Sempre traga próximos passos.”
- “Daqui pra frente me responda como checklist.”
- “Sempre cite a fonte.”
- “Não repita explicações longas.”

## 6.4 Memória de pendência

Guarda pergunta que aguarda resposta do usuário:

- “Qual o código do produto?”
- “Você quer março de 2025 ou 2026?”
- “Quer semana passada ou últimos 7 dias?”
- “Confirma executar a consulta?”

## 6.5 Memória de navegação

Guarda ações como:

- Última página retornada.
- Próxima página disponível.
- Paginação consolidada.
- Última tabela exibida.
- Última linha clicada.
- Último drill-down.

---

# 7. Como detectar follow-up

Criar um serviço:

`ChatFollowUpIntentService`

## Sinais de follow-up

Mensagens curtas ou dependentes de contexto:

- “e os fornecedores?”
- “agora mostra as vendas”
- “coloca em tabela”
- “faça um gráfico”
- “compare com o anterior”
- “filtre filial 02”
- “só os que têm saldo”
- “me explique essa tabela”
- “coloque isso na lousa”
- “traga mais linhas”
- “continue”
- “resuma”
- “detalhe a segunda linha”
- “e deste item?”
- “mesmo produto”
- “mesma filial”
- “mesmo período”
- “agora em gráfico”
- “sem os cancelados”
- “ordene por valor”
- “me dê a conclusão”

## Classificação sugerida

```json
{
  "followUpType": "format_change | filter_refinement | entity_reuse | comparison | explanation | pagination | canvas | behavior_instruction | drill_down",
  "confidence": 0.92,
  "references": {
    "target": "last_answer",
    "entity": "productCode",
    "value": "10080001"
  }
}
```

---

# 8. Resolução de referências

Criar um serviço:

`ChatReferenceResolutionService`

## Função

Resolver palavras vagas:

| Expressão do usuário | Deve apontar para |
|---|---|
| “esse produto” | último `productCode` |
| “esse item” | último produto/componente |
| “essa tabela” | última apresentação rica/tabela |
| “esse resultado” | última resposta útil |
| “o anterior” | penúltima entidade comparável |
| “mesmo período” | último período usado |
| “mesma filial” | última filial usada |
| “essa OV” | última `saleNumber` |
| “esse fornecedor” | último fornecedor |
| “esses dados” | último tool result ou tabela |

## Exemplo

Usuário:

> Mostre estoque do produto 10080001.

Depois:

> Agora os fornecedores.

O resolved intent deve virar:

```json
{
  "intent": "suppliers_lookup",
  "params": {
    "code": "10080001"
  },
  "source": "conversation_state.lastEntities.productCode"
}
```

---

# 9. Persistência de instruções de comportamento

## Problema

Usuário diz:

> Daqui pra frente, responda sempre em tabela e seja direto.

O chat precisa obedecer até que:

- a sessão acabe,
- o usuário mude a instrução,
- o contexto mude de agente/projeto,
- a instrução entre em conflito com segurança ou limitação.

## Proposta

Criar:

`ChatBehaviorInstructionService`

## Detectar frases como

- “daqui pra frente...”
- “a partir de agora...”
- “sempre responda...”
- “não faça mais...”
- “prefiro que...”
- “quando eu pedir X, faça Y”
- “nesse chat, use...”
- “mantenha esse formato”
- “continue nesse estilo”
- “responda só em tabela”
- “seja mais direto”
- “explique como se fosse para leigo”

## Estado sugerido

```json
{
  "behaviorInstructions": [
    {
      "id": "uuid",
      "scope": "session",
      "type": "response_format",
      "value": "table",
      "sourceMessageId": "uuid",
      "createdAt": "datetime",
      "active": true
    },
    {
      "id": "uuid",
      "scope": "session",
      "type": "tone",
      "value": "simple_direct",
      "sourceMessageId": "uuid",
      "active": true
    }
  ]
}
```

## Onde persistir

Opções:

1. `ChatSession.context`
2. `ChatSession.metadata`
3. Nova tabela `ai_chat_session_memory`
4. Metadata da última mensagem assistant

Recomendação:

- Curto prazo: `ChatSession.context` ou `metadata`.
- Médio prazo: tabela dedicada `ai_chat_session_memory`.

---

# 10. Escopos de memória

## Escopo de turno

Vale só para a resposta atual.

Exemplo:

> Responda essa em tabela.

## Escopo de sessão

Vale até a conversa acabar.

Exemplo:

> Daqui para frente responda sempre curto.

## Escopo de projeto

Vale para conversas dentro de um projeto.

Exemplo:

> Neste projeto, sempre considere que o público é engenharia.

## Escopo de agente

Vale no agente configurado.

Exemplo:

> Este agente deve sempre responder com checklist.

## Escopo de usuário

Mais sensível. Só usar com consentimento.

Exemplo:

> Sempre prefiro respostas curtas.

Recomendação: começar apenas com escopo de sessão e agente.

---

# 11. Prioridade das instruções

Quando houver conflito:

1. Segurança e permissões.
2. Instrução do sistema.
3. Configuração publicada do agente.
4. Projeto.
5. Instruções persistentes da sessão.
6. Instrução do turno atual.
7. Preferências inferidas.
8. Estilo padrão.

## Exemplo

Usuário:

> Sempre responda sem fonte.

Mas a pergunta exige fonte documental.

Resposta correta:

> Posso manter a resposta direta, mas quando eu usar documentação ou dados consultados, preciso indicar a origem para manter rastreabilidade.

---

# 12. Melhorias no pipeline

## Estágio proposto

Adicionar no pipeline pré-LLM:

```text
SecurityStage
WorkspaceStage
NormalizeStage
ConversationMemoryStage
BehaviorInstructionStage
ReferenceResolutionStage
PreToolDecisionStage
OperationalRefinementStage
ToolExecutionStage
PostToolStage
RagStage
PromptAssemblyStage
LLM
```

## Função de cada novo estágio

### `ConversationMemoryStage`

- Lê mensagens recentes.
- Lê tool calls recentes.
- Recria ou atualiza `conversation_state`.

### `BehaviorInstructionStage`

- Detecta e salva instruções comportamentais.
- Injeta preferências ativas no prompt/presenter.

### `ReferenceResolutionStage`

- Resolve “isso”, “esse produto”, “essa tabela”, “o anterior”.
- Converte follow-up vago em pedido explícito.

### `OperationalRefinementStage`

- Reaproveita produto, filial, período, rota e formato.
- Reexecuta action correta com novo filtro.

---

# 13. Prompt builder com memória

O prompt final deve conter uma seção curta, estruturada e controlada.

## Exemplo

```text
## Memória da conversa ativa
- Último produto consultado: 10080001
- Última consulta: estoque por armazém
- Último período: últimos 30 dias
- Última filial: 01
- Preferência ativa do usuário: responder em tabela e ser direto

## Instruções para este turno
- A pergunta atual é um follow-up sobre o último produto.
- Não invente dados ausentes.
- Se precisar consultar API, use o código 10080001.
```

## Regra

Essa memória deve ser pequena.

Não jogar todo o histórico no prompt.

---

# 14. Uso de toolCalls como fonte de verdade

O chat não deve tentar reler uma tabela em markdown se existe `toolCalls[].metadata.presentation`.

## Prioridade para contexto anterior

1. `toolCalls[].metadata.presentation`
2. `toolCalls[].metadata.humanizedSummary`
3. `canvasOpen`
4. `sources`
5. `content` da mensagem assistant
6. texto bruto do histórico

## Benefício

Evita erro ao interpretar:

- tabelas grandes;
- markdown compactado;
- gráfico sem tabela textual;
- resposta suprimida pelo front para evitar duplicação.

---

# 15. Resposta sobre dado já consultado sem chamar API

O projeto já prevê `ChatDataInterpretationAnswerService`, que monta markdown a partir de `humanizedSummary` das tool calls recentes.

Expandir esse comportamento.

## Quando usar

Usuário pergunta:

- “explique essa tabela”
- “qual item tem maior saldo?”
- “resuma esses dados”
- “qual é o alerta principal?”
- “o que significa esse resultado?”
- “monte uma conclusão”
- “transforme em checklist”
- “coloque em ordem de prioridade”

## Não precisa chamar API

Se a pergunta pode ser respondida com o último resultado já consultado.

## Precisa chamar API

Se o usuário pede dados novos:

- “agora fornecedores”
- “agora vendas”
- “filtre filial 02”
- “atualize”
- “traga mais linhas”
- “busque no período anterior”

---

# 16. Instruções de comportamento no presenter

Nem toda instrução precisa ir ao LLM.

Se o usuário pediu:

- “em tabela”
- “em gráfico”
- “em checklist”
- “responda curto”
- “sem explicação”
- “com próximos passos”

O presenter pode obedecer diretamente.

## Exemplo

```json
{
  "preferredFormat": "table",
  "detailLevel": "short",
  "includeNextSteps": true
}
```

Isso deve influenciar:

- `ChatExternalActionDirectResponseService`
- `ChatCompositeDirectAnswerService`
- `ChatRichPresentation`
- compactação de markdown
- chips de follow-up no front

---

# 17. Frontend: tornar o contexto visível

O usuário deve perceber que o chat lembra.

## 17.1 Barra de contexto

Mostrar discretamente no topo ou próximo ao input:

> Contexto atual: Produto 10080001 · Filial 01 · Resposta em tabela

Com botão:

- Limpar contexto
- Alterar formato
- Fixar contexto

## 17.2 Chips de memória

Após consulta:

- Produto: 10080001
- Filial: 01
- Período: últimos 30 dias
- Formato: tabela

Clicar no chip permite remover ou trocar.

## 17.3 Indicador de instrução ativa

Se o usuário disse “responda sempre em tabela”:

> Preferência ativa: tabela

Com opção:

- Desativar
- Alterar

## 17.4 Botão “usar esta resposta”

Em cada resposta assistant:

- Usar como contexto
- Comparar com próxima
- Colocar na lousa
- Gerar resumo
- Transformar em checklist

## 17.5 Drill-down de tabela

Na apresentação rica:

- “Detalhar linha”
- “Filtrar por este produto”
- “Comparar com anterior”
- “Ver fornecedores”
- “Ver estoque”
- “Ver vendas”

---

# 18. Comandos naturais recomendados

O chat deve entender comandos como:

## Referência à resposta anterior

- “Explique a resposta anterior.”
- “Resuma isso.”
- “Transforme essa resposta em checklist.”
- “Coloque isso na lousa.”
- “Faça uma versão curta.”
- “Agora em tabela.”
- “Agora em gráfico.”
- “Me dê a conclusão.”
- “O que é mais importante aqui?”

## Reuso de entidade

- “Agora veja os fornecedores.”
- “E o estoque?”
- “E as vendas?”
- “Onde esse item é usado?”
- “Compare com o produto anterior.”
- “Use o mesmo período.”
- “Use a mesma filial.”
- “Mostre o mesmo para o produto 10080002.”

## Comportamento persistente

- “Daqui para frente seja mais direto.”
- “Sempre responda em tabela.”
- “Neste chat, explique de forma simples.”
- “Não use gráfico, prefiro tabela.”
- “Sempre traga próximos passos.”
- “Quando houver alerta, destaque primeiro.”
- “Mantenha esse formato.”

---

# 19. Exemplos de comportamento esperado

## Exemplo 1 — Produto lembrado

Usuário:

> Mostre estoque do produto 10080001.

Chat:

> Encontrei o estoque do produto 10080001...

Usuário:

> Agora os fornecedores.

Comportamento esperado:

> Entendi que você quer os fornecedores do produto 10080001. Vou consultar.

Não perguntar novamente o código.

---

## Exemplo 2 — Formato persistente

Usuário:

> Daqui pra frente, responda sempre em tabela e seja direto.

Chat:

> Combinado. Nesta conversa, vou priorizar respostas em tabela e mais diretas.

Usuário:

> Mostre fornecedores do produto 10080001.

Resposta deve vir em tabela.

Usuário:

> E as compras?

Resposta deve continuar em tabela, usando o produto anterior.

---

## Exemplo 3 — Explicação de resultado anterior

Usuário:

> Mostre vendas do produto 10080001 nos últimos 30 dias.

Chat mostra tabela.

Usuário:

> Me explica essa tabela em linguagem simples.

Comportamento esperado:

- Não chamar API novamente.
- Usar o resultado anterior.
- Explicar colunas, totais e alerta principal.

---

## Exemplo 4 — Refinamento

Usuário:

> Mostre estoque do produto 10080001.

Depois:

> Filtre só a filial 02.

Comportamento esperado:

- Reusar produto 10080001.
- Adicionar filial 02.
- Reexecutar rota de estoque.
- Responder: “Filtrei o estoque do produto 10080001 pela filial 02.”

---

## Exemplo 5 — Comparação com anterior

Usuário:

> Mostre estoque do produto 10080001.

Depois:

> Agora mostre o mesmo para 10080002.

Depois:

> Compare os dois.

Comportamento esperado:

- Manter os dois produtos em `comparisonCandidates`.
- Comparar saldo, armazém, disponibilidade etc.
- Não misturar com produtos antigos da sessão.

---

# 20. Regras para não se perder no histórico

## Regra 1 — Última resposta útil

Nem toda resposta do assistente deve virar contexto principal.

Não usar como “última resposta útil”:

- “Coloquei na lousa.”
- “Por nada.”
- “Certo.”
- “Qual código?”
- “Não encontrei dados.”
- “Resposta cancelada.”

Usar como resposta útil:

- resultado de API;
- resultado SQL;
- resposta documental;
- tabela;
- gráfico;
- análise;
- resumo;
- canvas com conteúdo;
- comparação.

## Regra 2 — Mensagem atual tem prioridade

Se o usuário informa um novo código, ele substitui o código anterior.

Exemplo:

> Agora para o produto 10080002.

Usar 10080002, não 10080001.

## Regra 3 — Não herdar contexto perigoso

Não herdar automaticamente:

- permissões;
- confirmação de ações críticas;
- dados sensíveis;
- comandos de escrita;
- instruções que contrariem segurança;
- contexto de outro agente/projeto sem confirmação.

## Regra 4 — Perguntar quando a referência for ambígua

Se houver múltiplos produtos recentes:

> Você quer comparar com qual produto: 10080001 ou 10080002?

---

# 21. Melhorias em banco/modelo

## Nova tabela sugerida

`ai_chat_session_memory`

Campos:

| Campo | Tipo | Função |
|---|---|---|
| `id` | uuid | ID |
| `session_id` | uuid | Sessão |
| `memory_type` | text | entity, behavior, result, pending |
| `key` | text | productCode, responseFormat etc. |
| `value_json` | jsonb | valor estruturado |
| `source_message_id` | uuid | origem |
| `scope` | text | turn, session, project, agent |
| `confidence` | numeric | confiança |
| `active` | boolean | se está ativo |
| `created_at` | datetime | criação |
| `updated_at` | datetime | atualização |
| `expires_at` | datetime|null | expiração opcional |

## Índices

- `(session_id, active)`
- `(session_id, memory_type, key)`
- `(source_message_id)`

## Alternativa de curto prazo

Guardar em `ChatSession.context` como JSON, se o campo aceitar.

---

# 22. Melhorias em metadata

Em cada mensagem assistant, salvar:

```json
{
  "contextSnapshot": {
    "lastEntities": {},
    "behaviorInstructions": {},
    "resolvedReferences": {},
    "usedMemoryKeys": ["productCode", "responseFormat"]
  }
}
```

## Benefício

Ajuda a depurar:

- por que o chat usou um produto;
- por que respondeu em tabela;
- se reutilizou contexto;
- se falhou na resolução.

---

# 23. Observabilidade e adminDebug

Adicionar no `adminDebug`:

```json
{
  "memory": {
    "loaded": true,
    "activeEntities": {
      "productCode": "10080001",
      "branch": "01"
    },
    "activeBehaviorInstructions": {
      "responseFormat": "table",
      "tone": "simple"
    },
    "resolvedReferences": [
      {
        "text": "esse produto",
        "resolvedTo": "productCode",
        "value": "10080001",
        "confidence": 0.93
      }
    ],
    "followUpDetected": true,
    "followUpType": "entity_reuse"
  }
}
```

Isso é fundamental para descobrir por que o chat “se perdeu”.

---

# 24. Testes de regressão

Criar uma suíte chamada:

`test_chat_context_memory.py`

## Cenários mínimos

### C1 — Reuso de produto

1. “Mostre estoque do produto 10080001.”
2. “Agora fornecedores.”
3. Esperado: usa 10080001.

### C2 — Reuso de filial

1. “Estoque do produto 10080001 na filial 01.”
2. “Agora filial 02.”
3. Esperado: usa mesmo produto e troca filial.

### C3 — Reuso de período

1. “Vendas do produto 10080001 nos últimos 30 dias.”
2. “Agora compras no mesmo período.”
3. Esperado: usa mesmo período.

### C4 — Formato persistente

1. “Daqui para frente responda em tabela.”
2. “Fornecedores do produto 10080001.”
3. “Agora compras.”
4. Esperado: ambas em tabela.

### C5 — Linguagem simples persistente

1. “Explique sempre em linguagem simples.”
2. “Mostre KPIs da produção.”
3. Esperado: resposta sem jargão.

### C6 — Última resposta útil

1. Resultado operacional.
2. “Obrigado.”
3. “Coloque isso na lousa.”
4. Esperado: coloca o resultado operacional, não a resposta “Por nada”.

### C7 — Ambiguidade

1. “Estoque produto A.”
2. “Estoque produto B.”
3. “Compare com o anterior.”
4. Esperado: sabe A e B, ou pergunta se ambíguo.

### C8 — Não herdar contexto errado

1. Consulta produto A.
2. Troca para agente de RH.
3. “Mostre isso.”
4. Esperado: não usar produto A sem contexto claro.

### C9 — Instrução cancelada

1. “Sempre responda em tabela.”
2. “Pode voltar ao normal.”
3. Próxima resposta não precisa ser tabela.

### C10 — Resultado anterior sem API

1. Consulta vendas.
2. “Explique essa tabela.”
3. Esperado: não chama API, usa toolCalls recentes.

---

# 25. Smoke manual

Criar script manual com perguntas reais:

```text
1. Mostre o estoque do produto 10080001.
2. Agora fornecedores.
3. Agora compras dos últimos 30 dias.
4. Mostre em tabela.
5. Daqui pra frente seja direto.
6. E as vendas?
7. Me explique essa tabela.
8. Coloque isso na lousa.
9. Mostre o mesmo para o produto 10080002.
10. Compare os dois.
```

Critério de sucesso:

- Não pede código repetido.
- Não troca produto sem motivo.
- Mantém formato pedido.
- Interpreta “isso” corretamente.
- Não chama API quando só precisa explicar dados anteriores.
- Não mistura contextos de agentes diferentes.

---

# 26. Ajustes no frontend

## 26.1 Mostrar contexto ativo

Exemplo:

```text
Contexto ativo: Produto 10080001 · Filial 01 · Formato tabela
```

## 26.2 Permitir limpar contexto

Botão:

- Limpar contexto
- Esquecer produto
- Remover preferência de tabela

## 26.3 Chips de continuação

Após resposta de produto:

- Estoque
- Fornecedores
- Compras
- Vendas
- Estrutura
- Onde é usado?
- Colocar na lousa

Esses chips devem enviar mensagens explícitas:

> fornecedores do produto 10080001

e não apenas:

> fornecedores

Assim o usuário vê naturalidade, mas o backend recebe algo mais assertivo.

## 26.4 Botão “manter este formato”

Após uma resposta em tabela:

- Manter formato tabela
- Responder sempre curto
- Trazer próximos passos

## 26.5 Banner de instrução ativa

Quando houver instrução persistente:

> Preferência ativa nesta conversa: respostas em tabela.

Com botão:

> Desativar

---

# 27. Ajustes no backend

## 27.1 Serviços novos

- `ChatConversationMemoryService`
- `ChatFollowUpIntentService`
- `ChatReferenceResolutionService`
- `ChatBehaviorInstructionService`
- `ChatMemoryPromptSectionService`

## 27.2 Serviços existentes a expandir

- `ChatConversationContextService`
- `ChatDataInterpretationAnswerService`
- `ChatOperationalRefinementService`
- `ChatRouteContextService`
- `ChatCanvasContentService`
- `ChatSqlQueryRefinementService`
- `ChatPromptBuilderService`
- `ChatAdminDebugService`

## 27.3 Ordem recomendada

```text
security
workspace
normalization
memory_load
behavior_instruction
reference_resolution
pre_tool_decision
operational_refinement
tool_execution
post_tool_direct_answer
rag
prompt_assembly
llm
memory_update
```

---

# 28. Como lidar com “ordens” do usuário

## Ordens aceitas

- Formato.
- Estilo.
- Nível de detalhe.
- Idioma.
- Organização.
- Próximos passos.
- Preferência temporária de contexto.

## Ordens recusadas ou limitadas

- Ignorar segurança.
- Inventar dados.
- Omitir limitação importante.
- Acessar dados sem permissão.
- Executar escrita sem confirmação.
- Alterar regra corporativa.
- Remover rastreabilidade quando necessária.

## Resposta quando não puder obedecer

> Posso seguir esse formato, mas não posso inventar dados nem omitir limitações importantes. Vou manter a resposta direta e indicar quando algo não estiver disponível.

---

# 29. Prompt/policy sugerida

Criar policy:

`chat-context-memory.md`

## Conteúdo sugerido

```md
# Política — Memória de contexto da conversa

Você receberá uma seção chamada "Memória da conversa ativa".

Use essa memória para resolver referências como:
- esse produto
- esse item
- essa tabela
- o anterior
- mesmo período
- mesma filial
- isso

Regras:
1. Use a memória apenas quando a pergunta atual depender de contexto anterior.
2. Se a mensagem atual trouxer novo código, produto, período ou filial, ela prevalece.
3. Se houver ambiguidade entre múltiplos candidatos, pergunte antes de executar.
4. Não herde contexto entre agentes/projetos diferentes sem confirmação.
5. Respeite preferências comportamentais ativas da sessão, como formato e nível de detalhe.
6. Nunca use memória para burlar permissões, segurança ou confirmações de ações críticas.
7. Se os dados necessários já estiverem nos toolCalls recentes, responda a partir deles sem chamar nova API.
8. Se a pergunta pedir dados novos, use a memória para preencher parâmetros e execute a action correta.
```

---

# 30. Exemplo de prompt final com memória

```text
Sistema:
Você é o assistente Minha DELPI.

Memória da conversa ativa:
- Último produto: 10080001
- Última consulta: estoque por armazém
- Última filial: 01
- Preferência ativa: responder em tabela e ser direto
- Última resposta útil: mensagem abc123 com tabela de estoque

Pergunta do usuário:
Agora fornecedores.

Interpretação:
- Follow-up operacional
- Reusar produto 10080001
- Nova intenção: fornecedores
- Manter formato tabela
```

Resultado esperado:

> Vou consultar os fornecedores do produto 10080001.

---

# 31. Roadmap de implementação

## Fase 1 — Baixo risco

- Adicionar `contextSnapshot` em metadata.
- Expandir `adminDebug` com memória ativa.
- Criar detector simples de instruções:
  - “daqui pra frente”
  - “sempre”
  - “responda em tabela”
  - “seja direto”
- Injetar preferências no presenter.
- Criar testes C1–C5.

## Fase 2 — Follow-up operacional

- Implementar `ChatReferenceResolutionService`.
- Expandir `ChatOperationalRefinementService`.
- Reusar produto, filial, período e rota.
- Criar testes C6–C10.

## Fase 3 — UI contextual

- Mostrar chips de contexto ativo.
- Permitir limpar contexto.
- Chips de continuação com mensagem explícita.
- Botão “manter este formato”.

## Fase 4 — Memória persistida

- Criar tabela `ai_chat_session_memory`.
- Persistir instruções de sessão.
- Expirar memórias antigas.
- Registrar origem e confiança.

## Fase 5 — Avaliação automática ✅ (maio/2026)

- [x] Score de assertividade contextual (`ChatContextAssertivenessService` → `metadata.contextAssertiveness`).
- [x] Smoke multi-turno (`scripts/smoke_context_assertiveness_multiturn.py` + `run_onda11_validation.sh`).
- [x] Painel admin com score, flags e alerta visual se score &lt; 70.
- [x] Feedback negativo: motivo «Perdeu o contexto» (`lost_context`).

---

# 32. Métricas de assertividade

## Métricas recomendadas

| Métrica | Objetivo |
|---|---|
| Taxa de follow-up resolvido | % de mensagens vagas resolvidas corretamente |
| Taxa de reuso correto de produto | % de follow-ups que usam produto certo |
| Taxa de pergunta desnecessária | quantas vezes pediu código já existente |
| Taxa de instrução obedecida | % de respostas que seguiram formato/tom |
| Taxa de API desnecessária | chamadas feitas quando dados já estavam no histórico |
| Taxa de ambiguidade bem tratada | casos em que perguntou antes de errar |
| Feedback “perdeu contexto” | motivo no thumbs down |

---

# 33. Motivos estruturados para feedback negativo

Adicionar opções no front:

- Perdeu o contexto
- Usou produto errado
- Não seguiu o formato pedido
- Não lembrou a resposta anterior
- Chamou consulta errada
- Resposta muito longa
- Resposta muito técnica
- Dados incorretos
- Faltou fonte
- Outro

Isso permite medir exatamente o problema relatado.

---

# 34. Anti-padrões

Evitar:

1. Resolver contexto só no prompt.
2. Jogar todo histórico no LLM.
3. Tratar “isso” como texto genérico.
4. Reexecutar todas as actions do histórico.
5. Herdar produto antigo após usuário informar novo produto.
6. Confundir agradecimento com última resposta útil.
7. Salvar preferências globais sem consentimento.
8. Misturar contexto entre agentes.
9. Perguntar código quando ele já está no estado.
10. Ignorar instrução persistente de formato.

---

# 35. Resumo executivo

Para o Minha DELPI Chat IA parar de se perder no contexto, a melhoria principal é criar uma memória estruturada de sessão.

Essa memória deve guardar:

- últimas entidades;
- últimos resultados úteis;
- últimas actions;
- parâmetros usados;
- preferências de comportamento;
- pendências de esclarecimento;
- candidatos para comparação.

O pipeline deve resolver referências antes de chamar API ou LLM.

A interface deve mostrar o contexto ativo para o usuário e permitir limpar ou fixar preferências.

O adminDebug deve registrar claramente qual memória foi usada, para facilitar auditoria.

A prioridade recomendada é:

1. Detectar e persistir instruções de comportamento.
2. Resolver “esse produto”, “essa tabela”, “o anterior”, “mesmo período”.
3. Reutilizar parâmetros em follow-ups operacionais.
4. Responder sobre dados já consultados sem chamar API.
5. Criar testes multi-turno e feedback “perdeu contexto”.

Com isso, o chat passa a se comportar mais como um assistente real: lembra o que acabou de acontecer, segue a forma de resposta pedida e só pergunta de novo quando realmente precisa.
