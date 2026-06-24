# PAC Qualidade — Planos de Ação (`/quality/action-plans`)

CRUD e leitura consolidada de **planos de ação central de qualidade** (PAC), persistidos no PostgreSQL de plugins (`schema quality`).

**Plugin consumidor:** `plugins/quality-action-plans`  
**Agente GPT (escrita alternativa):** `api-pac-quality` em `pac-api.minhadelpi.com.br` — mesma base Postgres, autenticação por API key.  
**Migrations:** `api-delpi/migrations/plugins/quality-action-plans/` (V001–V004)

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10).

**Headers obrigatórios (plugin):**

```http
Authorization: Bearer <access_token>
X-Delpi-Caller-App: quality-action-plans
```

---

## Permissões

| Operação | Permissões aceitas (qualquer uma) |
|----------|-----------------------------------|
| Leitura | `api-delpi.access`, `api-delpi.quality.access`, `api-delpi.quality.action-plans.read`, `dashboard-quality.view`, `quality-action-plans.access`, `quality-action-plans.read`, `quality-action-plans.manage` |
| Escrita | `api-delpi.access`, `api-delpi.quality.access`, `quality-action-plans.access`, `quality-action-plans.write`, `quality-action-plans.manage` |

Registrar manifesto: `plugins/quality-action-plans/scripts/register-manifest.sh`

---

## Endpoints — leitura

| Método | Rota | `operationId` | Descrição |
|--------|------|---------------|-----------|
| GET | `/quality/action-plans/dashboard` | `get_quality_action_plans_dashboard` | Cards executivos |
| GET | `/quality/action-plans` | `list_quality_action_plans` | Listagem paginada |
| GET | `/quality/action-plans/overdue` | `list_quality_action_plans_overdue` | Planos com ações vencidas |
| GET | `/quality/action-plans/{plan_id}` | `get_quality_action_plan_detail` | Detalhe (plano + Ishikawa + 5 Porquês + ações + histórico) |

### GET `/quality/action-plans/dashboard`

**Query:** `branch_code` (`01` \| `02`, opcional)

**`data` (consolidado):**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `open_plans` | int | Planos abertos |
| `critical_open` | int | Críticos abertos |
| `waiting_validation` | int | Aguardando validação |
| `completed_this_month` | int | Concluídos no mês corrente |
| `overdue_actions` | int | Ações vencidas |
| `overdue_plans` | int | Planos com ação vencida |
| `by_branch` | array | `{ branch_code, open_plans, critical_open }` — só sem filtro de filial |
| `branch_code` | string | Presente quando filtrado por filial |

### GET `/quality/action-plans` e `/overdue`

**Query comum:** `status`, `severity`, `product_code`, `customer_name`, `owner_user_id`, `branch_code`, `page`, `page_size`

**`data`:** `{ items: [...], pagination: { page, page_size, total, total_pages } }`

---

## Endpoints — escrita

| Método | Rota | `operationId` | Descrição |
|--------|------|---------------|-----------|
| POST | `/quality/action-plans` | `create_quality_action_plan` | Criar plano (`branch_code` obrigatório) |
| PATCH | `/quality/action-plans/{plan_id}/status` | `update_quality_action_plan_status` | Atualizar status do plano |
| PUT | `/quality/action-plans/{plan_id}/ishikawa` | `upsert_quality_action_plan_ishikawa` | Ishikawa (upsert) |
| PUT | `/quality/action-plans/{plan_id}/five-whys` | `upsert_quality_action_plan_five_whys` | 5 Porquês (upsert) |
| POST | `/quality/action-plans/{plan_id}/actions` | `create_quality_action_plan_actions` | Criar uma ou mais ações |
| PATCH | `/quality/action-plans/{plan_id}/actions/{action_id}` | `update_quality_action_plan_action` | Atualizar ação |
| POST | `/quality/action-plans/{plan_id}/effectiveness-review` | `record_quality_action_plan_effectiveness` | Registrar eficácia |

### POST `/quality/action-plans` — corpo mínimo

```json
{
  "title": "Reclamação cliente — cabo X",
  "branch_code": "01",
  "severity": "high",
  "status": "triage",
  "customer_name": "Cliente ABC",
  "reported_problem": "Descrição do problema"
}
```

- `branch_code`: `01` ou `02` (obrigatório)
- `status` inicial: `draft` ou `triage`
- Código gerado automaticamente: `PAC-YYYY-####` (sequência `quality_action_plan`)

### Status do plano

`draft` → `triage` → `containment` → `root_cause_analysis` → `action_plan_defined` → `in_progress` → `waiting_validation` → `completed` | `cancelled`

### Tipos de ação

`containment`, `corrective`, `preventive`, `verification`, `standardization`, `training`

---

## Inteligência (api-pac-quality)

Casos similares, padrões de solução e sugestão de ações permanecem na **api-pac-quality** (`POST /quality/action-plans/intelligence/*`), consumidos pelo agente GPT — não expostos na api-delpi nesta fase.

---

## Testes

```bash
cd delpi-central
.venv/bin/python -m pytest api-delpi/tests/test_quality_action_plans_dashboard.py \
  api-delpi/tests/test_quality_action_plans_write_use_cases.py -q
```

Smoke manual (container):

```bash
docker exec delpi-api-delpi python -c "
from app.composition.quality_action_plans_composer import build_quality_action_plan_read_repository
print(build_quality_action_plan_read_repository().get_dashboard_summary(branch_code='01'))
"
```
