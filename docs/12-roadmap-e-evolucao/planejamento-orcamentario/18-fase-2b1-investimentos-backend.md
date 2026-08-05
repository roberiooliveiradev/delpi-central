# 18 — Fase 2B.1 — Investimentos CAPEX (backend)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-04  
**Escopo:** migration V004, entidade, regras, repository, use cases, endpoints CRUD, autorização por CC, rascunho, concorrência otimista, auditoria, testes.  
**Fora:** frontend, anexos, submissão, aprovação, consolidação, exportações.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO
```

---

## 1. Migration e estrutura

Arquivo: `api-delpi/migrations/plugins/planejamento-orcamentario/V004__create_capex_investments.sql`

Tabela: `planejamento_orcamentario.capex_investments`

| Aspecto | Detalhe |
|---------|---------|
| FKs | `exercise_id`, `unit_id`, `area_id`, `cost_center_id`, `category_id` → catálogos existentes |
| Valor | `NUMERIC(18,2)` — nunca float |
| Status | `draft` \| `archived` |
| Concorrência | `version INTEGER` (≥ 1) |
| Soft-archive | `archived_by` / `archived_at` — sem DELETE físico |

Aplicação:

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin planejamento-orcamentario
```

V001–V004 = **APLICADA**.

---

## 2. Campos

Alinhamento com a planilha original (§2.3) e Carta:

| Campo | Spec / regra |
|-------|----------------|
| `category_id` | Categoria ativa de `capex_categories` (≠ conta contábil) |
| `accounting_account_code` | Nullable — separado, sem fonte ERP nesta fase |
| `description` | Obrigatória para `is_complete` |
| `justification` | Opcional |
| `probable_supplier_name` / `_code` | Opcional, informativo |
| `estimated_amount` | Decimal > 0 para completo |
| `currency` | Default `BRL` |
| `required_date` | Data Rcbto / bem disponível |
| `priority` | `1`–`4` (planilha; não low/medium/high) |
| `origin` | `national` \| `imported` |
| `classification` | Opcional `1`–`6` |
| `shift` | Opcional turno `1`–`3` |
| `application` / `observations` | Opcionais |

---

## 3. Rascunho e completude

- Criação e edição permitem campos nulos (rascunho).
- Response inclui `is_complete` e `missing_fields` (ex.: `description`, `estimated_amount`, `category_id`, `required_date`, `priority`, `origin`, …).
- Submissão **não** implementada.

---

## 4. Autorização

Para criar/listar/consultar/editar/arquivar:

1. Autenticado + permissão de acesso ao app  
2. `BudgetGuidanceAcknowledgementGuard.assert_modules_unlocked`  
3. `BudgetResponsibilityGuard.assert_user_has_budget_responsibility` no CC  

Listagem filtra aos CCs do usuário. Admin (`.admin`) lista/consulta sem restrição de CC (auditável). Mutações de admin ainda passam pelo guard do CC alvo. IDOR por ID → `budget_capex_investment_not_found`.

---

## 5. Endpoints

Prefixo: `/apps/api-delpi/planejamento-orcamentario`

| Método | Path |
|--------|------|
| GET | `/capex/investments` (filtros: exercício, CC, categoria, prioridade, origem, status, `q`, paginação) |
| POST | `/capex/investments` |
| GET | `/capex/investments/{id}` |
| PUT | `/capex/investments/{id}` (`version` obrigatório) |
| POST | `/capex/investments/{id}/archive` |

---

## 6. Concorrência

`PUT` exige `version` atual. Update atômico `WHERE id AND version`. Divergência → HTTP **409** `budget_capex_version_conflict` + auditoria `capex_investment.version_conflict`.

---

## 7. Auditoria

`entity_type=capex_investment`: `created`, `updated`, `category_changed`, `amount_changed`, `date_changed`, `cost_center_changed`, `archived`, `version_conflict`. Sem JWT/secrets/binários.

---

## 8. Códigos de erro

`budget_capex_investment_not_found`, `budget_capex_category_invalid`, `budget_capex_cost_center_forbidden`, `budget_capex_value_invalid`, `budget_capex_date_invalid`, `budget_capex_status_invalid`, `budget_capex_version_conflict`, `budget_capex_archived`, `budget_guidance_acknowledgement_required`.

---

## 9. Testes

```bash
docker exec delpi-api-delpi python -m pytest tests/unit/planejamento_orcamentario -q
```

Suite PO: **62 passed**.  
`test_capex_investment_use_cases.py`: **15 passed** (rascunho, completo, categoria inativa, CC sem responsabilidade, ack, valor, data, edição, concorrência, conflito, archive, escopo, filtros/paginação, IDOR, troca de CC, `is_complete`, admin list).

Health: `delpi-api-delpi` **healthy**; `GET /capex/investments` sem auth → **401**.

---

## 10. Arquivos

**Criados**

- `V004__create_capex_investments.sql`
- `capex_investment_constants.py`
- `capex_investment_use_cases.py`
- `test_capex_investment_use_cases.py`
- `18-fase-2b1-investimentos-backend.md`

**Alterados**

- `exceptions.py`, `postgres_budget_planning_repository.py`, composer, router, `route_contract_registry.py`

---

## 11. Pendências

1. Frontend de cadastro CAPEX (2B.2).  
2. Anexos, submissão e workflow de aprovação.  
3. Conta contábil ERP quando houver fonte confiável.  
4. Smoke HTTP autenticado (JWT).
