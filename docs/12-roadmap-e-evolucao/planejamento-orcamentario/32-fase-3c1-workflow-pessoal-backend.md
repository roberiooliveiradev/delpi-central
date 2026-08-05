# 32 — Fase 3C.1 — Workflow Pessoal backend (submissão e aprovação)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-05  
**Escopo:** estados do plano de Pessoal, submissão, fila de aprovação, request-changes / reject / approve, histórico append-only, bloqueio de linhas conforme status, concorrência otimista, permissões, testes.  
**Fora:** frontend de workflow, notificações, consolidação, exportação, salários, benefícios, encargos, pré-requisito de Receita.  
**Commit:** nenhum (conforme brief).

Regra principal: a aprovação ocorre sobre o **plano de Pessoal** (agregado por exercício + filial + centro de custo) — não linha a linha.

---

## Status

```text
STATUS: CONCLUÍDO
```

---

## 1. Migration e tabelas

Arquivo: `api-delpi/migrations/plugins/planejamento-orcamentario/V010__create_personnel_plan_workflow.sql`

### `planejamento_orcamentario.personnel_plans` (alterações)

| Campo | Detalhe |
|-------|---------|
| `status` | `draft` \| `submitted` \| `changes_requested` \| `rejected` \| `approved` |
| `version` | otimistic lock (≥ 1; já existia na V008) |
| `submitted_by` / `submitted_at` | submissão |
| `reviewed_by` / `reviewed_at` / `decision_comment` | decisão |

### `planejamento_orcamentario.personnel_plan_history`

Append-only (`id`, `plan_id`, `action`, `previous_status`, `new_status`, `comment`, `actor_sub`, `actor_name`, `created_at`) com trigger anti UPDATE/DELETE.

