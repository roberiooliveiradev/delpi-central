# Core API — Estatísticas de uso por usuário

> **Código:** `GetUserUsageStatisticsUseCase`, `SqlAlchemyEngagementRepository` (métodos `user_*`)  
> **Controllers:** `rbac_controller.py`, `me_controller.py`  
> **Status:** documentação oficial (ago/2026)

Analytics de **uso individual** (aberturas, tempo, apps e rotas) para um titular específico. Contrato **único** consumido pelo admin e pelo self-service do titular.

---

## Endpoints

| Método | Path | Auth | Descrição |
|--------|------|------|-----------|
| GET | `/admin/rbac/users/{user_id}/usage` | JWT + `rbac.manage` | Uso do usuário alvo (drill-down admin) |
| GET | `/me/usage` | JWT (titular) | Uso do usuário autenticado — **nunca** expõe dados de terceiros |

**Query:** `periodDays=7|30|90` (default `30`). Alias legado: `period_days`.

**Erros:**

| Código | Quando |
|--------|--------|
| `400` | `periodDays` inválido |
| `401` | Sem JWT |
| `404` | Usuário inexistente (rota admin) |
| `403` | Sem permissão (rota admin) |

---

## Contrato de resposta (`UserUsageStatistics`)

Campos em **camelCase** (JSON direto, sem envelope `data`).

```json
{
  "generatedAt": "2026-08-24T13:00:00Z",
  "periodDays": 30,
  "user": {
    "id": "uuid",
    "name": "Maria Silva",
    "email": "maria@example.com",
    "active": true,
    "lastLoginAt": "2026-08-20T12:00:00Z"
  },
  "consent": { "granted": true },
  "summary": {
    "totalOpens": 142,
    "appsUsed": 8,
    "totalDurationSeconds": 45240,
    "portalDurationSeconds": 15120,
    "appDurationSeconds": 30120,
    "avgSessionSeconds": 1080,
    "lastAppUsageAt": "2026-08-24T10:00:00Z"
  },
  "activity": {
    "opensSeries": [{ "date": "2026-08-24", "opens": 5 }],
    "durationSeries": [{ "date": "2026-08-24", "totalSeconds": 900 }]
  },
  "rankings": {
    "topAppsByOpens": [{ "id": "commercial", "name": "Comercial", "count": 42 }],
    "topAppsByDuration": [{ "id": "commercial", "name": "Comercial", "count": 18000 }],
    "topRoutes": [{ "id": "/apps/commercial", "name": "/apps/commercial", "count": 12 }]
  },
  "coverage": {
    "trackingEnabled": true,
    "sessionsRecorded": 4,
    "eventsInPeriod": 142
  }
}
```

### Sem consentimento `usage_tracking`

- `consent.granted` = `false`
- `summary`, `activity` e `rankings` retornam **zeros / listas vazias**
- Identidade do usuário (`user`) permanece visível ao admin
- Não é erro HTTP — permite banner informativo na UI

---

## Camada de aplicação

| Componente | Arquivo |
|------------|---------|
| Use case | `app/application/use_cases/admin/get_user_usage_statistics_use_case.py` |
| Consent gate | `app/domain/services/usage_tracking_consent_service.py` |
| Agregações | `app/infrastructure/persistence/sqlalchemy/engagement_repository.py` |

Métodos de repositório (filtro `user_id` + janela `since`):

| Método | Retorno |
|--------|---------|
| `user_usage_summary` | KPIs agregados |
| `user_opens_by_day` | Série `{ date, opens }` |
| `user_duration_by_day` | Série `{ date, totalSeconds }` |
| `user_apps_by_opens` | Ranking apps (excl. `backend-only`) |
| `user_apps_by_duration` | Ranking por segundos em sessões |
| `user_routes_by_opens` | Ranking `route_path` |
| `user_count_events_since` / `user_count_sessions_since` | Cobertura |

Engajamento **global** da plataforma continua em `GetEngagementStatisticsUseCase` → `GET /admin/statistics/engagement`.

---

## LGPD

| Evento | Comportamento |
|--------|---------------|
| Revogação `usage_tracking` | `purge_usage_tracking_data` apaga `app_usage_events` **e** `usage_sessions` |
| Leitura sem consentimento | Zeros — não reexpõe histórico anterior |
| Export titular | `usage_sessions` ainda **não** incluídas em `GET /me/data-export` (P1 futuro) |

Ver [rastreamento-uso-apps.md](./rastreamento-uso-apps.md) §5–§6.

---

## Testes

```bash
docker exec delpi-core-api pytest \
  app/tests/test_engagement_repository_user_methods.py \
  app/tests/test_get_user_usage_statistics_use_case.py \
  app/tests/test_user_usage_statistics_controller.py \
  app/tests/test_me_usage_controller.py \
  app/tests/test_usage_tracking_purge_service.py -q
```

---

## Portal (consumidor)

| Superfície | Cliente | Hook |
|------------|---------|------|
| Admin → Editar usuário → aba Uso | `adminApi.getAdminUserUsageStatistics` | `useAdminUserUsageStats` |
| `/profile` → Meu uso | `coreApi.getMyUsageStatistics` | `useMyUsageStats` |

UI compartilhada: `UserUsagePanel`. Ver [meu-uso-perfil-e-admin.md](../06-portal-frontend/meu-uso-perfil-e-admin.md).

---

## Documentos relacionados

- [controllers-e-rotas.md](./controllers-e-rotas.md) — §5 `/me`, §6 RBAC, §7 estatísticas
- [rastreamento-uso-apps.md](./rastreamento-uso-apps.md) — coleta de eventos e sessões
- [admin-estatisticas.md](../06-portal-frontend/admin-estatisticas.md) — engajamento global no Admin
