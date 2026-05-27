# 04 — Actions OpenAPI por agente

Actions externas são providers OpenAPI globais vinculados a agentes. O chat comum não deve executar actions externas. O fluxo correto é:

**Provider api-delpi:** após deploy da API, reimporte o OpenAPI e mantenha o documento RAG [`../knowledge/api-delpi-rotas-agente.md`](../knowledge/api-delpi-rotas-agente.md) indexado. O pipeline seleciona rotas por `path`, `summary` e scoring de intent (Onda 10); `operationId` estável quando definido em `api-delpi/app/interface/http/openapi_agent_metadata.py`.

```text
Agente -> Provider/API -> Rotas/actions importadas do OpenAPI -> Permissões por agente
```

## Tipos principais

### `ChatActionProvider`

```json
{
  "id": "uuid",
  "providerKey": "api-delpi",
  "name": "API DELPI",
  "type": "openapi",
  "baseUrl": "https://...",
  "openApiUrl": "https://.../openapi.json",
  "privacyPolicyUrl": "https://...",
  "authMode": "none|user_token|api_key",
  "authConfig": {},
  "latestSchema": {},
  "latestSchemaHash": "string|null",
  "latestSchemaImportedAt": "datetime|null",
  "enabled": true,
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

### `ChatActionCatalogItem`

```json
{
  "id": "uuid",
  "actionId": "api_delpi.products.get_product_stock",
  "operationId": "get_product_stock",
  "method": "GET",
  "path": "/products/{code}/stock",
  "summary": "Consulta produto por código",
  "description": "...",
  "tags": ["products"],
  "parametersSchema": [],
  "requestBodySchema": null,
  "responseSchema": {},
  "sensitivity": "read|sql|export|write|admin|destructive",
  "enabled": true,
  "deprecated": false
}
```

### `ChatAgentActionProvider`

```json
{
  "id": "uuid",
  "agentId": "uuid",
  "providerKey": "api-delpi",
  "providerName": "API DELPI",
  "providerType": "openapi",
  "baseUrl": "https://...",
  "openApiUrl": "https://.../openapi.json",
  "privacyPolicyUrl": "https://...",
  "enabled": true,
  "allowRead": true,
  "allowWrite": false,
  "allowAdmin": false,
  "requiresConfirmationForWrite": true,
  "actionCount": 96,
  "createdAt": "datetime",
  "updatedAt": "datetime"
}
```

## Auth modes

| `authMode` | Comportamento |
|---|---|
| `none` | Não adiciona autenticação à chamada externa. |
| `user_token` | Repassa o `Authorization` do usuário para a API externa. Use para APIs internas que validam permissões do usuário, como API DELPI. |
| `api_key` | Usa `authConfig` para montar header de autenticação. |

Exemplo `api_key`:

```json
{
  "authMode": "api_key",
  "authConfig": {
    "headerName": "Authorization",
    "scheme": "bearer",
    "apiKey": "token-ou-chave"
  }
}
```

## Sensitivity

| Sensitivity | Uso |
|---|---|
| `read` | Rotas de leitura. |
| `sql` | Rotas que executam SQL somente leitura. |
| `export` | Exportações/arquivos. |
| `write` | Escrita. |
| `admin` | Operações administrativas. |
| `destructive` | Operações destrutivas. |

---

## GET `/chat/action-providers`

Lista providers globais disponíveis.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatActionProvider[]`

---

## GET `/chat/actions`

Lista actions/rotas importadas.

### Permissão

`minha-delpi.chat.access`

### Query params

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `providerKey` | `string` | Filtra rotas de um provider. Também aceita `provider_key`. |

### Resposta `200`

`ChatActionCatalogItem[]`

---

## POST `/chat/agents/{agentId}/providers/create`

Cria provider, importa schema e vincula ao agente em um único fluxo.

### Permissão

`minha-delpi.chat.tools.manage`; se o agente é oficial/system, exige `minha-delpi.chat.admin` ou superadmin.

### Body

```json
{
  "providerKey": "api-delpi",
  "name": "API DELPI",
  "type": "openapi",
  "baseUrl": "https://minhadelpi.com.br/apps/api-delpi",
  "openApiUrl": "https://minhadelpi.com.br/apps/api-delpi/openapi.json",
  "privacyPolicyUrl": "https://...",
  "authMode": "user_token",
  "authConfig": {},
  "enabled": true,
  "allowRead": true,
  "allowWrite": true,
  "allowAdmin": false,
  "requiresConfirmationForWrite": true
}
```

