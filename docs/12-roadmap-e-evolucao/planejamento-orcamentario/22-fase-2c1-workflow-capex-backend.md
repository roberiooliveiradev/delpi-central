# 22 — Fase 2C.1 — Workflow CAPEX backend (submissão e aprovação)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-05  
**Escopo:** agregado `capex_plans` por exercício+CC, migration V006, submissão, fila de aprovação, request-changes / reject / approve, histórico append-only, bloqueio de edição conforme status, permissões, testes.  
**Fora:** frontend, notificações por e-mail, exportações, conta contábil, consolidação executiva.  
**Commit:** nenhum (conforme brief).

Regra principal: a aprovação ocorre sobre o **conjunto de investimentos** de um centro de custo em determinado exercício — não linha a linha.

---

## Status

```text
STATUS: CONCLUÍDO
```

---

## 1. Migration e tabelas

Arquivo: `api-delpi/migrations/plugins/planejamento-orcamentario/V006__create_capex_plans_and_workflow.sql`

### `planejamento_orcamentario.capex_plans`

| Campo | Detalhe |
|-------|---------|
| `id` | UUID PK |
| `exercise_id` / `unit_id` / `area_id` / `cost_center_id` | contexto organizacional |
| `status` | `draft` \| `submitted` \| `changes_requested` \| `rejected` \| `approved` |
| `version` | otimistic lock (≥ 1) |
| `submitted_by` / `submitted_at` | submissão |
| `reviewed_by` / `reviewed_at` / `decision_comment` | decisão |
| `created_*` / `updated_*` | auditoria de linha |

Unicidade: `UNIQUE (exercise_id, cost_center_id)`.

Investimentos **não** são duplicados — permanecem em `capex_investments` ligados por exercício+CC.

### `planejamento_orcamentario.capex_plan_history`

Append-only (`plan_id`, `action`, `previous_status`, `new_status`, `comment`, `actor_sub`, `actor_name`, `created_at`) com trigger anti UPDATE/DELETE.

