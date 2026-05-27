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
  "agentKey": "string|null"
}
```

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
  "canvasOpen": null
}
```

`canvasOpen` (opcional): `{ "title", "markdown", "sourceMessageId" }` quando o usuário pede envio à lousa.

---

## POST `/chat/sessions/{sessionId}/messages/{messageId}/resend/stream`

Reenvia uma mensagem do usuário existente com streaming SSE (útil após falha ou para regenerar resposta).

### Permissão

`minha-delpi.chat.ask`

### Body

Opcional (mesmo formato do envio normal, se o backend aceitar override de contexto).

### Resposta

Mesmos eventos SSE de `messages/stream` (ver lista abaixo).

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
| `sources` | Após RAG | `sources` |
| `tool_calls` | Após tools | `toolCalls`, `adminGuidelines` |
| `admin_guidelines` | Diretrizes ativas | `adminGuidelines` |
| `assistant_pending` | Resposta persistida vazia, antes do LLM/playback | `messageId` |
| `token` | Streaming legado (`CHAT_PERSIST_BEFORE_PLAYBACK=false`) | `content` |
| `canvas_open` | Pedido de lousa («coloque na lousa/canvas/canva») | `title`, `markdown`, `sourceMessageId`, `messageId` |
| `playback` | Resposta final já no banco; front anima texto | `messageId`, `answer`, `sources`, `toolCalls` |
| `done` | Fim do turno | `messageId`, `answer`, `sources`, `toolCalls`, `playback?`, `canvasOpen?` |
| `error` | Falha | `detail` ou `message` |

Fluxo típico com `CHAT_PERSIST_BEFORE_PLAYBACK=true` (default):

```text
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

**Lousa:** interpreta «lousa», «canvas» e «canva» (sem `canva.com`) como a lousa DELPI; exige `capabilities.canvas !== false` no agente. O conteúdo vem da **última mensagem `assistant`** do histórico.

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
  "rating": 1
}
```

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
  "rating": 1,
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

Persistência: tabela `ai_chat_message_feedback` (único por `message_id` + `user_id`).
