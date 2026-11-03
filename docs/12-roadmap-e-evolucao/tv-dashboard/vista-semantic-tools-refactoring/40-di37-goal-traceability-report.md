# 40 — VISTA/TV DI-3.7 GOAL TRACEABILITY & BINDING CLOSURE REPORT

**Data:** 2026-11-02 · **Commit:** `0df042f911` · **Deploy:** `srv-api`
imagem `sha256:18f9c815f7dc`

## Root cause — `ROOT_CAUSE_PROVEN`

- `interpretedGoals`/`ignoredGoals` existiam no contrato mas nunca
  eram populados — união de candidatos sem vínculo objetivo→bloco.
- Fontes cross-domain (Kaizen em produtividade+5S) entravam por
  associação de categoria ampla (`quality` compartilhada com
  auditorias) — associação por categoria não é justificativa.
- O score-floor misturava escalas de queries distintas e cortava
  cobertura de domínio citado.

## Correção — `EXTEND` (owner: `suggest_change`/bindingPlan +
queries multi-intent DI-3.6.3)

- **`goal_map`** por token forte (≤4, variantes morfológicas
  `tok`/`tok.rstrip("s")`/`tok+indicador`/`tok+parceiro`) —
  `{operationIds, categories}` via `suggest` canônico.
- **`_goals_of`** — associação estrita: operationId nos opIds do
  objetivo **ou** token presente no oid. Categoria sozinha não
  justifica.
- **`justified` filter** — candidato sem objetivo é descartado
  quando há justificados; floor de score isenta goal-justificados.
- **Payload** — `interpretedGoals` `[{goal, categories, status}]`,
  `ignoredGoals`, `servesGoals` por bloco, `goals` por candidato.

## Evidência — "produtividade e auditorias 5S"

| Antes | Depois |
|---|---|
| `interpretedGoals=[]`, `ignoredGoals=[]` | `auditorias`+`produtividade`+`fabrica` → `COVERED` |
| chart: `kaizen_savings` injustificado | chart: `audit_5s_summary_series` (objetivo `auditorias`) |
| blocos sem papel declarado | `kpi_view`/`table_view` servem ambos os objetivos |

5S isolado: transformômetro fora; table `conformidades`→NC lists.
Kaizen isolado: objetivo `kaizen`→séries/records justificados.

## Testes

**2455/2455 PASS** — `test_design_intelligence_di37.py` 6 casos
(multi-intent goals, servesGoals, kaizen exige goal, 5S-only,
single-intent, campo goals); di36 assertion alinhada.

## Resíduos honestos

- `dataReadiness` segue `pending_source_selection` — binding final
  exige `data_block_preview`/DataModel (residual contratual).
- `E2E_PREVIEW = PENDING` — preview visual exige homologação
  autorizada; evidência de serviço apenas.

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel de produtividade e
    auditorias 5S da fábrica","dry_run":true})
```
→ `interpretedGoals` populado + `ignoredGoals` + `servesGoals`
por bloco + `goals` por candidato — kaizen/transformômetro ausentes
sem objetivo correspondente; sem persistência.

## Veredito

**`DI37_ACCEPTANCE = PASS`** —
`GOAL_TRACEABILITY_VERIFIED` + `SOURCE_SELECTION_VERIFIED`;
`BINDING_RESOLUTION_VERIFIED` e `PREVIEW_VERIFIED` seguem
condicionados ao canal autorizado de homologação.
