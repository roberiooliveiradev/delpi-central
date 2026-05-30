# 03 — Agentes

Agentes são **chats com camadas extras**: prompt de sistema, skills, actions OpenAPI autorizadas e escopo de conhecimento. A **inteligência transversal** (intenção, pipeline, tools, comparações, resposta direta) vive no **chat base** e é **herdada** por todos os agentes — ver [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md).

Actions externas/OpenAPI são **configuradas por agente** (subset permitido); a execução e o pipeline seguem o mesmo motor do chat.

Roadmap de evolução da gestão (UI + API): [`../roadmap/agentes-gestao-melhorias.md`](../roadmap/agentes-gestao-melhorias.md) (ondas 1–7 concluídas).

## Comportamento no chat (runtime)

1. A **sessão** guarda `agent_key` (ou herda `default_agent_key` do projeto).
2. A cada mensagem, `ChatWorkspaceContextService` resolve o agente ativo (`get_enabled_by_key`).
3. O prompt do LLM recebe, nesta ordem: diretrizes admin → contexto do projeto → **`system_prompt` do agente** → RAG (escopo da especialização) → tools executadas.
4. **Skills** ativas em `metadata.skills` injetam policies de comportamento (ex.: Especialista SQL). Ver [`11-skills.md`](11-skills.md).
5. **Tools/actions** só rodam se estiverem habilitadas no agente (`allowedActionIds` / providers vinculados).
6. Limites do agente: `max_tool_calls`, `requires_confirmation_for_write`, `capabilities` em `metadata`.

Modelo conceitual completo: [`12-modelo-conceitual.md`](12-modelo-conceitual.md).

Metadados da resposta podem incluir `intelligence` (RAG, tools, timings) e `adminDebug.intelligence.timings` para admins. Ver ondas de inteligência em [`../roadmap/README.md`](../roadmap/README.md).

### `metadata.intelligence` (piloto sandbox)

| Campo | Tipo | Uso |
|-------|------|-----|
| `nativeToolCallingEnabled` | `boolean` | Opt-in por agente para `ChatNativeToolCallingService` (requer env + admin) |

Exemplo para agente piloto de tools internas via LLM:

```json
"metadata": {
  "intelligence": {
    "nativeToolCallingEnabled": true
  }
}
```

## Tipos

### `ChatAgent`

