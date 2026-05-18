# API HTTP — Strategic Indicators

**Base URL (gateway):**

```text
/apps/strategic-indicators-api/strategic-indicators
```

**Autenticação:** `Authorization: Bearer <JWT>` (Keycloak, `delpi_auth`).  
**Formato:** JSON direto nas rotas de leitura (sem envelope `success`/`data`), exceto onde indicado.

Documentação interativa: `/apps/strategic-indicators-api/docs`

---

## Filtros globais (leitura)

| Query | Descrição |
|-------|-----------|
| `department_id` | Filtrar por departamento |
| `branch` | Filial (visão por unidade) |
| `competence` | Competência `YYYY-MM` (ex.: `2026-05`) |
| `start_date`, `end_date` | Intervalo alternativo |

---

## Leitura e dashboards

### GET `/executive-summary`

**Permissão:** `strategic-indicators.view`

Resumo executivo (IGD, departamentos, comparativo atual vs mês anterior).

---

### GET `/departments`

**Permissão:** `strategic-indicators.view`

Lista departamentos com scores agregados.

---

### GET `/departments/{department_id}`

**Permissão:** `strategic-indicators.view`

Detalhe de um departamento. `404` se não existir.

---

### GET `/indicators`

**Permissão:** `strategic-indicators.view`

Indicadores calculados do período.

```json
{
  "items": [ { "indicator_id": "...", "score": 85.0, "value": 95.2, "...": "..." } ],
  "errors": [],
  "partial_success": false
}
```

---

### GET `/alerts`

**Permissão:** `strategic-indicators.view`

Alertas derivados de metas e desempenho (usa snapshot comparativo).

---

### GET `/trends`

**Permissão:** `strategic-indicators.trends.view`

| Query | Default | Descrição |
|-------|---------|-----------|
| `months` | `6` | Histórico em meses (`2`–`12`) |

Série temporal. Usa `get_series_snapshot_optimized` e, quando habilitado, cache `period_scores` no Postgres.

---

### GET `/presentation`

**Permissão:** `strategic-indicators.view`

Payload agregado para tela de apresentação.

| Query | Default | Descrição |
|-------|---------|-----------|
| `months` | `6` | Meses para tendências embutidas |
| `include` | (todas) | Seções separadas por vírgula |

Valores de `include`:

- `executive_summary`
- `departments_overview`
- `department_details_by_id`
- `indicators_by_department_id`
- `alerts`
- `trends`

O MFE costuma chamar primeiro com subset (overview) e depois trends em request separada.

---

## Configurações e governança

**Permissão:** `strategic-indicators.settings.manage`

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/settings` | Pesos, parâmetros, governança |
| PUT | `/settings` | Atualiza parâmetros/governança |
| GET | `/settings/audit` | Auditoria (`limit`, `entity_key`) |

---

## Change requests

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/change-requests` | Lista (`limit`, `offset`, `total`) |
| POST | `/change-requests` | Cria solicitação |
| POST | `/change-requests/{id}/comments` | Comentário |
| POST | `/change-requests/{id}/submit` | Submete |

---

## Admin — departamentos e indicadores

| Método | Rota |
|--------|------|
| GET/POST | `/admin/departments` |
| PUT | `/admin/departments/{department_id}` |
| POST | `/admin/departments/{department_id}/activate` \| `/deactivate` |
| DELETE | `/admin/departments/{department_id}` |
| GET/POST | `/admin/departments/{department_id}/indicators` |
| PUT | `/admin/indicators/{indicator_id}` |
| POST | `/admin/indicators/{indicator_id}/activate` \| `/deactivate` |
| DELETE | `/admin/indicators/{indicator_id}` |

---

## Metas analíticas (`indicator-goals`)

| Método | Rota | Notas |
|--------|------|-------|
| GET | `/indicator-goals` | Filtros: `indicator_id`, `goal_year`, `department_id`, `active_only` |
| GET | `/indicator-goals/history` | `indicator_id` obrigatório |
| POST | `/indicator-goals` | Cria meta |
| PUT | `/indicator-goals/{goal_id}` | Atualiza |
| POST | `/indicator-goals/{goal_id}/activate` | Ativa versão |
| DELETE | `/indicator-goals/{goal_id}` | Desativa (soft) |
| GET | `/admin/goal-years/overview` | Visão por ano |
| POST | `/admin/indicator-goals/bulk-create` | Lote |
| POST | `/admin/indicator-goals/duplicate-year` | Duplica entre anos |
| POST | `/admin/indicator-goals/fill-missing` | Preenche faltantes |

Campos principais: `goal_year`, `goal_value`, `goal_periodicity`, `goal_mode`, `monthly_targets`, `version`, `is_active`.

---

## Health

| Rota | Descrição |
|------|-----------|
| `GET /health` (raiz da API) | Status do serviço (`{"status":"online"}`) |
| `GET /strategic-indicators/health` | Health do módulo (se exposto no router) |

---

## Permissões (resumo)

| Permissão | Uso |
|-----------|-----|
| `strategic-indicators.view` | Painel, departments, indicators, presentation |
| `strategic-indicators.trends.view` | Trends |
| `strategic-indicators.settings.manage` | Settings, admin, metas, change requests |

Declaradas no manifesto do plugin e na Core API.
