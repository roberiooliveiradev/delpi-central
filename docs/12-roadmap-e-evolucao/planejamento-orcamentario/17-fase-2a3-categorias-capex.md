# 17 — Fase 2A.3 — Categorias de investimento CAPEX

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-04  
**Escopo:** migration V003, catálogo backend, seed idempotente, endpoints admin/público autenticado, tela administrativa, filtro `responsibility_type` server-side, testes.  
**Fora:** itens CAPEX, fornecedor, valor, datas, anexos, submissão/aprovação, alteração de manifesto, reset de banco.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO COM RESSALVAS
```

Ressalva: smoke autenticado da tela no portal permanece bloqueado (JWT/manifesto — Fase 1.1). Validação técnica: V003 aplicada, seed inspecionado, testes, build e `remoteEntry.js` HTTP 200.

---

## 1. Migration e seed

Arquivo: `api-delpi/migrations/plugins/planejamento-orcamentario/V003__create_capex_categories.sql`

Tabela: `planejamento_orcamentario.capex_categories`

| Coluna | Observação |
|--------|------------|
| `code` | UNIQUE, imutável na aplicação |
| `name` | obrigatório |
| `is_active` | desativação lógica |
| `is_system_default` | marca seed inicial |
| auditoria | `created_*`, `updated_*`, `deactivated_*` |

Seed: **24** categorias com `ON CONFLICT (code) DO NOTHING` (não sobrescreve edições administrativas).

Nomes (categoria de investimento ≠ conta contábil ERP): Computadores e Periféricos … Climatização e Ventilação Industrial (lista completa no SQL / `capex_category_constants.py`).

Aplicação:

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin planejamento-orcamentario
```

Resultado: V001–V003 **APLICADA**; inspeção: **24** linhas (`is_system_default=24`, `is_active=24`); primeira `COMPUTADORES_PERIFERICOS`, última `CLIMATIZACAO_VENTILACAO_INDUSTRIAL`. Idempotência do seed coberta por `ON CONFLICT DO NOTHING` + teste unitário de não sobrescrita.

---

## 2. Endpoints

Prefixo: `/apps/api-delpi/planejamento-orcamentario`

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/capex/categories` | access (+ derivados) — só ativas, `display_order` |
| GET | `/admin/capex/categories` | scopes.manage / admin — filtros `is_active`, `q` |
| POST | `/admin/capex/categories` | scopes.manage / admin |
| PUT | `/admin/capex/categories/{id}` | scopes.manage / admin |
| POST | `…/{id}/deactivate` | scopes.manage / admin |
| POST | `…/{id}/reactivate` | scopes.manage / admin |

Auditoria (`entity_type=capex_category`): `created`, `updated`, `order_changed`, `deactivated`, `reactivated`.

---

## 3. Tela administrativa

| Item | Valor |
|------|-------|
| Rota | `/apps/planejamento-orcamentario/admin/categorias-capex` |
| Título | Categorias de Investimento |
| Gate UI | `scopes.manage` ou `admin` |
| Ações | listar, pesquisar, filtrar status, criar, editar nome/descrição/ordem, desativar/reativar |
| Código | editável só na criação |

Card **Categorias CAPEX** na home administrativa.

---

## 4. Correção filtro `responsibility_type`

- Backend: query param em `GET /admin/budget-responsibilities` → use case → repository.
- Frontend: `listAdminBudgetResponsibilities` envia o parâmetro na query; **removido** filtro local em memória.

---

## 5. Testes

| Pacote | Resultado |
|--------|-----------|
| Backend `tests/unit/planejamento_orcamentario` | **47 passed** |
| Frontend Vitest | **43 passed** |
| Lint MFE | 0 errors |
| Typecheck / build | OK |

Cobertura categorias: seed/idempotência (constantes + fake), duplicidade, nome obrigatório, CRUD, código imutável, deactivate/reactivate, listagem pública só ativas, autorização, search/status.  
Responsabilidades: `test_list_filter_by_responsibility_type` + teste MFE de query string.

---

## 6. Build e smoke técnico

| Item | Resultado |
|------|-----------|
| Container MFE | rebuild sequencial |
| `remoteEntry.js` | HTTP **200** |
| Shell `/admin/categorias-capex` | HTTP **200** |
| Bundle | strings da feature presentes |
| API sem auth | categorias → **401** |
| Smoke autenticado portal | **BLOCKED** |

---

## 7. Arquivos principais

**Criados**

- `V003__create_capex_categories.sql`
- `capex_category_constants.py`, `capex_category_use_cases.py`
- `test_capex_category_use_cases.py`
- `AdminCategoriasCapexPage.tsx` (+ `.test.tsx`)
- `budgetPlanningApi.responsibilities.test.ts`
- `17-fase-2a3-categorias-capex.md`

**Alterados**

- repository, responsibility use cases/router, composer, route_contract_registry, exceptions
- MFE: API/types, routing, App, AdminHome, AdminResponsaveis (hint + filtro server-side)

---

## 8. Pendências

1. Homologação autenticada no portal.
2. Cadastro de itens de investimento CAPEX (próxima fase) consumindo o catálogo ativo.
3. Permissões `.capex.*` no manifesto quando o módulo expandir.
