# 05 — Indicadores Estratégicos (Strategic Indicators)

Prefixo: `/strategic-indicators`

Plugin: `strategic-indicators` — banco PostgreSQL dedicado + snapshots de métricas TOTVS/RH.

**Formato de resposta:** JSON direto (sem envelope `success`/`data`), exceto onde indicado.

## Filtros globais (leitura)

Várias rotas de leitura aceitam:

| Query | Descrição |
|---|---|
| `department_id` | UUID do departamento. |
| `branch` | Filial. |
| `competence` | Competência (ex.: `2026-05`). |
| `start_date`, `end_date` | Intervalo alternativo. |

---

## Leitura e dashboards

### GET /strategic-indicators/executive-summary

**Permissão:** `strategic-indicators.view`

Resumo executivo consolidado por departamento/indicador.

---

### GET /strategic-indicators/departments

**Permissão:** `strategic-indicators.view`

Lista departamentos com scores agregados.

---

### GET /strategic-indicators/departments/{department_id}

**Permissão:** `strategic-indicators.view`

Detalhe de um departamento. Retorna `404` se não existir.

---

### GET /strategic-indicators/indicators

**Permissão:** `strategic-indicators.view`

Lista indicadores calculados.

**Resposta (estrutura):**

```json
{
  "items": [
    {
      "department_id": "...",
      "department_name": "...",
      "indicator_id": "...",
      "indicator_name": "...",
      "weight_pct": 10.0,
      "goal_label": "...",
      "goal_value": 100.0,
      "goal_periodicity": "monthly",
      "goal_mode": "standard",
      "monthly_targets": [],
      "scope_type": "...",
      "performance_direction": "higher_is_better",
      "value": 95.2,
      "score": 85.0,
      "gap": -4.8,
      "trend": "up",
      "classification": "warning",
      "source": "totvs",
      "value_unit": "%",
      "value_prefix": null,
      "value_suffix": null,
      "value_decimals": 2
    }
  ],
  "errors": [],
  "partial_success": false
}
```

---

### GET /strategic-indicators/alerts

**Permissão:** `strategic-indicators.view`

Alertas derivados de metas e desempenho.

---

### GET /strategic-indicators/trends

**Permissão:** `strategic-indicators.trends.view`

| Query | Default | Descrição |
|---|---|---|
| `months` | `6` | Histórico em meses (`2`–`12`). |

Série temporal por indicador/departamento.

---

### GET /strategic-indicators/presentation

**Permissão:** `strategic-indicators.view`

Payload agregado para tela de apresentação (inclui tendências).

| Query | Default |
|---|---|
| `months` | `6` |

---

## Configurações e governança

**Permissão:** `strategic-indicators.settings.manage` (todas as rotas desta seção).

### GET /strategic-indicators/settings

Retorna pesos, metas legadas, parâmetros e governança.

```json
{
  "weights": {},
  "goals": {},
  "parameters": {},
  "governance": {},
  "meta": {
    "source": "...",
    "updated_at": "...",
    "updated_by_email": "..."
  }
}
```

---

### PUT /strategic-indicators/settings

Atualiza parâmetros e governança. Corpo: `UpdateStrategicIndicatorsSettingsBodySchema` (`parameters`, `governance`).

Auditoria: usuário extraído de `request.state.user` (`sub`/`id`, `email`).

---

### GET /strategic-indicators/settings/audit

| Query | Default |
|---|---|
| `limit` | `20` (máx. `200`) |
| `entity_key` | filtro opcional |

---

## Change requests

Fluxo de solicitação de alteração de configuração.

| Método | Rota | Descrição |
|---|---|---|
| GET | `/change-requests` | Lista solicitações. |
| POST | `/change-requests` | Cria (`title`, `description`, `target_block`, `proposed_payload`). |
| POST | `/change-requests/{id}/comments` | Comentário (`comment_text`). |
| POST | `/change-requests/{id}/submit` | Submete para aprovação. |

---

## Administração — departamentos e indicadores estruturais

| Método | Rota | Descrição |
|---|---|---|
| GET | `/admin/departments` | Lista departamentos admin. |
| POST | `/admin/departments` | Cria departamento. |
| PUT | `/admin/departments/{department_id}` | Atualiza. |
| POST | `/admin/departments/{department_id}/activate` | Reativa. |
| POST | `/admin/departments/{department_id}/deactivate` | Desativa. |
| DELETE | `/admin/departments/{department_id}` | Exclui. |
| GET | `/admin/departments/{department_id}/indicators` | Indicadores do departamento. |
| POST | `/admin/departments/{department_id}/indicators` | Cria indicador. |
| PUT | `/admin/indicators/{indicator_id}` | Atualiza indicador. |
| POST | `/admin/indicators/{indicator_id}/activate` | Ativa. |
| POST | `/admin/indicators/{indicator_id}/deactivate` | Desativa. |
| DELETE | `/admin/indicators/{indicator_id}` | Remove. |

Schemas de corpo: `CreateDepartmentBodySchema`, `UpdateDepartmentBodySchema`, `CreateDepartmentIndicatorBodySchema`, `UpdateDepartmentIndicatorBodySchema`.

---

## Metas analíticas (indicator goals)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/indicator-goals` | Lista (`indicator_id`, `goal_year`, `department_id`, `active_only`). |
| GET | `/indicator-goals/history` | Histórico (`indicator_id` obrigatório). |
| POST | `/indicator-goals` | Cria meta. |
| PUT | `/indicator-goals/{goal_id}` | Atualiza. |
| POST | `/indicator-goals/{goal_id}/activate` | Ativa versão. |
| DELETE | `/indicator-goals/{goal_id}` | Desativa (soft). |
| GET | `/admin/goal-years/overview` | Visão por ano. |
| POST | `/admin/indicator-goals/bulk-create` | Criação em lote. |
| POST | `/admin/indicator-goals/duplicate-year` | Duplica metas entre anos. |
| POST | `/admin/indicator-goals/fill-missing` | Preenche metas faltantes. |

Campos principais de meta serializada:

| Campo | Descrição |
|---|---|
| `goal_year`, `goal_label`, `goal_value` | Ano e valor alvo. |
| `goal_periodicity`, `goal_mode` | Periodicidade e modo (`standard`, etc.). |
| `monthly_targets` | Metas mensais quando aplicável. |
| `version`, `is_active`, `valid_from`, `valid_to` | Versionamento. |

---

## Health do módulo

Ver [01-health.md](./01-health.md) — `GET /strategic-indicators/health`.
