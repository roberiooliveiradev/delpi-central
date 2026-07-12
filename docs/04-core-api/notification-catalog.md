# Catálogo de notificações — fontes e categorias

> **Arquivo:** `docs/04-core-api/notification-catalog.md`  
> **Status:** documentação oficial (jul/2026)  
> **JSON canônico:** `core-api/app/content/notification_catalog.json`

---

## 1. Objetivo

Centralizar em **um único registro** as **categorias** de notificação (silenciáveis ou não) e os **apps emissores** (`sourceApp`) que disparam alertas para o sino da Minha DELPI.

Antes deste catálogo, categorias e rótulos ficavam espalhados em Python (`notification_constants.py`) e em vários componentes do Portal. Agora:

| Camada | Fonte |
|--------|--------|
| **Core API** | `notification_catalog.json` → `NotificationCatalogService` |
| **Portal** | `GET /me/notifications/catalog` (+ fallback local espelhado) |
| **Integrações** | `category` + `sourceApp` devem existir no catálogo |

---

## 2. Estrutura do JSON

```json
{
  "version": 1,
  "categories": {
    "api_console": {
      "label": "Console API DELPI",
      "icon": "activity",
      "mutable": true,
      "kind": "app",
      "sourceApps": ["api-delpi-console"],
      "pluginId": "api-delpi-console"
    }
  },
  "legacyCategoryAliases": {
    "quality": "quality_action_plans"
  }
}
```

### Campos por categoria

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `label` | Sim | Texto exibido nas preferências, cards e filtros |
| `icon` | Sim | Nome do ícone (portal mapeia para Lucide) |
| `mutable` | Sim | `false` = usuário **não** pode silenciar (`system`) |
| `kind` | Sim | `platform` (transversal) ou `app` (emissor de plugin) |
| `sourceApps` | Se `kind=app` | IDs lógicos usados em `sourceApp` / `metadata.source` |
| `pluginId` | Recomendado p/ app | ID do plugin no portal (`apps.id`) — usado no filtro RBAC |

### Aliases legados

`legacyCategoryAliases` normaliza categorias antigas no dispatch (ex.: `quality` → `quality_action_plans`).

---

## 3. API HTTP

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/me/notifications/catalog` | Catálogo completo (autenticado) |
| GET | `/me/notifications/preferences` | Preferências + campo `categories` |
| PATCH | `/me/notifications/preferences` | Resposta também inclui `categories` |

Exemplo `GET /me/notifications/catalog`:

```json
{
  "version": 1,
  "categories": [
    {
      "id": "api_console",
      "label": "Console API DELPI",
      "icon": "activity",
      "mutable": true,
      "kind": "app",
      "sourceApps": ["api-delpi-console"],
      "pluginId": "api-delpi-console"
    }
  ],
  "legacyCategoryAliases": {
    "quality": "quality_action_plans"
  }
}
```

---

## 4. Checklist — novo app que envia notificação

1. **Plugin no portal** — `POST /admin/apps/register` com manifesto (RBAC, `basePath`).
2. **Categoria no catálogo** — entrada `kind: "app"` em `notification_catalog.json`:
   - `sourceApps` = valor de `sourceApp` no POST `/integrations/notifications`
   - `pluginId` = `apps.id` do manifesto
   - `mutable: true` se o usuário pode silenciar
3. **Espelho no Portal** — atualizar `portal/src/utils/notificationCatalog.ts` → `FALLBACK_NOTIFICATION_CATALOG` (offline).
4. **Backend emissor** — chamar Core API com `category` e `sourceApp` do catálogo.
5. **CI** — `python scripts/check_notification_catalog.py --check`
6. **Testes** — `app/tests/test_notification_catalog_service.py` + smoke do emissor.

Não é necessário editar `NotificationPreferencesPanel`, `NotificationCard` etc. — consomem o catálogo via API.

---

## 5. Emissores registrados hoje

| Categoria | Label | sourceApp | Plugin |
|-----------|-------|-----------|--------|
| `api_console` | Console API DELPI | `api-delpi-console` | `api-delpi-console` |
| `quality_action_plans` | Planos de ação (PAC) | `quality-action-plans` | `quality-action-plans` |
| `auditoria_5s` | Auditoria 5S | `auditoria-5s` | `auditoria-5s` |
| `controle_mp` | Controle MP | `controle_mp` | `controle-mp` |

Categorias `platform` (boas-vindas, aniversário, comunicado, …) não têm `sourceApp` — são disparadas pela Core API ou Admin.

---

## 6. RBAC e deep link

`notification_app_access_service.py` usa `pluginId` / `sourceApps` do catálogo para mapear `sourceApp` → app do portal antes de entregar a notificação.

Regra inalterada: só recebe no sino quem tem permissão para abrir o app (`GET /me/apps`).

---

## 7. Gate CI

```bash
cd core-api
python scripts/check_notification_catalog.py --check
pytest app/tests/test_notification_catalog_service.py -q
```

---

## 8. Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [notificacoes.md](./notificacoes.md) | API de notificações, preferências, integrações |
| [conectar-aplicacao-iframe.md](../10-guias-operacionais/conectar-aplicacao-iframe.md) | Envio via `/integrations/notifications` |
| [notificacoes-ricas.md](../12-roadmap-e-evolucao/notificacoes-ricas.md) | Roadmap de campanhas e templates |
