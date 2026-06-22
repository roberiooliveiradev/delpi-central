# 05 — Projetos, fontes, anexos e artefatos

## Projetos

### `ChatProject`

```json
{
  "id": "uuid",
  "name": "Projeto",
  "description": "string|null",
  "instructions": "string|null",
  "default_agent_key": "string|null",
  "visibility": "private|public",
  "icon": "string|null",
  "color": "string|null",
  "archived_at": "datetime|null",
  "metadata": {},
  "access_role": "owner|editor|viewer",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### GET `/chat/projects`

Lista projetos.

Permissão: `minha-delpi.chat.access`

Query params:

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `archived` | `boolean` | Quando `true`, lista arquivados. |

Resposta: `ChatProject[]`

### POST `/chat/projects`

Cria projeto.

Permissão: `minha-delpi.chat.access`

```json
{
  "name": "Projeto X",
  "description": "Descrição",
  "visibility": "private",
  "icon": "folder",
  "metadata": {}
}
```

Resposta `201`: `ChatProject`

### PATCH `/chat/projects/{projectId}`

Atualiza projeto.

Permissão: `minha-delpi.chat.access`

```json
{
  "name": "Novo nome",
  "description": "Nova descrição",
  "visibility": "public",
  "icon": "folder",
  "metadata": {},
  "archived": false
}
```

Resposta `200`: `ChatProject`

### DELETE `/chat/projects/{projectId}`

Remove projeto.

Permissão: `minha-delpi.chat.access`

Resposta: `204 No Content`

### POST `/chat/projects/{projectId}/share`

> **Desabilitado (jun/2026):** retorna `501 feature_not_enabled`. Ver [projetos-colaborativos-futuro.md](../roadmap/projetos-colaborativos-futuro.md).

Compartilha projeto.

Permissão: `minha-delpi.chat.access`

```json
{
  "targetUserId": "uuid",
  "role": "viewer"
}
```

Resposta:

```json
{
  "ok": true
}
```

### GET `/chat/projects/{projectId}/shares`

> **Desabilitado (jun/2026):** retorna `501 feature_not_enabled`.

Lista compartilhamentos do projeto (somente `owner`).

Permissão: `minha-delpi.chat.access`

Resposta: array com `target_user_id`, `target_user_name`, `target_user_email` (quando disponível), `role`, `created_at`.

### DELETE `/chat/projects/{projectId}/shares/{targetUserId}`

> **Desabilitado (jun/2026):** retorna `501 feature_not_enabled`.

Revoga compartilhamento (somente `owner`).

Permissão: `minha-delpi.chat.access`

Resposta: `204 No Content`

---

## Fontes de projeto e agente

`ChatWorkspaceSource`:

```json
{
  "id": "uuid",
  "title": "Fonte",
  "source_type": "manual|file|attachment",
  "source_ref": "string|null",
  "scope": "string|null",
  "project_id": "uuid|null",
  "agent_key": "string|null",
  "attachment_id": "uuid|null",
  "original_filename": "string|null",
  "content_type": "string|null",
  "active": true,
  "metadata": {},
  "created_at": "datetime",
  "updated_at": "datetime",
  "chunk_count": 3
}
```

### GET `/chat/projects/{projectId}/sources`

Lista fontes de projeto.

Permissão: `minha-delpi.chat.access`

### POST `/chat/projects/{projectId}/sources`

Cria fonte de projeto.

Permissão: `minha-delpi.chat.ask`

Aceita dois formatos:

#### JSON

```json
{
  "title": "Fonte manual",
  "content": "Conteúdo a indexar",
  "metadata": {}
}
```

#### Multipart

```text
file=<arquivo>
```

### GET `/chat/agents/{agentId}/sources`

Lista fontes de agente.

Permissão: `minha-delpi.chat.access`

### POST `/chat/agents/{agentId}/sources`

Cria fonte de agente.

Permissão: `minha-delpi.chat.ask`

Aceita JSON ou multipart, como fonte de projeto.

### DELETE `/chat/sources/{sourceId}`

Remove/desativa fonte.

Permissão: `minha-delpi.chat.ask`

Resposta: `204 No Content`

### GET `/chat/sources/{sourceId}/download`

Baixa o arquivo da fonte (agente, projeto ou nota de texto).

Permissão: `minha-delpi.chat.access`

Resposta `200`: arquivo binário com header `Content-Disposition: attachment; filename="..."`.

Notas de texto são exportadas como `.md` quando não há arquivo no storage.

---

## Anexos

### `ChatAttachment`

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "message_id": "uuid|null",
  "project_id": "uuid|null",
  "agent_key": "string|null",
  "filename": "arquivo.pdf",
  "original_filename": "Arquivo.pdf",
  "content_type": "application/pdf",
  "size_bytes": 12345,
  "status": "uploaded|indexed|unsupported|index_failed",
  "metadata": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### POST `/chat/attachments`

Faz upload e cria sessão quando necessário.

Permissão: `minha-delpi.chat.ask`

Multipart:

```text
file=<arquivo>
projectId=<uuid opcional>
agentKey=<string opcional>
context=<string opcional>
```

Resposta:

```json
{
  "session": {},
  "attachment": {}
}
```

### POST `/chat/sessions/{sessionId}/attachments`

Upload de anexo para sessão existente.

Permissão: `minha-delpi.chat.ask`

Multipart:

```text
file=<arquivo>
```

Resposta `201`: `ChatAttachment`

### GET `/chat/sessions/{sessionId}/attachments`

Lista anexos de uma sessão.

Permissão: `minha-delpi.chat.access`

Resposta `200`: `ChatAttachment[]`

### DELETE `/chat/attachments/{attachmentId}`

Remove anexo.

Permissão: `minha-delpi.chat.ask`

Resposta: `204 No Content`

### GET `/chat/attachments/{attachmentId}/download`

Baixa o arquivo anexado à conversa.

Permissão: `minha-delpi.chat.access`

Resposta `200`: arquivo binário com header `Content-Disposition: attachment; filename="..."`.

### Armazenamento em disco

Os bytes do arquivo **não** ficam no Postgres — só `storage_path` na tabela `ai_chat_attachments`.

| Ambiente | Raiz (`CHAT_ATTACHMENT_STORAGE_PATH`) | Layout |
|----------|----------------------------------------|--------|
| Docker (compose) | `/data/delpi/chat-attachments` (volume no host) | `{user_id}/{session_id}/{uuid}{ext}` |
| Local / testes | `/tmp/minha-delpi-chat-attachments` (default) | idem |

Fontes de projeto/agente usam `CHAT_SOURCE_STORAGE_PATH` (`ChatSourceFileStorage`).

Operações (backup, `DELPI_DATA_HOST_DIR`, migração de anexos em `/tmp`): [`docs/operations/chat-attachment-storage.md`](../operations/chat-attachment-storage.md).

---

## Artefatos

### `ChatArtifact`

```json
{
  "id": "uuid",
  "session_id": "uuid",
  "message_id": "uuid|null",
  "user_id": "uuid",
  "type": "markdown|table|json|report",
  "title": "Título",
  "content": "conteúdo",
  "metadata": {},
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### GET `/chat/sessions/{sessionId}/artifacts`

Lista artefatos de uma sessão.

Permissão: `minha-delpi.chat.access`

### POST `/chat/sessions/{sessionId}/artifacts`

Cria artefato.

Permissão: `minha-delpi.chat.ask`

```json
{
  "type": "markdown",
  "title": "Relatório",
  "content": "# Relatório",
  "messageId": "uuid|null",
  "metadata": {}
}
```

### PATCH `/chat/artifacts/{artifactId}`

Atualiza artefato.

Permissão: `minha-delpi.chat.ask`

```json
{
  "title": "Novo título",
  "content": "novo conteúdo",
  "metadata": {}
}
```

### DELETE `/chat/artifacts/{artifactId}`

Remove artefato.

Permissão: `minha-delpi.chat.ask`

Resposta: `204 No Content`
