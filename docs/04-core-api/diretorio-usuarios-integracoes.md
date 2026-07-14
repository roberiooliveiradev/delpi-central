# Core API — diretório de usuários (integrações S2S)

> **Código:** `core-api/app/interfaces/http/integrations_directory_controller.py`  
> **Base URL (gateway):** `/core-api`

Permite que backends (api-delpi, api-pac-quality) busquem usuários Delpi **ativos** com acesso a um app, sem JWT de usuário final.

---

## Autenticação S2S

```http
Authorization: Bearer <CORE_API_INTEGRATIONS_SERVICE_TOKEN>
```

Alternativa aceita em todas as rotas `@require_service_token`:

```http
X-Delpi-Service-Token: <mesmo valor>
```

| Erro | Causa |
|------|-------|
| 401 | Token ausente |
| 403 | Token inválido ou `CORE_API_INTEGRATIONS_SERVICE_TOKEN` não configurado na Core API |

Rate limit: padrão **60 req / 60 s** por IP+path (`integration_rate_limit` — mesmas variáveis das notificações).

---

## GET `/integrations/directory/users`

| Query | Descrição |
|-------|-----------|
| `q` ou `query` | Texto de busca (mín. 2 caracteres; menor → `items: []`) |
| `limit` | 1–20 (default `10`) |
| `app` | App id para elegibilidade (default `quality-action-plans`) |
| `permission` | Código RBAC opcional (ex.: `quality-action-plans.read`) |

**Resposta 200:**

```json
{
  "items": [
    { "id": "uuid", "name": "Maria Silva", "email": "m***@empresa.com.br" }
  ]
}
```

**Regras:**

- Apenas usuários **ativos** no Core DB.
- Elegibilidade = mesma regra de `GET /me/apps` (`DirectoryUserEligibilityService`).
- E-mail sempre **mascarado** (LGPD).
- **Não** exclui caller (não há JWT de usuário nesta rota).

---

## Rotas JWT (usuário autenticado)

Arquivo: `me_controller.py`.

| Método | Path | Diferença vs S2S |
|--------|------|------------------|
| GET | `/me/directory/users` | Exclui o usuário autenticado por padrão; `include_self=true` mantém o caller nos resultados (atribuição de responsável); `app` opcional (sem default) |
| POST | `/me/directory/users/lookup` | Body `{ "ids": ["uuid", ...] }` — resolve nomes para shares/listas |

Proxy chat: `minha-delpi-ai-api` → `GET /chat/users/search`.

---

## Consumidores PAC

| Serviço | Rota pública | `operationId` | Upstream |
|---------|--------------|---------------|----------|
| **api-delpi** | `GET /quality/action-plans/assignable-users` | `list_quality_action_plan_assignable_users` | Esta rota S2S |
| **api-pac-quality** | `GET /quality/action-plans/assignable-users` | `pac_search_assignable_users` | Esta rota S2S (via `CoreApiDirectoryGateway`) |

Contrato api-delpi: `meta.entity` = `directory_user`, `meta.shape` = `paged_list`.

---

## Variáveis de ambiente

| Variável | Onde configurar |
|----------|-----------------|
| `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | Core API (validação) + api-delpi + api-pac-quality (cliente) |
| `CORE_API_BASE_URL` ou `CORE_API_URL` | api-delpi, api-pac-quality — URL interna (ex.: `http://delpi-core-api:8000`) |

Sem Core API configurada na api-pac-quality: `GET /assignable-users` retorna **503** `CORE_API_UNAVAILABLE`; `/health` reporta `core_api_directory: not_configured`.

---

## Documentos relacionados

- [controllers-e-rotas.md](./controllers-e-rotas.md)
- [../../api-delpi/docs/api/quality-action-plans-pac.md](../../api-delpi/docs/api/quality-action-plans-pac.md)
- [../../../api-pac-quality/docs/contrato-http-api-pac-api-delpi.md](../../../api-pac-quality/docs/contrato-http-api-pac-api-delpi.md) (repositório `api-pac-quality`, irmão de `delpi-central`)
