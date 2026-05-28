# 00 — Visão geral, autenticação e convenções

## Base URL

```text
/apps/minha-delpi-ai/api
```

Os blueprints atuais expõem:

| Prefixo | Responsabilidade |
|---|---|
| `/health` | Health check público. |
| `/chat` | Chat, sessões, agentes, projects, sources, anexos, artefatos e actions por agente. |
| `/knowledge` | Ingestão e busca na base de conhecimento. |
| `/tools` | Execução direta de tools internas. |
| `/admin` | Administração, métricas, providers globais, audit logs e documentos de knowledge. |

## Autenticação

A API usa Bearer Token Keycloak/core-api na maioria das rotas:

```http
Authorization: Bearer <access_token>
```

Os decorators de permissão usam constantes centralizadas, por exemplo:

```python
CHAT_ACCESS_PERMISSION = "minha-delpi.chat.access"
CHAT_TOOLS_MANAGE_PERMISSION = "minha-delpi.chat.tools.manage"
```

## Formato de erro

Erros seguem o padrão:

```json
{
  "errors": [
    {
      "code": "invalid_request",
      "message": "Request body must be a JSON object",
      "path": "_global"
    }
  ]
}
```

Códigos HTTP comuns:

| Código | Uso típico |
|---|---|
| `200` | Operação concluída com payload. |
| `201` | Recurso criado. |
| `204` | Recurso removido sem payload. |
| `400` | Payload inválido, JSON ausente ou parâmetro obrigatório. |
| `403` | Permissão insuficiente. |
| `404` | Recurso inexistente ou inacessível ao usuário. |
| `429` | Rate limit, quando configurado. |
| `500` | Erro interno não tratado. |

## Permissões

| Constante | Valor | Uso |
|---|---|---|
| `CHAT_ACCESS_PERMISSION` | `minha-delpi.chat.access` | Leitura/uso básico do módulo. |
| `CHAT_ASK_PERMISSION` | `minha-delpi.chat.ask` | Envio de mensagens, fontes e anexos. |
| `CHAT_HISTORY_VIEW_PERMISSION` | `minha-delpi.chat.history.view` | Histórico, quando aplicável. |
| `CHAT_KNOWLEDGE_MANAGE_PERMISSION` | `minha-delpi.chat.knowledge.manage` | Ingestão/gestão de conhecimento. |
| `CHAT_TOOLS_USE_PERMISSION` | `minha-delpi.chat.tools.use` | Uso de ferramentas/actions. |
| `CHAT_TOOLS_MANAGE_PERMISSION` | `minha-delpi.chat.tools.manage` | Gerenciar agentes/actions próprios. |
| `CHAT_ADMIN_PERMISSION` | `minha-delpi.chat.admin` | Administração, inclusive agentes oficiais/system. |

## Agentes oficiais vs próprios

- `visibility = "system"` ou `owner_user_id = null`: agente oficial/system.
- Agente próprio: tem `owner_user_id` e visibilidade `private` ou `public`.
- `tools.manage`: gerencia agentes próprios e suas actions.
- `chat.admin` ou superadmin: gerencia agentes oficiais/system.

Acesso na listagem: oficiais/públicos, próprios e compartilhados (`ai_chat_agent_share`). Detalhes de API: `03-agentes.md`. Evolução da gestão: `../roadmap/agentes-gestao-melhorias.md`.

### Agente na conversa

- Sessão com `agent_key` (ou projeto com `default_agent_key`).
- Agentes precisam estar **publicados** (`published_version >= 1`) para uso por visitantes; o runtime aplica `published_config` (snapshot).
- Cada mensagem monta contexto com `system_prompt`, especialização RAG, skills ativas, `allowedActionIds` e limites do agente.
- O chat **sem agente** não executa external actions OpenAPI vinculadas a agentes; skills globais (SQL, `company-knowledge`) seguem env defaults.
- Perguntas sobre o **assistente** («quem te criou») usam resposta canônica direta (sem LLM) por padrão — ver [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md).
- Turnos persistem `metadata.adminDebug` no banco; a API só devolve esse campo a usuários admin — ver `02-chat-sessoes-mensagens.md`.

## Capabilities

O frontend deve consultar:

```http
GET /chat/capabilities
```

Retorno típico:

```json
{
  "permissions": ["minha-delpi.chat.access"],
  "isSuperadmin": false,
  "canManageAgents": true,
  "canManageOwnAgents": true,
  "canManageOfficialAgents": false,
  "canManageTools": true,
  "canUseTools": true
}
```

## Streaming SSE

`POST /chat/sessions/{sessionId}/messages/stream` usa Server-Sent Events.

Eventos esperados:

| Evento | Payload |
|---|---|
| `sources` | `{ "sources": [...] }` |
| `tool_calls` | `{ "toolCalls": [...] }` |
| `assistant_pending` | `{ "messageId": "..." }` |
| `token` | `{ "content": "..." }` (modo legado sem persist-before-playback) |
| `canvas_open` | `{ "title", "markdown", "sourceMessageId", "messageId" }` |
| `playback` | `{ "messageId", "answer", "sources", "toolCalls" }` |
| `done` | payload compatível com `SendChatMessageResponse` (`playback`, `canvasOpen` opcionais) |
| `error` | `{ "message": "..." }` |
