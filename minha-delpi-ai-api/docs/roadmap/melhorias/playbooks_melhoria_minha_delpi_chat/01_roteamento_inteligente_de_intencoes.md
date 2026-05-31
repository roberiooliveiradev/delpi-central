# Playbook 01 — Roteamento inteligente de intenções

> **Status (31/05/2026):** [Parcial](../STATUS_ROADMAP_MELHORIAS.md) — `ChatIntentRouterService`, `adminDebug.intentRoute`, estágio `intent:*`, `subIntent` operacional, `resolvedFromMemory` em follow-ups. Backlog: feedback de roteamento errado no MFE.

## Objetivo

Melhorar a capacidade do Minha DELPI Chat IA de decidir corretamente o que fazer com cada mensagem do usuário:

- responder direto;
- usar LLM;
- usar RAG;
- consultar action/API;
- usar SQL;
- usar lousa/canvas;
- tratar como tarefa textual;
- pedir parâmetro faltante;
- continuar um follow-up.

O roteamento é uma das camadas mais importantes do chat, porque evita que perguntas simples acionem consultas erradas e evita que tarefas textuais sejam confundidas com consultas operacionais.

---

## Problemas que este playbook resolve

- O usuário pede “corrija este texto” e o chat tenta consultar API.
- O usuário pergunta “o que você consegue consultar?” e o chat interpreta como execução.
- O usuário pede “agora fornecedores” e o chat perde o produto anterior.
- O usuário pede “coloque isso na lousa” e o chat não sabe qual resposta usar.
- O usuário pede “mostre vendas do mês passado” e o chat não resolve corretamente o período.
- O usuário pede uma explicação de uma tabela anterior e o chat consulta a API novamente sem necessidade.
- O usuário pergunta algo simples, como “quem é você?”, e o chat chama RAG ou LLM sem necessidade.

---

## Princípio central

Antes de chamar o LLM ou qualquer action, o backend deve classificar a intenção da mensagem.

O chat deve ter um pipeline assim:

```text
Mensagem do usuário
  → segurança
  → contexto do workspace
  → normalização
  → classificação de intenção
  → resolução de referências
  → decisão de rota
  → execução, RAG ou resposta direta
  → montagem da resposta
```

---

## Categorias principais de intenção

| Categoria | Exemplos | Ação recomendada |
|---|---|---|
| `small_talk` | oi, obrigado, valeu | resposta direta |
| `identity` | quem é você? | resposta direta |
| `capabilities` | o que você consegue consultar? | resposta direta com botões |
| `utility` | que horas são? | resposta direta |
| `text_task` | corrija, traduza, resuma | LLM com policy textual |
| `operational_query` | estoque, produto, fornecedor | action/API |
| `sql_task` | monte/revise/execute SQL | skill SQL/action se permitido |
| `rag_question` | dúvida sobre documento/processo | RAG + LLM |
| `canvas_task` | coloque isso na lousa | canvas service |
| `follow_up` | agora fornecedores, faça o mesmo | resolver contexto |
| `clarification_answer` | sim, não, 2026, filial 02 | responder pendência |

---

## Serviço recomendado

Criar ou evoluir:

`ChatIntentRouterService`

### Entrada

```json
{
  "message": "agora fornecedores",
  "normalizedMessage": "agora fornecedores",
  "sessionId": "...",
  "agentKey": "agente-minha-delpi",
  "previousMessages": [],
  "activeContext": {}
}
```

### Saída

```json
{
  "intent": "operational_query",
  "subIntent": "supplier_lookup",
  "isFollowUp": true,
  "confidence": 0.91,
  "requiresTool": true,
  "requiresRag": false,
  "requiresLlm": false,
  "resolvedParams": {
    "productCode": "10080001"
  }
}
```

---

## Ordem de prioridade

Quando uma mensagem se encaixar em várias categorias, seguir esta prioridade:

1. Segurança e bloqueios.
2. Resposta a pendência ativa.
3. Tarefa textual explícita.
4. Lousa/canvas.
5. Follow-up com contexto.
6. Consulta operacional.
7. SQL.
8. RAG/documentação.
9. Capacidades/identidade/utility/small talk.
10. LLM geral.

---

## Regras importantes

### Tarefa textual tem prioridade

Se o usuário disser:

> Corrija este texto: o estoque está baixo.

Não consultar estoque. Corrigir a frase.

### Consulta operacional explícita tem prioridade

Se o usuário disser:

> Qual o estoque do produto 10080001?

Consultar API/action.

### Tarefa mista deve decompor

Se o usuário disser:

> Consulte o estoque do produto 10080001 e escreva um e-mail para compras.

Fluxo:

1. Consultar estoque.
2. Gerar e-mail com base no resultado.
3. Não inventar dados ausentes.

### Follow-up deve herdar contexto

Se o usuário disser:

> Agora fornecedores.

E o último produto foi `10080001`, usar:

> fornecedores do produto 10080001

### Perguntas de capacidade não devem executar action

Se o usuário perguntar:

> Você consegue consultar estoque?

Responder o que consegue fazer e oferecer botão “Consultar estoque”.

---

## Detecção de tarefas textuais

Palavras-chave:

- corrigir;
- revisar;
- reescrever;
- traduzir;
- resumir;
- escrever;
- redigir;
- transformar em e-mail;
- criar ata;
- criar comunicado;
- melhorar texto;
- deixar mais formal;
- deixar mais simples.

Ações:

- não consultar action operacional;
- acionar policy de texto;
- usar LLM;
- oferecer chips de continuação.

---

## Detecção de consultas operacionais

Palavras-chave:

- produto;
- estoque;
- fornecedor;
- cliente;
- estrutura;
- BOM;
- LMP;
- OV;
- vendas;
- compras;
- nota fiscal;
- preço;
- roteiro;
- inspeção;
- KPI;
- SQL.

Ações:

- validar parâmetros;
- reaproveitar contexto;
- selecionar action;
- apresentar resultado estruturado.

---

## Detecção de follow-up

Frases típicas:

- agora fornecedores;
- e as vendas?;
- faça o mesmo;
- compare com o anterior;
- use o mesmo período;
- coloque isso na lousa;
- transforme em tabela;
- gere gráfico;
- próxima página;
- explique essa tabela.

Ações:

- resolver referências;
- evitar pedir dados já conhecidos;
- reaproveitar última action ou última entidade;
- perguntar se houver ambiguidade.

---

## Detecção de lousa/canvas

Frases típicas:

- coloque isso na lousa;
- atualize a lousa;
- acrescente na lousa;
- transforme essa resposta em documento;
- salve esse resumo;
- abra na lousa.

Ações:

- usar última resposta útil;
- ignorar respostas como “por nada” ou “coloquei na lousa”;
- se for atualização operacional, permitir action antes do canvas.

---

## Exemplos de roteamento

### Exemplo 1

Usuário:

> Corrija: os produto chegou atrasado

Roteamento:

```json
{
  "intent": "text_task",
  "subIntent": "correct",
  "requiresTool": false,
  "requiresLlm": true
}
```

### Exemplo 2

Usuário:

> Estoque do produto 10080001

Roteamento:

```json
{
  "intent": "operational_query",
  "subIntent": "stock_lookup",
  "requiresTool": true,
  "params": {
    "productCode": "10080001"
  }
}
```

### Exemplo 3

Usuário:

> Agora fornecedores

Roteamento:

```json
{
  "intent": "operational_query",
  "subIntent": "supplier_lookup",
  "isFollowUp": true,
  "resolvedFromMemory": {
    "productCode": "10080001"
  }
}
```

---

## Implementação sugerida

### Fase 1

- Criar lista de intenções e prioridades.
- Criar testes para cada intenção.
- Adicionar logs no `adminDebug`.

### Fase 2

- Criar `ChatIntentRouterService`.
- Integrar antes de `ExternalActionSelectionService`.
- Bloquear actions em tarefas textuais puras.

### Fase 3

- Usar memória de sessão para follow-ups.
- Enviar `resolvedIntent` em metadata/adminDebug.

### Fase 4

- Adicionar feedback específico:
  - consulta errada;
  - perdeu contexto;
  - interpretou errado;
  - não seguiu formato.

---

## Testes mínimos

- “Corrija este texto” não chama API.
- “O que você consegue consultar?” não executa action.
- “Estoque do produto 10080001” chama action correta.
- “Agora fornecedores” reaproveita produto.
- “Coloque isso na lousa” usa última resposta útil.
- “Sim” responde pendência ativa.
- “Traduza para inglês” usa modo textual.
- “Mostre vendas do mês passado” resolve período.
- “Execute essa SQL” só executa se action permitida.
- “Quem é você?” usa resposta direta.

---

## Métricas

- Taxa de intenção correta.
- Taxa de action errada.
- Taxa de tarefa textual que acionou action indevida.
- Taxa de follow-up resolvido.
- Taxa de pergunta de parâmetro desnecessária.
- Feedback “consulta errada”.
- Feedback “perdeu contexto”.

---

## Resumo executivo

O roteamento inteligente é a base para o chat ser confiável. Ele deve decidir, antes do LLM e antes das actions, qual caminho seguir. A melhoria principal é separar claramente tarefas textuais, consultas operacionais, RAG, lousa, SQL, respostas diretas e follow-ups.
