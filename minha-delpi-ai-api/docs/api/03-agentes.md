# 03 — Agentes

Agentes são contextos especializados do Minha DELPI Chat. Actions externas/OpenAPI pertencem aos agentes, não ao chat comum.

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
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

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

### Resposta `200`

`ChatAgent[]`

> `system_prompt` não é retornado na listagem.

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
    "archived": false
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
    "role": "viewer",
    "created_at": "datetime|null"
  }
]
```

---

## DELETE `/chat/agents/{agentId}/shares/{targetUserId}`

Revoga compartilhamento (somente `owner`).

### Permissão

`minha-delpi.chat.tools.manage`

### Resposta

`204 No Content`

---

## POST `/chat/agents/{agentId}/preview`

Simula uma pergunta ao agente (instruções, RAG de especialização, diretrizes e tools planejadas).

### Permissão

`minha-delpi.chat.tools.manage` + papel `owner`, `editor` ou `system`

### Body

```json
{
  "message": "O que você consegue fazer?",
  "generateAnswer": true
}
```

### Resposta `200`

Mesmo formato de `POST /admin/agent/simulate` (`answerPreview`, `chunks`, `plannedToolCalls`, etc.).

---

## POST `/chat/agents/{agentId}/duplicate`

Cria cópia privada do agente para o usuário atual (instruções, metadados e limites). Não copia fontes nem compartilhamentos.

### Permissão

`minha-delpi.chat.tools.manage` + papel `owner`, `editor` ou `system`

### Body (opcional)

```json
{
  "copyActions": true
}
```

Quando `copyActions` é `true` (padrão), replica providers e actions configurados no agente de origem.

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
