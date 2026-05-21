# API HTTP — Strategic Indicators

**Última atualização:** 2026-05-21

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

Campos relevantes quando **não há medição** no período:

| Campo | Com medição | Sem medição |
|-------|-------------|-------------|
| `value` | número | `null` |
| `score` | número | `null` |
| `gap` | número | `null` |
| `has_value` | `true` | `false` |
| `classification` | faixa de desempenho | `Sem dados preenchidos` |

```json
{
  "items": [
    {
      "indicator_id": "financial-fixed-cost",
      "value": null,
      "score": null,
      "gap": null,
      "has_value": false,
      "classification": "Sem dados preenchidos"
    },
    {
      "indicator_id": "financial-ebitda",
      "value": 13.5,
      "score": 8.2,
      "gap": -1.3,
      "has_value": true,
      "classification": "Alto Desempenho"
    }
  ],
  "errors": [],
  "partial_success": false
}
```

`GET /departments/{id}` e `GET /presentation` usam o mesmo contrato em `indicators` / `realized` (valores `null` por filial quando não houver dado na unidade).

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

---

## Tabela rápida de endpoints

Prefixo: `/apps/strategic-indicators-api/strategic-indicators`

| Método | Endpoint | Permissão |
|--------|----------|-----------|
| GET | `/health` | — |
| GET | `/executive-summary` | `strategic-indicators.view` |
| GET | `/departments` | `strategic-indicators.view` |
| GET | `/departments/{department_id}` | `strategic-indicators.view` |
| GET | `/indicators` | `strategic-indicators.view` |
| GET | `/alerts` | `strategic-indicators.view` |
| GET | `/trends` | `strategic-indicators.trends.view` |
| GET | `/presentation` | `strategic-indicators.view` |
| GET | `/settings` | `strategic-indicators.settings.manage` |
| PUT | `/settings` | `strategic-indicators.settings.manage` |
| GET | `/settings/audit` | `strategic-indicators.settings.manage` |
| GET | `/change-requests` | `strategic-indicators.settings.manage` |
| POST | `/change-requests` | `strategic-indicators.settings.manage` |
| POST | `/change-requests/{id}/comments` | `strategic-indicators.settings.manage` |
| POST | `/change-requests/{id}/submit` | `strategic-indicators.settings.manage` |
| GET | `/admin/departments` | `strategic-indicators.settings.manage` |
| POST | `/admin/departments` | `strategic-indicators.settings.manage` |
| PUT | `/admin/departments/{id}` | `strategic-indicators.settings.manage` |
| POST | `/admin/departments/{id}/activate` | `strategic-indicators.settings.manage` |
| POST | `/admin/departments/{id}/deactivate` | `strategic-indicators.settings.manage` |
| DELETE | `/admin/departments/{id}` | `strategic-indicators.settings.manage` |
| GET | `/admin/departments/{id}/indicators` | `strategic-indicators.settings.manage` |
| POST | `/admin/departments/{id}/indicators` | `strategic-indicators.settings.manage` |
| PUT | `/admin/indicators/{id}` | `strategic-indicators.settings.manage` |
| POST | `/admin/indicators/{id}/activate` | `strategic-indicators.settings.manage` |
| POST | `/admin/indicators/{id}/deactivate` | `strategic-indicators.settings.manage` |
| DELETE | `/admin/indicators/{id}` | `strategic-indicators.settings.manage` |
| GET | `/indicator-goals` | `strategic-indicators.settings.manage` |
| GET | `/indicator-goals/history` | `strategic-indicators.settings.manage` |
| POST | `/indicator-goals` | `strategic-indicators.settings.manage` |
| PUT | `/indicator-goals/{goal_id}` | `strategic-indicators.settings.manage` |
| POST | `/indicator-goals/{goal_id}/activate` | `strategic-indicators.settings.manage` |
| DELETE | `/indicator-goals/{goal_id}` | `strategic-indicators.settings.manage` |
| GET | `/admin/goal-years/overview` | `strategic-indicators.settings.manage` |
| POST | `/admin/indicator-goals/bulk-create` | `strategic-indicators.settings.manage` |
| POST | `/admin/indicator-goals/duplicate-year` | `strategic-indicators.settings.manage` |
| POST | `/admin/indicator-goals/fill-missing` | `strategic-indicators.settings.manage` |

---

## Convenções de resposta

### Leitura (grupo A/B)

- JSON direto no corpo (sem `{ success, data }`).
- Rotas via `run_logged_read_route` aplicam `to_json_safe` (suporte a `Decimal` do Postgres).
- Headers: `Cache-Control: private, max-age=300`, `ETag` para revalidação.
- Campo opcional `partial_success: true` quando há erros parciais de medição.

### Escrita (admin)

- Respostas conforme use case (objeto criado/atualizado ou `HTTPException`).
- Mutações invalidam cache de snapshot in-process.

### Códigos HTTP

| Código | Situação |
|--------|----------|
| 200 | Sucesso |
| 401 | JWT ausente/inválido |
| 403 | Sem permissão RBAC |
| 404 | Departamento/indicador/meta não encontrado |
| 422 | Validação Pydantic (query/body) |
| 500 | Erro não tratado (ver logs `*_failed`) |

---

## Autenticação

Middleware `jwt_middleware` (`delpi_auth`) valida o token Keycloak.

Decorators nas rotas:

- `@require_permission("strategic-indicators.view")`
- `@require_any_permission(...)` quando aplicável

O Swagger em `/docs` aceita token via integração do portal (`postMessage` DELPI_AUTH), igual api-delpi.
