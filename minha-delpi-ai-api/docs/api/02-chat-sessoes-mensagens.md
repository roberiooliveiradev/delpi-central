# 02 — Chat, sessões, mensagens e streaming

## Tipos principais

### `ChatSession`

```json
{
  "id": "uuid",
  "title": "string|null",
  "context": "string|null",
  "project_id": "uuid|null",
  "agent_key": "string|null",
  "is_pinned": false,
  "pinned_at": "datetime|null",
  "archived_at": "datetime|null",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### `ChatMessage`

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "role": "user|assistant|system",
  "content": "string",
  "metadata": {},
  "created_at": "datetime",
  "user_feedback": 1
}
```

| Campo | Descrição |
|-------|-----------|
| `user_feedback` | Presente em mensagens `assistant` do histórico do usuário: `1` (útil), `-1` (não útil) ou omitido/`null` se não avaliada. |
| `user_feedback_reason` | Motivo estruturado do thumbs down (ex.: `incomplete`, `wrong_data`), quando informado. IDs válidos vêm de `personality_playbook.json` → `feedbackReasons`. |
| `branch` | Em perguntas `user` com variações (irmãs): `{ currentIndex, total, siblingIds }` para navegação « 1 / N ». |
| `adminDebug` | Diagnóstico do turno (pipeline, RAG, tools, LLM). **Persistido** em toda mensagem `assistant`; **retornado** no JSON só para admin (ver abaixo). |
| `contextSnapshot` | Snapshot pós-turno da memória de contexto (entidades, follow-up, referências). Persistido no `assistant`. |
| `contextAssertiveness` | Score 0–100 e `flags` de assertividade contextual do turno. Persistido no `assistant`. |
| `followUpSuggestions` | Chips «Próximos passos» (`label`, `query`) após respostas operacionais. |

### `metadata.adminDebug` (diagnóstico de turno)

Montado por `ChatAdminDebugService` em todo envio/stream/resend e salvo em `ChatMessage.metadata`.

| Quem vê | Comportamento |
|---------|----------------|
| Usuário comum | Campo **omitido** em `GET /chat/sessions/{id}/messages` e nas respostas de envio |
| Admin (`minha-delpi.chat.admin` ou superadmin) | Presente em `POST .../messages`, evento SSE `done` e histórico |

Estrutura resumida: `workspace`, `pipeline` (`skipRag`, `fastPath`, `analysisMode`, …), `tooling`, `rag` (`sources`, `ragContextText`, opcional `sourcesNote`), `llm.messages`, `recordedAt`.

Na resposta HTTP/SSE ao admin, o objeto pode incluir também (mesclado após o turno):

| Campo | Descrição |
|-------|-----------|
| `memory` | Resumo compacto de `contextSnapshot` (`lastEntities`, follow-up) |
| `contextAssertiveness` | Mesmo conteúdo de `metadata.contextAssertiveness` |
| `intelligence` | Timings e estágios do pipeline (`timings`, `pipeline.stages`, …) |

Validação de identidade do assistente («quem te criou?»), com atalho direto (default):

- `pipeline.skipRag === true`, `rag.ragContextText` vazio, resposta em poucos segundos.
- `directResponse: true` no evento `done` (stream) ou metadado equivalente.
- Para homologar RAG+LLM: `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED=false` no `.env` da API.

