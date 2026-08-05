# 24 — Fase 2D.1: Consolidação gerencial CAPEX (backend)

**Data:** 2026-08-05  
**Branch:** `feat/planejamento-orcamentario`  
**Escopo:** indicadores consolidados, agrupamentos, filtros gerenciais, detalhamento paginado, exportação Excel, autorização, auditoria e testes backend.  
**Fora:** frontend, PDF, Receita, Pessoal, integração contábil, alterações de workflow, migrations novas.

---

## 1. Objetivo

Disponibilizar na `api-delpi` a consolidação gerencial dos investimentos CAPEX **não arquivados**, com filtros aplicados no backend e exportação Excel síncrona (openpyxl em memória).

---

## 2. Modelo de dados (sem migration)

Reutiliza:

| Tabela | Origem |
|--------|--------|
| `capex_investments` | V004 |
| `capex_plans` | V006 |
| `capex_categories` / org_* | V001–V003 |

Join canônico: investimento ↔ plano por `(exercise_id, cost_center_id)`. Plano ausente ⇒ status efetivo `draft`.

**Moeda:** o fluxo atual grava `BRL`. A consolidação **não soma moedas distintas**. Se o conjunto filtrado tiver mais de uma moeda, a API responde `422` com `budget_capex_consolidation_currency_conflict`.

---

## 3. Indicadores (`summary`)

| Campo | Significado |
|-------|-------------|
| `total_estimated_amount` | Soma decimal dos valores previstos |
| `investment_count` | Qtde de investimentos |
| `cost_center_count` | CCs distintos |
| `plans_*_count` | Planos por status (contagem de pares exercício+CC) |
| `approved_amount` | Valor de investimentos cujo plano está `approved` |
| `in_review_amount` | Valor com plano `submitted` ou `changes_requested` |
| `incomplete_investment_count` | Itens incompletos (mesmos campos de completude da 2B.1) |
| `currency` | Moeda única do conjunto |

---

## 4. Filtros (backend)

`exercise_id` **ou** `year` (obrigatório) + opcionais:

- `unit_id`, `area_id`, `cost_center_id`
- `category_id`, `priority`, `origin`
- `plan_status`
- `required_date_from`, `required_date_to` (Data Rcbto)

Arquivados (`status = archived`) são **sempre excluídos**.

---

## 5. Agrupamentos

| Path | Dimensão |
|------|----------|
| `/capex/consolidation/by-unit` | unidade |
| `/by-area` | área |
| `/by-cost-center` | centro de custo (+ status do plano) |
| `/by-category` | categoria |
| `/by-priority` | prioridade |
| `/by-origin` | origem |
| `/by-month` | mês da Data Rcbto |
| `/by-plan-status` | status do planejamento |

Cada item: `code`, `description`, `investment_count`, `total_amount`, `percent_of_total`.

---

## 6. Detalhamento

`GET …/capex/consolidation/details` — paginado (`page`, `page_size` ≤ 200), ordenação whitelist (`sort_by` / `sort_dir`).

Campos: exercício, unidade, área, CC, responsável, descrição, categoria, prioridade, origem, fornecedor, valor, Data Rcbto, completude, status do plano.

---

## 7. Endpoints

Prefixo: `/planejamento-orcamentario`

| Método | Path | operationId | Permissão router |
|--------|------|-------------|------------------|
| GET | `/capex/consolidation/summary` | `get_…_capex_consolidation_summary` | consolidation view (+ access/submit/admin) |
| GET | `/capex/consolidation/by-*` | `list_…_by_*` | idem |
| GET | `/capex/consolidation/details` | `list_…_details` | idem |
| GET | `/capex/consolidation/export.xlsx` | `export_…_xlsx` | **export** (+ admin) |

Resposta JSON: envelope `api_delpi_success`. Export: `StreamingResponse` XLSX.

---

## 8. Autorização

| Permissão | Efeito |
|-----------|--------|
| `planejamento-orcamentario.capex.consolidation.view` | Consolidação em todos os escopos (sem filtro de responsabilidade) |
| `planejamento-orcamentario.admin` | Inclui consolidação e export |
| `planejamento-orcamentario.access` / `.capex.submit` | Podem consultar, **limitados aos CCs** da responsabilidade CAPEX |
| `planejamento-orcamentario.capex.export` | Exportação Excel (obrigatória; gestor comum sem esta perm = 403) |

Manifesto atualizado (sem import automático de permissões no core).

IDOR: filtro `cost_center_id` fora do escopo do gestor ⇒ `budget_capex_cost_center_forbidden`.

---

## 9. Exportação Excel

Arquivo em memória (`BytesIO` + openpyxl), sem macros/fórmulas externas.

**Abas:** Resumo · Investimentos · Por Centro de Custo · Por Categoria · Por Mês  

**Nome:** `planejamento-capex-{ano}-AAAA-MM-DD.xlsx`  

Recursos: cabeçalhos legíveis, auto-filter, freeze da linha 1, valores numéricos, datas reais, formato monetário, larguras razoáveis. Conteúdo restrito aos filtros aplicados.

---

## 10. Auditoria

| Ação | Quando |
|------|--------|
| `capex_consolidation.summary_viewed` | Consulta do resumo |
| `capex_consolidation.exported` | Geração Excel |

Payload: filtros públicos, contagens, filename, timestamp — **sem** binário/JWT/planilha completa.

---

## 11. Arquivos principais

- `app/domain/services/planejamento_orcamentario/capex_consolidation_*.py`
- `app/application/use_cases/…/capex_consolidation_use_cases.py`
- `app/application/services/…/capex_consolidation_excel_builder.py`
- `postgres_budget_planning_repository.py` → `list_capex_consolidation_rows`
- `planejamento_orcamentario_router.py`, `route_contract_registry.py`, `api_delpi_permissions.py`, `deps.py`, composer
- `plugins/…/planejamento-orcamentario.manifest.json`
- `tests/unit/planejamento_orcamentario/test_capex_consolidation_use_cases.py`

---

## 12. Testes e validação

```bash
docker exec delpi-api-delpi python -m pytest tests/unit/planejamento_orcamentario/ -q
# 109 passed (2026-08-05)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
# V001–V006 APLICADAS
# health: {"status":"online"}
```

Excel gerado e validado estruturalmente nos testes (abas, cabeçalhos, números, datas, filtros).

---

## 13. Pendências

- Frontend da consolidação / tela de export (fase posterior).
- PDF executivo.
- Importar novas permissões no core (operacional, fora desta fase).
- Smoke HTTP autenticado dos novos endpoints em ambiente com exercício populado.
- Regeneração OpenAPI / inventário de cobertura de rotas quando o CI do pacote exigir.

---

## 14. Status

**STATUS: CONCLUÍDO COM RESSALVAS**

Ressalvas: sem exercício CAPEX populado no banco local para export autenticado live; smoke HTTP dos endpoints novos não exercitado com JWT; permissões novas no manifesto ainda precisam ser importadas no core pelo operador.