```json
{
  "id": "uuid",
  "key": "openapi-actions",
  "name": "Ações OpenAPI",
  "description": "string|null",
  "enabled": true,
  "metadata": {},
  "owner_user_id": "uuid|null",
  "visibility": "system|private|public",
  "category": "string|null",
  "icon": "string|null",
  "response_style": "string|null",
  "max_tool_calls": 3,
  "requires_confirmation_for_write": true,
  "access_role": "system|owner|editor|viewer",
  "published_version": 0,
  "published_at": "datetime|null",
  "has_unpublished_changes": false,
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Publicação (rascunho vs produção)

| Campo | Função |
|---|---|
| `published_version` | Número da versão publicada (`0` = nunca publicado) |
| `published_at` | Data/hora da última publicação |
| `has_unpublished_changes` | `true` quando o rascunho no builder difere do snapshot publicado |

**Runtime no chat:** usuários finais só conversam com agentes que tenham `published_version >= 1`. O backend aplica `published_config` (snapshot de instruções, metadados, skills e limites) na resolução por `agent_key`. Editores veem o rascunho no builder; visitantes usam apenas a versão publicada.

---

## Regras de permissão

| Cenário | Permissão |
|---|---|
| Listar agentes acessíveis | `minha-delpi.chat.access` |
| Criar agente próprio | `minha-delpi.chat.tools.manage` |
| Editar/excluir agente próprio | `minha-delpi.chat.tools.manage` + papel `owner/editor` conforme operação |
| Criar agente oficial/system | `minha-delpi.chat.admin` ou superadmin |
| Editar/excluir agente oficial/system | `minha-delpi.chat.admin` ou superadmin |
| Compartilhar agente | `minha-delpi.chat.tools.manage` |

Agente oficial é identificado por `visibility = "system"`, `owner_user_id = null` ou `access_role = "system"`.

---

## GET `/chat/agents`

Lista agentes acessíveis ao usuário.

### Permissão

`minha-delpi.chat.access`

### Query

| Parâmetro | Descrição |
|-----------|-----------|
| `includeDisabled=true` | Inclui agentes com `enabled=false` (gestores com `tools.manage`) |
| `includeStats=true` | Inclui `sessionsInWindow` e `totalSessions` (owner/editor/system) |
| `hours` | Janela em horas para `sessionsInWindow` (padrão 168) |

### Resposta `200`

`ChatAgent[]`

> `system_prompt` não é retornado na listagem. Com `includeStats=true`, cada item pode trazer `sessionsInWindow` e `totalSessions`.

---

## GET `/chat/agents/{agentId}`

Detalhe de um agente acessível ao usuário.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

`ChatAgent` com campos adicionais quando o usuário pode editar:

- `system_prompt` — preenchido para `access_role` `owner`, `editor` ou `system`
- omitido para `viewer`

### Erros

| Status | Situação |
|--------|----------|
| `404` | Agente inexistente ou sem acesso |

---

## POST `/chat/agents`

Cria agente.

### Permissão

`minha-delpi.chat.tools.manage`

Para `visibility = "system"`, o backend também exige `canManageOfficialAgents`, isto é, `minha-delpi.chat.admin` ou superadmin.

### Body

```json
{
  "key": "meu-agente",
  "name": "Meu Agente",
  "description": "Agente para consultas específicas",
  "visibility": "private",
  "icon": "bot",
  "metadata": {
    "color": "#2563eb"
  },
  "systemPrompt": "Você é um agente especializado...",
  "category": "geral",
  "responseStyle": "objetivo"
}
```

### Criar agente oficial

```json
{
  "name": "Agente Oficial DELPI",
  "visibility": "system",
  "systemPrompt": "..."
}
```

### Resposta `201`

`ChatAgent`

### Erros

| Status | Situação |
|--------|----------|
| `409` | `key` já existente para o escopo do agente |

---

## PATCH `/chat/agents/{agentId}`

Atualiza agente.

### Permissão

`minha-delpi.chat.tools.manage`; agentes oficiais exigem `minha-delpi.chat.admin` ou superadmin.

### Body

Todos os campos são opcionais:

```json
{
  "name": "Nome atualizado",
  "description": "Descrição",
  "visibility": "private",
  "icon": "bot",
  "metadata": {
    "color": "#111827",
    "archived": false,
    "intelligence": {
      "nativeToolCallingEnabled": false
    }
  },
  "systemPrompt": "Novo prompt",
  "category": "ações",
  "responseStyle": "detalhado",
  "enabled": true,
  "maxToolCalls": 5,
  "requiresConfirmationForWrite": true
}
```

### Resposta `200`

Inclui `system_prompt` quando o usuário tem papel `owner`, `editor` ou `system`.

`ChatAgent`

---

## DELETE `/chat/agents/{agentId}`

Remove agente.

### Permissão

`minha-delpi.chat.tools.manage`; agentes oficiais exigem `minha-delpi.chat.admin` ou superadmin.

### Resposta

`204 No Content`

---

## POST `/chat/agents/{agentId}/share`

Compartilha agente com outro usuário.

### Permissão

`minha-delpi.chat.tools.manage`

### Body

```json
{
  "targetUserId": "uuid",
  "role": "viewer"
}
```

`role` pode ser `viewer` ou `editor`.

### Resposta `200`

```json
{
  "ok": true
}
```

---

## GET `/chat/agents/{agentId}/shares`

Lista compartilhamentos do agente (somente `owner`).

### Permissão

`minha-delpi.chat.tools.manage`

### Resposta `200`

```json
[
  {
    "id": "uuid",
    "target_user_id": "uuid",
    "target_user_name": "Nome (quando disponível)",
    "target_user_email": "email@empresa.com",
    "role": "viewer",
    "created_at": "datetime|null"
  }
]
```

Reenviar `POST .../share` com o mesmo `targetUserId` atualiza o papel (`viewer` / `editor`).

---

## DELETE `/chat/agents/{agentId}/shares/{targetUserId}`

Revoga compartilhamento (somente `owner`).

### Permissão

`minha-delpi.chat.tools.manage`

### Resposta

`204 No Content`

---

## POST `/chat/agents/preview`

Simula um agente **ainda não salvo** (rascunho do builder).

### Permissão

`minha-delpi.chat.tools.manage`

### Body

```json
{
  "message": "O que você consegue fazer?",
  "generateAnswer": true,
  "draft": {
    "name": "Meu agente",
    "systemPrompt": "...",
    "metadata": { "skills": { "sql": { "authoring": true } } }
  }
}
```

### Resposta `200`

Mesmo formato de `POST /admin/agent/simulate`.

---

## POST `/chat/agents/{agentId}/preview`

Simula uma pergunta ao agente (instruções, RAG de especialização, diretrizes e tools planejadas).

### Permissão

`minha-delpi.chat.tools.manage` + papel `owner`, `editor` ou `system`

### Body

```json
{
  "message": "O que você consegue fazer?",
  "generateAnswer": true,
  "draft": {}
}
```

O campo opcional `draft` sobrescreve temporariamente instruções/metadados do agente salvo (útil para testar antes de publicar).

### Resposta `200`

Mesmo formato de `POST /admin/agent/simulate` (`answerPreview`, `chunks`, `plannedToolCalls`, etc.).

---

## POST `/chat/agents/{agentId}/publish`

Publica o rascunho atual do agente: incrementa `published_version`, grava `published_config` e registra entrada em `ai_chat_agent_versions`.

### Permissão

`minha-delpi.chat.tools.manage` + papel `owner`, `editor` ou `system`; agentes oficiais exigem `chat.admin` ou superadmin.

### Body

Nenhum (ou `{}`).

### Resposta `200`

`ChatAgent` com `published_version`, `published_at`, `has_unpublished_changes: false` e `system_prompt` quando editável.

### Erros

| Status | Situação |
|--------|----------|
| `404` | Agente inexistente ou sem permissão de edição |

---

## GET `/chat/agents/{agentId}/versions`

Lista histórico de publicações (últimas 30 versões).

### Permissão

`minha-delpi.chat.tools.manage` + acesso de edição ao agente

### Resposta `200`

```json
[
  {
    "id": "uuid",
    "version": 3,
    "event": "published",
    "createdAt": "2026-05-27T12:00:00+00:00",
    "createdBy": "uuid"
  }
]
```

---

## POST `/chat/agents/{agentId}/duplicate`

Cria cópia privada do agente para o usuário atual (instruções, metadados e limites). Não copia compartilhamentos.

### Permissão

`minha-delpi.chat.tools.manage` + papel `owner`, `editor` ou `system`

### Body (opcional)

```json
{
  "copyActions": true,
  "copySources": false
}
```

Quando `copyActions` é `true` (padrão), replica providers e actions configurados no agente de origem. Com `copySources: true`, reingere as fontes de conhecimento vinculadas ao agente de origem.

### Resposta `201`

`ChatAgent` (novo registro com `key` única e nome com sufixo `(cópia)`)

---

## GET `/chat/agents/{agentId}/stats`

Estatísticas de uso do agente (sessões e mensagens por `agent_key`, providers/actions vinculados).

### Permissão

`minha-delpi.chat.tools.manage` + papel `owner`, `editor` ou `system`

### Query

| Parâmetro | Descrição |
|-----------|-----------|
| `hours` | Janela em horas (padrão 168, máx. 2160) |

### Resposta `200`

```json
{
  "agentKey": "meu-agente",
  "windowHours": 168,
  "sessionsInWindow": 3,
  "messagesInWindow": 42,
  "totalSessions": 12,
  "actionProvidersCount": 2,
  "sharesCount": 1
}
```

`sharesCount` só é preenchido para o dono do agente.

---

## GET `/chat/agents/{agentId}/export`

Exporta configuração portável do agente (instruções, metadados, providers/actions vinculados). Não inclui segredos de API nem fontes de conhecimento.

### Permissão

`minha-delpi.chat.tools.manage` + papel `owner`, `editor` ou `system`

### Resposta `200`

```json
{
  "exportVersion": 1,
  "exportedAt": "2026-05-18T12:00:00+00:00",
  "suggestedKey": "meu-agente",
  "agent": { "name": "...", "systemPrompt": "...", "metadata": {} },
  "actionProviders": [],
  "actions": []
}
```

---

## POST `/chat/agents/import`

Cria agente a partir de um export (`exportVersion: 1`).

### Permissão

`minha-delpi.chat.tools.manage`

### Body

```json
{
  "export": { "exportVersion": 1, "agent": { "name": "Novo agente" }, "actionProviders": [], "actions": [] },
  "key": "opcional",
  "name": "opcional",
  "applyActions": true
}
```

### Resposta `201`

`ChatAgent` criado (visibilidade padrão `private`, salvo override por admin).

---

## POST `/chat/agents/{agentId}/transfer`

Transfere a propriedade do agente para outro usuário.

### Permissão

`minha-delpi.chat.tools.manage` + papel `owner`

### Body

```json
{
  "newOwnerUserId": "uuid-do-novo-dono"
}
```

### Resposta `204`

Sem corpo. Remove compartilhamento prévio do novo dono, se existir.

---

## GET `/chat/users/search`

Busca usuários do diretório corporativo para compartilhar agentes ou projetos.

### Permissão

`minha-delpi.chat.tools.manage`

### Query

| Parâmetro | Descrição |
|-----------|-----------|
| `q` | Termo de busca (mínimo 2 caracteres) |
| `limit` | Máximo de resultados (padrão 10, máx. 20) |

### Resposta `200`

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Nome",
      "email": "email@empresa.com"
    }
  ]
}
```