Também aceita `schema`, `schemaJson` ou `schema_json` para importação inline.

### Resposta `201`

```json
{
  "provider": {},
  "import": {
    "found": true,
    "actionsImported": 96,
    "schemaHash": "..."
  },
  "linked": true
}
```

---

## GET `/chat/agents/{agentId}/providers`

Lista providers vinculados ao agente.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatAgentActionProvider[]`

---

## PUT `/chat/agents/{agentId}/providers`

Cria ou atualiza vínculo entre agente e provider existente.

### Permissão

`minha-delpi.chat.tools.manage`; agente oficial/system exige `chat.admin` ou superadmin.

### Body

```json
{
  "providerKey": "api-delpi",
  "enabled": true,
  "allowRead": true,
  "allowWrite": false,
  "allowAdmin": false,
  "requiresConfirmationForWrite": true
}
```

### Resposta `200`

```json
{
  "saved": true
}
```

---

## GET `/chat/agents/{agentId}/providers/{providerKey}`

Detalha provider vinculado ao agente, incluindo schema salvo.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatActionProvider`

---

## PATCH `/chat/agents/{agentId}/providers/{providerKey}`

Atualiza configurações do provider/API.

### Permissão

`minha-delpi.chat.tools.manage`; agente oficial/system exige `chat.admin` ou superadmin.

### Body

```json
{
  "name": "API DELPI",
  "baseUrl": "https://...",
  "openApiUrl": "https://.../openapi.json",
  "privacyPolicyUrl": "https://...",
  "authMode": "user_token",
  "authConfig": {},
  "enabled": true
}
```

### Resposta `200`

`ChatActionProvider`

---

## POST `/chat/agents/{agentId}/providers/{providerKey}/import`

Atualiza/importa rotas a partir da URL OpenAPI configurada.

### Permissão

`minha-delpi.chat.tools.manage`; agente oficial/system exige `chat.admin` ou superadmin.

### Resposta `200`

```json
{
  "found": true,
  "actionsImported": 96,
  "schemaHash": "..."
}
```

---

## GET `/chat/agents/{agentId}/actions`

Lista overrides de actions configurados para o agente.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

```json
[
  {
    "id": "uuid",
    "agentId": "uuid",
    "providerKey": "api-delpi",
    "actionId": "api_delpi.health.root_health_get",
    "enabled": true,
    "sensitivity": "read",
    "requiresConfirmation": false,
    "createdAt": "datetime",
    "updatedAt": "datetime"
  }
]
```

---

## PUT `/chat/agents/{agentId}/actions`

Cria ou atualiza override de action no agente.

### Permissão

`minha-delpi.chat.tools.manage`; agente oficial/system exige `chat.admin` ou superadmin.

### Body

```json
{
  "providerKey": "api-delpi",
  "actionId": "api_delpi.health.root_health_get",
  "sensitivity": "read",
  "requiresConfirmation": false,
  "enabled": true
}
```

### Resposta `200`

```json
{
  "ok": true
}
```

---

## POST `/chat/agents/{agentId}/providers/{providerKey}/actions/{actionId}/test`

Executa teste direto de uma rota/action.

### Permissão

`minha-delpi.chat.access`

### Body

```json
{
  "pathParams": {
    "code": "PRD001"
  },
  "query": {
    "limit": "10"
  },
  "body": {
    "sql": "select * from tabela limit 10"
  }
}
```

### Resposta `200`

```json
{
  "ok": true,
  "statusCode": 200,
  "durationMs": 22,
  "url": "https://...",
  "responsePreview": "{...}",
  "errorMessage": null
}
```

---

## GET `/chat/agents/{agentId}/providers/{providerKey}/actions/{actionId}/logs`

Lista logs de teste de uma rota/action.

### Permissão

`minha-delpi.chat.access`

### Query params

| Parâmetro | Tipo | Default |
|---|---|---|
| `limit` | `number` | `20` |

### Resposta `200`

```json
[
  {
    "id": "uuid",
    "providerKey": "api-delpi",
    "actionId": "api_delpi.health.root_health_get",
    "method": "GET",
    "url": "https://...",
    "requestPayload": {},
    "statusCode": 200,
    "ok": true,
    "durationMs": 22,
    "responsePreview": "{...}",
    "errorMessage": null,
    "createdAt": "datetime"
  }
]
```
