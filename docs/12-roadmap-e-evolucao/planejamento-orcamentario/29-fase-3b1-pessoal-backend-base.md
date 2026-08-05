# 29 — Fase 3B.1: Orçamento de Pessoal (backend base)

**Data:** 2026-08-05  
**Branch:** `feat/planejamento-orcamentario`  
**Tipo:** backend — plano por filial/CC + linhas de headcount  
**Migration:** `V008__create_personnel_budget_base.sql`

> **Atualização (Fase 3B.1.1):** a decisão de **catálogo administrativo de cargos** (`personnel_positions` + `position_id` + permissão `personnel.positions.manage`) foi **substituída** por cargo digitado livremente (`position_name`). Ver [`30-fase-3b1-1-cargo-livre.md`](./30-fase-3b1-1-cargo-livre.md) e migration `V009`. O histórico abaixo descreve o que a V008 criou; o modelo vigente pós-V009 não usa mais o catálogo.

---

## Decisões

| Tema | Decisão |
|------|---------|
| Identidade do plano | `exercise_id + unit_id + cost_center_id` |
| Conteúdo das linhas | uma linha por **cargo** |
| Cargos | **texto livre** na linha (`position_name`) — **não** catálogo admin e **não** ERP *(desde 3B.1.1; V008 ainda criava catálogo, removido na V009)* |
| ERP | continua só para **centros de custo** (Fase 3A.1) |
| Status do plano | somente `draft` (sem workflow nesta fase) |
| Coluna «Previsto» | campo `headcount_forecast` — **nomenclatura original** preservada; sem mensalização |
| Totais | calculados na resposta; **não** persistidos |
| Workflow / consolidação / salários / anexos | **fora** desta fase |

### Âncoras de headcount (planilha)

| Coluna planilha | Campo técnico |
|-----------------|---------------|
| Dez/2025 | `headcount_dec_2025` |
| Out/2026 | `headcount_oct_2026` |
| Previsto | `headcount_forecast` |
| Dez/2027 | `headcount_dec_2027` |

Inteiros ≥ 0; `NULL` permitido (rascunho parcial); zero permitido.

---

## Tabelas (V008 — histórico)

- `personnel_positions` — catálogo *(removido na V009)*  
- `personnel_plans` — `UNIQUE(exercise_id, unit_id, cost_center_id)`; FK composta para `org_cost_centers(branch, code)`  
- `personnel_plan_lines` — na V008: unique ativo `(plan_id, position_id)`; na V009: `position_name` + unique `(plan_id, lower(BTRIM(position_name)))`  

Também: `budget_responsibilities.module` passa a aceitar `personnel`.

---

## Endpoints (vigentes pós-3B.1.1)

| Método | Path |
|--------|------|
| POST | `/personnel/plans/resolve` |
| GET | `/personnel/plans` · `/personnel/plans/{id}` |
| POST | `/personnel/plans/{plan_id}/lines` |
| PUT | `/personnel/lines/{line_id}` (`version` obrigatório; body com `position_name`) |
| POST | `/personnel/lines/{line_id}/archive` |

Endpoints de catálogo `/personnel/positions` e `/admin/personnel/positions` foram **removidos** na 3B.1.1.

Conflito de versão → HTTP 409 `budget_personnel_line_version_conflict`.

---

## Permissões (manifesto — sem auto-import/atribuição)

- `planejamento-orcamentario.personnel.view`
- `planejamento-orcamentario.personnel.edit`

A permissão `planejamento-orcamentario.personnel.positions.manage` foi **removida** na 3B.1.1.

---

## Responsabilidades

Mesmo mecanismo: `module = personnel` + exercício + usuário + filial + centro de custo.  
CAPEX permanece `module = capex`.

---

## Validação (na entrega da 3B.1)

| Gate | Resultado |
|------|-----------|
| `run_plugins_migrations.py status --plugin planejamento-orcamentario` | V001–V008 APLICADAS (sem reset) |
| Inspeção DDL | tabelas, FKs compostas, unique ativos, check `module IN (capex, personnel)` |
| `pytest tests/unit/planejamento_orcamentario/` | 144 passed |
| Health API | HTTP 200 / healthy |

Validação vigente após cargo livre: ver [`30-fase-3b1-1-cargo-livre.md`](./30-fase-3b1-1-cargo-livre.md) (V001–V009).

---

## Fora de escopo

Frontend, workflow, submissão, aprovação, anexos, notificações, salários, encargos, benefícios, exportação, consolidação.
