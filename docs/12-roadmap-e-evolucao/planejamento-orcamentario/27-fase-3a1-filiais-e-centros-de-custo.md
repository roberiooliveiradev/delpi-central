# 27 — Fase 3A.1: Filiais e centros de custo

**Data:** 2026-08-05  
**Branch:** `feat/planejamento-orcamentario`  
**Tipo:** backend + migration incremental (`up` only)

---

## 1. Objetivo

Garantir a identidade funcional:

```text
exercício + filial + centro de custo
```

O mesmo código de CC pode existir nas filiais `01` (Jaraguá do Sul/SC) e `02` (Rio Bananal/ES) sem colisão.

---

## 2. Estratégia de chave

| Camada | Identidade |
|--------|------------|
| Interna | `org_cost_centers.id` (UUID) |
| Externa / negócio | `UNIQUE (branch, code)` |
| Filhos (responsabilidades, CAPEX, escopos) | FK composta `(unit_id\|unit_code, cost_center_id\|cost_center_code) → (branch, code)` |

- `cost_center_id` nos vínculos continua sendo o **código** de negócio.  
- `unit_id` / `branch` é a filial (`01`\|`02`).  
- Autorização e listagens usam pares `(unit_id, cost_center_id)` para não vazar entre filiais.

---

## 3. Migration V007

Arquivo: `api-delpi/migrations/plugins/planejamento-orcamentario/V007__make_cost_centers_branch_aware.sql`

1. **Guard:** se algum CC existente tiver `unit_code` nulo ou fora de `{01,02}`, a migration **falha** com mensagem clara (sem filial padrão arbitrária).  
2. Recria `org_cost_centers` com `id`, `branch`, `code`, `source`, `UNIQUE(branch,code)`, `CHECK branch IN ('01','02')` e `branch = unit_code`.  
3. Recria FKs compostas e uniques:
   - responsabilidades ativas: `(exercise_id, module, user_sub, unit_id, cost_center_id)`
   - planos CAPEX: `(exercise_id, unit_id, cost_center_id)`

Aplicar somente com:

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin planejamento-orcamentario
```

**Não** usar `reset`.

---

## 4. Consulta ERP

| Item | Valor |
|------|--------|
| Fonte | `dbo.vw_fin_despesas_centro_custo` (mesma do plugin `financeiro-centro-custo`) |
| SQL | `build_centros_custo_catalog_by_branch_query` |
| Provider | `DespesasCentroCustoRepository.list_centros_custo_by_branch` |
| Endpoint | `GET /planejamento-orcamentario/org/erp-cost-centers?branch=01` |

Retorno deduplicado: `{ branch, code, description }`. Somente leitura; sem folha/colaboradores.

---

## 5. Cadastro interno a partir do ERP

`POST /planejamento-orcamentario/admin/org/cost-centers/from-erp`

```json
{ "branch": "01", "code": "1234", "unit_id": "01" }
```

Valida filial, existência no ERP, impede duplicidade `(branch, code)`, grava descrição do ERP (`source=erp`), audita `org_cost_center.from_erp`. Não aceita descrição livre.

---

## 6. Compatibilidade CAPEX

Sem mudança de regras funcionais de workflow/consolidação. Ajustes técnicos:

- resolução de CC por filial + código;  
- planos/investimentos/responsabilidades isolados por filial;  
- joins de consolidação em `(unit_id, cost_center_id)`;  
- `resolve` de plano aceita `unit_id` opcional.

---

## 7. Testes

- `tests/unit/planejamento_orcamentario/test_org_cost_centers_branch_aware.py`  
- regressão da suíte `tests/unit/planejamento_orcamentario/`  
- SQL catálogo: `tests/test_financeiro_despesas_centro_custo_filtros_sql.py`

---

## 8. Pendências

- Frontend / select admin ERP (fora do escopo 3A.1).  
- Módulo Pessoal (3A.0+).  
- Cobertura da view de despesas pode não listar todos os CCs orçamentários (já documentado em 3A.0 / D-PE-4).