Aplicação (somente `up`, sem reset):

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin planejamento-orcamentario
```

V001–V010 = **APLICADA**. Nenhum reset de schema/volume.

---

## 2. Estados e transições

| Status | Edição de linhas |
|--------|------------------|
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

Transições arbitrárias → `budget_personnel_plan_invalid_transition`.  
Reabertura / restauração: **não** nesta fase.

---

## 3. Submissão

`POST /personnel/plans/{id}/submit` com `version` (+ comentário opcional).

Validações: exercício `open|closing`; ack das orientações vigentes; responsabilidade ativa `personnel` na filial+CC; permissão `personnel.submit` (ou admin); ≥ 1 linha ativa; cargo válido; os quatro headcounts preenchidos; sem valores negativos; versão atual.

Efeitos: status `submitted`; `submitted_by`/`submitted_at`; limpa campos de review anteriores; histórico + auditoria; mutações de linha bloqueadas via `assert_personnel_plan_allows_mutation`.

Incompleto → `budget_personnel_plan_incomplete` com `meta.incomplete_lines` (`id`, `position_name`, `missing_fields`).

Pré-requisito de Receita: **não** implementado (regra ainda não confirmada).

---

## 4. Aprovação

Fila: `GET /personnel/review-queue` (default `status=submitted`; filtros exercício/filial/área/CC/status/responsável; paginação).

Decisões (somente a partir de `submitted`, com `version`):

| Ação | Comentário | Novo status |
|------|------------|-------------|
| request-changes | obrigatório | `changes_requested` |
| reject | obrigatório | `rejected` |
| approve | opcional | `approved` |

Segregação: quem `submitted_by` não decide o próprio plano (exceto admin) → `budget_personnel_approval_forbidden`.

Conflito de versão → HTTP 409 `budget_personnel_plan_version_conflict`.

Aprovação repetida → `budget_personnel_plan_already_approved`.

---

## 5. Bloqueios nas linhas

`personnel_plan_guard.assert_personnel_plan_allows_mutation` consultado em criar / editar / arquivar linha.

Liberado só em `draft` e `changes_requested`. Caso contrário → `budget_personnel_plan_locked`.

---

## 6. Endpoints

Prefixo: `/planejamento-orcamentario`

| Método | Path | operation_id |
|--------|------|----------------|
| POST | `/personnel/plans/{plan_id}/submit` | `submit_…_personnel_plan` |
| GET | `/personnel/plans/{plan_id}/history` | `list_…_personnel_plan_history` |
| GET | `/personnel/review-queue` | `list_…_personnel_review_queue` |
| GET | `/personnel/review/{plan_id}` | `get_…_personnel_review` |
| POST | `/personnel/review/{plan_id}/request-changes` | `request_changes_…` |
| POST | `/personnel/review/{plan_id}/reject` | `reject_…` |
| POST | `/personnel/review/{plan_id}/approve` | `approve_…` |

Contratos em `route_contract_registry.py` (`entity`: `personnel_plan` / `personnel_plan_history`).

---

## 7. Permissões e manifesto

Novas (declaradas, **sem** auto-import / atribuição):

```text
planejamento-orcamentario.personnel.submit
planejamento-orcamentario.personnel.approve
```

Mantidas: `personnel.view`, `personnel.edit`.

Atualizados: `api_delpi_permissions.py`, `planejamento-orcamentario.manifest.json` (0.2.4), `plugins/.../src/utils/permissions.ts` (constantes; sem UI de workflow).

---

## 8. Testes

Suíte: `tests/unit/planejamento_orcamentario/`.

Novo: `test_personnel_plan_workflow_use_cases.py` (23 casos) — submit válido/sem linhas/incompleto/sem responsabilidade/sem ack, lock após submit, request-changes + edição, reenvio, reject sem/com comentário + lock, transição inválida, approve, approve repetida, SoD + bypass admin, edição pós-approve, conflito de versão, histórico, fila filtrada, isolamento filiais 01/02, rotas com prefixo, regressão CAPEX+Pessoal.

Fake de Pessoal estendido com `transition_personnel_plan` / histórico / filtros da fila.

---

## 9. Arquivos principais

| Área | Path |
|------|------|
| Migration | `migrations/plugins/planejamento-orcamentario/V010__…sql` |
| Domain | `personnel_budget_constants.py`, `personnel_plan_guard.py`, `exceptions.py` |
| Application | `personnel_plan_use_cases.py` |
| Infra | `postgres_budget_planning_repository.py` |
| HTTP | `planejamento_orcamentario_router.py`, registry, permissions, deps |
| MFE (só declaração) | manifesto 0.2.4 + `permissions.ts` |
| Testes | `test_personnel_plan_workflow_use_cases.py` (+ FakeRepo em `test_personnel_plan_use_cases.py`) |
| Doc | este arquivo |

---

## 10. Pendências

- Frontend da fila / submissão / decisões (fase seguinte).
- Notificações.
- Consolidação / exportação de Pessoal.
- Salários, benefícios, encargos.
- Pré-requisito de Receita (quando confirmado).
- Atribuição operacional das novas permissões a grupos (manual).

---

## 11. Validação executada

| Check | Resultado |
|-------|-----------|
| Branch `feat/planejamento-orcamentario` | OK |
| Containers `postgres-plugins` + `api-delpi` | healthy / running |
| V010 `up` | nenhuma pendente (já aplicada) |
| Status V001–V010 | **APLICADA** |
| Schema `personnel_plans` / `personnel_plan_history` | OK (status, colunas, FK, índices, trigger) |
| Append-only (UPDATE/DELETE em TX + ROLLBACK) | OK; leftover = 0 |
| `pytest …/test_personnel_plan_workflow_use_cases.py` | **23 passed** |
| `pytest tests/unit/planejamento_orcamentario/` | **163 passed** |
| Health `http://127.0.0.1:8000/health` (api-delpi) | 200 `{"status":"online"}` |
| Health via gateway → `api-delpi:8000/health` | 200 `{"status":"online"}` |
| Manifesto 0.2.4 submit/approve | OK (sem import/atribuição) |
| Reset de schema | **não** executado |