Aplicação (somente `up`, sem reset):

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin planejamento-orcamentario
```

V001–V006 = **APLICADA**. Nenhum reset de schema/volume.

---

## 2. Estados e transições

| Status | Edição de investimentos/anexos |
|--------|--------------------------------|
| (plano inexistente ≡ draft) | liberada |
| `draft` | liberada |
| `changes_requested` | liberada |
| `submitted` | bloqueada |
| `rejected` | somente leitura |
| `approved` | bloqueada |

Transições válidas (`PLAN_TRANSITIONS`):

```text
draft              → submit           → submitted
changes_requested  → submit           → submitted
submitted          → request_changes  → changes_requested
submitted          → reject           → rejected
submitted          → approve          → approved
```

Transições arbitrárias → `budget_capex_plan_invalid_transition`.

---

## 3. Submissão

`POST /capex/plans/{id}/submit` com `version` (+ comentário opcional).

Validações: exercício `open|closing`; ack das orientações vigentes; responsabilidade ativa no CC; permissão `capex.submit` (ou admin); ≥ 1 investimento ativo (`status=draft`); todos `is_complete`; categorias ativas; valores > 0; versão atual.

Efeitos: status `submitted`; `submitted_by`/`submitted_at`; limpa campos de review anteriores; histórico + auditoria; mutações de investimento/anexo bloqueadas via `assert_plan_allows_mutation`.

Incompleto → `budget_capex_plan_incomplete` com `meta.incomplete_investments` (`id`, `description`, `missing_fields`).

Resolve get-or-create: `POST /capex/plans/resolve` (`exercise_id` + `cost_center_id`).

---

## 4. Aprovação

Fila: `GET /capex/review-queue` (default `status=submitted`; filtros exercício/unidade/área/CC/status/responsável; paginação).

Decisões (somente a partir de `submitted`, com `version`):

| Ação | Comentário | Novo status |
|------|------------|-------------|
| request-changes | obrigatório | `changes_requested` |
| reject | obrigatório | `rejected` |
| approve | opcional | `approved` |

Segregação: quem `submitted_by` não decide o próprio plano (exceto admin) → `budget_capex_approval_forbidden`.

Conflito de versão → HTTP 409 `budget_capex_plan_version_conflict`.

Aprovação repetida → `budget_capex_plan_already_approved`.

---

## 5. Bloqueios em investimentos e anexos

`capex_plan_guard.assert_plan_allows_mutation` consultado em:

- criar / editar / arquivar investimento;
- upload / arquivar anexo.

Liberado só em `draft` e `changes_requested` (ou plano ainda inexistente). Caso contrário → `budget_capex_plan_locked`.

---

## 6. Endpoints

Prefixo: `/planejamento-orcamentario`

| Método | Path | operation_id |
|--------|------|----------------|
| GET | `/capex/plans` | `list_…_capex_plans` |
| POST | `/capex/plans/resolve` | `resolve_…_capex_plan` |
| GET | `/capex/plans/{plan_id}` | `get_…_capex_plan` |
| POST | `/capex/plans/{plan_id}/submit` | `submit_…_capex_plan` |
| GET | `/capex/plans/{plan_id}/history` | `list_…_capex_plan_history` |
| GET | `/capex/review-queue` | `list_…_capex_review_queue` |
| GET | `/capex/review/{plan_id}` | `get_…_capex_review` |
| POST | `/capex/review/{plan_id}/request-changes` | `request_changes_…` |
| POST | `/capex/review/{plan_id}/reject` | `reject_…` |
| POST | `/capex/review/{plan_id}/approve` | `approve_…` |

Contratos em `route_contract_registry.py` (`entity`: `capex_plan` / `capex_plan_history`).

---

## 7. Permissões e manifesto

Novas (declaradas, **sem** auto-import / atribuição):

```text
planejamento-orcamentario.capex.submit
planejamento-orcamentario.capex.approve
```

Atualizados: `api_delpi_permissions.py`, `planejamento-orcamentario.manifest.json`, `plugins/.../src/utils/permissions.ts`.

---

## 8. Testes

Suíte: `tests/unit/planejamento_orcamentario/` — **99 passed**.

Novo: `test_capex_plan_use_cases.py` cobre resolve/unicidade, submit válido/sem itens/incompleto/sem responsabilidade/sem ack, lock em submitted, request-changes + edição, reenvio, reject sem comentário, approve, approve repetida, edição pós-approve, approver sem perm, SoD submitter≠approver, IDOR entre CCs, histórico, conflito de versão, fila filtrada.

FakeRepos de investment/attachment estendidos com `get_capex_plan_by_exercise_cc`.

---

## 9. Arquivos principais

| Área | Path |
|------|------|
| Migration | `migrations/plugins/planejamento-orcamentario/V006__…sql` |
| Domain | `capex_plan_constants.py`, `capex_plan_guard.py`, `exceptions.py` |
| Application | `capex_plan_use_cases.py` (+ locks em investment/attachment) |
| Infra | `postgres_budget_planning_repository.py` (CRUD/transição/histórico) |
| HTTP | `planejamento_orcamentario_router.py`, registry, permissions |
| MFE perms (só declaração) | manifesto + `permissions.ts` |
| Testes | `test_capex_plan_use_cases.py` |
| Doc | este arquivo |

---

## 10. Pendências

- Frontend da fila / submissão / decisões (Fase 2C.2+).
- Notificações por e-mail.
- Exportações, conta contábil, consolidação executiva.
- Atribuição operacional das novas permissões a grupos (manual, fora deste brief).

---

## 11. Validação executada

| Check | Resultado |
|-------|-----------|
| V006 status | APLICADA (V001–V006) |
| Tabelas / UNIQUE / CHECK / índices / trigger append-only | OK |
| `pytest tests/unit/planejamento_orcamentario/` | 99 passed |
| Health API (`/health`) | 200 |
| Reset de schema | **não** executado |
