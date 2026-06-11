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
| POST | `/chat/typing-suggestions` | `chat.access` |
| GET | `/chat/assistant/catalog` | `chat.access` |

Query opcional em `/chat/assistant/catalog`: `q` (busca), `agentId` (disponibilidade no agente), `limit` (1–50).

Resposta inclui `userContext` (`canUseTools`, `isSuperadmin`, `canOpenAdmin`) e `availability.requiresProfilePermission` (funcionalidades bloqueadas pelo perfil, ocultas em `features`).

| Método | Path | Permissão |
|---|---|---|
| POST | `/chat/assistant/help-events` | `chat.access` |

Body: `{ "event": "help_panel_open" | … | "typing_correction_offered" | "typing_correction_accepted" | "typing_correction_dismissed", "metadata": {} }`.

Body `POST /chat/typing-suggestions`: `{ "text": "estouque do produto 90262404", "locale": "pt-BR" }` → `{ "hasSuggestions", "corrected", "changes", "protectedSpans" }`.

## Chat — Sessões e mensagens

| Método | Path | Permissão |
|---|---|---|
| POST | `/chat/sessions` | `chat.access` |
| GET | `/chat/sessions` | `chat.access` |
| GET | `/chat/sessions/{sessionId}/messages` | `chat.access` |
| POST | `/chat/sessions/{sessionId}/messages` | `chat.ask` |
| POST | `/chat/sessions/{sessionId}/messages/stream` | `chat.ask` |
| POST | `/chat/sessions/{sessionId}/messages/{messageId}/resend/stream` | `chat.ask` |
| PATCH | `/chat/sessions/{sessionId}` | `chat.access` |
| DELETE | `/chat/sessions/{sessionId}` | `chat.access` |
| PATCH | `/chat/sessions/{sessionId}/pin` | `chat.access` |
| PATCH | `/chat/sessions/{sessionId}/unpin` | `chat.access` |
| PATCH | `/chat/sessions/{sessionId}/archive` | `chat.access` |
| PATCH | `/chat/sessions/{sessionId}/unarchive` | `chat.access` |
| PATCH | `/chat/messages/{messageId}` | `chat.ask` |
| PUT | `/chat/sessions/{sessionId}/messages/{messageId}/feedback` | `chat.ask` |

## Chat — Agentes

| Método | Path | Permissão |
|---|---|---|
| GET | `/chat/agents` | `chat.access` |
| GET | `/chat/agents?includeDisabled=true` | `chat.access` |
| GET | `/chat/agents?includeStats=true&hours=168` | `chat.access` |
| GET | `/chat/agents/{agentId}` | `chat.access` |
| POST | `/chat/agents` | `tools.manage`; `chat.admin` para oficial |
| PATCH | `/chat/agents/{agentId}` | `tools.manage`; `chat.admin` para oficial |
| DELETE | `/chat/agents/{agentId}` | `tools.manage`; `chat.admin` para oficial |
| POST | `/chat/agents/{agentId}/share` | `tools.manage` |
| GET | `/chat/agents/{agentId}/shares` | `tools.manage` (owner) |
| DELETE | `/chat/agents/{agentId}/shares/{targetUserId}` | `tools.manage` (owner) |
| POST | `/chat/agents/preview` | `tools.manage` |
| POST | `/chat/agents/{agentId}/preview` | `tools.manage` |
| POST | `/chat/agents/{agentId}/publish` | `tools.manage` |
| GET | `/chat/agents/{agentId}/versions` | `tools.manage` |
| POST | `/chat/agents/{agentId}/duplicate` | `tools.manage` |
| GET | `/chat/agents/{agentId}/export` | `tools.manage` |
| POST | `/chat/agents/import` | `tools.manage` |
| GET | `/chat/agents/{agentId}/stats` | `tools.manage` |
| POST | `/chat/agents/{agentId}/transfer` | `tools.manage` (owner) |
| GET | `/chat/users/search` | `tools.manage` |

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
| GET | `/chat/skills` | `chat.access` |
| GET | `/chat/agents/{agentId}/skills` | `chat.access` |
| PUT | `/chat/agents/{agentId}/skills` | `tools.manage`; `chat.admin` para oficial |
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
| GET | `/chat/projects/{projectId}/shares` | `chat.access` (owner) |
| DELETE | `/chat/projects/{projectId}/shares/{targetUserId}` | `chat.access` (owner) |

