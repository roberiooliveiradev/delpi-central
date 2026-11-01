# 33 — VISTA/TV DI-3.3 AUTONOMOUS DATA BINDING EXECUTION REPORT

**Data:** 2026-10-31 · **Commit:** `7bf273b8e5` · **Deploy:** `srv-api`
imagem `sha256:adc1ad699184`

## Root cause — `ROOT_CAUSE_PROVEN`

Recipes materializam blocos `kpi_view`/`chart_view`/`table_view`
(visuais, sem binding). As variantes `data_*` carregam bindings.
A cadeia `suggest_change → plan → ops` nunca consultava
`TvDataRouteSuggestService` — nenhuma etapa canônica de vinculação
existia no fluxo de composição.

## Correção — `REUSE_DECISION = EXTEND`

`suggest_change`: após ops materializadas (recipe ou planner-ready),
quando há blocos de dados no payload, consulta
`TvDataRouteSuggestService.suggest` (descoberta canônica, read-only)
e anexa `bindingPlan`:

- `state`: `RESOLVED` (1 candidato) / `NEEDS_SOURCE_SELECTION`
  (>1, ambiguidade preservada — nunca pick silencioso) /
  `NEEDS_CONTEXT` (0 — insuficiência tipada honesta).
- `dataBlockOps`: contagem de blocos de dados na proposta.
- `dataRouteCandidates`: projeção slim (operationId/path/category/
  description/method) — sem fabricar métricas ou DataModels.

## Estado de binding observado

- "crie um painel para acompanhar produtividade e problemas da
  fábrica" → `ready` + 3 data ops + 6 candidatos →
  `NEEDS_SOURCE_SELECTION` (OEE produção/realizado/meta/visão geral
  etc. — ambiguidade de negócio real, seleção preservada).
- "quero acompanhar vendas e metas" → `ready` + 2 ops + 8 candidatos →
  `NEEDS_SOURCE_SELECTION`.

## Testes

**2413/2413 PASS** — `test_design_intelligence_di33.py` 4 casos
(bindingPlan presente, ambiguidade não resolvida silenciosamente,
ops+plan juntos, heading-only sem plan). DI-3.1 test atualizado
(produtividade agora tem marcador canônico DI-3.2).

## Limitações residuais honestas

- `bindingPlan` classifica a seleção — a operação `upsert_block`
  com `bindings` concretos exige seleção de fonte pelo usuário ou
  por fluxo autorizado de `data_block`/`data_model` ops (operações
  tipadas existentes — não duplicadas aqui).
- Preview de pixels fora do escopo MCP — host text-only (registrado,
  não alegado).

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel para acompanhar
    produtividade e problemas da fábrica","dry_run":true})
```
→ `status="ready"`, `ops` tipadas, `bindingPlan.state=
NEEDS_SOURCE_SELECTION` + `dataRouteCandidates` — sem persistência.
Seleção final: `analyze.data_block_preview` /
`execute.apply_mutation` com a fonte escolhida pelo usuário.

## Veredito

**`DI33_ACCEPTANCE = PASS`** — composição agora carrega plano de
binding verificável classificado honestamente; seleção de fonte
ambígua preservada (invariante de segurança semântica); seis verbos
e owners canônicos intactos.
