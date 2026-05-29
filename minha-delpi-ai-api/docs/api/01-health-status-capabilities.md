# 01 — Health, status e capabilities

## GET `/health`

Health check público.

### Resposta `200`

```json
{
  "status": "ok"
}
```

O formato exato depende de `HealthCheckUseCase`.

---

## GET `/chat/status`

Retorna status funcional do módulo de chat para o usuário autenticado.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

Objeto retornado por `GetChatStatusUseCase`.

---

## GET `/chat/capabilities`

Retorna permissões e capacidades resolvidas pelo backend, incluindo bypass de superadmin e permissões vindas do core-api `/me`.

### Permissão

`minha-delpi.chat.access`

### Resposta `200`

```json
{
  "permissions": [
    "minha-delpi.chat.access",
    "minha-delpi.chat.tools.manage"
  ],
  "isSuperadmin": false,
  "canManageAgents": true,
  "canManageOwnAgents": true,
  "canManageOfficialAgents": false,
  "canManageTools": true,
  "canUseTools": true,
  "knowledgeDocumentMaxChars": 2000000
}
```

### Regras

- `canManageOwnAgents = true` quando usuário é superadmin, tem `minha-delpi.chat.tools.manage` ou `minha-delpi.chat.admin`.
- `canManageOfficialAgents = true` quando usuário é superadmin ou tem `minha-delpi.chat.admin`.
- `canUseTools = true` quando pode gerenciar tools ou tem `minha-delpi.chat.tools.use`.

### Uso pelo frontend

Use este endpoint para controlar botões de:

- Gerenciar agentes.
- Criar agente.
- Criar agente oficial.
- Configurar actions.
- Excluir agente oficial/system.
