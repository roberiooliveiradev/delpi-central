# 15 — Fase 2A.1 — Responsabilidades orçamentárias (backend)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-04  
**Escopo:** modelagem, migration V002, domínio, repository, casos de uso, endpoints, RBAC, auditoria, testes.  
**Fora:** frontend, categorias CAPEX, itens CAPEX, workflow/aprovação, alteração de manifesto.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO
```

---

## 1. Conceito

| Camada | Papel |
|--------|--------|
| **RBAC** | O que o usuário pode fazer (`scopes.manage` / `admin` / `access`) |
| **Catálogo org** | Unidades, áreas e centros de custo (`org_*`) |
| **Responsabilidade** | Sobre quais CCs o usuário trabalha no exercício/módulo |

Uma permissão RBAC **não** substitui o vínculo de responsabilidade.

Nesta fase o único módulo permitido é `capex`.

---

## 2. Migration

Arquivo: `api-delpi/migrations/plugins/planejamento-orcamentario/V002__create_budget_responsibilities.sql`  
**V001 não foi alterada.**

Tabela: `planejamento_orcamentario.budget_responsibilities`

Campos principais: `id`, `exercise_id`, `module`, `user_sub`, snapshots de nome/e-mail, `unit_id` / `area_id` / `cost_center_id` (códigos do catálogo interno), `responsibility_type` (`owner`|`collaborator`), vigência, `is_active`, auditoria de criação/atualização/desativação.

Unicidade ativa:

```text
UNIQUE (exercise_id, module, user_sub, cost_center_id) WHERE is_active = TRUE
```

### Aplicação (dev)

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin planejamento-orcamentario
```

Resultado homologado: `V001` e `V002` = **APLICADA**; schema inspecionado (colunas, índices, FKs, checks).

---

## 3. Regras

- Vários CCs por usuário; vários usuários por CC.
- Vínculo por exercício; módulo `capex`.
- Inativo ou fora da vigência não concede acesso.
- CC/unidade/área apenas do catálogo; hierarquia validada (CC → unidade/área).
- Exercício arquivado bloqueia criação/reativação.
- Sem exclusão física (soft deactivate).
- Reativação bloqueada se houver conflito ativo equivalente.
- Guard: `BudgetResponsibilityGuard.assert_user_has_budget_responsibility`.

---

## 4. Endpoints

Prefixo: `/apps/api-delpi/planejamento-orcamentario`

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/admin/budget-responsibilities` | scopes.manage / admin |
| POST | `/admin/budget-responsibilities` | scopes.manage / admin |
| GET | `/admin/budget-responsibilities/{id}` | scopes.manage / admin |
| PUT | `/admin/budget-responsibilities/{id}` | scopes.manage / admin |
| POST | `/admin/budget-responsibilities/{id}/deactivate` | scopes.manage / admin |
| POST | `/admin/budget-responsibilities/{id}/reactivate` | scopes.manage / admin |
| GET | `/capex/my-responsibilities` | access (+ derivados) |

`my-responsibilities` usa **somente** o `user_sub` do JWT (`build_actor()`). Não há parâmetro `user_sub` na rota pessoal.

Manifesto **não** alterado nesta fase.

---

## 5. Auditoria

Eventos em `audit_events` (`entity_type=budget_responsibility`):

- `responsibility.created`
- `responsibility.updated` / `responsibility.type_changed` / `responsibility.validity_changed`
- `responsibility.deactivated`
- `responsibility.reactivated`

Payload: estado público do vínculo (sem JWT, secrets ou resposta completa do diretório).

---

## 6. Testes

```bash
docker exec delpi-api-delpi python -m pytest tests/unit/planejamento_orcamentario -q
```

**34 passed** (inclui suite Fase 1 + `test_budget_responsibility_use_cases.py`).

Cobertura 2A.1: criação, multi-CC, multi-usuário, duplicidade, CC inválido, hierarquia, vigência, expirado/inativo, deactivate/reactivate/conflito, sem permissão, my-responsibilities/JWT, guard, módulo ≠ capex, IDOR admin, auditoria tipo/vigência.

---

## 7. Arquivos

**Criados**

- `api-delpi/migrations/plugins/planejamento-orcamentario/V002__create_budget_responsibilities.sql`
- `api-delpi/app/domain/services/planejamento_orcamentario/responsibility_constants.py`
- `api-delpi/app/domain/services/planejamento_orcamentario/responsibility_guard.py`
- `api-delpi/app/application/use_cases/planejamento_orcamentario/budget_responsibility_use_cases.py`
- `api-delpi/tests/unit/planejamento_orcamentario/test_budget_responsibility_use_cases.py`
- `docs/12-roadmap-e-evolucao/planejamento-orcamentario/15-fase-2a1-responsabilidades-backend.md`

**Alterados**

- `exceptions.py`, `postgres_budget_planning_repository.py`, `planejamento_orcamentario_composer.py`
- `planejamento_orcamentario_router.py`, `route_contract_registry.py`

---

## 8. Pendências (próximas fases)

1. UI admin de vínculos (picker Core directory + catálogo CC).
2. Permissões/manifesto `.capex.*` quando o módulo CAPEX for exposto.
3. Consumo do guard nos casos de uso de itens CAPEX (Fase 2A seguinte).
4. Testes de integração HTTP com JWT real (opcional; unitários cobrem regras).

---

## 9. Rollback operacional

Não executar `reset` em ambiente com dados. Para reverter código: remover rotas/use cases e deixar V002 aplicada (tabela vazia é inofensiva). Nova migration só se for necessário dropar a tabela em sandbox local com confirmação explícita.