## Chat — Fontes, anexos e artefatos

| Método | Path | Permissão |
|---|---|---|
| GET | `/chat/projects/{projectId}/sources` | `chat.access` |
| POST | `/chat/projects/{projectId}/sources` | `chat.ask` |
| GET | `/chat/agents/{agentId}/sources` | `chat.access` |
| POST | `/chat/agents/{agentId}/sources` | `chat.ask` |
| DELETE | `/chat/sources/{sourceId}` | `chat.ask` |
| GET | `/chat/sources/{sourceId}/download` | `chat.access` |
| POST | `/chat/attachments` | `chat.ask` |
| POST | `/chat/sessions/{sessionId}/attachments` | `chat.ask` |
| GET | `/chat/sessions/{sessionId}/attachments` | `chat.access` |
| GET | `/chat/attachments/{attachmentId}/download` | `chat.access` |
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

## Admin — Skills (catálogo)

| Método | Path | Permissão |
|---|---|---|
| GET | `/admin/skills` | `tools.manage` |
| POST | `/admin/skills` | `tools.manage` |
| PUT | `/admin/skills/{skillId}` | `tools.manage` |
| DELETE | `/admin/skills/{skillId}` | `tools.manage` |

## Admin

| Método | Path | Permissão |
|---|---|---|
| GET | `/admin/external-action-providers` | `chat.admin` |
| POST | `/admin/external-action-providers` | `chat.admin` |
| POST | `/admin/external-action-providers/{providerKey}/schema` | `chat.admin` |
| POST | `/admin/external-action-providers/{providerKey}/reload-schema` | `chat.admin` |
| GET | `/admin/external-actions` | `chat.admin` |
| GET | `/admin/system-check` | `chat.admin` |
| GET | `/admin/tools/health` | `chat.admin` |
| GET | `/admin/metrics/summary` | `chat.admin` |
| GET | `/admin/metrics/timeseries` | `chat.admin` |
| GET | `/admin/metrics/cost-table` | `chat.admin` |
| PUT | `/admin/metrics/cost-table` | `chat.admin` |
| GET | `/admin/llm/status` | `chat.admin` |
| GET | `/admin/rbac/summary` | `chat.admin` |
| GET | `/admin/rbac/profiles` | `chat.access` |
| GET | `/admin/knowledge/documents` | `chat.admin` |
| PATCH | `/admin/knowledge/documents/{documentId}/metadata` | `chat.admin` |
| POST | `/admin/knowledge/ingest/preview` | `chat.admin` |
| GET | `/admin/responses/evaluations/summary` | `chat.admin` |
| GET | `/admin/responses/candidates` | `chat.admin` |
| GET | `/admin/responses/messages/{messageId}/evaluation-context` | `chat.admin` |
| GET | `/admin/responses/evaluations` | `chat.admin` |
| POST | `/admin/responses/evaluations` | `chat.admin` |
| GET | `/admin/agents/specializations/catalog` | `chat.admin` |
| GET | `/admin/agents/specialized` | `chat.admin` |
| PUT | `/admin/agents/{agentId}/specialization` | `chat.admin` |
| GET | `/admin/security/config` | `chat.admin` |
| GET | `/admin/security/summary` | `chat.admin` |
| GET | `/admin/security/events` | `chat.admin` |
| POST | `/admin/security/scan` | `chat.admin` |
| POST | `/admin/knowledge/documents/{documentId}/deactivate` | `chat.admin` |
| POST | `/admin/knowledge/documents/{documentId}/reactivate` | `chat.admin` |
| POST | `/admin/knowledge/documents/{documentId}/reindex` | `chat.admin` |
| POST | `/admin/agent/simulate` | `chat.admin` |
| GET | `/admin/audit-logs` | `chat.admin` |
| GET | `/admin/audit-logs/timeline` | `chat.admin` |
| GET | `/admin/audit-logs/export` | `chat.admin` |
| GET | `/admin/audit-logs/{logId}` | `chat.admin` |
