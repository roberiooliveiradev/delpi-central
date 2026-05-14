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
  "created_at": "datetime"
}
```

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
  "toolCalls": []
}
```

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

```text
event: sources
data: {"sources": [...]}


event: tool_calls
data: {"toolCalls": [...]}


event: token
data: {"content": "Olá"}


event: done
data: {"messageId": "...", "answer": "...", "sources": [], "toolCalls": []}
```

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
