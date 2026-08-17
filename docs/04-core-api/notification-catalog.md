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
    "commercial": {
      "label": "Portal Comercial",
      "notificationLabel": "Faturar notas fiscais",
      "icon": "briefcase",
      "mutable": true,
      "kind": "app",
      "sourceApps": ["commercial"],
      "pluginId": "commercial"
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
| `label` | Sim | Texto curto (filtros, histórico, badge) |
| `notificationLabel` | **Sim** | **Nome da notificação** no card de Preferências (título) |
| `icon` | Condicional | **`kind=platform`:** obrigatório (Minha Delpi). **`kind=app`:** último recurso; a API **substitui** por `apps.icon` do manifesto publicado (`NotificationCatalogIconService`) |
| `mutable` | Sim | `false` = usuário **não** pode silenciar (`system`) |
| `kind` | Sim | `platform` (transversal) ou `app` (emissor de plugin) |
| `sourceApps` | Se `kind=app` | IDs lógicos usados em `sourceApp` / `metadata.source` |
| `pluginId` | Se `kind=app` | ID do plugin no portal (`apps.id`) — nome do app na 2ª linha do card |

### Padrão visual das Preferências (obrigatório)

Todo card de preferência segue **somente** este layout (não reinventar no MFE):

```text
{notificationLabel}     ← o que o usuário silencia / marca importante / e-mail
{nome do app}           ← plugin via pluginId ou «Minha Delpi» (platform)
{Silenciada|Importante|E-mail|Recebendo}
[+ ícone] [estrela] [sino] [envelope]  ← auto-save
```

### Canais

| Canal | Quando |
|-------|--------|
| **In-app** (sino + histórico) | Sempre, se categoria não muted |
| **Painel importante + chime** | Categoria em `importantCategories` e unread |
| **Toast do SO** | Web Notification API; preferência local + permission; qualquer não muted (aba aberta) |
| **E-mail (Graph)** | `importantCategories` **sempre** (se não muted) **ou** opt-in `emailCategories` |

- **Estrela:** `importantCategories` — `isImportant=true`, painel + e-mail automático.
- **Sino:** `mutedCategories` — zera in-app, toast e e-mail; remove importante/e-mail da categoria.
- **Envelope:** `emailCategories` — e-mail opt-in (importante não precisa do envelope).
- Mute × importante × e-mail: reconciliados em `notification_preference_policy` (`reconcile_mute_important_and_email`).
- Tour «Conheça o portal»: quests `page-notifications-important`, `page-notifications-email`, `page-notifications-desktop-toast` **guiam** até Preferências — não duplicam a UI.

Ícone de plugin: **manifesto publicado** (`apps.icon`), nunca hardcode no catálogo como fonte de verdade.

Visibilidade: categorias `kind=app` só entram nas preferências se o usuário tiver o `pluginId` em `GET /me/apps` (mesma regra de autorização do launcher). Platform permanece sempre.

Implementação: `resolveNotificationPreferenceDisplay` + `NotificationCatalogIconService` + `filter_mutable_categories_for_user` + `NotificationPreferencesPanel` + `ImportantNotificationAttention`.  
Regra Cursor: `.cursor/rules/notification-catalog-preferences.mdc`.

### Severidade visual (`type`)

Campo `type` no dispatch / notificação (contrato **EN**; labels PT só na UI):

| Label PT | `type` | Cor | Aliases aceitos no ingest |
|----------|--------|-----|---------------------------|
| Aviso | `info` | azul | `aviso`, `informação` |
| Atenção | `warning` | amarelo | `atenção`, `atencao` |
| Alerta | `error` | vermelho | `alerta`, `erro` |
| Sucesso | `success` | verde | `sucesso` |

Persistido sempre o valor EN. O painel de atenção importante e os cards usam o tom via `resolveNotificationSeverityTone` / classes `--info|--warning|--error|--success`. **Importante** (`isImportant` / preferência) é independente da severidade.

### Aliases legados (categoria)

`legacyCategoryAliases` normaliza categorias antigas no dispatch (ex.: `quality` → `quality_action_plans`, `cadastro_kaizen` → `kaizometro`).

---

## 3. API HTTP

| Método | Path | Descrição |
|--------|------|-----------|
| GET | `/me/notifications/catalog` | Catálogo completo (autenticado) |
| GET | `/me/notifications/preferences` | Preferências (`mutedCategories`, `importantCategories`, `emailCategories`) + `categories` |
| PATCH | `/me/notifications/preferences` | Body: `mutedCategories` (obrigatório) + `importantCategories` / `emailCategories` (opcionais); resposta espelha GET |

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

1. **Plugin no portal** — `POST /admin/apps/register` com manifesto (RBAC, `basePath`, **`icon`**).
2. **Categoria no catálogo** — entrada em `notification_catalog.json`:
   - `notificationLabel` = frase do que se silencia (ex.: «Faturar notas fiscais») — **obrigatório**
   - `label` = nome curto do módulo / filtro
   - `kind: "app"` + `sourceApps` = valor de `sourceApp` no POST `/integrations/notifications`
   - `pluginId` = `apps.id` do manifesto (liga o ícone publicado)
   - `mutable: true` se o usuário pode silenciar
   - `icon` opcional em app (não é a fonte de verdade)
3. **Espelho no Portal** — atualizar `FALLBACK_NOTIFICATION_CATALOG` com o **mesmo** `notificationLabel` / `pluginId`.
4. **Backend emissor** — chamar Core API com `category` e `sourceApp` do catálogo.
5. **CI** — `python scripts/check_notification_catalog.py --check` (valida JSON + espelho do portal).
6. **Testes** — `app/tests/test_notification_catalog_service.py` + smoke do emissor.

**Não** alterar o layout de `NotificationPreferencesPanel` por feature — só o catálogo + ícone no manifesto.

---

## 5. Emissores registrados hoje

| Categoria | Label | sourceApp | Plugin |
|-----------|-------|-----------|--------|
| `api_console` | Console API DELPI | `api-delpi-console` | `api-delpi-console` |
| `quality_action_plans` | Planos de ação (PAC) | `quality-action-plans` | `quality-action-plans` |
| `auditoria_5s` | Auditoria 5S | `auditoria-5s` | `auditoria-5s` |
| `central_agendamento` | Central de Agendamento | `central-agendamento` | `central-agendamento` |
| `kaizometro` | Kaizômetro | `kaizometro` | `kaizometro` |
| `lancamento_notas_fiscais` | Lançamento de Notas Fiscais | `lancamento-notas-fiscais` | `lancamento-notas-fiscais` |
| `invoice_issuance` | Emissão de Notas Fiscais | `invoice-issuance` | `invoice-issuance` |
| `controle_mp` | Controle MP | `controle_mp` | `controle-mp` |
| `tv_dashboard` | Painéis TV | `tv-dashboard` | `tv-dashboard` |
| `commercial` | Portal Comercial | `commercial` | `commercial` |

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
| `.cursor/rules/notification-catalog-preferences.mdc` | Padrão obrigatório do card de Preferências |