Arquitetura: [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md#diagnóstico-admin-admindebug).

---

## POST `/chat/sessions`

Cria uma sessão.

### Permissão

`minha-delpi.chat.access`

### Body

```json
{
  "title": "Nova conversa",
  "context": "geral",
  "projectId": "uuid|null",
  "agentId": "uuid|null",
  "forkFromSessionId": "uuid|null",
  "forkUntilMessageId": "uuid|null"
}
```

`forkFromSessionId` + `forkUntilMessageId` — **continuar daqui**: nova sessão com histórico copiado até a mensagem indicada (contexto acima preservado). Se o ponto de corte for uma **pergunta user** e já existir **resposta assistant** no ramo ativo da sessão de origem, a resposta também é copiada (evita conversa “travada” aguardando resposta). Mensagens copiadas recebem `metadata.delivery.status = ready`.

### Resposta `201`

`ChatSession`

---

## GET `/chat/sessions`

Lista sessões do usuário.

### Permissão

`minha-delpi.chat.access`

### Query params

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `archived` | `boolean` | Quando `true`, lista arquivadas. |

### Resposta `200`

```json
[
  {
    "id": "uuid",
    "title": "Minha conversa",
    "context": "geral",
    "project_id": null,
    "agent_key": null,
    "is_pinned": false,
    "pinned_at": null,
    "archived_at": null,
    "created_at": "datetime",
    "updated_at": "datetime"
  }
]
```

---

## POST `/chat/sessions/{sessionId}/memory/clear`

Desativa memória persistida da sessão (produto/filial em foco, preferências de formato/tom).

### Permissão

`minha-delpi.chat.ask`

### Resposta `200`

```json
{ "cleared": 2 }
```

---

## GET `/chat/sessions/{sessionId}/memory/context`

Retorna chips de contexto persistido, resumo da barra e visão para o modal «Memória usada».

### Permissão

`minha-delpi.chat.ask`

### Resposta `200`

```json
{
  "chips": [{ "label": "Produto 10080001", "kind": "product", "value": "10080001" }],
  "summary": "Produto 10080001 · Pergunta: Compare…",
  "usage": { "topic": "estoque", "userContextItems": ["Pergunta: Compare…"] }
}
```

---

## POST `/chat/sessions/{sessionId}/memory/context-items`

Adiciona item de contexto manual (classificação automática).

### Body (exemplos)

Texto livre:

```json
{ "content": "Filial 01, priorizar tabela" }
```

Pergunta da conversa:

```json
{
  "content": "Qual o estoque do 10080001?",
  "role": "user",
  "messageId": "uuid-da-mensagem"
}
```

Par pergunta + resposta:

```json
{
  "question": "Compare com o anterior",
  "answer": "A diferença é o prazo de entrega.",
  "questionMessageId": "uuid-user",
  "answerMessageId": "uuid-assistant"
}
```

Re-adicionar a mesma mensagem substitui o item anterior (dedup por `messageId`).

### Resposta `200`

Mesmo formato de `GET .../memory/context`.

---

## DELETE `/chat/sessions/{sessionId}/memory/context-items/{itemId}`

Remove um item (`itemId` = campo `value` do chip, uuid do item).

### Resposta `200`

Mesmo formato de `GET .../memory/context`.

---

## GET `/chat/sessions/{sessionId}/messages`

Lista mensagens de uma sessão.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatMessage[]`

---

## POST `/chat/sessions/{sessionId}/messages`

Envia mensagem sem streaming.

### Permissão

`minha-delpi.chat.ask`

### Body

```json
{
  "message": "Explique o status do produto X",
  "context": "geral",
  "attachmentIds": ["uuid"]
}
```

### Resposta `200`

```json
{
  "messageId": "uuid",
  "answer": "Resposta do assistente",
  "sources": [],
  "toolCalls": [],
  "canvasOpen": null,
  "adminDebug": null
}
```

| Campo | Descrição |
|-------|-----------|
| `canvasOpen` | Opcional: `{ "title", "markdown", "sourceMessageId" }` quando o usuário pede envio à lousa. |
| `adminDebug` | Objeto de diagnóstico; **só preenchido** para solicitante admin. Demais usuários recebem `null` ou campo ausente. |

---

## Ramificações (branches) — maio/2026

Cada mensagem forma uma **árvore** via `parent_message_id`. A sessão guarda `active_leaf_message_id` (folha do ramo ativo).

| Ação | Comportamento |
|------|----------------|
| **Envio normal** | Nova mensagem user com `parent` = folha ativa; resposta assistant filha do user; folha avança. |
| **Editar e reenviar** | Cria **nova** mensagem user irmã (mesmo `parent`); ramo anterior permanece; folha segue o novo ramo. A pergunta da variação é persistida e commitada **no início** do stream (`user_persisted`), como no envio normal. |
| **Alternar variação** | `PATCH .../active-branch` com `anchorUserMessageId` (pergunta user do ramo desejado). |
| **Continuar daqui** | `POST /chat/sessions` com `forkFromSessionId` + `forkUntilMessageId` → **nova conversa** (não abre branch na mesma sessão). |
| **Cancelar stream** | Cliente aborta o SSE; pergunta já commitada permanece no banco. Reenviar usa o `messageId` da pergunta **âncora** (original ou variação), mesmo que ela não esteja no caminho ativo exibido. |

### UI (plugin `minha-delpi-chat`)

| Elemento | Comportamento |
|----------|----------------|
| Setas **1 / N** | Em perguntas user com irmãos; alterna ramo via `PATCH .../active-branch`. |
| **Continuar daqui** | Ícone de branch em user e assistant; abre nova sessão (fork). |
| **Editar e reenviar** | Card de edição fecha ao enviar; IDs `optimistic-*` bloqueados até `user_persisted`. |
| **Parar** | Aborta SSE, recarrega histórico e limpa UI de streaming/playback. |

`GET .../messages` retorna só o **caminho ativo** (raiz → folha). Perguntas user com irmãos incluem:

```json
"branch": { "currentIndex": 2, "total": 2, "siblingIds": ["...", "..."] }
```

---

## POST `/chat/sessions/{sessionId}/messages/{messageId}/resend/stream`

Reenvia uma mensagem do usuário existente com streaming SSE — abre **nova variação (branch)**, sem apagar histórico anterior.

O path `{messageId}` é a pergunta **âncora** (user) a partir da qual se cria a variação irmã. Pode ser uma pergunta fora do caminho ativo (ex.: variação anterior após trocar ramo).

A **nova** pergunta da variação é criada e commitada **antes** do prepare (`user_persisted`), igual ao envio normal — cancelar o stream após parar não perde a pergunta no banco.

### Permissão

`minha-delpi.chat.ask`

### Body

Opcional (mesmo formato do envio normal, se o backend aceitar override de contexto).

### Resposta

Mesmos eventos SSE de `messages/stream` (ver lista abaixo).

---

## PATCH `/chat/sessions/{sessionId}/active-branch`

Alterna o ramo ativo da conversa (UI « 1 / 2 »).

### Body

```json
{ "anchorUserMessageId": "uuid-da-pergunta-user" }
```

### Resposta

`200` — lista de mensagens do **novo caminho ativo** (mesmo formato de `GET .../messages`).

---

## POST `/chat/sessions/{sessionId}/messages/stream`

Envia mensagem com streaming SSE.

### Permissão

`minha-delpi.chat.ask`

### Body

Mesmo de envio normal:

```json
{
  "message": "teste de streaming pelo agente Minha DELPI Chat",
  "context": "geral",
  "attachmentIds": null
}
```

### Eventos SSE

| Evento | Quando | Payload principal |
|--------|--------|-------------------|
| `status` | Etapas intermediárias | `message` |
| `activity` | Durante prepare/tools/RAG (log em tempo real) | `entry` (`id`, `phase`, `group`, `verb`, `target`, `state`, `message`, …) — mesma `id` atualiza a linha no painel |
| `sources` | Após RAG | `sources` |
| `tool_calls` | Após tools | `toolCalls`, `adminGuidelines` |
| `admin_guidelines` | Diretrizes ativas | `adminGuidelines` |
| `assistant_pending` | Placeholder assistant persistido (`delivery=generating`), antes do LLM/playback | `messageId` |
| `user_persisted` | Pergunta do usuário persistida **antes** do prepare (commit incremental) | `messageId` |
| `token` | Streaming legado (`CHAT_PERSIST_BEFORE_PLAYBACK=false`) | `content` |
| `canvas_open` | Pedido de lousa («coloque na lousa/canvas/canva») | `title`, `markdown`, `sourceMessageId`, `messageId` |
| `playback` | Resposta final já no banco; front anima texto | `messageId`, `answer`, `sources`, `toolCalls` |
| `done` | Fim do turno | `messageId`, `answer`, `sources`, `toolCalls`, `playback?`, `canvasOpen?`, `adminDebug?` (admin) |
| `error` | Falha | `detail` ou `message` |

Fluxo típico com `CHAT_PERSIST_BEFORE_PLAYBACK=true` (default):

A pergunta fica persistida e commitada **antes** do prepare (tools/RAG) — tanto no **envio normal** quanto no **reenvio** (`resend/stream`). O plugin substitui mensagens `optimistic-*` ao receber `user_persisted`. Recarregar o histórico mid-stream já mostra a pergunta do usuário.

Após respostas operacionais, `metadata.followUpSuggestions` pode trazer chips de « Próximos passos » (playbook `personality_playbook.json`); desabilitável por agente via `metadata.personality.suggestFollowUps`.

```text
event: user_persisted
data: {"messageId": "..."}

event: status
data: {"message": "Conectado. Preparando resposta..."}

event: activity
data: {"entry": {...}}

event: sources
data: {"sources": [...]}

event: tool_calls
data: {"toolCalls": [...]}

event: assistant_pending
data: {"messageId": "..."}

event: canvas_open
data: {"title": "Perfil", "markdown": "...", "sourceMessageId": "...", "messageId": "..."}

event: playback
data: {"messageId": "...", "answer": "Coloquei ... na lousa", "sources": [], "toolCalls": []}

event: done
data: {"messageId": "...", "answer": "...", "playback": true, "canvasOpen": {...}}
```

Com `CHAT_PERSIST_BEFORE_PLAYBACK=false`, tokens chegam em `event: token` até `done`.

**Lousa:** interpreta «lousa», «canvas» e «canva» (sem `canva.com`) como a lousa DELPI; exige `capabilities.canvas !== false` no agente.

| Intenção | Exemplos | Origem do markdown |
|----------|----------|-------------------|
| Cópia | «coloque na lousa», «manda para o canvas» | Última resposta **útil** do assistente (ignora confirmações de lousa) |
| Append | «acrescente isso na lousa» | Conteúdo já na lousa (`canvasOpen` no histórico) + última resposta útil |
| Append + API | «acrescente na lousa a descrição do produto 10080049» | Lousa existente + resultado da consulta OpenAPI (tool call) |

Resposta curta no chat («Coloquei …» / «Atualizei a lousa …»); conteúdo completo em `canvas_open` / `canvasOpen`. Ver [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md).

**Apresentação rica:** `toolCalls[].metadata.presentation` (e `tablePresentation` quando o primário é gráfico) alimenta `ChatRichPresentation` no plugin. O campo `answer` não deve repetir os mesmos dados em markdown tabular — ver compactação em [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md).

### Comportamento do pipeline (referência)

| Tipo de pergunta | RAG | Resposta típica |
|------------------|-----|-----------------|
| Operacional (produto, estoque, KPI) | Pode ser omitido (fast path) | Action direta ou LLM curto |
| Small talk («olá», «obrigado») | Não | Resposta direta `ChatSmallTalkService` |
| Meta composta (perfil + capacidades + assistente) | Não | Resposta direta `ChatMetaDirectAnswerService` |
| Lousa — cópia / append | Não | `canvas_open` + confirmação curta; append operacional pode incluir `toolCalls` |
| Identidade do **usuário** («quem sou eu») | Não | Resposta direta via Core API / contexto |
| Identidade do **assistente** («quem te criou») | **Não** (default) | Resposta canônica `identity.json` via `build_direct_answer`; `pipeline.skipRag: true`, `directResponse: true` |
| Capacidades («consegue buscar por grupo?») | Não | Resposta direta `ChatCapabilitiesService` |

Detalhes: [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md).

---

## PATCH `/chat/sessions/{sessionId}`

Renomeia a sessão.

### Permissão

`minha-delpi.chat.access`

### Body

```json
{
  "title": "Novo título"
}
```

### Resposta `200`

`ChatSession`

---

## DELETE `/chat/sessions/{sessionId}`

Remove uma sessão.

### Permissão

`minha-delpi.chat.access`

### Resposta

`204 No Content`

---

## PATCH `/chat/sessions/{sessionId}/pin`

Fixa a sessão.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatSession`

---

## PATCH `/chat/sessions/{sessionId}/unpin`

Remove fixação.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatSession`

---

## PATCH `/chat/sessions/{sessionId}/archive`

Arquiva a sessão.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatSession`

---

## PATCH `/chat/sessions/{sessionId}/unarchive`

Desarquiva a sessão.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatSession`

---

## PATCH `/chat/messages/{messageId}`

Atualiza conteúdo de uma mensagem.

### Permissão

`minha-delpi.chat.ask`

### Body

```json
{
  "content": "conteúdo atualizado"
}
```

### Resposta `200`

`ChatMessage`

---

## PUT `/chat/sessions/{sessionId}/messages/{messageId}/feedback`

Registra ou remove feedback do usuário em uma mensagem do **assistente**.

### Permissão

`minha-delpi.chat.ask`

### Body

```json
{
  "rating": 1,
  "reason": "incomplete"
}
```

| Campo | Descrição |
|-------|-----------|
| `rating` | Ver tabela abaixo |
| `reason` | Opcional; só aplicável com `rating: -1`. ID estruturado do playbook (`feedbackReasons`). Omitir ou `null` remove o motivo. |

| `rating` | Comportamento |
|----------|----------------|
| `1` | Resposta útil (thumbs up) |
| `-1` | Resposta não útil (thumbs down) |
| `null` | Remove feedback existente |

### Resposta `200`

Com rating:

```json
{
  "messageId": "uuid",
  "userId": "uuid",
  "rating": -1,
  "reason": "incomplete",
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

Ao remover:

```json
{
  "removed": true
}
```

### Erros

| Código | Situação |
|--------|----------|
| `400` | Mensagem inexistente na sessão, não é `assistant`, ou `rating` inválido |
| `403` | Sessão de outro usuário |

Persistência: tabela `ai_chat_message_feedback` (único por `message_id` + `user_id`; coluna opcional `reason`, migração `n6o7p8q9r0s1`).

---

## Inteligência transversal (comportamento do assistente)

O envio de mensagens (`POST .../messages` e `.../stream`) passa pelo **mesmo pipeline** para chat livre, sessão com agente ou simulação admin. Regras de roteamento, comparação de estruturas, capacidades e typos estão na **camada base** — não duplicadas no JSON do agente.

| Tema | Comportamento |
|------|----------------|
| Agente com actions **api-delpi** | `ExternalActionSelectionService` escolhe a rota antes do LLM (fast path operacional). |
| Busca por **grupo** | `GET /products/search` com `group_code`; o número após «grupo» não é tratado como código de produto. |
| Pergunta **«consegue…?»** | Resposta de capacidades sem executar API (`ChatCapabilitiesService`). |
| **Comparação** de estruturas | Múltiplas consultas + síntese; não reutiliza só o histórico. |
| Documentos na base | Limite configurável `KNOWLEDGE_DOCUMENT_MAX_CHARS` (default 2.000.000 caracteres). |
| Typos leves | Normalização (ex.: ebita→ebitda, coonsegue→consegue) na seleção de rotas. |

Documentação detalhada:

- [Camadas de preparação antes do LLM](../architecture/chat-pre-llm-layers.md)
- [Arquitetura — inteligência no chat base](../architecture/chat-intelligence-base.md)
- [Mapa de rotas api-delpi para agentes](../knowledge/api-delpi-rotas-agente.md)
- [Auditoria e testes de regressão](../roadmap/api-delpi-chat-intelligence-audit.md)
