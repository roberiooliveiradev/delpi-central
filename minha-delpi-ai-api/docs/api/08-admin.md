# 08 — Admin API

Todos os endpoints abaixo exigem `minha-delpi.chat.admin`.

## External action providers globais

### GET `/admin/external-action-providers`

Lista providers externos globais.

### POST `/admin/external-action-providers`

Cria provider externo global.

Body típico:

```json
{
  "providerKey": "api-delpi",
  "name": "API DELPI",
  "type": "openapi",
  "baseUrl": "https://...",
  "openApiUrl": "https://.../openapi.json",
  "authMode": "user_token",
  "authConfig": {},
  "enabled": true
}
```

### POST `/admin/external-action-providers/{providerKey}/schema`

Importa schema OpenAPI enviado no body.

```json
{
  "schema": {
    "openapi": "3.0.0",
    "paths": {}
  }
}
```

### POST `/admin/external-action-providers/{providerKey}/reload-schema`

Recarrega schema usando `openApiUrl` salvo no provider.

### GET `/admin/external-actions`

Lista actions externas globais.

Query params:

| Parâmetro | Descrição |
|---|---|
| `provider` | Filtra por provider key. |

---

## Saúde operacional

### GET `/admin/system-check`

Executa checks administrativos do sistema.

### GET `/admin/metrics/summary`

Resumo de métricas administrativas.

### GET `/admin/llm/status`

Status do provider LLM configurado.

---

## Administração da base de conhecimento

### GET `/admin/knowledge/documents`

Lista documentos de knowledge.

Query params:

| Parâmetro | Default | Descrição |
|---|---:|---|
| `limit` | `20` | Quantidade máxima. |
| `offset` | `0` | Paginação. |
| `search` | — | Filtro textual. |
| `active` | — | Filtro por ativo/inativo. |

### POST `/admin/knowledge/documents/{documentId}/deactivate`

Desativa documento.

Rate limit: `admin_actions`.

### POST `/admin/knowledge/documents/{documentId}/reactivate`

Reativa documento.

Rate limit: `admin_actions`.

### POST `/admin/knowledge/documents/{documentId}/reindex`

Reindexa documento.

Rate limit: `admin_actions`.

---

## Auditoria

### GET `/admin/audit-logs`

Lista logs administrativos.

Query params:

| Parâmetro | Default |
|---|---:|
| `limit` | `100` |
