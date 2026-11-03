# 39 — VISTA/TV DI-3.6.3 UNIFIED ELIGIBILITY & MULTI-INTENT REPORT

**Data:** 2026-10-31 · **Commit:** `b9acf9210b` · **Deploy:** `srv-api`
imagem `sha256:d1c444482143`

## RC-A — eligibility bypass — `ROOT_CAUSE_PROVEN` + `CONTRACT_DRIFT`

`download_audit_5s_nc_attachment`/`download_audit_5s_response_attachment`
declaravam `metaShape=scalar` + `["kpi","auto"]` no catálogo derivado
— metadado incorreto promovia downloads/binários a KPI.

**Fix (`EXTEND`):** `_eligible()` unificado — non-GET +
`document_export` + prefixos `download_`/`export_`/`upload_`/`import_`
(binário/anexo por contrato de operação) fora de **todos** os
caminhos: query bruta, query de propósito e fallback de catálogo.

## RC-B — Kaizen coverage — `ROOT_CAUSE_PROVEN`

"resultados Kaizen" → `unsupported`: gate de score ≥8.0 barrava o
top Kaizen (6.0); score isolado não separa domínio real de
gibberish (10.0).

**Fix:** gate semântico = score ≥6.0 + domínio real ≠"other" +
`token_hit` (token forte da mensagem presente nos top-3). Kaizen
compõe via `TV_KPI_SERIES_TABLE` genérica; `xyzzy foobar` segue
`unsupported`.

## RC-C — multi-intent — `ROOT_CAUSE_PROVEN`

"produtividade + 5S" → ranking top-14 todo `quality` (produção
cortada pelo limit); âncora só quality; cap 8 destruía adições por
ordem de inserção.

**Fix:** per-token `suggest` (≤4 tokens fortes, top-3) merge em
`qualified` + union dedupe(propósito+bruta) + sort por score antes
do cap — **ambos** os objetivos preservados:
`get_production_factory_shifts` + `list_audit_5s_*`/`nonconformities`.

## Antes/depois

| Cenário | Antes | Depois |
|---|---|---|
| 5S KPI | `download_audit_5s_*` | `audit_5s_summary`, `nonconformity_series` |
| Kaizen | `unsupported`, ops=[] | `proposal` + kaizen sources |
| Produção+5S | só quality | produção E qualidade |
| Gibberish | proposal (permissivo) | `unsupported` honesto |

## Testes

**2449/2449 PASS** — `test_design_intelligence_di363.py` 6 casos
(downloads fora, Kaizen compõe, multi-intent ambos domínios,
gibberish unsupported, 5S presente, produção limpa).

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel de produtividade e
    auditorias 5S da fábrica","dry_run":true})
```
→ `ready` + ops + `bindingPlan.blocks[]` com fontes de **ambos**
domínios; 5S isolado sem downloads; Kaizen explícito compõe;
sem persistência.

## Veredito

**`DI363_ACCEPTANCE = PASS`** — elegibilidade unificada em todos os
caminhos, cobertura Kaizen por gate semântico, multi-intent com
preservação de objetivos citados.
