# 30 — Fase 3B.1.1: cargo livre nas linhas de Pessoal

**Data:** 2026-08-05  
**Branch:** `feat/planejamento-orcamentario`  
**Tipo:** backend — substitui catálogo de cargos por `position_name` textual  
**Migration:** `V009__replace_personnel_position_catalog_with_free_text.sql`  
**Pré-requisito:** Fase 3B.1 (`V008`) aplicada; **não** editar V008; **não** usar `reset`

---

## Decisão funcional

Não haverá catálogo administrativo de cargos nem busca no ERP.

O usuário informa o **nome do cargo** diretamente em cada linha do plano, por exemplo:

- Operador de Produção  
- Líder de Produção  
- Analista de Qualidade  
- Supervisor de Logística  

A decisão de catálogo da Fase 3B.1 (`personnel_positions` + `position_id`) fica **substituída** por esta fase.

---

## Migration V009

| Passo | Ação |
|-------|------|
| 1 | `ADD COLUMN position_name VARCHAR(200)` (nullable até backfill) |
| 2 | Backfill: `position_name = BTRIM(personnel_positions.name)` via `position_id` |
| 3 | Guard: `RAISE EXCEPTION` se alguma linha ficar sem nome |
| 4 | `NOT NULL` + check trim não vazio / `char_length <= 200` |
| 5 | Drop FK/índices/`position_id` |
| 6 | Unique ativo: `(plan_id, lower(BTRIM(position_name)))` onde `is_active` |
| 7 | `DROP TABLE personnel_positions` |

Limite documentado: **200 caracteres** após trim. Acentos e caracteres comuns são preservados (sem slug/código interno).

---

## Contrato da linha

```json
{
  "position_name": "Operador de Produção",
  "headcount_dec_2025": 20,
  "headcount_oct_2026": 22,
  "headcount_forecast": 23,
  "headcount_dec_2027": 25,
  "observations": null
}
```

Respostas retornam `position_name` (nunca `position_id`). Mantidos: rascunho parcial, headcounts ≥ 0, versionamento otimista, arquivamento lógico, totais calculados, isolamento filial/CC, `module = personnel`.

---

## Duplicidade

Duas linhas ativas no **mesmo plano** com o mesmo cargo (case-insensitive + trim) → `budget_personnel_line_duplicate_position`.

O mesmo nome é permitido em outro centro de custo, outra filial ou outro exercício.

---

## Remoção do catálogo

Removidos endpoints, use cases, schemas, contratos e permissão:

- `/personnel/positions`
- `/admin/personnel/positions`
- `planejamento-orcamentario.personnel.positions.manage`

Mantidos:

- `planejamento-orcamentario.personnel.view`
- `planejamento-orcamentario.personnel.edit`

Manifesto SemVer: **0.2.2** (pronto para importação manual; sem auto-import/atribuição nesta fase).

---

## Erros novos / ajustados

| Código | Uso |
|--------|-----|
| `budget_personnel_position_name_required` | vazio / só espaços |
| `budget_personnel_position_name_too_long` | > 200 caracteres |
| `budget_personnel_line_duplicate_position` | duplicidade no plano |

Demais erros de plano, responsabilidade, headcount e concorrência permanecem.

---

## Fora de escopo

Frontend, workflow, consolidação, exportação, salários/encargos.

---

## Validação (entrega)

| Gate | Resultado |
|------|-----------|
| `up --plugin planejamento-orcamentario` | V009 aplicada sem reset (só pendentes) |
| Schema | sem `personnel_positions`; `position_name VARCHAR(200) NOT NULL`; unique `uq_po_personnel_plan_line_active_position_name` |
| `pytest tests/unit/planejamento_orcamentario/` | **140 passed** (CAPEX + Pessoal + V009/arquivo + sandbox de backfill) |
| Health API | HTTP 200 `{"status":"online"}` |
| Migrations | V001–V009 APLICADAS |
