# Core API — Rastreamento de uso de aplicações

> **Status:** documentação oficial (maio/2026)  
> **Código:** `core-api/app/interfaces/socket/`, `core-api/app/interfaces/http/app_usage_controller.py`, `core-api/app/application/use_cases/admin/record_*_app_usage_use_case.py`

---

## 1. Objetivo

Registrar **qual usuário** usou **qual app** (e, quando aplicável, **qual rota** ou **qual plugin originou** a chamada), para:

- painel Admin → Estatísticas → **Aplicações** (uso ao vivo + ranking 30 dias);
- métricas de adoção (`trackableActive` vs `backendOnlyActive`);
- auditoria agregada respeitando LGPD (consentimento `usage_tracking`).

**Fonte de verdade:** tabela `app_usage_events` (`postgres-core`).

---

## 2. Canais de coleta

| Canal | Origem | O que grava | Consentimento |
|-------|--------|-------------|---------------|
| **Socket.IO (portal)** | `app_usage.open` | App aberto no `AppHost` / link external | `usage_tracking` |
| **Socket.IO (portal)** | `app_usage.ping` / `close` | Store ao vivo (TTL) | `usage_tracking` |
| **Integração HTTP** | `POST /integrations/app-usage/record` | Chamadas à **api-delpi** (e futuros backends) | `usage_tracking` |
| **Presença** | `connect`, `presence.ping` | Online no portal (store separado) | `usage_tracking` |

Apps **`backend-only`** (ex.: `api-delpi`, `core-api`) **não** entram em métricas de adoção nem em apps fantasmas; podem ser registrados via integração com `appId` técnico.

---

## 3. Endpoint de integração (serviço)

Autenticação: **token de serviço** (`CORE_API_INTEGRATIONS_SERVICE_TOKEN`), não JWT de usuário.

```http
POST /core-api/integrations/app-usage/record
Authorization: Bearer <CORE_API_INTEGRATIONS_SERVICE_TOKEN>
X-Delpi-Caller-App: dashboard-commercial   # opcional — id do manifesto do plugin
Content-Type: application/json

{
  "appId": "api-delpi",
  "userId": "<uuid-do-usuario>",
  "routePath": "/commercial/proposals"
}
```

| Resposta | Significado |
|----------|-------------|
| `201 { "recorded": true }` | Evento persistido (consentimento ativo) |
| `200 { "recorded": false, "skipped": "usage_tracking_consent" }` | Titular sem consentimento — operação idempotente, não é erro |
| `401` | Token de serviço ausente ou inválido |

Implementação: `RecordIntegratedAppUsageUseCase`, `usage_tracking_consent_service.py`.

---

## 4. api-delpi — hook automático

Middleware pós-autenticação (`app_usage_tracking_middleware.py`):

1. Ignora paths públicos (`/health`, `/docs`, …) e requests com token de serviço interno.
2. Só registra respostas **2xx** de usuários autenticados.
3. Repassa header **`X-Delpi-Caller-App`** recebido do cliente.
4. Debounce **5 minutos** por `(userId, routePath)` antes de POST na Core API.

Variáveis no container `api-delpi`:

| Variável | Descrição |
|----------|-----------|
| `CORE_API_BASE_URL` | Ex.: `http://core-api:8000` |
| `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | Mesmo valor da Core API |
| `APP_USAGE_TRACKING_ENABLED` | `true` / `false` (default `true`) |
| `APP_USAGE_APP_ID` | Id registrado na Core API (default `api-delpi`) |

Plugins dashboards enviam o header em `httpClient.ts` — ver [08-plugins/README.md](../08-plugins/README.md).

---

## 5. LGPD

| Finalidade | Propósito no consentimento | Base legal |
|------------|---------------------------|------------|
| Uso de apps + presença + rotas api-delpi | `usage_tracking` | Art. 7º, I (consentimento) |
| Aniversários | `birthday_notifications` | Art. 7º, I |

Comportamentos (maio/2026):

- Socket **não** registra presença/uso ao vivo sem `usage_tracking`.
- **Revogação** de `usage_tracking` → purge de `app_usage_events` + stores ao vivo/presença (`usage_tracking_purge_service`).
- **Anonimização** do titular → inclui purge de eventos de uso.
- **Exportação** (`GET /me/export`) inclui campo `callerAppId` nos eventos.
- Política de privacidade do portal documenta `localStorage` `delpi.portal.recentApps.v1`.

Ver também [ropa-registro-tratamento.md](../13-auditoria-lgpd/ropa-registro-tratamento.md) §4.

---

## 6. Modelo de dados

Tabela `app_usage_events`:

| Coluna | Descrição |
|--------|-----------|
| `user_id` | UUID do titular |
| `app_id` | Id do app na Core API (`apps.id`) |
| `route_path` | Rota normalizada (portal ou api-delpi) |
| `caller_app_id` | Plugin originador (opcional), ex.: `dashboard-quality` |
| `opened_at` | Timestamp UTC |
| `source` | `portal` \| `integration` |

Migration: `m9n0o1p2q3_app_usage_caller_app.py`.

---

## 7. Admin — métricas

`GET /admin/apps/usage` e snapshot em `GET /admin/statistics`:

| Campo | Descrição |
|-------|-----------|
| `liveNow` | Sessões Socket.IO com app ativo |
| `topLast30Days` | Apps por usuários únicos |
| `ghostActive` | Cadastrados + `active`, sem uso na janela — **exclui `backend-only`** |
| `trackableActive` | Ativos rastreáveis (microfrontend, iframe, external) |
| `backendOnlyActive` | Serviços sem UI (informativo) |

UI: [admin-estatisticas.md](../06-portal-frontend/admin-estatisticas.md).

---

## 8. Variáveis de ambiente (Core API)

| Variável | Default | Descrição |
|----------|---------|-----------|
| `APP_USAGE_ENABLED` | `true` | Liga rastreamento |
| `APP_USAGE_TTL_SECONDS` | `90` | TTL store ao vivo |
| `APP_USAGE_HISTORY_DAYS` | `30` | Janela ranking / fantasmas |
| `APP_USAGE_STORE` | `memory` | Store ao vivo (`memory`; Redis futuro) |
| `USER_PRESENCE_ENABLED` | `true` | Presença online |
| `USER_PRESENCE_TTL_SECONDS` | `90` | TTL presença |
| `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | — | Token para integrações (api-delpi, jobs) |

Detalhes: [variaveis-de-ambiente.md](../02-infraestrutura/variaveis-de-ambiente.md).

---

## 9. Testes

```bash
# Core API
docker exec delpi-core-api pytest app/tests/test_app_usage_ghost_apps.py \
  app/tests/test_record_integrated_app_usage_use_case.py \
  app/tests/test_app_usage_controller_integration.py -q

# api-delpi (rotas Google Sheets + middleware)
docker exec delpi-api-delpi sh -c 'cd /app && PYTHONPATH=/app pytest \
  tests/test_google_sheets_routes_live.py \
  tests/test_app_usage_tracker.py \
  tests/test_app_usage_tracking_middleware.py -q'
```

Testar api-delpi **sem VPN TOTVS**: [12-testes-sem-totvs-google-sheets.md](../../api-delpi/docs/api/12-testes-sem-totvs-google-sheets.md).

---

## 10. Documentos relacionados

- [event-driven-e-socket.md](../01-arquitetura/event-driven-e-socket.md) §12.1 e §12.2
- [controllers-e-rotas.md](./controllers-e-rotas.md) §7
- [backend-only.md](../05-plugin-system/backend-only.md)
- [visao-geral-api-delpi.md](../07-api-delpi/visao-geral-api-delpi.md)
