# 31 — VISTA/TV DI-3.1 MCP COMPOSITION INTEGRATION EXECUTION REPORT

**Data:** 2026-10-31 · **Commit:** `a66f66164d` · **Deploy:** `srv-api`
imagem `sha256:afe3ecbb5838`

## Root cause — `ROOT_CAUSE_PROVEN`

Pipeline real do `analyze.intent_materialization`:

`analyze → suggest_change → PresentationCommandPlannerService.plan →
PresentationSuggestOpsService.materialize`

O materialize só casa **capabilities atômicas** (`add_kpi_from_route`
etc.). Pedidos amplos `COMPOSE_SLIDE` sem marcador de recipe/caixila
→ `ops=[]` → `clarification` (contexto faltando) ou `not_command`/
`unsupported` (contexto presente, sem match). O ChatGPT reproduziu
exatamente isso: contexto completo + intenção reconhecida + `ops=[]`.

## Correção — `REUSE_DECISION = EXTEND`

`suggest_change` (dispatch): quando `designIntent == COMPOSE_SLIDE`
e o plano retorna `unsupported`/`not_command`, aplica
`PresentationRecipeService.resolve_from_nl` → `ops_for_recipe`:

- recipe match → `status=ready` + ops tipadas + `recipeId` +
  `matchedCapabilityKeys=["recipe:..."]`.
- sem match → `status=unsupported` + `compositionHints` (ids de
  recipes candidatas) — gap tipado honesto em vez de `not_command`
  sem contexto útil.

`PresentationSuggestOpsService`/`PresentationRecipeService` são os
owners existentes — nenhum engine/planner/registry novo.

## Defeito upstream adicional resolvido — `EXECUTION_DRIFT`

`3bf75b7e94` (Task36 FrontA) reescrevia **todo** `error_kind=
validation` para `ARGUMENT_VALIDATION` em `tool_bridge._error_result`
— engolia códigos de domínio (`INVALID_CHANGE`, `PROPOSAL_NOT_FOUND`,
`data_model.migration_conflict`). Corrigido: rewrite só para códigos
genéricos (`VALIDATION_ERROR`/vazio/`ARGUMENT_VALIDATION`); códigos
de domínio passam verbatim com `recoverable=true`.

## Testes

- `test_design_intelligence_di31.py`: 7 casos (recipe→ready+ops,
  hints em unsupported, clarificação legítima preservada, KPI route
  selection preservada, advisory, viewer denial).
- B4/B5 stale assertions `VALIDATION_ERROR`→`ARGUMENT_VALIDATION`.
- Focado: **52/52**; suite completa: **2398/2398 PASS** (~2389+9
  novos fixes).

## Produção

`srv-api` · merge contendo `a66f66164d` · imagem `afe3ecbb5838` ·
container **Up** · OpenAPI 6 `vista_*` · rollback: `git revert
a66f66164d`.

## Veredito

**`DI31_ACCEPTANCE = PASS`** — pedidos amplos com recipe reconhecível
agora materializam ops; pedidos sem match recebem `unsupported` +
`compositionHints` tipados; domínio e seis verbos preservados; sem
mutações durante proposta. Pendência externa de canal humano A5
(doc 25) não relacionada a este fix permanece.
