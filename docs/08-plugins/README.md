# Minha DELPI — Plugins do monorepo

> **Status:** documentação oficial  
> **Código:** `plugins/`  
> **Registro:** Core API `POST /core-api/admin/apps/register`

---

## 1. Como um plugin entra na plataforma

```text
Manifesto JSON (delpi.manifest.json)
  → POST /core-api/admin/apps/register
  → Core API cria app, permissões, rotas, versão
  → GET /core-api/me/apps (usuários autorizados)
  → Portal monta menu + AppHost
  → Gateway serve /apps/<id>/assets/*
```

Documentação do contrato: [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md).

---

## 2. Inventário no repositório

| Pasta | `id` (manifesto) | Tipo | `basePath` | Container Docker (dev) |
|---|---|---|---|---|
| `plugins/strategic-indicators` | `strategic-indicators` | microfrontend | `/apps/strategic-indicators` | `delpi-strategic-indicators` |
| `plugins/minha-delpi-chat` | `minha-delpi-chat` | microfrontend | `/apps/minha-delpi-chat` | `delpi-minha-delpi-chat` |
| `plugins/dashboard-lmps` | `dash-lmps` | iframe | `/dash-lmps` | `delpi-dashboard-lmps` |
| `plugins/dashboard-delpi` | (ver manifesto) | microfrontend | `/apps/dashboard-delpi` | `delpi-dashboard-delpi` |
| `plugins/helpdesk` | (ver manifesto) | — | — | Pode ser externo / legado |
| `plugins/idd_production` | (ver manifesto) | — | — | Avaliar registro na Core API |

**Atenção:** o `id` na URL de assets (`/apps/{id}/`) deve coincidir com o sufixo do container `delpi-{id}` no Nginx. Manifestos com `basePath` fora de `/apps/...` ainda precisam de rotas React no Portal compatíveis com o path registrado na Core API.

---

## 3. Backends consumidos pelos plugins

| Plugin | API principal |
|---|---|
| Indicadores Estratégicos | `/apps/strategic-indicators-api/strategic-indicators/*` |
| Dashboard LMPs | `/apps/api-delpi/engineering/lmps/*` |
| Minha DELPI Chat | `/apps/minha-delpi-ai/api/*` (não é Core API) |
| Dashboard DELPI | `/apps/api-delpi/products/*` (consultas produto) |

---

## 4. Build e assets

Cada plugin com UI gera build em `dist/` (Vite). O gateway expõe:

```text
GET /apps/<plugin-id>/assets/remoteEntry.js   # sem cache
GET /apps/<plugin-id>/assets/<chunk>.js       # cache longo
```

Module Federation: `renderMode: "federated"` + `entryUrl` apontando para `remoteEntry.js`.

---

## 5. Permissões típicas (exemplos)

Declaradas no manifesto e persistidas na Core API:

| Plugin | Permissões (exemplos) |
|---|---|
| strategic-indicators | `strategic-indicators.view`, `strategic-indicators.settings.manage`, … |
| dash-lmps | `dash-lmps.access` |
| minha-delpi-chat | `minha-delpi.chat.access`, `minha-delpi.chat.ask`, … |

Lista completa: seed + manifestos em `plugins/*/`.

---

## 6. Documentação por plugin

| Plugin | Doc específica |
|---|---|
| Chat / IA | [minha-delpi-ai-api/docs/api/](../../minha-delpi-ai-api/docs/api/README.md) |
| Indicadores | [api-delpi/docs/api/05-indicadores-estrategicos.md](../../api-delpi/docs/api/05-indicadores-estrategicos.md) |
| API operacional | [api-delpi/docs/api/](../../api-delpi/docs/api/README.md) |

---

## 7. Criar novo plugin

1. Copiar estrutura de `plugins/strategic-indicators` ou `minha-delpi-chat`.
2. Definir `delpi.manifest.json` (schema `1.0.0`).
3. Build → registrar na Core API.
4. Adicionar serviço `delpi-<id>` no `docker-compose.dev.yml`.
5. Validar `remoteEntry.js` via gateway.

Guia operacional: [../10-guias-operacionais/registrar-plugin.md](../10-guias-operacionais/registrar-plugin.md).
