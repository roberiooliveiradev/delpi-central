# 10 — Referência rápida de endpoints

## Health

| Método | Path | Permissão |
|---|---|---|
| GET | `/health` | Público |

## Chat — Status e capabilities

| Método | Path | Permissão |
|---|---|---|
| GET | `/chat/status` | `chat.access` |
| GET | `/chat/capabilities` | `chat.access` |

## Chat — Sessões e mensagens

| Método | Path | Permissão |
|---|---|---|
| POST | `/chat/sessions` | `chat.access` |
| GET | `/chat/sessions` | `chat.access` |
| GET | `/chat/sessions/{sessionId}/messages` | `chat.access` |
| POST | `/chat/sessions/{sessionId}/messages` | `chat.ask` |
| POST | `/chat/sessions/{sessionId}/messages/stream` | `chat.ask` |
| PATCH | `/chat/sessions/{sessionId}` | `chat.access` |
| DELETE | `/chat/sessions/{sessionId}` | `chat.access` |
| PATCH | `/chat/sessions/{sessionId}/pin` | `chat.access` |
| PATCH | `/chat/sessions/{sessionId}/unpin` | `chat.access` |
| PATCH | `/chat/sessions/{sessionId}/archive` | `chat.access` |
| PATCH | `/chat/sessions/{sessionId}/unarchive` | `chat.access` |
| PATCH | `/chat/messages/{messageId}` | `chat.ask` |

## Chat — Agentes

| Método | Path | Permissão |
|---|---|---|
| GET | `/chat/agents` | `chat.access` |
| POST | `/chat/agents` | `tools.manage`; `chat.admin` para oficial |
| PATCH | `/chat/agents/{agentId}` | `tools.manage`; `chat.admin` para oficial |
| DELETE | `/chat/agents/{agentId}` | `tools.manage`; `chat.admin` para oficial |
| POST | `/chat/agents/{agentId}/share` | `tools.manage` |

## Chat — Actions/OpenAPI por agente

| Método | Path | Permissão |
|---|---|---|
| GET | `/chat/action-providers` | `chat.access` |
| GET | `/chat/actions` | `chat.access` |
| POST | `/chat/agents/{agentId}/providers/create` | `tools.manage`; `chat.admin` para oficial |
| GET | `/chat/agents/{agentId}/providers` | `chat.access` |
| PUT | `/chat/agents/{agentId}/providers` | `tools.manage`; `chat.admin` para oficial |
| GET | `/chat/agents/{agentId}/providers/{providerKey}` | `chat.access` |
| PATCH | `/chat/agents/{agentId}/providers/{providerKey}` | `tools.manage`; `chat.admin` para oficial |
| POST | `/chat/agents/{agentId}/providers/{providerKey}/import` | `tools.manage`; `chat.admin` para oficial |
| GET | `/chat/agents/{agentId}/actions` | `chat.access` |
| PUT | `/chat/agents/{agentId}/actions` | `tools.manage`; `chat.admin` para oficial |
| POST | `/chat/agents/{agentId}/providers/{providerKey}/actions/{actionId}/test` | `chat.access` |
| GET | `/chat/agents/{agentId}/providers/{providerKey}/actions/{actionId}/logs` | `chat.access` |

## Chat — Projetos

| Método | Path | Permissão |
|---|---|---|
| GET | `/chat/projects` | `chat.access` |
| POST | `/chat/projects` | `chat.access` |
| PATCH | `/chat/projects/{projectId}` | `chat.access` |
| DELETE | `/chat/projects/{projectId}` | `chat.access` |
| POST | `/chat/projects/{projectId}/share` | `chat.access` |

## Chat — Fontes, anexos e artefatos

| Método | Path | Permissão |
|---|---|---|
| GET | `/chat/projects/{projectId}/sources` | `chat.access` |
| POST | `/chat/projects/{projectId}/sources` | `chat.ask` |
| GET | `/chat/agents/{agentId}/sources` | `chat.access` |
| POST | `/chat/agents/{agentId}/sources` | `chat.ask` |
| DELETE | `/chat/sources/{sourceId}` | `chat.ask` |
| POST | `/chat/attachments` | `chat.ask` |
| POST | `/chat/sessions/{sessionId}/attachments` | `chat.ask` |
| GET | `/chat/sessions/{sessionId}/attachments` | `chat.access` |
| DELETE | `/chat/attachments/{attachmentId}` | `chat.ask` |
| GET | `/chat/sessions/{sessionId}/artifacts` | `chat.access` |
| POST | `/chat/sessions/{sessionId}/artifacts` | `chat.ask` |
| PATCH | `/chat/artifacts/{artifactId}` | `chat.ask` |
| DELETE | `/chat/artifacts/{artifactId}` | `chat.ask` |

## Knowledge

| Método | Path | Permissão |
|---|---|---|
| POST | `/knowledge/documents` | `knowledge.manage` |
| POST | `/knowledge/search` | `chat.access` |

## Tools

| Método | Path | Permissão |
|---|---|---|
| POST | `/tools/execute` | `tools.use` |

## Admin

| Método | Path | Permissão |
|---|---|---|
| GET | `/admin/external-action-providers` | `chat.admin` |
| POST | `/admin/external-action-providers` | `chat.admin` |
| POST | `/admin/external-action-providers/{providerKey}/schema` | `chat.admin` |
| POST | `/admin/external-action-providers/{providerKey}/reload-schema` | `chat.admin` |
| GET | `/admin/external-actions` | `chat.admin` |
| GET | `/admin/system-check` | `chat.admin` |
| GET | `/admin/metrics/summary` | `chat.admin` |
| GET | `/admin/llm/status` | `chat.admin` |
| GET | `/admin/knowledge/documents` | `chat.admin` |
| POST | `/admin/knowledge/documents/{documentId}/deactivate` | `chat.admin` |
| POST | `/admin/knowledge/documents/{documentId}/reactivate` | `chat.admin` |
| POST | `/admin/knowledge/documents/{documentId}/reindex` | `chat.admin` |
| GET | `/admin/audit-logs` | `chat.admin` |
