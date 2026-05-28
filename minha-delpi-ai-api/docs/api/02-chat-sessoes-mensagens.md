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
| `adminDebug` | Diagnóstico do turno (pipeline, RAG, tools, LLM). **Persistido** em toda mensagem `assistant`; **retornado** no JSON só para admin (ver abaixo). |

### `metadata.adminDebug` (diagnóstico de turno)

Montado por `ChatAdminDebugService` em todo envio/stream/resend e salvo em `ChatMessage.metadata`.

| Quem vê | Comportamento |
|---------|----------------|
| Usuário comum | Campo **omitido** em `GET /chat/sessions/{id}/messages` e nas respostas de envio |
| Admin (`minha-delpi.chat.admin` ou superadmin) | Presente em `POST .../messages`, evento SSE `done` e histórico |

Estrutura resumida: `workspace`, `pipeline` (`skipRag`, `fastPath`, `analysisMode`, …), `tooling`, `rag` (`sources`, `ragContextText`, opcional `sourcesNote`), `llm.messages`, `recordedAt`.

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
  "canvasOpen": null,
  "adminDebug": null
}
```

| Campo | Descrição |
|-------|-----------|
| `canvasOpen` | Opcional: `{ "title", "markdown", "sourceMessageId" }` quando o usuário pede envio à lousa. |
| `adminDebug` | Objeto de diagnóstico; **só preenchido** para solicitante admin. Demais usuários recebem `null` ou campo ausente. |

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
| `activity` | Durante prepare/tools/RAG (log em tempo real) | `entry` (`id`, `phase`, `group`, `verb`, `target`, `state`, `message`, …) — mesma `id` atualiza a linha no painel |
| `sources` | Após RAG | `sources` |
| `tool_calls` | Após tools | `toolCalls`, `adminGuidelines` |
| `admin_guidelines` | Diretrizes ativas | `adminGuidelines` |
| `assistant_pending` | Resposta persistida vazia, antes do LLM/playback | `messageId` |
| `token` | Streaming legado (`CHAT_PERSIST_BEFORE_PLAYBACK=false`) | `content` |
| `canvas_open` | Pedido de lousa («coloque na lousa/canvas/canva») | `title`, `markdown`, `sourceMessageId`, `messageId` |
| `playback` | Resposta final já no banco; front anima texto | `messageId`, `answer`, `sources`, `toolCalls` |
| `done` | Fim do turno | `messageId`, `answer`, `sources`, `toolCalls`, `playback?`, `canvasOpen?`, `adminDebug?` (admin) |
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

**Apresentação rica:** `toolCalls[].metadata.presentation` (e `tablePresentation` quando o primário é gráfico) alimenta `ChatRichPresentation` no plugin. O campo `answer` não deve repetir os mesmos dados em markdown tabular — ver compactação em [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md).

### Comportamento do pipeline (referência)

| Tipo de pergunta | RAG | Resposta típica |
|------------------|-----|-----------------|
| Operacional (produto, estoque, KPI) | Pode ser omitido (fast path) | Action direta ou LLM curto |
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
