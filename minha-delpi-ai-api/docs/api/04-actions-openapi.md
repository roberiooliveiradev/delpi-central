# 04 — Actions OpenAPI por agente

**Status:** vigente  
**Arquitetura:** OpenAPI-first universal  
**Checklist:** [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md)  
**Evals:** [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)

Actions externas são operations importadas de providers OpenAPI e vinculadas explicitamente a agentes. O chat comum não executa essas actions sem agente/capability autorizada.

```text
Provider OpenAPI
→ import/index
→ Action Catalog
→ agent binding
→ allowed actions
→ retrieval/planner
→ OpenAPI validator
→ policy/confirmation
→ executor HTTP genérico
→ schema-driven presentation
```

## Regra de plugabilidade

Uma API externa nunca vista pelo repositório deve funcionar após importar/indexar e vincular ao agente **sem** cadastrar markers, intents, selectors, parameter strategies ou presenters por endpoint.

O contrato técnico da operation vem do OpenAPI/Action Catalog.

---

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
  "summary": "Consulta estoque de um produto",
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
  "enabled": true,
  "allowRead": true,
  "allowWrite": false,
  "allowAdmin": false,
  "requiresConfirmationForWrite": true,
  "actionCount": 96
}
```

---

## Autenticação do provider

| `authMode` | Comportamento |
|---|---|
| `none` | Sem header de autenticação adicional. |
| `user_token` | Propaga o token do usuário para API compatível com a identidade DELPI. |
| `api_key` | Usa segredo configurado no provider para montar o header. |

Segredos de provider não entram em prompt, resposta ou logs.

---

## Sensitivity

| Valor | Uso |
|------|-----|
| `read` | Leitura |
| `sql` | Consulta SQL autorizada |
| `export` | Exportação/arquivo |
| `write` | Escrita |
| `admin` | Operação administrativa |
| `destructive` | Operação destrutiva |

Sensitivity é combinada com agent binding, RBAC/policy e confirmation. O modelo não pode relaxar essas regras.

---

# Endpoints

## GET `/chat/action-providers`

Lista providers globais visíveis ao usuário autorizado.

**Permissão:** `minha-delpi.chat.access`

**Resposta:** `ChatActionProvider[]`

---

## GET `/chat/actions`

Lista actions importadas.

**Permissão:** `minha-delpi.chat.access`

Query opcional: `providerKey` ou `provider_key`.

**Resposta:** `ChatActionCatalogItem[]`

---

## POST `/chat/agents/{agentId}/providers/create`

Cria provider, importa schema e vincula ao agente.

**Permissão:** `minha-delpi.chat.tools.manage`; agentes oficiais/system exigem também autorização administrativa aplicável.

```json
{
  "providerKey": "api-delpi",
  "name": "API DELPI",
  "type": "openapi",
  "baseUrl": "https://minhadelpi.com.br/apps/api-delpi",
  "openApiUrl": "https://minhadelpi.com.br/apps/api-delpi/openapi.json",
  "authMode": "user_token",
  "authConfig": {},
  "enabled": true,
  "allowRead": true,
  "allowWrite": true,
  "allowAdmin": false,
  "requiresConfirmationForWrite": true
}
```

Também pode aceitar schema inline conforme o contrato do endpoint.

Resposta típica `201`:

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

**Permissão:** `minha-delpi.chat.access`

---

## PUT `/chat/agents/{agentId}/providers`

Cria/atualiza o binding entre agente e provider existente.

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

Configuração operacional deve ser feita por API/script administrativo, não por migration de schema com dados de ambiente.

---

## GET `/chat/agents/{agentId}/providers/{providerKey}`

Detalha provider vinculado ao agente, incluindo schema/configuração permitida.

---

## PATCH `/chat/agents/{agentId}/providers/{providerKey}`

Atualiza configuração do provider.

Campos típicos:

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

---

## POST `/chat/agents/{agentId}/providers/{providerKey}/import`

Importa/reimporta o OpenAPI configurado e atualiza o Action Catalog/index.

| Query | Resposta | Comportamento |
|-------|----------|---------------|
| padrão | `200` | import síncrono |
| `?async=true` | `202` | job assíncrono |

Resposta assíncrona típica:

```json
{
  "jobId": "uuid",
  "providerKey": "api-delpi",
  "status": "queued",
  "phase": "queued",
  "progress": {"done": 0, "total": 0, "unit": "actions"},
  "pollUrl": "/chat/providers/api-delpi/import/jobs/uuid"
}
```

Resposta síncrona típica:

```json
{
  "found": true,
  "actionsImported": 96,
  "schemaHash": "..."
}
```

O import deve produzir dados suficientes para retrieval/planning a partir de summary/description/tags/params/body/response schema.

---

## GET `/chat/providers/{providerKey}/import/jobs/{jobId}`

Consulta progresso do job de import.

---

## GET `/chat/providers/{providerKey}/import/jobs/latest`

Retorna o último job conhecido do provider ou `404` se não existir.

---

## GET `/chat/agents/{agentId}/actions`

Lista overrides/actions do agente.

---

## PUT `/chat/agents/{agentId}/actions`

Cria/atualiza configuração de uma action no agente.

```json
{
  "providerKey": "api-delpi",
  "actionId": "api_delpi.health.root_health_get",
  "sensitivity": "read",
  "requiresConfirmation": false,
  "enabled": true
}
```

---

## POST `/chat/agents/{agentId}/providers/{providerKey}/actions/{actionId}/test`

Executa teste administrativo direto da action autorizada.

```json
{
  "pathParams": {"code": "PRD001"},
  "query": {"limit": "10"},
  "body": {}
}
```

Resposta típica:

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

O endpoint de teste não autoriza bypass de RBAC/policy/sensitivity.

---

## GET `/chat/agents/{agentId}/providers/{providerKey}/actions/{actionId}/logs`

Lista logs de teste da action conforme permissões. Logs devem aplicar redaction de secrets/tokens e limites de payload.

---

# Seleção em linguagem natural

Após import + binding:

```text
mensagem
→ decomposição quando composta
→ allowed actions
→ retrieval top-K
→ planner
→ OpenAPI validation
→ policy/confirmation
→ execution
```

Regras:

- específica vs genérica é resolvida semanticamente;
- planner só escolhe candidates autorizadas;
- required ausente gera clarify;
- nenhuma URL arbitrária pode ser produzida/executada pelo LLM;
- providers equivalentes não recebem bias por nome/prefixo;
- follow-up usa contexto estruturado;
- resposta não depende de presenter por endpoint.

---

# Testes obrigatórios

Mudanças neste fluxo seguem R1–R11.

Quando o motor de actions for alterado, provar:

1. actions semanticamente próximas;
2. multi-provider;
3. no-tool;
4. args/required/type/enum;
5. API externa desconhecida;
6. teste metamórfico de path/operationId;
7. pedido composto;
8. multi-turn;
9. safety/policy;
10. outcome/task success;
11. performance/efficiency.

Referências vigentes:

- [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md)
- [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md)
- [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)
- `.cursor/rules/openapi-first-universal-tool-routing.mdc`
- `.cursor/rules/ai-intelligence-evaluation.mdc`
