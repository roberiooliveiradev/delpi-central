# 38 — VISTA/TV DI-3.6.2 SEMANTIC BOUNDARY & INTENT COVERAGE REPORT

**Data:** 2026-10-31 · **Commit:** `35faceba86` · **Deploy:** `srv-api`
imagem `sha256:a3c7c82f63d6`

## Root cause A — `ROOT_CAUSE_PROVEN`

`_anchor_ok` usava o score da query de **propósito** (sufixos
"série"/"indicador"), não o da query bruta — cross-domain com
score alto no sufixo voltava: `get_openapi_diff`,
`commercial_rol_series`, `transformometro`, 5S/Kaizen.

**Fix:** `bare_scores` map (operationId→score da mensagem original);
âncora de categorias ≥0.7; domínio secundário só por bare-score
≥0.5. Produção limpa: `appointments_series`, `unproductive_hours`,
`eficiencia_series`, `oee_series`; 5S/Kaizen fora.

## Root cause B — `ROOT_CAUSE_PROVEN`

"auditorias 5S" → `unsupported`: nenhum marker de recipe match e o
fallback terminava em `unsupported`+hints sem verificar cobertura
do catálogo.

**Fix:** quando a query bruta produz fontes qualificadas (top ≥8.0
+ domínio real ≠"other"), compõe por recipe **genérica** do shape
dominante — `TV_TABLE_FOCUS` para listas (5S/NCs),
`TV_KPI_SERIES_TABLE` para multi-indicador — `proposal`+ops, sem
marker inventado, sem engine.

## Antes/depois

| Cenário | Antes | Depois |
|---|---|---|
| Produção chart | `commercial_rol`, `transformometro`, `5s_summary_series`, `kaizen_*` | `appointments_series`, `unproductive_hours`, `eficiencia_series`, `oee_series` |
| Produção table | dominada por 5S | `inspecoes`, `supplies_shipments` (fronteira legítima) |
| 5S explícito | `unsupported`, ops=[] | `proposal` + ops + audit-domain candidates |
| Vendas | OK | inalterado |

## Testes

**2443/2443 PASS** — `test_design_intelligence_di362.py` 7 casos
(5S/Kaizen fora de produção, 5S explícito compõe, Kaizen explícito
mantido, vendas inalterado); fixtures di31/di36 atualizadas ao novo
contrato de `proposal`.

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel de auditorias 5S e não
    conformidades","dry_run":true})
```
→ `status=proposal` + `ops` + `bindingPlan` com fontes audit
(nonconformities/5S). Produção: só fontes produção. Vendas:
comercial. Sem persistência.

## Veredito

**`DI362_ACCEPTANCE = PASS`** — boundary semântico provado por
bare-score e cobertura de intenção por recipe genérica condicionada
a cobertura real do catálogo.
